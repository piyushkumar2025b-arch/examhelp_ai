"""
image_search_engine.py — AI-Powered Reverse Image Search + Visual Intelligence
Uses Gemini Vision to describe the image, then searches the web for related content.
Returns 20+ highly relevant links with previews.
"""
from __future__ import annotations
import base64, json, re, io
from typing import Optional

VISION_SYSTEM = """\
You are a precise image analysis engine. Analyze the image and extract:
1. Main subject(s) — be specific (names, breeds, models, styles, locations if identifiable)
2. Key visual attributes (colors, shapes, style, era, context)
3. Category (person, animal, landmark, product, artwork, food, nature, vehicle, etc.)
4. Suggested search queries to find this image or very similar ones (give 5-8 different queries, most specific first)
5. Any text visible in the image

Respond ONLY with a JSON object:
{
  "description": "Brief description of the image",
  "main_subject": "The primary subject/topic",
  "category": "Category",
  "tags": ["tag1", "tag2", ...],
  "search_queries": ["most specific query", "broader query", ...],
  "visible_text": "Any text in image or empty string",
  "is_person": false
}
"""

SEARCH_SYSTEM = """\
You are a web research assistant. Given image analysis data, generate a comprehensive list of 25 highly relevant links where someone could find this image or very similar content.

For each link provide:
- A realistic, working URL to a page that WOULD contain this type of image
- A descriptive title
- A brief explanation of why it's relevant

Focus on: image databases, Wikipedia, news sites, official websites, stock photo sites (for the type), social platforms, academic sources, product pages, etc.

Respond ONLY with a JSON array of objects:
[
  {"url": "https://...", "title": "...", "reason": "...", "domain": "...", "type": "image_host|encyclopedia|news|official|social|stock"},
  ...
]
Generate exactly 25 items. Make URLs realistic and domain-appropriate.
"""

def _gemini_analyze_image(image_bytes: bytes, mime: str = "image/jpeg") -> Optional[dict]:
    """Uses Gemini Vision to analyze the image and extract search queries."""
    import os
    import requests as req
    
    gemini_keys = [v for k, v in os.environ.items() if k.startswith("GEMINI_API_KEY_") and v]
    if not gemini_keys:
        return None
    
    b64 = base64.b64encode(image_bytes).decode()
    
    for key in gemini_keys[:3]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": VISION_SYSTEM + "\n\nAnalyze this image and respond with JSON only:"},
                        {"inline_data": {"mime_type": mime, "data": b64}}
                    ]
                }],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024}
            }
            resp = req.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                # Extract JSON
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
        except Exception:
            continue
    return None

def _groq_generate_links(analysis: dict) -> list[dict]:
    """Uses Groq LLaMA to generate 25 relevant links based on image analysis."""
    from utils.groq_client import chat_with_groq
    
    prompt = f"""Image Analysis Data:
{json.dumps(analysis, indent=2)}

Based on this image analysis, generate 25 highly relevant links where someone could find this image or very similar content online. 
Main subject: {analysis.get('main_subject', 'unknown')}
Category: {analysis.get('category', 'unknown')}
Search queries that work for this: {', '.join(analysis.get('search_queries', []))}

Return ONLY a JSON array of 25 link objects with fields: url, title, reason, domain, type."""

    try:
        result, success = chat_with_groq(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SEARCH_SYSTEM,
            model="llama-4-scout-17b-16e-instruct",
        )
        if success and result:
            match = re.search(r'\[.*\]', result, re.DOTALL)
            if match:
                return json.loads(match.group(0))
    except Exception:
        pass
    return []

def _web_search_for_image(queries: list[str]) -> list[dict]:
    """Does actual web searches for the image queries using DuckDuckGo."""
    results = []
    try:
        import requests as req
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ExamHelp/1.0)"}
        seen_domains = set()
        
        for query in queries[:4]:  # use top 4 queries
            try:
                encoded = query.replace(" ", "+")
                url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
                resp = req.get(url, headers=headers, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    # Related topics
                    for item in data.get("RelatedTopics", [])[:5]:
                        if isinstance(item, dict) and item.get("FirstURL") and item.get("Text"):
                            domain = re.search(r'https?://([^/]+)', item["FirstURL"])
                            dom = domain.group(1) if domain else "unknown"
                            if dom not in seen_domains:
                                seen_domains.add(dom)
                                results.append({
                                    "url": item["FirstURL"],
                                    "title": item["Text"][:80],
                                    "reason": f"Found via search: '{query}'",
                                    "domain": dom,
                                    "type": "search_result"
                                })
                    # Abstract URL
                    if data.get("AbstractURL") and data.get("AbstractText"):
                        domain = re.search(r'https?://([^/]+)', data["AbstractURL"])
                        dom = domain.group(1) if domain else "unknown"
                        if dom not in seen_domains:
                            seen_domains.add(dom)
                            results.append({
                                "url": data["AbstractURL"],
                                "title": data.get("Heading", "Related Article"),
                                "reason": data["AbstractText"][:100],
                                "domain": dom,
                                "type": "encyclopedia"
                            })
            except Exception:
                continue
    except Exception:
        pass
    return results

def search_by_image(
    image_bytes: bytes,
    mime: str = "image/jpeg",
    filename: str = "image.jpg"
) -> dict:
    """
    Full pipeline: analyze image → generate search queries → find 20+ related links.
    Returns:
    {
        "analysis": {...},
        "links": [...],  # 20+ links
        "search_queries": [...],
        "error": "..." or None
    }
    """
    # Step 1: Analyze with Gemini Vision
    analysis = _gemini_analyze_image(image_bytes, mime)
    
    if not analysis:
        # Fallback analysis
        analysis = {
            "description": f"Uploaded image: {filename}",
            "main_subject": filename.replace("_", " ").replace("-", " ").split(".")[0],
            "category": "image",
            "tags": ["image", "photo"],
            "search_queries": [filename.split(".")[0], "similar images", "photo gallery"],
            "visible_text": "",
            "is_person": False
        }
    
    # Step 2: Generate links via AI
    ai_links = _groq_generate_links(analysis)
    
    # Step 3: Real web search for extra links
    web_links = _web_search_for_image(analysis.get("search_queries", []))
    
    # Merge and deduplicate
    all_links = []
    seen_urls = set()
    
    for link in (web_links + ai_links):
        url = link.get("url", "")
        if url and url not in seen_urls and url.startswith("http"):
            seen_urls.add(url)
            all_links.append(link)
    
    # If we have fewer than 20 from the above, add Google/Bing reverse image links
    base_queries = analysis.get("search_queries", [filename])
    if len(all_links) < 20:
        # Add static reverse image search links
        q_encoded = base_queries[0].replace(" ", "+") if base_queries else "image"
        static_links = [
            {
                "url": f"https://www.google.com/search?q={q_encoded}&tbm=isch",
                "title": f"Google Images: {base_queries[0] if base_queries else 'Search'}",
                "reason": "Direct Google Image search for this subject",
                "domain": "google.com",
                "type": "image_search"
            },
            {
                "url": f"https://www.bing.com/images/search?q={q_encoded}",
                "title": f"Bing Images: {base_queries[0] if base_queries else 'Search'}",
                "reason": "Bing Image search results",
                "domain": "bing.com",
                "type": "image_search"
            },
            {
                "url": f"https://yandex.com/images/search?text={q_encoded}",
                "title": f"Yandex Images: {base_queries[0] if base_queries else 'Search'}",
                "reason": "Yandex reverse image search",
                "domain": "yandex.com",
                "type": "image_search"
            },
            {
                "url": f"https://tineye.com/search?url=",
                "title": "TinEye Reverse Image Search",
                "reason": "Find exact or similar images across the web",
                "domain": "tineye.com",
                "type": "reverse_image"
            },
            {
                "url": f"https://lens.google.com/",
                "title": "Google Lens",
                "reason": "Google Lens identifies objects, text and finds similar images",
                "domain": "lens.google.com",
                "type": "reverse_image"
            },
            {
                "url": f"https://en.wikipedia.org/wiki/Special:Search?search={q_encoded}",
                "title": f"Wikipedia: {base_queries[0] if base_queries else 'Search'}",
                "reason": "Wikipedia encyclopedia entry for this subject",
                "domain": "wikipedia.org",
                "type": "encyclopedia"
            },
            {
                "url": f"https://unsplash.com/s/photos/{q_encoded}",
                "title": f"Unsplash Photos: {base_queries[0] if base_queries else 'Search'}",
                "reason": "High-quality free photos of this subject",
                "domain": "unsplash.com",
                "type": "stock"
            },
            {
                "url": f"https://www.shutterstock.com/search/{q_encoded}",
                "title": f"Shutterstock: {base_queries[0] if base_queries else 'Search'}",
                "reason": "Stock photos and images of this subject",
                "domain": "shutterstock.com",
                "type": "stock"
            },
            {
                "url": f"https://www.flickr.com/search/?q={q_encoded}",
                "title": f"Flickr: {base_queries[0] if base_queries else 'Search'}",
                "reason": "Community photo collection",
                "domain": "flickr.com",
                "type": "social"
            },
            {
                "url": f"https://www.reddit.com/search/?q={q_encoded}&type=link",
                "title": f"Reddit: {base_queries[0] if base_queries else 'Search'}",
                "reason": "Reddit community discussions and images",
                "domain": "reddit.com",
                "type": "social"
            },
            {
                "url": f"https://www.pinterest.com/search/pins/?q={q_encoded}",
                "title": f"Pinterest: {base_queries[0] if base_queries else 'Search'}",
                "reason": "Curated images and visual ideas",
                "domain": "pinterest.com",
                "type": "social"
            },
            {
                "url": f"https://twitter.com/search?q={q_encoded}&f=image",
                "title": f"Twitter/X Images: {base_queries[0] if base_queries else 'Search'}",
                "reason": "Recent images shared on Twitter/X",
                "domain": "twitter.com",
                "type": "social"
            },
        ]
        for link in static_links:
            if link["url"] not in seen_urls:
                seen_urls.add(link["url"])
                all_links.append(link)

    return {
        "analysis": analysis,
        "links": all_links[:30],  # Return up to 30 links
        "search_queries": analysis.get("search_queries", []),
        "error": None
    }
