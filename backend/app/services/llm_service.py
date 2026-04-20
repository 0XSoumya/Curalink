from groq import Groq
from app.core.config import settings
import json
import os
import re

client = Groq(api_key=settings.GROQ_API_KEY)

# 🔥 Turn OFF debug
DEBUG = False


# ---------------------------
# 🔹 Utils
# ---------------------------

def clean_json_response(response: str):
    response = response.strip()

    if "```" in response:
        response = re.sub(r"```.*?\n", "", response)
        response = response.replace("```", "")

    match = re.search(r"\{.*\}", response, re.DOTALL)
    if match:
        return match.group(0)

    return response


def call_llm(prompt: str, model: str = "llama-3.1-8b-instant"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content


def load_prompt(name: str):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(base_dir, "prompts", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------
# 🔹 Parser
# ---------------------------

def parse_input(query: str, disease: str = None, location: str = None):
    disease = disease or ""

    prompt = f"""
Extract structured medical query information.

Return STRICT JSON:
{{
  "disease": "...",
  "query": "...",
  "location": "..."
}}

Input:
Query: {query}
Disease: {disease}
Location: {location}
"""

    response = call_llm(prompt)

    try:
        return json.loads(clean_json_response(response))
    except:
        return {
            "disease": disease,
            "query": query,
            "location": location,
        }


# ---------------------------
# 🔹 Query expansion
# ---------------------------

def expand_query(query: str, disease: str):
    disease = disease or ""

    prompt = f"""
Generate 4 search queries combining disease and intent.

Return ONLY JSON:
["query1", "query2", "query3", "query4"]

Disease: {disease}
Query: {query}
"""

    response = call_llm(prompt)

    try:
        return json.loads(clean_json_response(response))
    except:
        return [f"{query} {disease}"]


# ---------------------------
# 🔹 Follow-up detection
# ---------------------------

def detect_followup(current_query, previous_query, disease, chat_history):
    disease = disease or ""

    prompt_template = load_prompt("followup.txt")

    history_text = ""
    for h in chat_history[-3:]:
        history_text += f"Q: {h.get('query')}\nA: {h.get('response')}\n"

    prompt = f"""
{prompt_template}

Previous query: {previous_query}
Current query: {current_query}
Disease: {disease}

Chat history:
{history_text}
"""

    response = call_llm(prompt)

    try:
        return json.loads(clean_json_response(response))
    except:
        return {
            "is_followup": "no",
            "is_topic_shift": "no"
        }


# ---------------------------
# 🔥 GROUNDED REASONING ENGINE
# ---------------------------

def generate_response(query, disease, docs, trials):
    disease = disease or ""

    # 🔹 Format docs
    doc_blocks = []
    for i, d in enumerate(docs[:10]):
        doc_blocks.append(f"""
[Paper {i+1}]
Title: {d.get('title')}
Year: {d.get('year')}
Source: {d.get('source')}
Abstract: {d.get('abstract')}
""")

    docs_text = "\n".join(doc_blocks)

    # 🔹 Trials
    trial_blocks = []
    for i, t in enumerate(trials[:5]):
        trial_blocks.append(f"""
[Trial {i+1}]
Title: {t.get('title')}
Status: {t.get('status')}
Location: {t.get('location')}
""")

    trials_text = "\n".join(trial_blocks)

    prompt = f"""
You are a STRICT medical research assistant.

Rules:
- ONLY use provided papers
- DO NOT use outside knowledge
- If missing info → say "insufficient evidence"
- Every insight MUST cite [Paper X]
- Be concise and specific

-------------------------------------

Disease: {disease}
Query: {query}

Research Papers:
{docs_text}

Clinical Trials:
{trials_text}

-------------------------------------

Return STRICT JSON:

{{
  "overview": "...",
  "research_insights": [
    "... [Paper 1]",
    "... [Paper 2, Paper 3]"
  ],
  "clinical_trials": ["..."]
}}
"""

    response = call_llm(prompt, model="llama-3.3-70b-versatile")

    try:
        parsed = json.loads(clean_json_response(response))
    except:
        parsed = {
            "overview": "Unable to generate structured response.",
            "research_insights": [],
            "clinical_trials": [],
        }

    # 🔹 Sources
    sources = []
    for d in docs[:8]:
        sources.append({
            "title": d.get("title"),
            "authors": d.get("authors", "Unknown"),
            "year": d.get("year"),
            "platform": d.get("source"),
            "url": d.get("url"),
            "snippet": (d.get("abstract") or "")[:300]
        })

    parsed["sources"] = sources
    parsed["clinical_trials"] = trials[:5]

    return parsed