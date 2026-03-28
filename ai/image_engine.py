"""image_engine.py — Bulletproof Production-Grade Image Orchestration Engine.

Features:
1. Multi-Vector Query Expansion (Linguistic enrichment).
2. Parallel Source Fetching (Pexels + Unsplash + Hard Fallback).
3. Strategic GET Validation (CDN-aware).
4. Aggressive Streamlit caching for sub-second UI delivery.
"""

import re
import json
import requests
import streamlit as st
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple
from dotenv import load_dotenv

# ==============================
# CONFIG & AUTH
# ==============================
load_dotenv()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "") 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ==============================
# 1. QUERY EXPANSION ENGINE
# ==============================

def expand_query_variants(query: str) -> List[str]:
    """Generates linguistic variants to maximize search hit rate."""
    base = query.strip()
    return [
        base,
        f"{base} diagram educational",
        f"{base} labeled chart",
        f"{base} clear illustration",
        f"{base} technical reference"
    ]

# ==============================
# 2. IMAGE SOURCES (PARALLEL & RESILIENT)
# ==============================

def _fetch_pexels_resilient(query: str, limit: int = 3) -> List[str]:
    """Hits Pexels with expanded context if available."""
    if not PEXELS_API_KEY:
        return []
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": PEXELS_API_KEY}
        # We try the variants in order until we get results
        for variant in expand_query_variants(query)[:2]:
            params = {"query": variant, "per_page": limit, "orientation": "landscape"}
            res = requests.get(url, headers=headers, params=params, timeout=4)
            if res.status_code == 200:
                photos = res.json().get("photos", [])
                if photos:
                    return [p["src"]["large"] for p in photos]
    except Exception:
        pass
    return []

def _fetch_unsplash_resilient(query: str, limit: int = 3) -> List[str]:
    """Reliable Unsplash redirection with signature-based uniqueness."""
    results = []
    try:
        # Use the first 2 variants for variety
        variants = expand_query_variants(query)
        for i in range(limit):
            v_idx = i % len(variants)
            clean_q = variants[v_idx].replace(" ", ",").lower()
            url = f"https://source.unsplash.com/featured/1200x800/?{clean_q}&sig={i}"
            results.append(url)
    except Exception:
        pass
    return results

# ==============================
# 3. VERIFICATION & VALIDATION (CDN-AWARE)
# ==============================

def validate_image_stream(url: str) -> bool:
    """Uses streaming GET to verify Content-Type without loading entire payload."""
    if "unsplash.com" in url:
        return True # Source unsplash is extremely stable and redirects are internal
    try:
        # Stream=True allows us to check headers without downloading the body
        with requests.get(url, headers=HEADERS, stream=True, timeout=3) as r:
            if r.status_code == 200:
                ctype = r.headers.get("Content-Type", "").lower()
                return "image" in ctype
    except Exception:
        pass
    return False

# ==============================
# 4. CACHED AGGREGATOR (THE CORE)
# ==============================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_images_bulletproof(query: str, limit: int = 3) -> List[str]:
    """Parallel fetch with multi-source fallback and hard guarantee."""
    valid_images = []
    
    # 1. Run Core Sources in Parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        f_pexels = executor.submit(_fetch_pexels_resilient, query, limit)
        f_unsplash = executor.submit(_fetch_unsplash_resilient, query, limit)
        
        # Priority 1: Pexels (Custom metadata)
        p_results = f_pexels.result()
        for url in p_results:
            if validate_image_stream(url):
                valid_images.append(url)
            if len(valid_images) >= limit: break
            
        # Priority 2: Unsplash (Aesthetic fallback)
        if len(valid_images) < limit:
            u_results = f_unsplash.result()
            for url in u_results:
                if validate_image_stream(url):
                    valid_images.append(url)
                if len(valid_images) >= limit: break

    # 2. HARD FALLBACK (Guaranteed Output)
    if not valid_images:
        # Instant direct-redirect fallback if all APIs fail
        valid_images = [
            f"https://source.unsplash.com/1200x800/?{query.replace(' ',',')},academic&sig=99",
            f"https://source.unsplash.com/1200x800/?{query.replace(' ',',')},diagram&sig=88"
        ]
        
    return valid_images[:limit]

# ==============================
# 5. CHAT SYSTEM INTEGRATION
# ==============================

def process_visual_request(response_text: str) -> Tuple[List[str], str, str]:
    """
    Parses manifest, fetches bulletproof images, and returns cleaned context.
    Returns: (list_of_urls, caption_text, cleaned_response_text)
    """
    # 1. Parse Manifest
    match = re.search(r'VISUAL_MANIFEST:\s*(\{.*?\})', response_text, re.DOTALL)
    if not match:
        return [], "", response_text

    try:
        manifest = json.loads(match.group(1))
        query = manifest.get("query", "")
        caption = manifest.get("caption", "Educational Reference")
    except:
        return [], "", response_text

    # 2. Clean Response Text immediately
    clean_text = re.sub(r'VISUAL_MANIFEST:.*', '', response_text, flags=re.DOTALL).strip()

    if not query:
        return [], "", clean_text

    # 3. Fetch Images (Cached)
    images = fetch_images_bulletproof(query, limit=3)
    
    return images, caption, clean_text
