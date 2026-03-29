"""
context_focus_engine.py — Deep Internet Research Tool
"""

import streamlit as st
import requests
import re
import time
import json
from urllib.parse import urlparse
from utils import ai_engine

CONTEXT_TYPES = [
    "Technical Deep Dive", "News & Current Events", "Product Research",
    "Legal & Policy", "Medical & Health", "Financial & Markets",
    "Travel & Places", "General Knowledge", "Custom",
]

OUTPUT_FORMATS = [
    "Bullet Summary", "Full Report", "FAQ Style", "Timeline",
    "Comparison Table", "Raw Data Dump", "Executive Brief", "Reddit-style TLDR",
]

DEPTH_CONFIG = {
    "Quick (3 sources)": 3,
    "Standard (7 sources)": 7,
    "Deep (15 sources)": 15,
}

DATE_FILTERS = ["Any time", "Past week", "Past month", "Past year"]


def _web_search(query: str, num_results: int = 10) -> list:
    results = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                })
    except Exception:
        pass

    if not results:
        try:
            prompt = f"""Search the web for: "{query}"
Return a JSON array of {num_results} results. Each object: {{"title": "...", "url": "...", "snippet": "..."}}
Return ONLY real URLs from real websites. Never make up URLs."""
            raw = ai_engine.generate(prompt=prompt, model="llama-4-scout-17b-16e-instruct",
                                     json_mode=True, max_tokens=2048, temperature=0.1)
            data = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(data, list):
                results = data[:num_results]
        except Exception:
            pass

    return results


def _fetch_page_content(url: str, max_chars: int = 5000) -> dict:
    try:
        try:
            import trafilatura
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }, timeout=10)
            if resp.status_code == 200:
                text = trafilatura.extract(resp.text, include_comments=False, include_tables=True)
                if text and len(text) > 100:
                    og_image = ""
                    og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', resp.text)
                    if og_match:
                        og_image = og_match.group(1)
                    return {
                        "text": text[:max_chars],
                        "og_image": og_image,
                        "success": True,
                    }
        except ImportError:
            pass

        resp = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, timeout=10)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)
            text = re.sub(r'\n{3,}', '\n\n', text)

            og_image = ""
            og_tag = soup.find('meta', property='og:image')
            if og_tag:
                og_image = og_tag.get('content', '')

            return {"text": text[:max_chars], "og_image": og_image, "success": True}
    except Exception:
        pass
    return {"text": "", "og_image": "", "success": False}


def _summarize_source(text: str, max_words: int = 300) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def run_research(query: str, context_type: str, output_format: str, depth: str, date_filter: str, custom_format: str = "") -> dict:
    num_sources = DEPTH_CONFIG.get(depth, 7)

    search_query = query
    if date_filter == "Past week":
        search_query += " last week"
    elif date_filter == "Past month":
        search_query += " last month"
    elif date_filter == "Past year":
        search_query += " 2025 2026"

    search_results = _web_search(search_query, num_sources + 3)
    if not search_results:
        return {"error": "No search results found. Check your internet connection."}

    sources = []
    images = []
    progress_bar = st.progress(0, text="Fetching sources...")

    for i, result in enumerate(search_results[:num_sources]):
        progress_bar.progress((i + 1) / num_sources, text=f"Reading source {i+1}/{num_sources}...")
        url = result.get("url", "")
        if not url:
            continue

        page = _fetch_page_content(url)
        summary = _summarize_source(page["text"]) if page["success"] else result.get("snippet", "")

        domain = urlparse(url).netloc
        sources.append({
            "title": result.get("title", domain),
            "url": url,
            "domain": domain,
            "summary": summary,
            "raw_length": len(page.get("text", "")),
        })

        if page.get("og_image"):
            images.append(page["og_image"])

    progress_bar.progress(1.0, text="Generating report...")

    sources_text = "\n\n".join([
        f"SOURCE [{i+1}] — {s['title']} ({s['domain']})\n{s['summary']}"
        for i, s in enumerate(sources)
    ])

    format_instruction = output_format
    if output_format == "Custom" and custom_format:
        format_instruction = custom_format

    format_prompts = {
        "Bullet Summary": "Present findings as bullet points grouped by theme. Be concise.",
        "Full Report": "Write a comprehensive research report with introduction, sections, and conclusion.",
        "FAQ Style": "Present as a list of questions and detailed answers.",
        "Timeline": "Present as a chronological timeline of events/developments.",
        "Comparison Table": "Present as a comparison table using markdown table syntax.",
        "Raw Data Dump": "List all facts, statistics, and data points found, organized by source.",
        "Executive Brief": "Write a 200-word executive summary followed by key findings.",
        "Reddit-style TLDR": "Write a casual, Reddit-style TLDR. Be direct, opinionated, and include the key takeaway.",
    }

    prompt = f"""You are a research analyst. Based on the following {len(sources)} real sources, answer this research query:

QUERY: {query}
CONTEXT TYPE: {context_type}

SOURCES:
{sources_text}

OUTPUT FORMAT: {format_prompts.get(format_instruction, format_instruction)}

RULES:
- Only use information from the provided sources
- For each claim, note which source number supports it [1], [2], etc.
- Assign confidence (High/Medium/Low) to key facts based on source agreement
- Never invent facts or URLs
- Be thorough but avoid repetition"""

    try:
        response = ai_engine.generate(
            prompt=prompt,
            model="llama-4-scout-17b-16e-instruct",
            max_tokens=8192,
            temperature=0.3,
        )
    except Exception as e:
        response = f"Research generation failed: {e}"

    progress_bar.empty()

    return {
        "response": response,
        "sources": sources,
        "images": images[:8],
        "query": query,
        "num_sources": len(sources),
    }


def followup_question(question: str, previous_research: dict) -> str:
    sources_brief = "\n".join([
        f"[{i+1}] {s['title']} — {s['summary'][:200]}"
        for i, s in enumerate(previous_research.get("sources", []))
    ])

    prompt = f"""Previous research topic: {previous_research.get('query', '')}
Previous findings summary (from {previous_research.get('num_sources', 0)} sources):
{sources_brief[:3000]}

Follow-up question: {question}

Answer using the research context. If the question requires new information not in the sources, say so clearly."""

    try:
        return ai_engine.generate(prompt=prompt, model="llama-4-scout-17b-16e-instruct",
                                  max_tokens=4096, temperature=0.4)
    except Exception as e:
        return f"Follow-up failed: {e}"


def render_context_focus():
    st.markdown("""
<style>
.cf-header{background:linear-gradient(135deg,#0a0020 0%,#100018 100%);border:1px solid #4a2a8b;border-radius:16px;padding:28px 32px;margin-bottom:20px;}
.cf-title{font-size:2rem;font-weight:900;background:linear-gradient(135deg,#c084fc,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0 0 4px;}
.cf-sub{font-size:.9rem;color:#9090b8;}
.source-card{background:var(--bg2-glass);border:1px solid var(--bd-glass);border-radius:10px;padding:10px 14px;margin:6px 0;font-size:.82rem;}
.source-card:hover{border-color:var(--accent-bd);}
.confidence-high{color:#4ade80;font-weight:600;}
.confidence-medium{color:#fbbf24;font-weight:600;}
.confidence-low{color:#f87171;font-weight:600;}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="cf-header">
  <div class="cf-title">🔬 Context Focus — Deep Research</div>
  <div class="cf-sub">AI-powered internet research tool · Real sources · Multiple output formats · Follow-up analysis</div>
</div>
""", unsafe_allow_html=True)

    if "cf_research" not in st.session_state:
        st.session_state.cf_research = None
    if "cf_followup_chat" not in st.session_state:
        st.session_state.cf_followup_chat = []

    query = st.text_input("🔍 Research Topic / Query",
                          placeholder="e.g. Impact of AI on job market 2025, Best electric cars under $40k...",
                          key="cf_query")

    c1, c2 = st.columns(2)
    with c1:
        context_type = st.selectbox("📋 Context Type", CONTEXT_TYPES, key="cf_type")
        if context_type == "Custom":
            custom_type = st.text_input("Define your output format", key="cf_custom_type")
    with c2:
        output_format = st.selectbox("📄 Output Format", OUTPUT_FORMATS, key="cf_format")

    c3, c4 = st.columns(2)
    with c3:
        depth = st.selectbox("🔬 Research Depth", list(DEPTH_CONFIG.keys()), index=1, key="cf_depth")
    with c4:
        date_filter = st.selectbox("📅 Date Filter", DATE_FILTERS, key="cf_date")

    b1, b2 = st.columns([3, 1])
    with b1:
        research_btn = st.button("🚀 Start Research", type="primary", use_container_width=True,
                                 disabled=not query.strip(), key="cf_start")
    with b2:
        if st.button("💬 Back", use_container_width=True, key="cf_back"):
            st.session_state.app_mode = "chat"
            st.rerun()

    if research_btn and query.strip():
        with st.spinner("🔬 Conducting deep internet research..."):
            result = run_research(
                query, context_type, output_format, depth, date_filter,
                custom_format=st.session_state.get("cf_custom_type", "") if context_type == "Custom" else "",
            )
            st.session_state.cf_research = result
            st.session_state.cf_followup_chat = []

    if st.session_state.cf_research:
        research = st.session_state.cf_research

        if research.get("error"):
            st.error(research["error"])
        else:
            st.markdown("---")
            st.markdown(research.get("response", ""))

            st.markdown("---")
            st.markdown("### 📚 Sources")
            for i, s in enumerate(research.get("sources", [])):
                with st.expander(f"[{i+1}] {s['title'][:80]}"):
                    st.markdown(f"🌐 **{s['domain']}**")
                    st.markdown(f"🔗 [{s['url'][:80]}...]({s['url']})")
                    st.markdown(f"📝 {s['summary'][:500]}")

            images = research.get("images", [])
            if images:
                st.markdown("### 🖼️ Related Images")
                img_cols = st.columns(min(4, len(images)))
                for i, img_url in enumerate(images[:8]):
                    with img_cols[i % len(img_cols)]:
                        try:
                            st.image(img_url, use_container_width=True)
                        except Exception:
                            pass

            st.download_button(
                "📥 Download Research Report",
                data=research.get("response", "") + "\n\n---\n\n## Sources\n" +
                     "\n".join([f"[{i+1}] {s['title']} — {s['domain']} — {s['url']}"
                                for i, s in enumerate(research.get("sources", []))]),
                file_name="research_report.md",
                mime="text/markdown",
                use_container_width=True,
                key="cf_download",
            )

            st.markdown("---")
            st.markdown("### 💬 Ask Follow-up Questions")

            for msg in st.session_state.cf_followup_chat:
                icon = "🧑" if msg["role"] == "user" else "🔬"
                bg = "rgba(124,106,247,0.08)" if msg["role"] == "user" else "rgba(192,132,252,0.06)"
                st.markdown(f'<div style="background:{bg};border-radius:10px;padding:10px 14px;margin:6px 0;font-size:.9rem;">{icon} {msg["content"]}</div>',
                            unsafe_allow_html=True)

            followup_q = st.text_input("Ask a follow-up question",
                                       placeholder="e.g. What are the main counterarguments?",
                                       key="cf_followup_input")

            if st.button("📤 Ask", type="primary", use_container_width=True, key="cf_followup_btn") and followup_q.strip():
                st.session_state.cf_followup_chat.append({"role": "user", "content": followup_q})
                with st.spinner("Analyzing..."):
                    answer = followup_question(followup_q, research)
                    st.session_state.cf_followup_chat.append({"role": "assistant", "content": answer})
                st.rerun()
