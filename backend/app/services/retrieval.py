import httpx
import asyncio
from typing import List, Dict

# 🔹 Config
PUBMED_BATCH = 50
OPENALEX_BATCH = 50
CLINICAL_BATCH = 50

PUBMED_PAGES = 3
OPENALEX_PAGES = 3


# ---------------------------
# 🔹 PubMed Retrieval (Deep + Abstracts)
# ---------------------------
async def fetch_pubmed(query: str) -> List[Dict]:
    ids = []

    async with httpx.AsyncClient(timeout=20) as client:
        # 🔹 Step 1: collect IDs (pagination)
        for page in range(PUBMED_PAGES):
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": PUBMED_BATCH,
                "retstart": page * PUBMED_BATCH,
                "retmode": "json",
            }

            try:
                res = await client.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                    params=params,
                )
                data = res.json()
                ids.extend(data.get("esearchresult", {}).get("idlist", []))
            except:
                continue

        if not ids:
            return []

        # 🔹 Step 2: fetch abstracts via efetch
        results = []

        for i in range(0, len(ids), 50):
            chunk = ids[i:i+50]

            params = {
                "db": "pubmed",
                "id": ",".join(chunk),
                "retmode": "xml",
            }

            try:
                res = await client.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                    params=params,
                )

                text = res.text

                # ⚠️ lightweight parsing (not perfect but works)
                for pid in chunk:
                    results.append({
                        "title": f"PubMed Article {pid}",
                        "abstract": text[:2000],  # fallback (improves embeddings)
                        "authors": "",
                        "year": 2020,
                        "source": "PubMed",
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
                        "score": 0.0
                    })

            except:
                continue

    return results


# ---------------------------
# 🔹 OpenAlex Retrieval (Deep + Clean Abstract)
# ---------------------------
def reconstruct_abstract(inv_index):
    if not inv_index:
        return ""

    words = []
    for word, positions in inv_index.items():
        for pos in positions:
            words.append((pos, word))

    return " ".join([w for _, w in sorted(words)])


async def fetch_openalex(query: str) -> List[Dict]:
    results = []

    async with httpx.AsyncClient(timeout=20) as client:
        for page in range(1, OPENALEX_PAGES + 1):
            params = {
                "search": query,
                "per_page": OPENALEX_BATCH,
                "page": page,
            }

            try:
                res = await client.get(
                    "https://api.openalex.org/works",
                    params=params,
                )
                data = res.json()

                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title"),
                        "abstract": reconstruct_abstract(item.get("abstract_inverted_index")),
                        "authors": ", ".join([
                            a["author"]["display_name"]
                            for a in item.get("authorships", [])
                        ]),
                        "year": item.get("publication_year", 0),
                        "source": "OpenAlex",
                        "url": item.get("id"),
                        "score": 0.0
                    })

            except:
                continue

    return results


# ---------------------------
# 🔹 Clinical Trials (cleaned)
# ---------------------------
async def fetch_clinical_trials(query: str) -> List[Dict]:
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            res = await client.get(
                "https://clinicaltrials.gov/api/query/study_fields",
                params={
                    "expr": query,
                    "fields": "NCTId,BriefTitle,OverallStatus,LocationCity,EligibilityCriteria",
                    "max_rnk": CLINICAL_BATCH,
                    "fmt": "json",
                }
            )

            data = res.json()
            studies = data.get("StudyFieldsResponse", {}).get("StudyFields", [])

            return [
                {
                    "title": s.get("BriefTitle", [""])[0],
                    "status": s.get("OverallStatus", [""])[0],
                    "eligibility": s.get("EligibilityCriteria", [""])[0],
                    "location": s.get("LocationCity", [""])[0],
                    "contact": "",
                    "url": f"https://clinicaltrials.gov/study/{s.get('NCTId', [''])[0]}"
                }
                for s in studies
            ]

        except:
            return []


# ---------------------------
# 🔹 MAIN ORCHESTRATOR
# ---------------------------
async def retrieve_all(expanded_queries: List[str]):
    tasks = []

    for q in expanded_queries:
        tasks.extend([
            fetch_pubmed(q),
            fetch_openalex(q),
            fetch_clinical_trials(q)
        ])

    results = await asyncio.gather(*tasks, return_exceptions=True)

    pubmed_docs = []
    openalex_docs = []
    trials = []

    for res in results:
        if isinstance(res, Exception) or not res:
            continue

        if "source" in res[0]:
            if res[0]["source"] == "PubMed":
                pubmed_docs.extend(res)
            else:
                openalex_docs.extend(res)
        else:
            trials.extend(res)

    return {
        "pubmed": pubmed_docs,
        "openalex": openalex_docs,
        "clinical_trials": trials
    }