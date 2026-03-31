"""
news_engine.py — AI News Hub with Live Feeds
Fetches real AI news via free RSS feeds (no external API keys needed).
GNews/NewsData API calls silently skip if no key is provided.
"""
from __future__ import annotations
import re
import time
from typing import List, Dict, Optional
from datetime import datetime

NEWS_SOURCES = [
    {"name": "TechCrunch AI",  "url": "https://techcrunch.com/category/artificial-intelligence/feed/",        "type": "rss"},
    {"name": "The Verge AI",   "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",    "type": "rss"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/",                            "type": "rss"},
    {"name": "MIT Tech Review","url": "https://www.technologyreview.com/feed/",                                "type": "rss"},
    {"name": "Wired AI",       "url": "https://www.wired.com/feed/tag/artificial-intelligence/rss",           "type": "rss"},
    {"name": "ArXiv AI",       "url": "https://export.arxiv.org/rss/cs.AI",                                   "type": "rss"},
    {"name": "OpenAI Blog",    "url": "https://openai.com/blog/rss.xml",                                      "type": "rss"},
    {"name": "Google AI Blog", "url": "https://ai.googleblog.com/feeds/posts/default",                        "type": "rss"},
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss",                                   "type": "rss"},
    {"name": "Hugging Face",   "url": "https://huggingface.co/blog/feed.xml",                                 "type": "rss"},
]


def _get_optional_key(name: str) -> str:
    """Read an optional API key from Streamlit secrets or env — never raises."""
    try:
        import streamlit as st
        return st.secrets.get(name, "") or ""
    except Exception:
        import os
        return os.environ.get(name, "")


def fetch_gnews(query: str = "artificial intelligence", max_results: int = 20) -> List[Dict]:
    """Fetch news from GNews API if GNEWS_API_KEY is set, else return empty list."""
    gnews_key = _get_optional_key("GNEWS_API_KEY")
    if not gnews_key:
        return []
    try:
        import requests
        params = {
            "q": query, "lang": "en", "country": "us",
            "max": min(max_results, 10),
            "apikey": gnews_key, "sortby": "publishedAt",
        }
        resp = requests.get("https://gnews.io/api/v4/search", params=params, timeout=10)
        articles = resp.json().get("articles", [])
        return [{"title": a.get("title",""), "description": a.get("description",""),
                 "url": a.get("url",""), "source": a.get("source",{}).get("name",""),
                 "published": a.get("publishedAt",""), "image": a.get("image","")} for a in articles]
    except Exception:
        return []


def fetch_newsapi(query: str = "artificial intelligence", max_results: int = 20) -> List[Dict]:
    """Fetch from NewsData.io if NEWSDATA_API_KEY is set, else return empty list."""
    key = _get_optional_key("NEWSDATA_API_KEY") or _get_optional_key("GNEWS_API_KEY")
    if not key:
        return []
    try:
        import requests
        params = {"apikey": key, "q": query, "language": "en", "category": "technology"}
        resp = requests.get("https://newsdata.io/api/1/news", params=params, timeout=10)
        articles = resp.json().get("results", [])
        return [{"title": a.get("title",""), "description": a.get("description","") or a.get("content",""),
                 "url": a.get("link",""), "source": a.get("source_id",""),
                 "published": a.get("pubDate",""), "image": a.get("image_url","")}
                for a in articles[:max_results]]
    except Exception:
        return []


def fetch_rss_feed(url: str, source_name: str, max_items: int = 10) -> List[Dict]:
    """Fetch and parse an RSS/Atom feed — no API key needed."""
    try:
        import requests
        import xml.etree.ElementTree as ET
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(resp.content)
        items = []
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for item in root.findall(".//item")[:max_items]:
            title   = item.findtext("title", "").strip()
            desc    = re.sub(r'<[^>]+>', '', item.findtext("description", "").strip())[:400]
            link    = item.findtext("link", "").strip()
            pubdate = item.findtext("pubDate", "").strip()
            if title and link:
                items.append({"title": title, "description": desc, "url": link, "source": source_name, "published": pubdate, "image": ""})

        if not items:
            for entry in root.findall(".//atom:entry", ns)[:max_items]:
                title   = entry.findtext("atom:title", namespaces=ns, default="").strip()
                link_el = entry.find("atom:link", ns)
                link    = link_el.get("href", "") if link_el is not None else ""
                summary = re.sub(r'<[^>]+>', '', entry.findtext("atom:summary", namespaces=ns, default="").strip())[:400]
                pub     = entry.findtext("atom:published", namespaces=ns, default="").strip()
                if title and link:
                    items.append({"title": title, "description": summary, "url": link, "source": source_name, "published": pub, "image": ""})
        return items
    except Exception:
        return []


def fetch_all_ai_news(query: str = "AI artificial intelligence", max_per_source: int = 5) -> List[Dict]:
    """Fetch AI news from multiple free RSS sources + optional paid APIs."""
    all_articles = list(fetch_gnews(query, max_results=15))

    for rss_url, name in [
        ("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch AI"),
        ("https://venturebeat.com/category/ai/feed/", "VentureBeat AI"),
        ("https://export.arxiv.org/rss/cs.AI", "arXiv CS.AI"),
        ("https://huggingface.co/blog/feed.xml", "Hugging Face"),
    ][:2]:
        all_articles.extend(fetch_rss_feed(rss_url, name, max_per_source))

    seen, unique = set(), []
    for a in all_articles:
        key = a.get("title", "").lower()[:50]
        if key and key not in seen:
            seen.add(key)
            unique.append(a)
    return unique[:40]


def get_ai_tool_recommendations(use_case: str) -> str:
    from utils.ai_engine import generate
    prompt = f"""A user wants the best AI tool for: "{use_case}"

## 🏆 Best AI for: {use_case}

**#1 Top Pick**: [Name] — [Why it's the best, key strengths, pricing]
**#2 Runner Up**: [Name] — [What makes it good, when to choose it]
**#3 Budget Option**: [Name] — [Free/cheap option that works well]

### 📊 Quick Comparison Table
| Tool | Strengths | Weakness | Price |
|------|-----------|----------|-------|

### 💡 Pro Tips
- [Specific tip 1]
- [Specific tip 2]

Be specific, current, and genuinely helpful. Today: {datetime.now().strftime("%B %Y")}."""
    try:
        return generate(prompt=prompt) or "Could not generate recommendations."
    except Exception as e:
        return f"Error: {e}"


def summarize_article_with_ai(article: Dict) -> str:
    from utils.ai_engine import generate
    prompt = f"""Article from {article.get('source','')}:
Title: {article.get('title','')}
Content: {article.get('description','')}

Provide a 3-sentence expert analysis:
1. What happened / what this means
2. Why it matters for the AI field
3. What to watch next / implications"""
    try:
        return generate(prompt=prompt) or article.get("description", "")
    except Exception:
        return article.get("description", "")


def get_ai_trend_analysis() -> str:
    from utils.ai_engine import generate
    prompt = f"""As of {datetime.now().strftime("%B %Y")}, provide a comprehensive AI trends analysis:

## 🌊 Current AI Trends & Landscape

### 🔥 What's Hot Right Now
[Top 5 trending topics in AI]

### 🏭 Model Rankings (by capability)
[List top models with current capabilities]

### 💼 Best AI for Different Tasks
| Task | Best AI | Why |
|------|---------|-----|
| Coding | ... | ... |
| Writing | ... | ... |
| Research | ... | ... |
| Image Gen | ... | ... |

### 🚀 Emerging Technologies
[3 key emerging developments]

Be specific and accurate for {datetime.now().strftime("%B %Y")}."""
    try:
        return generate(prompt=prompt) or "Could not fetch trend analysis."
    except Exception as e:
        return f"Error: {e}"


TOPIC_CATEGORIES = {
    "🤖 General AI":          "artificial intelligence AI machine learning",
    "💬 LLMs & Chatbots":     "ChatGPT GPT Claude Gemini Llama language model chatbot",
    "🎨 Generative AI":       "image generation Midjourney Stable Diffusion DALL-E Sora video AI art",
    "🔬 AI Research":         "AI research paper arxiv neural network deep learning",
    "💼 AI in Business":      "AI business enterprise automation productivity",
    "🏥 AI in Healthcare":    "AI healthcare medical diagnosis drug discovery",
    "⚖️ AI Ethics & Policy":  "AI ethics regulation policy safety alignment",
    "🚗 AI in Robotics":      "AI robotics autonomous vehicle robot",
    "🎮 AI in Gaming":        "AI gaming game development NPC",
    "📱 AI Tools & Apps":     "AI tools apps productivity new AI release",
}
