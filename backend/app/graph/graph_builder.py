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
    if not state["is_followup"] or state["is_topic_shift"]:
        state["needs_retrieval"] = True
        return state

    docs = state.get("top_docs", []) + state.get("buffer_docs", [])

    if not docs:
        state["needs_retrieval"] = True
        return state

    doc_text = ""
    for d in docs[:6]:
        doc_text += f"""
Title: {d.get('title')}
Abstract: {d.get('abstract')}
"""

    prompt = f"""
Query: {state['final_query']}

Documents:
{doc_text}

Can these answer the query?

Answer ONLY: yes or no
"""

    decision = call_llm(prompt).lower()
    state["needs_retrieval"] = "no" not in decision

    return state


async def retrieve_node(state: GraphState):
    results = await retrieve_all(state["expanded_queries"])
    state["retrieval_results"] = results
    state["clinical_trials"] = results["clinical_trials"]
    return state


def rerank_node(state: GraphState):
    top_docs, buffer_docs = process_documents(
        state["final_query"],
        state["retrieval_results"]["pubmed"],
        state["retrieval_results"]["openalex"]
    )

    state["top_docs"] = top_docs
    state["buffer_docs"] = buffer_docs

    return state


def reasoning_node(state: GraphState):
    state["final_output"] = generate_response(
        query=state["final_query"],
        disease=state["parsed"]["disease"],
        docs=state["top_docs"] + state["buffer_docs"],
        trials=state.get("clinical_trials", [])
    )
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

    def route(state: GraphState):
        return "retrieve" if state["needs_retrieval"] else "rerank"

    graph.add_conditional_edges("sufficiency", route)

    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "reasoning")
    graph.add_edge("reasoning", END)

    return graph.compile()