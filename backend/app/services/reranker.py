import voyageai
from typing import List, Dict

# Initialize client (uses VOYAGE_API_KEY from env)
client = voyageai.Client()


def process_documents(query: str, pubmed_docs: List[Dict], openalex_docs: List[Dict]):
    # Combine docs
    docs = pubmed_docs + openalex_docs

    if not docs:
        return [], []

    # Prepare text for reranking
    texts = [
        (doc.get("title") or "") + " " + (doc.get("abstract") or "")
        for doc in docs
    ]

    try:
        # 🔥 Voyage reranking
        result = client.rerank(
            query=query,
            documents=texts,
            model="rerank-lite-1"
        )

        ranked_docs = []

        for r in result.results:
            doc = docs[r.index]
            doc["rerank_score"] = r.relevance_score
            ranked_docs.append(doc)

        ranked_docs = sorted(
            ranked_docs,
            key=lambda x: x.get("rerank_score", 0),
            reverse=True
        )

    except Exception as e:
        print("❌ Rerank failed:", e)
        # fallback → no rerank
        ranked_docs = docs

    top_docs = ranked_docs[:8]
    buffer_docs = ranked_docs[8:20]

    return top_docs, buffer_docs