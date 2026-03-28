import streamlit as st
import wikipedia
from duckduckgo_search import DDGS
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
        if any(w in query_lower for w in ["who is", "what is", "history of", "capital of", "define"]):
            return "factual"
        if any(w in query_lower for w in ["latest", "recent", "news", "today", "update"]):
            return "recent"
        if "search for" in query_lower:
            return "recent"
        return "complex"

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def search_duckduckgo(query: str, max_results=3):
        try:
            results = DDGS().text(query, max_results=max_results)
            if not results: return []
            return [{"title": r.get("title", ""), "snippet": r.get("body", ""), "link": r.get("href", "")} for r in results]
        except Exception:
            return []

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def search_wikipedia(query: str, max_results=1):
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
        intent = QueryEngine.classify_query(query)
        sources = []
        enriched_context = ""
        
        if intent == "factual":
            wiki_res = QueryEngine.search_wikipedia(query)
            if wiki_res:
                enriched_context += "### Wikipedia Knowledge:\n"
                for w in wiki_res:
                    enriched_context += f"**{w['title']}**: {w['snippet']}\n"
                    sources.append(w['link'])
            else:
                ddg_res = QueryEngine.search_duckduckgo(query, max_results=2)
                for d in ddg_res:
                    enriched_context += f"**{d['title']}**: {d['snippet']}\n"
                    sources.append(d['link'])
                    
        elif intent == "recent" or intent == "complex":
            # For complex queries, use DDG mainly, perhaps backing off to 2 results for speed
            ddg_res = QueryEngine.search_duckduckgo(query, max_results=2)
            if ddg_res:
                enriched_context += "### Real-Time Web Context:\n"
                for d in ddg_res:
                    enriched_context += f"**{d['title']}**: {d['snippet']}\n"
                    sources.append(d['link'])
                    
        elif intent == "math":
            # Attempt inline evaluation
            maybe_calc = query.lower().replace("calculate", "").replace("what is", "").strip()
            res = AppController.evaluate_expression(maybe_calc)
            if res and res != "Error":
                enriched_context += f"### Exact Calculation Engine Result:\n{res}\n"
                
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
