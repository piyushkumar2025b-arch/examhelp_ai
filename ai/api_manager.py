"""api_manager.py — Centralized API Orchestration (restored stub)."""

from utils.ai_engine import generate as ai_generate


class UnifiedAPIManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def call(api_name: str, query: str, **kwargs):
        manager = UnifiedAPIManager()
        return manager._route(api_name, query, **kwargs)

    def _route(self, api_name: str, query: str, **kwargs):
        from utils.query_engine import QueryEngine
        from utils.app_controller import AppController

        # Knowledge / research
        if api_name in ("wiki", "wikipedia"):
            return QueryEngine.search_wikipedia(query)
        elif api_name == "arxiv":
            return QueryEngine.search_arxiv(query)
        elif api_name in ("books", "google_books"):
            return QueryEngine.search_google_books(query)
        elif api_name == "open_library":
            return QueryEngine.search_open_library(query)
        elif api_name == "semantic_scholar":
            return QueryEngine.search_semantic_scholar(query)
        elif api_name == "pubmed":
            return QueryEngine.search_pubmed(query)
        elif api_name == "crossref":
            return QueryEngine.search_crossref(query)
        # Search / news
        elif api_name in ("search", "duckduckgo"):
            return QueryEngine.search_duckduckgo(query, max_results=kwargs.get("max_results", 3))
        elif api_name == "news":
            return QueryEngine.search_news(query)
        elif api_name == "stackoverflow":
            return QueryEngine.search_stack_overflow(query)
        # Dictionary
        elif api_name == "dict":
            result = QueryEngine.search_dictionary(query)
            return [{"title": query, "snippet": result, "link": ""}] if result else []
        # Math
        elif api_name == "math":
            return AppController.evaluate_expression(query)
        # Contests
        elif api_name == "contests":
            from utils.contest_engine import get_upcoming_contests
            return get_upcoming_contests()
        # LLM
        elif api_name == "llm":
            return ai_generate(prompt=query)
        # Key status
        elif api_name == "key_status":
            from utils.ai_engine import get_pool_status
            return get_pool_status()

        return f"Unknown API: {api_name}"
