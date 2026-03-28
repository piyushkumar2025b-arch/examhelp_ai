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
        from ai.plugin_registry import PLUGIN_REGISTRY
        
        # 1. KNOWLEDGE & RESEARCH (WIKI / ARXIV / BOOKS)
        if api_name in PLUGIN_REGISTRY["knowledge"] or api_name == "wiki":
            return QueryEngine.search_wikipedia(query)
        elif api_name in PLUGIN_REGISTRY["science"] or api_name == "arxiv":
            return QueryEngine.search_arxiv(query)
        elif api_name in PLUGIN_REGISTRY["literature"] or api_name == "books":
            return QueryEngine.search_google_books(query)
            
        # 2. SEARCH & NEWS
        elif api_name == "search" or api_name == "duckduckgo":
            return QueryEngine.search_duckduckgo(query, max_results=kwargs.get("max_results", 3))
            
        # 3. COMPUTATION & EVALUATION
        elif api_name in PLUGIN_REGISTRY["math"] or api_name == "math":
            return AppController.evaluate_expression(query)
            
        # 4. FILE PROCESSING & OCR
        elif api_name == "file":
            return FileEngine.process_upload(kwargs.get("file"), query)
            
        # 5. VISION & MULTIMEDIA (INTEGRATED WITH IMAGE ENGINE)
        elif api_name in PLUGIN_REGISTRY["visual"] or api_name == "image":
            from ai.image_engine import fetch_infinity_images
            return fetch_infinity_images(query, limit=kwargs.get("limit", 1))
            
        # 6. CONTEST TRACKING (NEW)
        elif api_name in PLUGIN_REGISTRY["contests"] or api_name == "contests":
            from utils.contest_engine import fetch_upcoming_contests
            return fetch_upcoming_contests()
            
        # 7. LLM CORE REASONING
        elif api_name == "llm":
            return chat_with_groq(kwargs.get("messages", []), json_mode=kwargs.get("json_mode", False))
            
        return f"Unknown API: {api_name}"

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

    def _fetch_unsplash_images(self, query: str, limit: int = 3) -> List[str]:
        """Fetch multiple high-quality educational visuals via Unsplash."""
        try:
            # Using the official public unsplash search endpoint for better results
            # Format: https://source.unsplash.com/featured/?<query>
            # We add keywords to query for academic quality
            refined_query = f"{query}, educational, technical"
            img_urls = []
            for i in range(limit):
                # Using unique query modifiers to get different images
                unique_query = f"{refined_query}&sig={i}"
                url = f"https://source.unsplash.com/featured/1200x800/?{unique_query}"
                img_urls.append(url)
            return img_urls
        except Exception:
            return []
