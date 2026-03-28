"""
news_engine.py — AI News Hub with Live APIs
Fetches real AI news, analyzes trends, recommends best AI tools.
"""
from __future__ import annotations
import re
import time
from typing import List, Dict, Optional
from datetime import datetime

NEWS_SOURCES = [
    # Free RSS/JSON feeds
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "type": "rss"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml", "type": "rss"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "type": "rss"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/", "type": "rss"},
    {"name": "Wired AI", "url": "https://www.wired.com/feed/tag/artificial-intelligence/rss", "type": "rss"},
    {"name": "ArXiv AI", "url": "https://export.arxiv.org/rss/cs.AI", "type": "rss"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "type": "rss"},
    {"name": "Google AI Blog", "url": "https://ai.googleblog.com/feeds/posts/default", "type": "rss"},
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss", "type": "rss"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "type": "rss"},
]

GNEWS_API_KEY = "pub_81eabdf5c5644e3fa2c7c0bc5e91c1b4"

def fetch_gnews(query: str = "artificial intelligence", max_results: int = 20) -> List[Dict]:
    """Fetch news from GNews API (free tier)"""
    try:
        import requests
        url = f"https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "en",
            "country": "us",
            "max": min(max_results, 10),
            "apikey": GNEWS_API_KEY,
            "sortby": "publishedAt",
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        articles = data.get("articles", [])
        return [{
            "title": a.get("title",""),
            "description": a.get("description",""),
            "url": a.get("url",""),
            "source": a.get("source",{}).get("name",""),
            "published": a.get("publishedAt",""),
            "image": a.get("image",""),
        } for a in articles]
    except Exception:
        return []

def fetch_newsapi(query: str = "artificial intelligence", max_results: int = 20) -> List[Dict]:
    """Fetch from NewsAPI (fallback, free tier)"""
    try:
        import requests
        # Using newsdata.io free tier as backup
        url = "https://newsdata.io/api/1/news"
        params = {
            "apikey": "pub_81eabdf5c5644e3fa2c7c0bc5e91c1b4",
            "q": query,
            "language": "en",
            "category": "technology",
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        articles = data.get("results", [])
        return [{
            "title": a.get("title",""),
            "description": a.get("description","") or a.get("content",""),
            "url": a.get("link",""),
            "source": a.get("source_id",""),
            "published": a.get("pubDate",""),
            "image": a.get("image_url",""),
        } for a in articles[:max_results]]
    except Exception:
        return []

def fetch_rss_feed(url: str, source_name: str, max_items: int = 10) -> List[Dict]:
    """Fetch and parse RSS feed."""
    try:
        import requests
        import xml.etree.ElementTree as ET
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(resp.content)
        
        items = []
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        # Try RSS 2.0
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title","").strip()
            desc = item.findtext("description","").strip()
            link = item.findtext("link","").strip()
            pubdate = item.findtext("pubDate","").strip()
            if title and link:
                # Strip HTML tags from description
                desc = re.sub(r'<[^>]+>', '', desc)[:400]
                items.append({"title": title, "description": desc, "url": link, "source": source_name, "published": pubdate, "image": ""})
        
        # Try Atom feed
        if not items:
            for entry in root.findall(".//atom:entry", ns)[:max_items]:
                title = entry.findtext("atom:title", namespaces=ns, default="").strip()
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                summary = entry.findtext("atom:summary", namespaces=ns, default="").strip()
                summary = re.sub(r'<[^>]+>', '', summary)[:400]
                published = entry.findtext("atom:published", namespaces=ns, default="").strip()
                if title and link:
                    items.append({"title": title, "description": summary, "url": link, "source": source_name, "published": published, "image": ""})
        
        return items
    except Exception:
        return []

def fetch_all_ai_news(query: str = "AI artificial intelligence", max_per_source: int = 5) -> List[Dict]:
    """Fetch AI news from multiple sources."""
    all_articles = []
    
    # Primary: GNews API
    gnews_articles = fetch_gnews(query, max_results=15)
    all_articles.extend(gnews_articles)
    
    # Secondary: RSS feeds (try a few)
    rss_to_try = [
        ("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch AI"),
        ("https://venturebeat.com/category/ai/feed/", "VentureBeat AI"),
        ("https://export.arxiv.org/rss/cs.AI", "arXiv CS.AI"),
        ("https://huggingface.co/blog/feed.xml", "Hugging Face"),
    ]
    
    for rss_url, name in rss_to_try[:2]:  # Limit to avoid timeouts
        articles = fetch_rss_feed(rss_url, name, max_per_source)
        all_articles.extend(articles)
    
    # Deduplicate by title
    seen_titles = set()
    unique_articles = []
    for a in all_articles:
        title_key = a.get("title","").lower()[:50]
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(a)
    
    return unique_articles[:40]

def get_ai_tool_recommendations(use_case: str) -> str:
    """Get AI recommendations for the best tool for a given use case."""
    from utils.groq_client import chat_with_groq
    
    prompt = f"""A user wants the best AI tool for: "{use_case}"

Provide a comprehensive, current recommendation covering:

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

### 🔗 Direct Links
- Tool name: [URL]

Be specific, current, and genuinely helpful. Include GPT-4, Claude, Gemini, and specialized tools as appropriate. Today's date context: {datetime.now().strftime("%B %Y")}."""

    try:
        result = chat_with_groq(
            messages=[{"role": "user", "content": prompt}],
            model="llama-4-scout-17b-16e-instruct",
        )
        if isinstance(result, tuple): result = result[0]
        return result or "Could not generate recommendations."
    except Exception as e:
        return f"Error: {e}"

def summarize_article_with_ai(article: Dict) -> str:
    """Get AI summary and analysis of a news article."""
    from utils.groq_client import chat_with_groq
    
    title = article.get("title", "")
    desc = article.get("description", "")
    source = article.get("source", "")
    
    prompt = f"""Article from {source}:
Title: {title}
Content: {desc}

Provide a 3-sentence expert analysis:
1. What happened / what this means
2. Why it matters for the AI field
3. What to watch next / implications

Keep it sharp, informative, expert-level."""

    try:
        result = chat_with_groq(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        if isinstance(result, tuple): result = result[0]
        return result or desc
    except Exception:
        return desc

def get_ai_trend_analysis() -> str:
    """Get current AI trends analysis."""
    from utils.groq_client import chat_with_groq
    
    prompt = f"""As of {datetime.now().strftime("%B %Y")}, provide a comprehensive AI trends analysis:

## 🌊 Current AI Trends & Landscape

### 🔥 What's Hot Right Now
[Top 5 trending topics in AI]

### 🏭 Model Rankings (by capability, {datetime.now().strftime("%B %Y")})
[List top models: GPT-4o, Claude 3.5, Gemini 2.0, Llama, etc. with current capabilities]

### 💼 Best AI for Different Tasks
| Task | Best AI | Why |
|------|---------|-----|
| Coding | ... | ... |
| Writing | ... | ... |
| Research | ... | ... |
| Image Gen | ... | ... |
| Video Gen | ... | ... |
| Voice | ... | ... |
| Data Analysis | ... | ... |

### 🚀 Emerging Technologies
[3 key emerging developments]

### 💰 AI Investment & Business News
[Key business developments]

Be specific and accurate for {datetime.now().strftime("%B %Y")}."""

    try:
        result = chat_with_groq(
            messages=[{"role": "user", "content": prompt}],
            model="llama-4-scout-17b-16e-instruct",
        )
        if isinstance(result, tuple): result = result[0]
        return result or "Could not fetch trend analysis."
    except Exception as e:
        return f"Error: {e}"

TOPIC_CATEGORIES = {
    "🤖 General AI": "artificial intelligence AI machine learning",
    "💬 LLMs & Chatbots": "ChatGPT GPT Claude Gemini Llama language model chatbot",
    "🎨 Generative AI": "image generation Midjourney Stable Diffusion DALL-E Sora video AI art",
    "🔬 AI Research": "AI research paper arxiv neural network deep learning",
    "💼 AI in Business": "AI business enterprise automation productivity",
    "🏥 AI in Healthcare": "AI healthcare medical diagnosis drug discovery",
    "⚖️ AI Ethics & Policy": "AI ethics regulation policy safety alignment",
    "🚗 AI in Robotics": "AI robotics autonomous vehicle robot",
    "🎮 AI in Gaming": "AI gaming game development NPC",
    "📱 AI Tools & Apps": "AI tools apps productivity new AI release",
}
