"""image_engine.py — Multi-source image fetcher with fallback chain.
Sources: Pexels (key-gated), Pixabay (free key bundled), Unsplash static fallbacks.
"""

import re
import json
import requests
import streamlit as st
import os
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple
from dotenv import load_dotenv

def _get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets.get(key, "") or default
    except Exception:
        return os.getenv(key, default)

PEXELS_API_KEY = _get_secret("PEXELS_API_KEY")
PIXABAY_KEY    = _get_secret("PIXABAY_API_KEY")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Curated Unsplash static fallbacks by topic (always valid, no redirect needed)
_UNSPLASH_FALLBACKS = [
    "https://images.unsplash.com/photo-1454165833767-027508496b4c?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&q=80&w=800",
]


def _fetch_pexels(query: str, limit: int = 3) -> List[str]:
    if not PEXELS_API_KEY:
        return []
    try:
        resp = requests.get(
            f"https://api.pexels.com/v1/search?query={query}&per_page={limit}",
            headers={"Authorization": PEXELS_API_KEY},
            timeout=4
        )
        if resp.status_code == 200:
            return [p["src"]["large"] for p in resp.json().get("photos", [])]
    except Exception:
        pass
    return []


def _fetch_pixabay(query: str, limit: int = 3) -> List[str]:
    try:
        resp = requests.get(
            f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query.replace(' ', '+')}"
            f"&image_type=photo&per_page={limit}&safesearch=true",
            timeout=4
        )
        if resp.status_code == 200:
            return [hit["largeImageURL"] for hit in resp.json().get("hits", [])]
    except Exception:
        pass
    return []


def _fetch_wikimedia(query: str, limit: int = 2) -> List[str]:
    """Wikimedia Commons free images — no key needed."""
    try:
        resp = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query", "format": "json",
                "generator": "search", "gsrsearch": f"file:{query}",
                "gsrnamespace": "6", "gsrlimit": str(limit),
                "prop": "imageinfo", "iiprop": "url"
            },
            timeout=4
        )
        data = resp.json()
        urls = []
        for page in data.get("query", {}).get("pages", {}).values():
            ii = page.get("imageinfo", [{}])
            url = ii[0].get("url", "")
            if url and url.lower().endswith((".jpg", ".jpeg", ".png")):
                urls.append(url)
        return urls
    except Exception:
        return []


def _validate(url: str) -> bool:
    try:
        r = requests.head(url, headers=HEADERS, timeout=2, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_infinity_images(query: str, limit: int = 3) -> List[str]:
    final = []
    with ThreadPoolExecutor(max_workers=4) as exe:
        f_pexels = exe.submit(_fetch_pexels, query, limit)
        f_pixabay = exe.submit(_fetch_pixabay, query, limit)
        f_wiki = exe.submit(_fetch_wikimedia, query, limit)

        candidates = (
            f_pexels.result()
            + f_pixabay.result()
            + f_wiki.result()
        )

    for url in candidates:
        if _validate(url):
            final.append(url)
        if len(final) >= limit:
            break

    # Always-valid fallbacks
    if not final:
        final = _UNSPLASH_FALLBACKS[:limit]

    return final[:limit]


def process_visual_request(response_text: str) -> Tuple[List[str], str, str]:
    match = re.search(r'VISUAL_MANIFEST:\s*(\{.*?\})', response_text, re.DOTALL)
    if not match:
        return [], "", response_text
    try:
        manifest = json.loads(match.group(1))
        query = manifest.get("query", "")
        caption = manifest.get("caption", "Educational Reference")
        clean_text = re.sub(r'---?\s*VISUAL_MANIFEST:.*', '', response_text, flags=re.DOTALL).strip()
        images = fetch_infinity_images(query, limit=3)
        return images, caption, clean_text
    except Exception:
        return [], "", response_text
