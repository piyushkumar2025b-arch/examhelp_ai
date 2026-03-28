"""api_manager.py — Centralized API Orchestration with parallel execution."""

import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from utils.file_engine import FileEngine
from utils.groq_client import chat_with_groq


class UnifiedAPIManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.executor = ThreadPoolExecutor(max_workers=10)
        return cls._instance

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def call(api_name: str, query: str, **kwargs) -> Any:
        manager = UnifiedAPIManager()
        return manager._route(api_name, query, **kwargs)

    def _route(self, api_name: str, query: str, **kwargs) -> Any:
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

        # File
        elif api_name == "file":
            return FileEngine.process_upload(kwargs.get("file"), query)

        # Images
        elif api_name == "image":
            from ai.image_engine import fetch_infinity_images
            return fetch_infinity_images(query, limit=kwargs.get("limit", 1))

        # Contests
        elif api_name == "contests":
            from utils.contest_engine import fetch_upcoming_contests
            return fetch_upcoming_contests()

        # LLM
        elif api_name == "llm":
            return chat_with_groq(kwargs.get("messages", []),
                                  json_mode=kwargs.get("json_mode", False))

        return f"Unknown API: {api_name}"

    def parallel_fetch(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple API calls concurrently."""
        results = {}
        with ThreadPoolExecutor(max_workers=max(len(tasks), 1)) as exe:
            futures = {}
            for task in tasks:
                name = task["name"]
                api = task["api"]
                query = task["query"]
                kwargs = task.get("kwargs", {})
                futures[name] = exe.submit(self._route, api, query, **kwargs)

            for name, future in futures.items():
                try:
                    results[name] = future.result(timeout=8)
                except Exception as e:
                    results[name] = []
        return results
