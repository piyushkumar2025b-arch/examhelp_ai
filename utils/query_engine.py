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

from utils.groq_client import chat_with_groq
from utils.app_controller import AppController

class QueryEngine:
    
    @staticmethod
    def classify_query(query: str):
        query_lower = query.lower()
        if any(w in query_lower for w in ["calculate", "plus", "minus", "divided by", "times"]) or ("+" in query_lower and "=" not in query_lower):
            return "math"
        if any(w in query_lower for w in ["plot", "graph", "draw", "curve"]):
            return "graph"
        if any(w in query_lower for w in ["who is", "what is", "history of", "capital of", "define", "concept of"]):
            return "factual"
        if any(w in query_lower for w in ["latest", "recent", "news", "today", "update", "happened"]):
            return "recent"
        if any(w in query_lower for w in ["code", "error", "exception", "python", "java", "script", "how to build", "syntax"]):
            return "code"
        if any(w in query_lower for w in ["paper", "research", "study", "journal", "abstract", "scientific"]):
            return "scientific"
        if any(w in query_lower for w in ["book", "author", "literature", "novel", "write", "summary of"]):
            return "literary"
        return "complex"

    # --- 10+ HEAVY DUTY FREE ACADEMIC APIS ---

    @staticmethod
    def search_google_books(query: str):
        try:
            url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=2"
            resp = requests.get(url, timeout=3)
            data = resp.json()
            items = data.get("items", [])
            return [{"title": i["volumeInfo"].get("title"), "snippet": i["volumeInfo"].get("description", "")[:400], "link": i["volumeInfo"].get("infoLink")} for i in items]
        except: return []

    @staticmethod
    def search_open_library(query: str):
        try:
            url = f"https://openlibrary.org/search.json?q={query}&limit=2"
            resp = requests.get(url, timeout=3)
            data = resp.json()
            docs = data.get("docs", [])
            return [{"title": d.get("title"), "snippet": f"Author: {', '.join(d.get('author_name', []))}", "link": f"https://openlibrary.org{d.get('key')}"} for d in docs if d.get("title")]
        except: return []

    @staticmethod
    def search_arxiv(query: str):
        try:
            # Simple atom feed parse-like regex for free extraction
            url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results=2"
            resp = requests.get(url, timeout=4)
            titles = re.findall(r'<title>(.*?)</title>', resp.text)[1:] # Skip main feed title
            summaries = re.findall(r'<summary>(.*?)</summary>', resp.text, re.DOTALL)
            links = re.findall(r'<id>(.*?)</id>', resp.text)[1:]
            return [{"title": t, "snippet": s[:400], "link": l} for t, s, l in zip(titles, summaries, links)]
        except: return []

    @staticmethod
    def search_stack_overflow(query: str):
        try:
            url = f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q={query}&site=stackoverflow"
            resp = requests.get(url, timeout=3)
            data = resp.json()
            items = data.get("items", [])
            return [{"title": i.get("title"), "snippet": "StackOverflow Answer", "link": i.get("link")} for i in items[:2]]
        except: return []

    @staticmethod
    def search_news(query: str):
        # Using a free aggregator mock if API key is missing, or fallback to DDG news
        return QueryEngine.search_duckduckgo(f"news {query}", max_results=2)

    @staticmethod
    def get_world_time(location: str = "London"):
        try:
            url = f"https://worldtimeapi.org/api/timezone/Europe/{location.capitalize()}"
            resp = requests.get(url, timeout=2)
            data = resp.json()
            return f"Current time in {location}: {data.get('datetime')}"
        except: return ""

    @staticmethod
    def get_weather(city: str):
        try:
            # Using free wttr.in for text-based weather context
            resp = requests.get(f"https://wttr.in/{city}?format=3", timeout=3)
            return resp.text.strip()
        except: return ""

    @staticmethod
    def search_dictionary(word: str):
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            resp = requests.get(url, timeout=2)
            data = resp.json()
            if isinstance(data, list):
                defns = data[0].get("meanings", [{}])[0].get("definitions", [{}])[0].get("definition", "")
                return defns
        except: return ""

    @staticmethod
    def search_biorxiv(query: str):
        try:
            url = f"https://api.biorxiv.org/details/biorxiv/2023-01-01/2025-12-31/0/{query}"
            resp = requests.get(url, timeout=4)
            data = resp.json()
            collection = data.get("collection", [])
            return [{"title": c.get("title"), "snippet": c.get("abstract", "")[:400], "link": f"https://doi.org/{c.get('doi')}"} for c in collection[:2]]
        except: return []

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def search_duckduckgo(query: str, max_results=3):
        if DDGS is None: return []
        try:
            results = DDGS().text(query, max_results=max_results)
            if not results: return []
            return [{"title": r.get("title", ""), "snippet": r.get("body", ""), "link": r.get("href", "")} for r in results]
        except Exception:
            return []

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def search_wikipedia(query: str, max_results=1):
        if wikipedia is None: return []
        try:
            results = wikipedia.search(query, results=max_results)
            if not results: return []
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
        from ai.api_manager import UnifiedAPIManager
        api_manager = UnifiedAPIManager()
        
        intent = QueryEngine.classify_query(query)
        sources = []
        enriched_context = ""
        
        # 0. RAG RETRIEVAL (Memory Layer)
        from memory.vector_store import VectorStore
        if "vector_store" in st.session_state and st.session_state.vector_store.is_active():
            rag_results = st.session_state.vector_store.search(query)
            if rag_results:
                enriched_context += "\n### Relevant Context (RAG):\n"
                for res in rag_results:
                    enriched_context += f"- {res}\n"
        # 1. Image Check (Multimedia Intent)
        image_url = None
        if "show me" in query.lower() or "image of" in query.lower():
            image_query = query.lower().replace("show me", "").replace("image of", "").replace("photo of", "").strip()
            image_url = api_manager.call("image", image_query)
        
        # 2. Parallel API Execution (The Performance Core)
        tasks = []
        if intent == "factual":
            tasks.append({"name": "wiki", "api": "wiki", "query": query})
            if len(query.split()) < 3:
                tasks.append({"name": "dict", "api": "dict", "query": query})
        elif intent == "scientific":
            tasks.append({"name": "arxiv", "api": "arxiv", "query": query})
            tasks.append({"name": "bio", "api": "biorxiv", "query": query})
        elif intent == "literary":
            tasks.append({"name": "books", "api": "books", "query": query})
        elif intent == "recent":
            tasks.append({"name": "news", "api": "search", "query": query, "kwargs": {"max_results": 2}})
        
        # Always run a supplementary DDG search in parallel for maximum depth
        tasks.append({"name": "search", "api": "search", "query": query, "kwargs": {"max_results": 2}})
        
        # Execute all tasks in parallel
        results = api_manager.parallel_fetch(tasks)
        
        # 3. Context Processing
        if results.get("wiki"):
            enriched_context += "### Wikipedia Knowledge:\n"
            for w in results["wiki"]:
                enriched_context += f"**{w['title']}**: {w['snippet']}\n"
                sources.append(w['link'])
                
        if results.get("arxiv"):
            for a in results["arxiv"]:
                enriched_context += f"**ArXiv Paper: {a['title']}**: {a['snippet']}\n"
                sources.append(a['link'])
                
        if results.get("search"):
            enriched_context += "\n### Research Context (Web):\n"
            for d in results["search"]:
                enriched_context += f"**{d['title']}**: {d['snippet']}\n"
                sources.append(d['link'])
        
        if image_url:
            enriched_context += f"\n\n[SYSTEM_VIEW: IMAGE_FOUND] Displaying verified visual content for query. (URL: {image_url})\n"

        final_prompt = query
        if enriched_context:
            final_prompt += f"\n\n{enriched_context}"
            
        return final_prompt, list(set(sources)), intent

    @staticmethod
    def get_structured_system_prompt(base_prompt: str):
        return f"""{base_prompt}
You are a GOD-LEVEL intelligence system. 
You are equipped with a Multi-API Context Fusion Engine (Web Search, Wikipedia, Math Eval) whose output is injected directly into your prompts if applicable.

CRITICAL FORMATTING RULES:
1. Provide a direct, highly accurate Answer immediately.
2. Group deeper explanations under a 'Key Points' list.
3. If real-world 'Sources' links were injected into your prompt context, ALWAYS append them cleanly at the very end in a bulleted list titled '### 🔗 Sources'. Do NOT hallucinate URLs. NEVER output sources if none were provided.
Be incredibly fast, concise, and structured.
"""
