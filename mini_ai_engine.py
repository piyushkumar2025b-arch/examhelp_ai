"""
mini_ai_engine.py — Free structured-answer engine (no paid AI quota)
Sources: DuckDuckGo Instant Answers · Wikipedia · Pollinations Text · Wikidata
"""
import requests, json, re
from typing import Optional, Dict, List

TIMEOUT = 10

# ── Format templates ──────────────────────────────────────────────────────────
FORMAT_TEMPLATES = {
    "Bullet Points":   "Answer ONLY in clean bullet points (•). Be concise.",
    "Numbered List":   "Answer ONLY as a numbered list. Each item on its own line.",
    "Short Paragraph": "Answer in 2-3 short, clear paragraphs.",
    "Table":           "Answer using a Markdown table with headers.",
    "Mind-Map Text":   "Answer as a mind-map in text form: main topic → subtopics → details.",
    "Step-by-Step":    "Answer as a numbered step-by-step guide.",
    "ELI5":            "Explain like I'm 5 years old — very simple language.",
    "Custom":          "",   # user provides their own instruction
}


def ddg_instant(query: str) -> Optional[Dict]:
    """DuckDuckGo Instant Answers — no key, returns abstract + related topics."""
    try:
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        abstract = data.get("AbstractText", "")
        source   = data.get("AbstractSource", "")
        url      = data.get("AbstractURL", "")
        related  = [t.get("Text","") for t in data.get("RelatedTopics", [])[:5] if isinstance(t, dict) and t.get("Text")]
        if not abstract and not related:
            return None
        return {"abstract": abstract, "source": source, "url": url, "related": related}
    except Exception:
        return None


def wiki_summary(query: str, sentences: int = 5) -> Optional[Dict]:
    """Wikipedia summary API — no key needed."""
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(query)}",
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        return {
            "title":   data.get("title", ""),
            "extract": data.get("extract", ""),
            "url":     data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "image":   data.get("thumbnail", {}).get("source", ""),
        }
    except Exception:
        return None


def wiki_search(query: str, limit: int = 5) -> List[Dict]:
    """Wikipedia opensearch — returns titles + snippets."""
    try:
        r = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action":"query","list":"search","srsearch":query,
                    "format":"json","srlimit":limit},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return []
        results = r.json().get("query",{}).get("search",[])
        out = []
        for item in results:
            snippet = re.sub(r"<[^>]+>","",item.get("snippet",""))
            out.append({"title":item["title"],"snippet":snippet,
                        "url":f"https://en.wikipedia.org/wiki/{requests.utils.quote(item['title'])}"})
        return out
    except Exception:
        return []


def pollinations_text(prompt: str, system: str = "") -> Optional[str]:
    """
    Pollinations.ai free text generation — no key, no quota.
    Uses the /v1/chat/completions OpenAI-compatible endpoint.
    """
    try:
        payload = {
            "model": "openai",
            "messages": [
                {"role": "system", "content": system or "You are a helpful, concise assistant."},
                {"role": "user",   "content": prompt},
            ],
            "max_tokens": 800,
            "temperature": 0.5,
        }
        r = requests.post(
            "https://text.pollinations.ai/v1/chat/completions",
            json=payload,
            timeout=30,
        )
        if r.status_code != 200:
            return None
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def structured_answer(
    query: str,
    fmt: str = "Bullet Points",
    custom_instruction: str = "",
    include_sources: bool = True,
    include_wiki: bool = True,
) -> Dict:
    """
    Main function — returns:
    {
        "answer":  str,          # formatted answer
        "sources": list[dict],   # [{title, url}]
        "wiki_image": str,       # optional image url
    }
    """
    sources_list = []
    wiki_img     = ""

    # 1. Gather context from DuckDuckGo & Wikipedia
    context_parts = []
    ddg = ddg_instant(query)
    if ddg and ddg.get("abstract"):
        context_parts.append(f"DuckDuckGo: {ddg['abstract']}")
        if ddg.get("url"):
            sources_list.append({"title": ddg.get("source","DuckDuckGo"), "url": ddg["url"]})

    if include_wiki:
        wk = wiki_summary(query)
        if wk and wk.get("extract"):
            context_parts.append(f"Wikipedia: {wk['extract'][:600]}")
            if wk.get("url"):
                sources_list.append({"title": wk["title"], "url": wk["url"]})
            wiki_img = wk.get("image","")

    context = "\n\n".join(context_parts)

    # 2. Build format instruction
    fmt_instr = custom_instruction if fmt == "Custom" and custom_instruction \
                else FORMAT_TEMPLATES.get(fmt, FORMAT_TEMPLATES["Bullet Points"])

    # 3. Generate answer via Pollinations
    system_prompt = f"{fmt_instr}\n\nIf context is provided, use it. Always be accurate and concise."
    user_prompt   = f"Question: {query}"
    if context:
        user_prompt += f"\n\nContext:\n{context}"

    answer = pollinations_text(user_prompt, system=system_prompt)

    # 4. Fallback: use DuckDuckGo abstract + wiki extract directly
    if not answer:
        lines = []
        if ddg and ddg.get("abstract"):
            lines.append(f"• {ddg['abstract']}")
        if include_wiki and ddg and ddg.get("related"):
            for rel in ddg["related"][:4]:
                lines.append(f"• {rel}")
        answer = "\n".join(lines) if lines else "⚠️ Could not retrieve an answer. Try a different query."

    return {
        "answer":     answer,
        "sources":    sources_list,
        "wiki_image": wiki_img,
    }
