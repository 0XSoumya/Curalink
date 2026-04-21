import httpx
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict

# 🔹 Config (Optimized for ~180-200 docs total across 6 expanded queries)
PUBMED_BATCH = 15     # 15 docs * 6 queries = 90 max
OPENALEX_BATCH = 15   # 15 docs * 6 queries = 90 max
CLINICAL_BATCH = 10   # 10 docs * 6 queries = 60 max

PUBMED_PAGES = 1      # Kept at 1 to prevent over-fetching
OPENALEX_PAGES = 1    # Kept at 1 to prevent over-fetching


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
                "sort": "relevance" # 🔥 Ensures we get the best matches, not just the newest
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

        # 🔹 Step 2: fetch abstracts via efetch and parse XML properly
        results = []

        # Chunk size matches our batch size now, so this will only loop once
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

                # Parse the XML response
                root = ET.fromstring(res.text)

                for article in root.findall(".//PubmedArticle"):
                    try:
                        # Extract PMID
                        pmid_elem = article.find(".//PMID")
                        if pmid_elem is None:
                            continue
                        pmid = pmid_elem.text

                        # Extract Title
                        title_elem = article.find(".//ArticleTitle")
                        title = title_elem.text if title_elem is not None else f"PubMed Article {pmid}"

                        # Extract Abstract
                        abstract_elements = article.findall(".//AbstractText")
                        abstract_text = " ".join([elem.text for elem in abstract_elements if elem.text])
                        
                        # Skip if there's no useful text for the LLM to reason over
                        if not abstract_text:
                            continue

                        # Extract Year
                        year_elem = article.find(".//PubDate/Year")
                        year = int(year_elem.text) if year_elem is not None else 2020

                        # Extract Authors (First 3 for brevity)
                        authors = []
                        for author in article.findall(".//Author")[:3]:
                            last_name = author.find("LastName")
                            initials = author.find("Initials")
                            if last_name is not None and initials is not None:
                                authors.append(f"{last_name.text} {initials.text}")
                        
                        author_str = ", ".join(authors) + (" et al." if len(article.findall(".//Author")) > 3 else "")

                        results.append({
                            "title": title,
                            "abstract": abstract_text,
                            "authors": author_str,
                            "year": year,
                            "source": "PubMed",
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            "score": 0.0
                        })
                    except Exception:
                        continue

            except Exception as e:
                print(f"Failed to fetch or parse PubMed chunk: {e}")
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

    # 🔥 Slice the final arrays to guarantee we never exceed 90 per source (keeping total under 200)
    return {
        "pubmed": pubmed_docs[:90],
        "openalex": openalex_docs[:90],
        "clinical_trials": trials[:60]
    }