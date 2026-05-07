"""
media_hub_engine.py — Free Image Search Engine (No AI, No Quota)
Supports: Unsplash Source CDN · Pexels · Pixabay · Openverse (CC)
All APIs are free; Unsplash Source & Openverse require no key at all.
Pexels & Pixabay need a free key (set in .streamlit/secrets.toml or .env).
"""

import requests
import io
import os
from typing import List, Dict, Optional

TIMEOUT = 10  # seconds for all HTTP calls

# ─────────────────────────────────────────────────────────────────────────────
# Key helpers — read from Streamlit secrets OR env vars, never crash if missing
# ─────────────────────────────────────────────────────────────────────────────

def _get_key(name: str) -> str:
    """Safely read an API key from st.secrets or env vars."""
    try:
        import streamlit as st
        return st.secrets.get(name, os.getenv(name, ""))
    except Exception:
        return os.getenv(name, "")


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 1 — Openverse (Creative Commons, NO KEY REQUIRED)
# ─────────────────────────────────────────────────────────────────────────────

def search_openverse(query: str, page: int = 1, per_page: int = 20) -> List[Dict]:
    """
    Search Openverse (CC-licensed images). No API key needed.
    Returns list of dicts: {url, thumb, title, author, license, source_url, width, height}
    """
    try:
        resp = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": query, "page": page, "page_size": per_page, "license_type": "all"},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return []
        data = resp.json().get("results", [])
        results = []
        for item in data:
            results.append({
                "url":        item.get("url", ""),
                "thumb":      item.get("thumbnail", item.get("url", "")),
                "title":      item.get("title", "Untitled"),
                "author":     item.get("creator", "Unknown"),
                "license":    item.get("license", ""),
                "source_url": item.get("foreign_landing_url", ""),
                "width":      item.get("width", 0),
                "height":     item.get("height", 0),
                "source":     "Openverse",
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 2 — Unsplash Source CDN  (NO KEY REQUIRED for direct embed URLs)
#   Note: Unsplash Source gives random-per-query images — great for browsing
#   For search with results list, use the Unsplash API (free, needs key)
# ─────────────────────────────────────────────────────────────────────────────

def search_unsplash(query: str, page: int = 1, per_page: int = 20) -> List[Dict]:
    """
    Search Unsplash via their public API (free key, 50 req/hr on demo).
    Falls back to CDN placeholder rows if no key is set.
    """
    key = _get_key("UNSPLASH_ACCESS_KEY")
    if key:
        try:
            resp = requests.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "page": page, "per_page": per_page},
                headers={"Authorization": f"Client-ID {key}"},
                timeout=TIMEOUT,
            )
            if resp.status_code != 200:
                return _unsplash_cdn_fallback(query, per_page)
            items = resp.json().get("results", [])
            results = []
            for item in items:
                results.append({
                    "url":        item["urls"]["regular"],
                    "thumb":      item["urls"]["small"],
                    "title":      item.get("description") or item.get("alt_description") or "Unsplash Photo",
                    "author":     item["user"]["name"],
                    "license":    "Unsplash License",
                    "source_url": item["links"]["html"],
                    "width":      item.get("width", 0),
                    "height":     item.get("height", 0),
                    "source":     "Unsplash",
                })
            return results
        except Exception:
            pass
    return _unsplash_cdn_fallback(query, per_page)


def _unsplash_cdn_fallback(query: str, count: int = 12) -> List[Dict]:
    """Generate Unsplash Source CDN URLs — no key needed, instant images."""
    results = []
    for i in range(min(count, 12)):
        w, h = 800, 600
        url = f"https://source.unsplash.com/{w}x{h}/?{query},{i}"
        results.append({
            "url":        url,
            "thumb":      f"https://source.unsplash.com/400x300/?{query},{i}",
            "title":      f"{query.title()} #{i+1}",
            "author":     "Unsplash",
            "license":    "Unsplash License",
            "source_url": f"https://unsplash.com/s/photos/{query.replace(' ', '-')}",
            "width":      w,
            "height":     h,
            "source":     "Unsplash",
        })
    return results


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 3 — Pexels (free key — 200 req/hr, sign up at pexels.com/api)
# ─────────────────────────────────────────────────────────────────────────────

def search_pexels(query: str, page: int = 1, per_page: int = 20) -> List[Dict]:
    """
    Search Pexels. Requires PEXELS_API_KEY in secrets/env.
    Returns [] gracefully if no key.
    """
    key = _get_key("PEXELS_API_KEY")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "page": page, "per_page": per_page},
            headers={"Authorization": key},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return []
        items = resp.json().get("photos", [])
        results = []
        for item in items:
            results.append({
                "url":        item["src"]["large"],
                "thumb":      item["src"]["medium"],
                "title":      item.get("alt", "Pexels Photo"),
                "author":     item.get("photographer", "Unknown"),
                "license":    "Pexels License (Free)",
                "source_url": item.get("url", ""),
                "width":      item.get("width", 0),
                "height":     item.get("height", 0),
                "source":     "Pexels",
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 4 — Pixabay (free key — 100 req/min, sign up at pixabay.com/api)
# ─────────────────────────────────────────────────────────────────────────────

def search_pixabay(query: str, page: int = 1, per_page: int = 20) -> List[Dict]:
    """
    Search Pixabay. Requires PIXABAY_API_KEY in secrets/env.
    Returns [] gracefully if no key.
    """
    key = _get_key("PIXABAY_API_KEY")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://pixabay.com/api/",
            params={
                "key":      key,
                "q":        query,
                "page":     page,
                "per_page": per_page,
                "image_type": "photo",
                "safesearch": "true",
            },
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return []
        items = resp.json().get("hits", [])
        results = []
        for item in items:
            results.append({
                "url":        item.get("largeImageURL", item.get("webformatURL", "")),
                "thumb":      item.get("previewURL", item.get("webformatURL", "")),
                "title":      ", ".join(item.get("tags", "").split(",")[:3]).strip(),
                "author":     item.get("user", "Unknown"),
                "license":    "Pixabay License (Free)",
                "source_url": item.get("pageURL", ""),
                "width":      item.get("imageWidth", 0),
                "height":     item.get("imageHeight", 0),
                "source":     "Pixabay",
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate search — queries all available sources
# ─────────────────────────────────────────────────────────────────────────────

def search_images(
    query: str,
    sources: Optional[List[str]] = None,
    page: int = 1,
    per_page: int = 20,
) -> List[Dict]:
    """
    Search across all enabled sources and return combined results.
    sources: list of 'Openverse', 'Unsplash', 'Pexels', 'Pixabay'
             (defaults to all)
    """
    if sources is None:
        sources = ["Openverse", "Unsplash", "Pexels", "Pixabay"]

    all_results: List[Dict] = []
    per_source = max(4, per_page // len(sources))

    for src in sources:
        if src == "Openverse":
            all_results.extend(search_openverse(query, page, per_source))
        elif src == "Unsplash":
            all_results.extend(search_unsplash(query, page, per_source))
        elif src == "Pexels":
            all_results.extend(search_pexels(query, page, per_source))
        elif src == "Pixabay":
            all_results.extend(search_pixabay(query, page, per_source))

    # Filter out entries with no URL
    return [r for r in all_results if r.get("url")]


# ─────────────────────────────────────────────────────────────────────────────
# Download helpers
# ─────────────────────────────────────────────────────────────────────────────

def download_image_bytes(url: str) -> Optional[bytes]:
    """Download image bytes from a URL. Returns None on failure."""
    try:
        resp = requests.get(url, timeout=TIMEOUT, stream=True)
        if resp.status_code == 200:
            return resp.content
        return None
    except Exception:
        return None


def bulk_download_zip(results: List[Dict]) -> Optional[bytes]:
    """
    Download all images in results list and bundle into a ZIP.
    Returns ZIP bytes or None if nothing downloaded.
    """
    import zipfile
    buf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, item in enumerate(results):
            img_bytes = download_image_bytes(item.get("url", ""))
            if img_bytes:
                ext = "jpg"
                if item["url"].endswith(".png"):
                    ext = "png"
                elif item["url"].endswith(".webp"):
                    ext = "webp"
                safe_title = "".join(c for c in item.get("title", f"image_{i}")[:30]
                                     if c.isalnum() or c in "_ -")
                zf.writestr(f"{i+1:03d}_{safe_title}.{ext}", img_bytes)
                count += 1
    if count == 0:
        return None
    buf.seek(0)
    return buf.read()


def extract_color_palette(img_bytes: bytes, n: int = 6) -> List[str]:
    """
    Extract dominant hex colors from image bytes using Pillow.
    Returns list of hex color strings like ['#ff6b6b', ...].
    Falls back to empty list if Pillow not available.
    """
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = img.resize((100, 100))  # downsample for speed
        pixels = list(img.getdata())
        # Simple bucket quantization
        from collections import Counter
        bucket = [(r // 32 * 32, g // 32 * 32, b // 32 * 32) for r, g, b in pixels]
        common = Counter(bucket).most_common(n)
        return [f"#{r:02x}{g:02x}{b:02x}" for (r, g, b), _ in common]
    except Exception:
        return []
