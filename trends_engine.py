"""
trends_engine.py — Free AI & OSS Trends Engine (no keys required for core features)
Sources: GitHub Trending (scrape) · GitHub REST API (public, 60 req/hr unauthed)
         HuggingFace Hub API (no key) · AI RSS feeds (no key)
"""
import requests, re
from typing import List, Dict, Optional
from html.parser import HTMLParser

TIMEOUT = 10
GITHUB_API = "https://api.github.com"
HF_API     = "https://huggingface.co/api"


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Trending (scrape github.com/trending — no key)
# ─────────────────────────────────────────────────────────────────────────────

def get_github_trending(language: str = "", period: str = "daily") -> List[Dict]:
    """
    Scrape GitHub trending page.
    period: 'daily' | 'weekly' | 'monthly'
    Returns list of {name, url, description, stars, forks, language, avatar}
    """
    url = f"https://github.com/trending/{requests.utils.quote(language)}?since={period}"
    try:
        r = requests.get(url, headers={"Accept":"text/html","User-Agent":"Mozilla/5.0"}, timeout=TIMEOUT)
        if r.status_code != 200:
            return _github_api_trending(language)
        html = r.text
        repos = []
        # Extract repo blocks via regex (lightweight, no BeautifulSoup needed)
        blocks = re.findall(r'<article class="Box-row">(.*?)</article>', html, re.S)
        for block in blocks[:25]:
            # Name / URL
            m_name = re.search(r'href="/([^"]+)".*?class="[^"]*lh-condensed[^"]*"', block, re.S)
            name = m_name.group(1) if m_name else ""
            # Description
            m_desc = re.search(r'<p[^>]*>\s*(.*?)\s*</p>', block, re.S)
            desc = re.sub(r'\s+', ' ', m_desc.group(1)).strip() if m_desc else ""
            desc = re.sub(r'<[^>]+>', '', desc)
            # Stars
            m_stars = re.search(r'aria-label="star".*?(\d[\d,]*)\s*stars', block, re.S)
            if not m_stars:
                m_stars = re.search(r'(\d[\d,]*)\s*stars', block, re.S)
            stars = m_stars.group(1).replace(",","") if m_stars else "0"
            # Language
            m_lang = re.search(r'itemprop="programmingLanguage"[^>]*>\s*([^<]+)\s*<', block)
            lang = m_lang.group(1).strip() if m_lang else ""

            if name:
                repos.append({
                    "name":        name,
                    "url":         f"https://github.com/{name}",
                    "description": desc[:200],
                    "stars":       int(stars) if stars.isdigit() else 0,
                    "language":    lang,
                    "avatar":      f"https://github.com/{name.split('/')[0]}.png?size=40",
                    "clone_url":   f"https://github.com/{name}.git",
                    "zip_url":     f"https://github.com/{name}/archive/refs/heads/main.zip",
                })
        return repos if repos else _github_api_trending(language)
    except Exception:
        return _github_api_trending(language)


def _github_api_trending(language: str = "") -> List[Dict]:
    """Fallback: GitHub API search for recently created starred repos."""
    try:
        params = {"q": f"stars:>100{' language:'+language if language else ''}",
                  "sort": "stars", "order": "desc", "per_page": 20}
        r = requests.get(f"{GITHUB_API}/search/repositories", params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        items = r.json().get("items", [])
        return [{
            "name":        item["full_name"],
            "url":         item["html_url"],
            "description": (item.get("description") or "")[:200],
            "stars":       item.get("stargazers_count", 0),
            "language":    item.get("language") or "",
            "avatar":      item["owner"]["avatar_url"],
            "clone_url":   item["clone_url"],
            "zip_url":     item["html_url"] + "/archive/refs/heads/main.zip",
        } for item in items]
    except Exception:
        return []


def search_github_repos(query: str, limit: int = 15) -> List[Dict]:
    """Search GitHub repos by keyword via public API."""
    try:
        r = requests.get(
            f"{GITHUB_API}/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "per_page": limit},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return []
        items = r.json().get("items", [])
        return [{
            "name":        item["full_name"],
            "url":         item["html_url"],
            "description": (item.get("description") or "")[:200],
            "stars":       item.get("stargazers_count", 0),
            "forks":       item.get("forks_count", 0),
            "language":    item.get("language") or "",
            "avatar":      item["owner"]["avatar_url"],
            "clone_url":   item["clone_url"],
            "zip_url":     item["html_url"] + "/archive/refs/heads/main.zip",
            "topics":      item.get("topics", [])[:5],
        } for item in items]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# HuggingFace Trending Models (no key)
# ─────────────────────────────────────────────────────────────────────────────

def get_hf_trending(limit: int = 15) -> List[Dict]:
    """HuggingFace trending models via public API."""
    try:
        r = requests.get(
            f"{HF_API}/models",
            params={"sort": "trending", "direction": -1, "limit": limit, "full": False},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return []
        items = r.json()
        return [{
            "name":       item.get("id",""),
            "url":        f"https://huggingface.co/{item.get('id','')}",
            "downloads":  item.get("downloads", 0),
            "likes":      item.get("likes", 0),
            "pipeline":   item.get("pipeline_tag",""),
            "tags":       item.get("tags",[])[:5],
        } for item in items]
    except Exception:
        return []


def get_hf_trending_datasets(limit: int = 10) -> List[Dict]:
    """HuggingFace trending datasets."""
    try:
        r = requests.get(
            f"{HF_API}/datasets",
            params={"sort":"trending","direction":-1,"limit":limit},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return []
        return [{"name":i.get("id",""),"url":f"https://huggingface.co/datasets/{i.get('id','')}",
                 "downloads":i.get("downloads",0),"likes":i.get("likes",0)} for i in r.json()]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# AI News via free RSS feeds (no key)
# ─────────────────────────────────────────────────────────────────────────────

AI_RSS_FEEDS = [
    ("The Verge AI",      "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("MIT Tech Review AI","https://www.technologyreview.com/feed/"),
    ("Ars Technica AI",   "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("VentureBeat AI",    "https://venturebeat.com/category/ai/feed/"),
    ("HuggingFace Blog",  "https://huggingface.co/blog/feed.xml"),
]


def _parse_rss(xml: str, source: str, limit: int) -> List[Dict]:
    items = re.findall(r'<item[^>]*>(.*?)</item>', xml, re.S)
    results = []
    for item in items[:limit]:
        title   = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.S)
        link    = re.search(r'<link[^>]*>([^<]+)</link>', item)
        if not link:
            link = re.search(r'<link[^>]*/>', item)
        desc    = re.search(r'<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item, re.S)
        img_url = re.search(r'<media:thumbnail[^>]+url="([^"]+)"', item)
        if not img_url:
            img_url = re.search(r'<enclosure[^>]+url="([^"]+)"', item)
        pub     = re.search(r'<pubDate[^>]*>(.*?)</pubDate>', item)

        t = re.sub(r'<[^>]+>','', title.group(1) if title else "").strip()
        l = link.group(1).strip() if link else ""
        d = re.sub(r'<[^>]+>','', desc.group(1) if desc else "")[:200].strip()
        results.append({
            "title":   t,
            "url":     l,
            "summary": d,
            "image":   img_url.group(1) if img_url else "",
            "date":    pub.group(1)[:30] if pub else "",
            "source":  source,
        })
    return results


def get_ai_news(limit_per_feed: int = 5) -> List[Dict]:
    """Fetch AI news from multiple free RSS feeds."""
    all_news = []
    for source, feed_url in AI_RSS_FEEDS:
        try:
            r = requests.get(feed_url, timeout=TIMEOUT,
                             headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code == 200:
                all_news.extend(_parse_rss(r.text, source, limit_per_feed))
        except Exception:
            continue
    return all_news
