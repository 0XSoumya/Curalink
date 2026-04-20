from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from typing import List, Dict

# 🔹 Models
embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


# ---------------------------
# 🔹 Deduplication (Improved)
# ---------------------------
def deduplicate_docs(docs: List[Dict]):
    unique = []
    seen = []

    for doc in docs:
        title = (doc.get("title") or "").lower()

        if not title:
            continue

        duplicate = False

        for t in seen:
            if fuzz.token_sort_ratio(title, t) > 92:
                duplicate = True
                break

        if not duplicate:
            seen.append(title)
            unique.append(doc)

    return unique


# ---------------------------
# 🔹 Embedding Filter
# ---------------------------
def embedding_filter(query: str, docs: List[Dict], top_k=60):
    texts = [
        (doc.get("title") or "") + " " + (doc.get("abstract") or "")
        for doc in docs
    ]

    query_emb = embedding_model.encode([query])
    doc_embs = embedding_model.encode(texts)

    sims = cosine_similarity(query_emb, doc_embs)[0]

    for i, doc in enumerate(docs):
        doc["embedding_score"] = float(sims[i])

    return sorted(docs, key=lambda x: x["embedding_score"], reverse=True)[:top_k]


# ---------------------------
# 🔹 Cross Encoder
# ---------------------------
def rerank(query: str, docs: List[Dict]):
    pairs = [
        (query, (doc.get("title") or "") + " " + (doc.get("abstract") or ""))
        for doc in docs
    ]

    scores = cross_encoder.predict(pairs)

    for i, doc in enumerate(docs):
        doc["cross_score"] = float(scores[i])

    return docs


# ---------------------------
# 🔹 Final Ranking
# ---------------------------
def final_rank(docs: List[Dict]):
    for doc in docs:
        year = doc.get("year", 0)

        recency = 0
        if year:
            recency = min((year - 2000) / 25, 1)

        doc["final_score"] = (
            0.65 * doc.get("cross_score", 0) +
            0.25 * doc.get("embedding_score", 0) +
            0.10 * recency
        )

    return sorted(docs, key=lambda x: x["final_score"], reverse=True)


# ---------------------------
# 🔹 MAIN PIPELINE
# ---------------------------
def process_documents(query: str, pubmed_docs, openalex_docs):
    all_docs = pubmed_docs + openalex_docs

    # 🔹 Dedup
    deduped = deduplicate_docs(all_docs)

    # 🔹 Embedding filter
    filtered = embedding_filter(query, deduped)

    # 🔹 Cross-encoder rerank
    reranked = rerank(query, filtered)

    # 🔹 Final scoring
    ranked = final_rank(reranked)

    top_docs = ranked[:8]
    buffer_docs = ranked[8:20]

    return top_docs, buffer_docs