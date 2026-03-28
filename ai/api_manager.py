"""api_manager.py — Centralized API Orchestration, Caching, and Optimization Layer."""

import streamlit as st
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

# Core Module Imports
from utils.query_engine import QueryEngine
from utils.app_controller import AppController
from utils.file_engine import FileEngine
from utils.web_handler import scrape_web_page
from utils.groq_client import chat_with_groq

class UnifiedAPIManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UnifiedAPIManager, cls).__new__(cls)
            cls._instance.executor = ThreadPoolExecutor(max_workers=10)
        return cls._instance

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def call(api_name: str, query: str, **kwargs) -> Any:
        """Centralized API call entry point with aggressive caching."""
        manager = UnifiedAPIManager()
        return manager._route(api_name, query, **kwargs)

    def _route(self, api_name: str, query: str, **kwargs) -> Any:
        # 1. Research & Knowledge APIs
        if api_name == "wiki":
            return QueryEngine.search_wikipedia(query)
        elif api_name == "search":
            return QueryEngine.search_duckduckgo(query, max_results=kwargs.get("max_results", 3))
        elif api_name == "books":
            return QueryEngine.search_google_books(query)
        elif api_name == "arxiv":
            return QueryEngine.search_arxiv(query)
            
        # 2. Logic & Tool APIs
        elif api_name == "math":
            return AppController.evaluate_expression(query)
        elif api_name == "file":
            return FileEngine.process_upload(kwargs.get("file"), query)
            
        # 3. Vision & Multimedia
        elif api_name == "image":
            return self._fetch_unsplash_image(query)
            
        # 4. LLM Reasoning
        elif api_name == "llm":
            return chat_with_groq(kwargs.get("messages", []), json_mode=kwargs.get("json_mode", False))
            
        return None

    def parallel_fetch(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple API calls simultaneously to minimize latency."""
        futures = {}
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(tasks)) as exec:
            for task in tasks:
                name = task["name"]
                api = task["api"]
                query = task["query"]
                kwargs = task.get("kwargs", {})
                futures[name] = exec.submit(self.call, api, query, **kwargs)
                
            for name, future in futures.items():
                try:
                    results[name] = future.result()
                except Exception as e:
                    results[name] = f"Error: {e}"
                    
        return results

    def _fetch_unsplash_image(self, query: str) -> Optional[str]:
        """Fetch high-quality educational visuals via Unsplash (Free API)."""
        try:
            # Using the source-redirect for zero-key instant image display
            # Format: https://source.unsplash.com/featured/?<query>
            image_url = f"https://source.unsplash.com/featured/800x600/?{query.replace(' ', ',')}"
            # Verify if it returns a 200 via a quick head request
            import requests
            resp = requests.head(image_url, allow_redirects=True, timeout=2)
            if resp.status_code == 200:
                return resp.url
        except Exception:
            pass
        return None
