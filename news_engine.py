"""
news_engine.py — AI News Hub v3.0
Fetches AI & general news via free RSS feeds + live JSON APIs.
Sources: RSS (TechCrunch, Verge, etc.) + SpaceFlight News + HackerNews.
All free, no API key needed.
"""
from __future__ import annotations
import re
from typing import List, Dict
from datetime import datetime
from free_apis import (
    parse_rss, duckduckgo_search, get_wikipedia_summary,
    get_spaceflight_news, get_hackernews_top,
)


NEWS_SOURCES = [
    {"name": "TechCrunch AI",   "url": "https://techcrunch.com/category/artificial-intelligence/feed/",     "type": "rss"},
    {"name": "The Verge AI",    "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",  "type": "rss"},
    {"name": "VentureBeat AI",  "url": "https://venturebeat.com/category/ai/feed/",                          "type": "rss"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/",                              "type": "rss"},
    {"name": "Wired AI",        "url": "https://www.wired.com/feed/tag/artificial-intelligence/rss",          "type": "rss"},
    {"name": "ArXiv AI",        "url": "https://export.arxiv.org/rss/cs.AI",                                 "type": "rss"},
    {"name": "OpenAI Blog",     "url": "https://openai.com/blog/rss.xml",                                    "type": "rss"},
    {"name": "Google AI Blog",  "url": "https://ai.googleblog.com/feeds/posts/default",                      "type": "rss"},
    {"name": "Anthropic News",  "url": "https://www.anthropic.com/news/rss",                                 "type": "rss"},
    {"name": "Hugging Face",    "url": "https://huggingface.co/blog/feed.xml",                               "type": "rss"},
]

TOPIC_CATEGORIES = {
    "🤖 General AI":         "artificial intelligence AI machine learning",
    "💬 LLMs & Chatbots":    "ChatGPT GPT Claude Gemini Llama language model chatbot",
    "🎨 Generative AI":      "image generation Midjourney Stable Diffusion DALL-E Sora video AI art",
    "🔬 AI Research":        "AI research paper arxiv neural network deep learning",
    "💼 AI in Business":     "AI business enterprise automation productivity",
    "🏥 AI in Healthcare":   "AI healthcare medical diagnosis drug discovery",
    "⚖️ AI Ethics & Policy": "AI ethics regulation policy safety alignment",
    "🚗 AI in Robotics":     "AI robotics autonomous vehicle robot",
    "🎮 AI in Gaming":       "AI gaming game development NPC",
    "📱 AI Tools & Apps":    "AI tools apps productivity new AI release",
}

# Reading time estimator (200 wpm average)
def _reading_time(text: str) -> int:
    words = len(text.split())
    return max(1, round(words / 200))


def _relevance_score(article: Dict, query: str) -> int:
    """Score article relevance to a query."""
    score = 0
    combined = (article.get("title", "") + " " + article.get("description", "")).lower()
    for word in query.lower().split():
        if word in combined:
            score += 3 if word in article.get("title", "").lower() else 1
    return score


def _get_optional_key(name: str) -> str:
    try:
        import streamlit as st
        return st.secrets.get(name, "") or ""
    except Exception:
        import os
        return os.environ.get(name, "")


def fetch_gnews(query: str = "artificial intelligence", max_results: int = 20) -> List[Dict]:
    gnews_key = _get_optional_key("GNEWS_API_KEY")
    if not gnews_key:
        return []
    try:
        import requests
        params = {"q": query, "lang": "en", "country": "us",
                  "max": min(max_results, 10), "apikey": gnews_key, "sortby": "publishedAt"}
        resp = requests.get("https://gnews.io/api/v4/search", params=params, timeout=10)
        articles = resp.json().get("articles", [])
        return [{
            "title": a.get("title", ""), "description": a.get("description", ""),
            "url": a.get("url", ""), "source": a.get("source", {}).get("name", ""),
            "published": a.get("publishedAt", ""), "image": a.get("image", ""),
            "reading_time": _reading_time(a.get("description", "")),
        } for a in articles]
    except Exception:
        return []


def fetch_rss_feed(url: str, source_name: str, max_items: int = 10) -> List[Dict]:
    """Fetch an RSS / Atom feed using free_apis.parse_rss (no external lib needed)."""
    raw_items = parse_rss(url, max_items=max_items)
    result = []
    for item in raw_items:
        desc = item.get("description", "")
        result.append({
            "title":        item.get("title", ""),
            "description":  desc,
            "url":          item.get("url", ""),
            "source":       source_name,
            "published":    item.get("published", ""),
            "image":        "",
            "reading_time": _reading_time(desc),
        })
    return result


def fetch_all_ai_news(query: str = "AI artificial intelligence", max_per_source: int = 6) -> List[Dict]:
    """Fetch AI news from 10 free RSS sources — no API key needed (deduped, scored, sorted)."""
    all_articles: List[Dict] = []

    # 10 free RSS feeds — all zero-auth, all public
    rss_sources = [
        ("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch AI"),
        ("https://venturebeat.com/category/ai/feed/",                     "VentureBeat AI"),
        ("https://export.arxiv.org/rss/cs.AI",                            "arXiv CS.AI"),
        ("https://huggingface.co/blog/feed.xml",                          "Hugging Face"),
        ("https://www.wired.com/feed/tag/artificial-intelligence/rss",    "Wired AI"),
        ("https://feeds.feedburner.com/oreilly/radar/atom",               "O'Reilly Radar"),
        ("https://machinelearningmastery.com/feed",                       "ML Mastery"),
        ("https://towardsdatascience.com/feed",                           "Towards Data Science"),
        ("https://bair.berkeley.edu/blog/feed.xml",                       "Berkeley AI Research"),
        ("https://ai.googleblog.com/feeds/posts/default",                 "Google AI Blog"),
    ]

    for rss_url, name in rss_sources:
        try:
            items = fetch_rss_feed(rss_url, name, max_per_source)
            all_articles.extend(items)
        except Exception:
            continue

    # GNews (if key available)
    all_articles.extend(fetch_gnews(query, max_results=15))

    # DuckDuckGo instant answer as context supplement
    try:
        ddg = duckduckgo_search(query)
        if ddg and ddg.get("abstract"):
            all_articles.insert(0, {
                "title":        ddg.get("heading", query),
                "description":  ddg.get("abstract", ""),
                "url":          ddg.get("url", ""),
                "source":       "DuckDuckGo",
                "published":    "",
                "image":        ddg.get("image", ""),
                "reading_time": _reading_time(ddg.get("abstract", "")),
            })
    except Exception:
        pass

    # Deduplicate + score + sort
    seen, unique = set(), []
    for a in all_articles:
        key = a.get("title", "").lower()[:60]
        if key and key not in seen:
            seen.add(key)
            a["relevance"] = _relevance_score(a, query)
            unique.append(a)

    unique.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    return unique[:40]


def filter_by_topic(articles: List[Dict], topic: str) -> List[Dict]:
    """Filter articles by a topic category."""
    query = TOPIC_CATEGORIES.get(topic, topic)
    keywords = query.lower().split()
    result = []
    for a in articles:
        combined = (a.get("title", "") + " " + a.get("description", "")).lower()
        if any(kw in combined for kw in keywords):
            result.append(a)
    return result


def get_ai_tool_recommendations(use_case: str) -> str:
    from utils.ai_engine import generate
    prompt = f"""USER INTENT: Best AI tool for "{use_case}"
TODAY: {datetime.now().strftime("%B %Y")}

STRUCTURED RECOMMENDATION:
1. TOP PICK: [Name] — Strongest performance, key pricing, core benefit
2. RUNNER UP: [Name] — Best alternative, who it's for
3. VALUE PICK: [Name] — Free or cost-effective option

COMPARISON TABLE:
| Tool | Core Strength | Major Weakness | Price Tier |
|------|--------------|----------------|-----------|

PRO TIPS:
- [Strategic tip specific to this use case]
- [What to avoid / common mistake]
"""
    try:
        return generate(prompt=prompt, engine_name="researcher") or "Recommendations unavailable."
    except Exception as e:
        return f"Error: {e}"


def summarize_article_with_ai(article: Dict) -> str:
    from utils.ai_engine import generate
    title  = article.get("title", "")
    desc   = article.get("description", "")

    # Try Wikipedia enrichment first (free, instant)
    wiki_context = ""
    if title:
        wiki = get_wikipedia_summary(title.split(" - ")[0][:50])
        if wiki and wiki.get("extract"):
            wiki_context = f"\nWikipedia context: {wiki['extract'][:300]}"

    prompt = f"""SOURCE: {article.get('source','')}
TITLE: {title}
CONTENT: {desc}{wiki_context}

EXPERT 3-POINT ANALYSIS:
1. SYNOPSIS: Exactly what happened — one clear sentence.
2. INDUSTRY IMPACT: How this shifts the AI landscape — be specific.
3. WHAT TO WATCH: Short-term implications or next developments.

Keep it sharp. Max 120 words total."""
    try:
        return generate(prompt=prompt, engine_name="researcher") or desc
    except Exception:
        return desc


def get_ai_trend_analysis() -> str:
    from utils.ai_engine import generate
    prompt = f"""PERIOD: {datetime.now().strftime("%B %Y")}
TASK: High-level current state of AI analysis.

REPORT:
🔥 CURRENT HOT TOPICS (5 topics, 1 sentence each)
🏆 TOP MODEL LEADERBOARD (5 models, brief ranking rationale)
🧪 EMERGING TECH (3 things currently in lab/early-release phase)
📊 MARKET SENTIMENT (2-3 sentences — investment, adoption, regulation)
"""
    try:
        return generate(prompt=prompt, engine_name="researcher") or "Trend analysis unavailable."
    except Exception as e:
        return f"Error: {e}"
