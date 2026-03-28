import streamlit as st

try:
    import wikipedia
except ImportError:
    wikipedia = None

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

import requests
import json
import re
import urllib.parse

from utils.groq_client import chat_with_groq
from utils.app_controller import AppController

class QueryEngine:

    @staticmethod
    def classify_query(query: str):
        q = query.lower()
        if any(w in q for w in ["calculate", "plus", "minus", "divided by", "times"]) or ("+" in q and "=" not in q):
            return "math"
        if any(w in q for w in ["plot", "graph", "draw", "curve"]):
            return "graph"
        if any(w in q for w in ["who is", "what is", "history of", "capital of", "define", "concept of"]):
            return "factual"
        if any(w in q for w in ["latest", "recent", "news", "today", "update", "happened"]):
            return "recent"
        if any(w in q for w in ["code", "error", "exception", "python", "java", "script", "how to build", "syntax"]):
            return "code"
        if any(w in q for w in ["paper", "research", "study", "journal", "abstract", "scientific"]):
            return "scientific"
        if any(w in q for w in ["book", "author", "literature", "novel", "write", "summary of"]):
            return "literary"
        return "complex"

    # ── Free Academic APIs ─────────────────────────────────────────────────

    @staticmethod
    def search_google_books(query: str):
        try:
            url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&maxResults=2"
            resp = requests.get(url, timeout=4)
            data = resp.json()
            items = data.get("items", [])
            return [{"title": i["volumeInfo"].get("title"),
                     "snippet": i["volumeInfo"].get("description", "")[:400],
                     "link": i["volumeInfo"].get("infoLink")} for i in items]
        except:
            return []

    @staticmethod
    def search_open_library(query: str):
        try:
            url = f"https://openlibrary.org/search.json?q={urllib.parse.quote(query)}&limit=2"
            resp = requests.get(url, timeout=4)
            data = resp.json()
            docs = data.get("docs", [])
            return [{"title": d.get("title"),
                     "snippet": f"Author: {', '.join(d.get('author_name', []))}",
                     "link": f"https://openlibrary.org{d.get('key')}"}
                    for d in docs if d.get("title")]
        except:
            return []

    @staticmethod
    def search_arxiv(query: str):
        try:
            url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results=2"
            resp = requests.get(url, timeout=5)
            titles = re.findall(r'<title>(.*?)</title>', resp.text)[1:]
            summaries = re.findall(r'<summary>(.*?)</summary>', resp.text, re.DOTALL)
            links = re.findall(r'<id>(http[^<]+)</id>', resp.text)
            return [{"title": t.strip(), "snippet": s.strip()[:400], "link": l.strip()}
                    for t, s, l in zip(titles, summaries, links)]
        except:
            return []

    @staticmethod
    def search_semantic_scholar(query: str):
        """Semantic Scholar — free, no key required."""
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit=2&fields=title,abstract,url,year"
            headers = {"User-Agent": "ExamHelpAI/1.0"}
            resp = requests.get(url, headers=headers, timeout=5)
            data = resp.json()
            results = []
            for p in data.get("data", []):
                results.append({
                    "title": p.get("title", ""),
                    "snippet": (p.get("abstract") or "")[:400],
                    "link": p.get("url", f"https://www.semanticscholar.org/paper/{p.get('paperId','')}")
                })
            return results
        except:
            return []

    @staticmethod
    def search_pubmed(query: str):
        """PubMed via NCBI Entrez — free, no key required."""
        try:
            search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={urllib.parse.quote(query)}&retmax=2&retmode=json"
            resp = requests.get(search_url, timeout=4)
            ids = resp.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []
            fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json"
            resp2 = requests.get(fetch_url, timeout=4)
            result_data = resp2.json().get("result", {})
            results = []
            for pmid in ids:
                item = result_data.get(pmid, {})
                title = item.get("title", "")
                if title:
                    results.append({
                        "title": title,
                        "snippet": f"Published: {item.get('pubdate', '')} | Source: {item.get('source', '')}",
                        "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    })
            return results
        except:
            return []

    @staticmethod
    def search_stack_overflow(query: str):
        try:
            url = f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q={urllib.parse.quote(query)}&site=stackoverflow&filter=withbody"
            resp = requests.get(url, timeout=4)
            data = resp.json()
            items = data.get("items", [])
            return [{"title": i.get("title"), "snippet": "StackOverflow Answer", "link": i.get("link")}
                    for i in items[:2]]
        except:
            return []

    @staticmethod
    def search_news(query: str):
        return QueryEngine.search_duckduckgo(f"news {query}", max_results=2)

    @staticmethod
    def get_weather(city: str):
        try:
            resp = requests.get(f"https://wttr.in/{urllib.parse.quote(city)}?format=3", timeout=3)
            return resp.text.strip()
        except:
            return ""

    @staticmethod
    def search_dictionary(word: str):
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
            resp = requests.get(url, timeout=3)
            data = resp.json()
            if isinstance(data, list):
                defns = data[0].get("meanings", [{}])[0].get("definitions", [{}])[0].get("definition", "")
                example = data[0].get("meanings", [{}])[0].get("definitions", [{}])[0].get("example", "")
                return defns + (f" (e.g. {example})" if example else "")
        except:
            return ""

    @staticmethod
    def search_crossref(query: str):
        """CrossRef — free DOI/paper search, no key needed."""
        try:
            url = f"https://api.crossref.org/works?query={urllib.parse.quote(query)}&rows=2&select=title,abstract,URL,author,published"
            headers = {"User-Agent": "ExamHelpAI/1.0 (mailto:support@examhelp.ai)"}
            resp = requests.get(url, headers=headers, timeout=5)
            items = resp.json().get("message", {}).get("items", [])
            results = []
            for item in items:
                title = " ".join(item.get("title", [""])) or ""
                abstract = " ".join(item.get("abstract", "").split()[:60]) if item.get("abstract") else ""
                results.append({"title": title, "snippet": abstract[:300], "link": item.get("URL", "")})
            return results
        except:
            return []

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def search_duckduckgo(query: str, max_results=3):
        if DDGS is None:
            return []
        try:
            results = DDGS().text(query, max_results=max_results)
            if not results:
                return []
            return [{"title": r.get("title", ""), "snippet": r.get("body", ""), "link": r.get("href", "")}
                    for r in results]
        except Exception:
            return []

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def search_wikipedia(query: str, max_results=1):
        if wikipedia is None:
            return []
        try:
            results = wikipedia.search(query, results=max_results)
            if not results:
                return []
            page = wikipedia.page(results[0], auto_suggest=False)
            return [{"title": page.title, "snippet": page.summary[:800] + "...", "link": page.url}]
        except wikipedia.exceptions.DisambiguationError as e:
            try:
                page = wikipedia.page(e.options[0], auto_suggest=False)
                return [{"title": page.title, "snippet": page.summary[:800] + "...", "link": page.url}]
            except:
                return []
        except Exception:
            return []

    @staticmethod
    def route_and_enrich(query: str, user_context: str = ""):
        intent = QueryEngine.classify_query(query)
        sources = []
        enriched_context = ""

        # RAG Retrieval only — instant, no network call
        try:
            import streamlit as st
            from memory.vector_store import VectorStore
            if "vector_store" in st.session_state and st.session_state.vector_store.is_active():
                rag_results = st.session_state.vector_store.search(query)
                if rag_results:
                    enriched_context += "\n### Relevant Context (RAG):\n"
                    for res in rag_results:
                        enriched_context += f"- {res}\n"
        except Exception:
            pass

        final_prompt = query
        if enriched_context:
            final_prompt += f"\n\n{enriched_context}"

        return final_prompt, sources, intent

    @staticmethod
    def get_structured_system_prompt(base_prompt: str):
        return f"""{base_prompt}
You are equipped with a Multi-API Context Fusion Engine (Web Search, Wikipedia, ArXiv, StackOverflow).

CRITICAL FORMATTING RULES:
1. Provide a direct, highly accurate answer immediately.
2. Group deeper explanations under a 'Key Points' list.
3. If 'Sources' links were injected into your context, append them at the end under '### 🔗 Sources'. Do NOT hallucinate URLs.
Be concise, accurate, and well-structured.
"""
