from langgraph.graph import StateGraph, END
from app.graph.state import GraphState

from app.services.llm_service import (
    parse_input,
    expand_query,
    generate_response,
    detect_followup,
    call_llm
)

from app.services.retrieval import retrieve_all
from app.services.reranker import process_documents


# ---------------------------
# 🔹 Nodes
# ---------------------------

def parse_node(state: GraphState):
    state["parsed"] = parse_input(
        query=state["query"],
        disease=state.get("disease"),
        location=state.get("location")
    )
    return state


def followup_node(state: GraphState):
    prev_query = state["chat_history"][-1]["query"] if state["chat_history"] else ""

    result = detect_followup(
        current_query=state["query"],
        previous_query=prev_query,
        disease=state["parsed"]["disease"],
        chat_history=state["chat_history"]
    )

    state["is_followup"] = result.get("is_followup") == "yes"
    state["is_topic_shift"] = result.get("is_topic_shift") == "yes"

    return state


def rewrite_query_node(state: GraphState):
    # Not a follow-up → use original
    if not state["is_followup"]:
        state["final_query"] = state["parsed"]["query"]
        return state

    history = ""
    for h in state["chat_history"][-3:]:
        history += f"Q: {h['query']}\nA: {h['response']}\n"

    prompt = f"""
Rewrite the query into a complete medical query.

Disease: {state['parsed']['disease']}
Chat history:
{history}

Current query:
{state['query']}

Return ONLY rewritten query.
"""

    rewritten = call_llm(prompt)
    state["final_query"] = rewritten.strip()

    return state


def expand_node(state: GraphState):
    state["expanded_queries"] = expand_query(
        query=state["final_query"],
        disease=state["parsed"]["disease"]
    )
    return state


def sufficiency_node(state: GraphState):
    # 🔥 Initialize our fallback flags
    state["retrieval_attempted"] = False 
    state["is_insufficient"] = False     

    # If not follow-up OR topic shift → retrieve
    if not state["is_followup"] or state["is_topic_shift"]:
        state["needs_retrieval"] = True
        return state

    docs = state.get("top_docs", []) + state.get("buffer_docs", [])

    # If docs exist → reuse initially
    if docs:
        state["needs_retrieval"] = False
    else:
        state["needs_retrieval"] = True

    return state


async def retrieve_node(state: GraphState):
    results = await retrieve_all(state["expanded_queries"])
    state["retrieval_results"] = results
    state["clinical_trials"] = results["clinical_trials"]
    
    # 🔥 Mark that we have hit the APIs this turn
    state["retrieval_attempted"] = True 
    return state


def rerank_node(state: GraphState):
    # If we have fresh retrieval results from the current turn
    if state.get("retrieval_results"):
        top_docs, buffer_docs = process_documents(
            state["final_query"],
            state["retrieval_results"]["pubmed"],
            state["retrieval_results"]["openalex"]
        )
        state["top_docs"] = top_docs
        state["buffer_docs"] = buffer_docs
    else:
        # FOLLOW-UP SCENARIO: We skipped retrieval, so we must re-rank 
        # the cached documents against the NEW follow-up query.
        cached_docs = state.get("top_docs", []) + state.get("buffer_docs", [])
        if cached_docs:
            top_docs, buffer_docs = process_documents(
                state["final_query"],
                cached_docs,
                []
            )
            state["top_docs"] = top_docs
            state["buffer_docs"] = buffer_docs

    return state


def reasoning_node(state: GraphState):
    docs = state.get("top_docs", []) + state.get("buffer_docs", [])

    output = generate_response(
        query=state["final_query"],
        disease=state["parsed"]["disease"],
        docs=docs,
        trials=state.get("clinical_trials", [])
    )
    
    state["final_output"] = output

    # 🔥 Check if the LLM declared insufficient evidence
    overview_text = output.get("overview", "").lower()
    insights_text = str(output.get("research_insights", [])).lower()

    if "insufficient evidence" in overview_text or "insufficient evidence" in insights_text:
        state["is_insufficient"] = True
    else:
        state["is_insufficient"] = False

    return state


# ---------------------------
# 🔹 Graph Builder
# ---------------------------

def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("parse", parse_node)
    graph.add_node("followup", followup_node)
    graph.add_node("rewrite", rewrite_query_node)
    graph.add_node("expand", expand_node)
    graph.add_node("sufficiency", sufficiency_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("reasoning", reasoning_node)

    graph.set_entry_point("parse")

    graph.add_edge("parse", "followup")
    graph.add_edge("followup", "rewrite")
    graph.add_edge("rewrite", "expand")
    graph.add_edge("expand", "sufficiency")

    # Conditional routing from sufficiency
    def route_sufficiency(state: GraphState):
        return "retrieve" if state["needs_retrieval"] else "rerank"

    graph.add_conditional_edges("sufficiency", route_sufficiency)

    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "reasoning")

    # 🔥 NEW: Conditional routing from reasoning (The Fallback Loop)
    def route_after_reasoning(state: GraphState):
        # If evidence is insufficient AND we haven't already tried a fresh retrieval this turn
        if state.get("is_insufficient") and not state.get("retrieval_attempted"):
            print("🔄 Insufficient evidence detected. Looping back to retrieve new documents...")
            return "retrieve"
        return END

    graph.add_conditional_edges("reasoning", route_after_reasoning)

    return graph.compile()