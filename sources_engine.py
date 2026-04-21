"""
sources_engine.py — Best Sources Generator for ExamHelp AI
- Text topic OR image upload
- AI identifies image subject (Gemini vision)
- DuckDuckGo, Wikipedia, CrossRef, arXiv, News sources
- Quality scoring (.edu/.gov > Wikipedia > .org > news > other)
- AI structured summary (3 paragraphs + key facts + misconceptions)
- Export sources as PDF or clipboard copy
"""
from __future__ import annotations
import streamlit as st
import requests
import urllib.parse
import json
import time
from typing import Optional, List, Dict


# ─────────────────────────────────────────────────────────────────────────────
# AI HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _ai_generate(prompt: str, image_bytes: Optional[bytes] = None, max_tokens: int = 1024) -> str:
    """Call AI engine — with optional image for vision."""
    try:
        from utils import ai_engine
        if image_bytes:
            return ai_engine.generate_with_image(prompt, image_bytes, max_tokens=max_tokens)
        return ai_engine.generate(prompt, max_tokens=max_tokens)
    except Exception:
        try:
            from utils.groq_client import chat_with_groq
            return chat_with_groq([{"role": "user", "content": prompt}], max_tokens=max_tokens)
        except Exception:
            return ""


# ─────────────────────────────────────────────────────────────────────────────
# QUALITY SCORING
# ─────────────────────────────────────────────────────────────────────────────

def _quality_score(url: str, source_type: str) -> int:
    """Score a source URL by domain quality."""
    url_lower = url.lower()
    if ".edu" in url_lower: return 95
    if ".gov" in url_lower: return 95
    if "arxiv.org" in url_lower: return 93
    if "pubmed" in url_lower or "ncbi.nlm.nih.gov" in url_lower: return 92
    if "doi.org" in url_lower: return 90
    if "wikipedia.org" in url_lower: return 88
    if ".org" in url_lower: return 80
    if "nature.com" in url_lower or "science.org" in url_lower: return 92
    if source_type == "Academic": return 88
    if source_type == "News": return 70
    return 65


def _source_type(url: str) -> str:
    url_lower = url.lower()
    if any(x in url_lower for x in ["arxiv", "pubmed", "ncbi", "doi", "scholar", "jstor", "researchgate"]): return "Academic"
    if any(x in url_lower for x in [".edu", ".gov"]): return "Official"
    if "wikipedia.org" in url_lower: return "Encyclopedia"
    if any(x in url_lower for x in ["news", "bbc", "reuters", "guardian", "times", "post", "cnn", "ndtv"]): return "News"
    return "Web"


TYPE_EMOJI = {
    "Academic": "🎓",
    "Official": "🏛️",
    "Encyclopedia": "📖",
    "News": "📰",
    "Web": "🌐",
}

TYPE_COLOR = {
    "Academic": "#6366f1",
    "Official": "#0891b2",
    "Encyclopedia": "#059669",
    "News": "#d97706",
    "Web": "#6b7280",
}


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE FETCHERS
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_wikipedia(topic: str) -> List[Dict]:
    sources = []
    try:
        slug = urllib.parse.quote(topic.replace(" ", "_"))
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}",
            timeout=6, headers={"User-Agent": "ExamHelpAI/1.0"}
        )
        if r.status_code == 200:
            d = r.json()
            url = d.get("content_urls", {}).get("desktop", {}).get("page", "")
            if url:
                sources.append({
                    "title": d.get("title", topic),
                    "url": url,
                    "snippet": d.get("extract", "")[:300],
                    "type": "Encyclopedia",
                    "quality_score": 88,
                })
    except Exception:
        pass

    # Also search Wikipedia
    try:
        r = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(topic)}&limit=3&format=json",
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            titles, _, urls = data[1], data[2], data[3]
            for t, u in zip(titles, urls):
                if u and u not in [s["url"] for s in sources]:
                    sources.append({
                        "title": t,
                        "url": u,
                        "snippet": "",
                        "type": "Encyclopedia",
                        "quality_score": 85,
                    })
    except Exception:
        pass
    return sources[:3]


def _fetch_arxiv(topic: str) -> List[Dict]:
    sources = []
    try:
        query = urllib.parse.quote(topic)
        r = requests.get(
            f"https://export.arxiv.org/api/query?search_query=all:{query}&max_results=3&sortBy=relevance",
            timeout=7
        )
        if r.status_code == 200:
            import re
            entries = re.findall(r"<entry>(.*?)</entry>", r.text, re.DOTALL)
            for entry in entries[:3]:
                title_m = re.search(r"<title>(.*?)</title>", entry)
                link_m  = re.search(r'<id>(.*?)</id>', entry)
                summ_m  = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                if title_m and link_m:
                    sources.append({
                        "title": title_m.group(1).strip().replace("\n", " "),
                        "url": link_m.group(1).strip(),
                        "snippet": (summ_m.group(1).strip()[:250] if summ_m else ""),
                        "type": "Academic",
                        "quality_score": 93,
                    })
    except Exception:
        pass
    return sources


def _fetch_crossref(topic: str) -> List[Dict]:
    sources = []
    try:
        r = requests.get(
            f"https://api.crossref.org/works?query={urllib.parse.quote(topic)}&rows=3",
            timeout=6, headers={"User-Agent": "ExamHelpAI/1.0 (mailto:examhelp@ai.com)"}
        )
        if r.status_code == 200:
            items = r.json().get("message", {}).get("items", [])
            for item in items[:3]:
                title_list = item.get("title", [])
                doi = item.get("DOI", "")
                if title_list and doi:
                    sources.append({
                        "title": title_list[0],
                        "url": f"https://doi.org/{doi}",
                        "snippet": f"DOI: {doi}",
                        "type": "Academic",
                        "quality_score": 92,
                    })
    except Exception:
        pass
    return sources


def _fetch_duckduckgo(topic: str) -> List[Dict]:
    sources = []
    try:
        r = requests.get(
            f"https://api.duckduckgo.com/?q={urllib.parse.quote(topic)}&format=json&no_redirect=1",
            timeout=6
        )
        if r.status_code == 200:
            data = r.json()
            # Abstract
            if data.get("AbstractURL"):
                sources.append({
                    "title": data.get("Heading", topic),
                    "url": data["AbstractURL"],
                    "snippet": data.get("AbstractText", "")[:300],
                    "type": "Web",
                    "quality_score": _quality_score(data["AbstractURL"], "Web"),
                })
            # Related topics
            for rel in data.get("RelatedTopics", [])[:4]:
                if isinstance(rel, dict) and rel.get("FirstURL"):
                    sources.append({
                        "title": rel.get("Text", "")[:80],
                        "url": rel["FirstURL"],
                        "snippet": rel.get("Text", "")[:200],
                        "type": _source_type(rel["FirstURL"]),
                        "quality_score": _quality_score(rel["FirstURL"], "Web"),
                    })
    except Exception:
        pass
    return sources[:4]


def gather_all_sources(topic: str, instructions: str = "") -> List[Dict]:
    """Gather sources from all providers, deduplicate, and rank by quality."""
    all_sources: List[Dict] = []

    all_sources.extend(_fetch_wikipedia(topic))
    all_sources.extend(_fetch_arxiv(topic))
    all_sources.extend(_fetch_crossref(topic))
    all_sources.extend(_fetch_duckduckgo(topic))

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for s in all_sources:
        if s["url"] and s["url"] not in seen_urls:
            seen_urls.add(s["url"])
            # Re-score with our scoring function
            s["quality_score"] = max(s["quality_score"], _quality_score(s["url"], s["type"]))
            s["type_emoji"] = TYPE_EMOJI.get(s["type"], "🌐")
            s["type_color"] = TYPE_COLOR.get(s["type"], "#6b7280")
            unique.append(s)

    # Sort by quality score
    unique.sort(key=lambda x: x["quality_score"], reverse=True)
    return unique[:12]


# ─────────────────────────────────────────────────────────────────────────────
# AI SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def generate_ai_summary(topic: str, instructions: str = "") -> dict:
    """Generate structured AI summary of a topic."""
    inst_part = f"Special focus: {instructions}. " if instructions.strip() else ""
    prompt = (
        f"You are a research assistant. {inst_part}Topic: '{topic}'\n\n"
        f"Provide a comprehensive response in this EXACT markdown format:\n\n"
        f"## 📖 Overview\n[3 paragraphs explaining the topic clearly]\n\n"
        f"## 🔑 Key Facts\n- [fact 1]\n- [fact 2]\n- [fact 3]\n- [fact 4]\n- [fact 5]\n\n"
        f"## ❗ Why It Matters\n[1-2 paragraphs on real-world significance]\n\n"
        f"## 🚫 Common Misconceptions\n- [misconception 1 → truth]\n- [misconception 2 → truth]\n\n"
        f"## 📚 Learning Path\n[Brief guide on how to study this topic in depth]"
    )
    content = _ai_generate(prompt, max_tokens=1200)
    return {"content": content, "topic": topic}


def identify_image_subject(image_bytes: bytes) -> str:
    """Use AI vision to identify what an image shows."""
    prompt = "Identify what this image shows in 1-2 sentences. Be specific and precise."
    result = _ai_generate(prompt, image_bytes=image_bytes, max_tokens=100)
    if not result:
        return ""
    return result.strip()


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def sources_to_markdown(sources: List[Dict], topic: str) -> str:
    """Format sources as clean markdown for download."""
    lines = [f"# Best Sources for: {topic}\n", f"*Generated by ExamHelp AI*\n\n---\n"]
    for i, s in enumerate(sources, 1):
        lines.append(f"### {i}. {s['title']}")
        lines.append(f"- **Type:** {s['type_emoji']} {s['type']}")
        lines.append(f"- **Quality Score:** {s['quality_score']}/100")
        lines.append(f"- **URL:** {s['url']}")
        if s.get("snippet"):
            lines.append(f"- **Preview:** {s['snippet'][:200]}")
        lines.append("")
    return "\n".join(lines)


def sources_to_pdf_bytes(sources: List[Dict], topic: str, summary: str = "") -> Optional[bytes]:
    """Export sources and summary to PDF."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        import io

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                topMargin=50, bottomMargin=50,
                                leftMargin=60, rightMargin=60)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle("Title", parent=styles["Title"],
                                     fontSize=18, textColor=colors.HexColor("#4f46e5"))
        story.append(Paragraph(f"Best Sources: {topic}", title_style))
        story.append(Spacer(1, 12))

        if summary:
            story.append(Paragraph("AI Summary", styles["Heading2"]))
            for line in summary.split("\n")[:20]:
                if line.strip():
                    story.append(Paragraph(line.strip(), styles["BodyText"]))
            story.append(Spacer(1, 12))

        story.append(Paragraph("Sources", styles["Heading2"]))
        for i, s in enumerate(sources, 1):
            story.append(Paragraph(f"{i}. {s['title']}", styles["Heading3"]))
            story.append(Paragraph(
                f"Type: {s['type']} | Quality: {s['quality_score']}/100 | <link href='{s['url']}'>{s['url'][:60]}</link>",
                styles["BodyText"]
            ))
            if s.get("snippet"):
                story.append(Paragraph(s["snippet"][:200], styles["BodyText"]))
            story.append(Spacer(1, 8))

        doc.build(story)
        return buf.getvalue()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT PAGE
# ─────────────────────────────────────────────────────────────────────────────

def render_sources_page():
    """Main Streamlit page for Best Sources Generator."""
    st.markdown("""
<style>
.src-card{background:rgba(15,23,42,0.7);border:1px solid rgba(255,255,255,0.08);
border-radius:14px;padding:16px 20px;margin:8px 0;transition:all .2s ease;}
.src-card:hover{border-color:rgba(99,102,241,0.4);transform:translateX(4px);}
.src-badge{display:inline-block;padding:3px 10px;border-radius:100px;
font-size:.72rem;font-weight:700;letter-spacing:1px;margin-right:8px;}
.src-quality{height:4px;border-radius:100px;margin-top:8px;background:rgba(255,255,255,0.05);}
.src-q-fill{height:100%;border-radius:100px;background:linear-gradient(90deg,#6366f1,#8b5cf6);}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.07),rgba(6,182,212,0.04));
border:1px solid rgba(99,102,241,0.15);border-radius:20px;padding:28px 32px;margin-bottom:24px;">
  <div style="font-family:monospace;font-size:10px;letter-spacing:4px;
  color:rgba(99,102,241,0.6);text-transform:uppercase;margin-bottom:8px;">AI RESEARCH ENGINE</div>
  <div style="font-size:1.8rem;font-weight:900;color:#fff;margin-bottom:6px;">🔍 Best Sources Generator</div>
  <div style="color:rgba(255,255,255,0.45);font-size:.9rem;">
    Wikipedia · arXiv · CrossRef · DuckDuckGo · All free, no keys — quality-ranked instantly.
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Input Section ─────────────────────────────────────────────────────────
    col_in, col_img = st.columns([3, 1])
    with col_in:
        topic = st.text_area(
            "📝 Enter topic or paste text",
            placeholder="e.g. CRISPR Gene Editing, Quantum Computing, French Revolution, Climate Change...",
            height=100, key="src_topic"
        )
    with col_img:
        img_file = st.file_uploader("📷 Or upload image", type=["jpg","jpeg","png","webp"], key="src_img")
        if img_file:
            st.image(img_file, use_column_width=True)

    instructions = st.text_input(
        "🎯 Custom focus (optional)",
        placeholder="e.g. Focus on Indian sources, academic papers only, historical perspective...",
        key="src_instructions"
    )

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        search_btn = st.button("🔍 Find Best Sources", type="primary", use_container_width=True, key="src_search")
    with col_btn2:
        ai_only = st.checkbox("AI Summary only", key="src_ai_only")

    # ── Image Topic Detection ─────────────────────────────────────────────────
    detected_topic = topic.strip()
    if img_file and not topic.strip():
        with st.spinner("🤖 Identifying image subject..."):
            detected_topic = identify_image_subject(img_file.read())
            if detected_topic:
                st.info(f"🔍 **Detected topic:** {detected_topic}")
            else:
                st.warning("Could not identify image. Please also enter a topic manually.")

    # ── Main Search ───────────────────────────────────────────────────────────
    if search_btn and detected_topic:
        tabs = st.tabs(["📚 Sources", "🤖 AI Summary", "📥 Export"])

        with tabs[0]:
            if not ai_only:
                with st.spinner("🔍 Searching Wikipedia, arXiv, CrossRef, DuckDuckGo..."):
                    sources = gather_all_sources(detected_topic, instructions)
                    st.session_state["src_sources"] = sources
                    st.session_state["src_topic_saved"] = detected_topic

                if sources:
                    st.markdown(f"Found **{len(sources)} sources** ranked by quality")

                    # Filter bar
                    type_filter = st.multiselect(
                        "Filter by type",
                        ["Academic", "Official", "Encyclopedia", "News", "Web"],
                        default=["Academic", "Official", "Encyclopedia", "News", "Web"],
                        key="src_filter"
                    )
                    filtered = [s for s in sources if s["type"] in type_filter]

                    for s in filtered:
                        color = s.get("type_color", "#6b7280")
                        emoji = s.get("type_emoji", "🌐")
                        st.markdown(f"""
<div class="src-card">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
    <span class="src-badge" style="background:{color}22;color:{color};">{emoji} {s['type']}</span>
    <span style="font-size:.75rem;color:#94a3b8;">Quality: {s['quality_score']}/100</span>
  </div>
  <div style="font-weight:700;color:#f8fafc;margin-bottom:4px;">{s['title']}</div>
  <div style="font-size:.8rem;color:#6366f1;word-break:break-all;margin-bottom:6px;">
    <a href="{s['url']}" target="_blank" style="color:#818cf8;">{s['url'][:80]}{'...' if len(s['url']) > 80 else ''} →</a>
  </div>
  {f'<div style="font-size:.82rem;color:#94a3b8;">{s["snippet"][:200]}...</div>' if s.get("snippet") else ""}
  <div class="src-quality"><div class="src-q-fill" style="width:{s['quality_score']}%;"></div></div>
</div>
""", unsafe_allow_html=True)
                else:
                    st.warning("No sources found. Try a different topic or check your internet connection.")
            else:
                st.info("AI Summary only mode — switch to 'AI Summary' tab.")

        with tabs[1]:
            with st.spinner("🤖 Generating AI structured summary..."):
                summary_data = generate_ai_summary(detected_topic, instructions)
                st.session_state["src_summary"] = summary_data["content"]

            if summary_data["content"]:
                st.markdown(summary_data["content"])
            else:
                st.error("AI summary unavailable. Check API key.")

        with tabs[2]:
            stored_sources = st.session_state.get("src_sources", [])
            stored_topic   = st.session_state.get("src_topic_saved", detected_topic)
            stored_summary = st.session_state.get("src_summary", "")

            if stored_sources:
                md_text = sources_to_markdown(stored_sources, stored_topic)
                full_text = f"{md_text}\n\n---\n\n## AI Summary\n\n{stored_summary}"
            else:
                md_text = stored_summary
                full_text = stored_summary

            st.markdown("### 📥 Download Sources")
            c1, c2, c3 = st.columns(3)

            with c1:
                st.download_button(
                    "⬇️ Download Markdown",
                    full_text.encode(),
                    file_name=f"sources_{detected_topic[:30].replace(' ','_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="src_dl_md"
                )
            with c2:
                if stored_sources:
                    pdf_bytes = sources_to_pdf_bytes(stored_sources, stored_topic, stored_summary)
                    if pdf_bytes:
                        st.download_button(
                            "⬇️ Download PDF",
                            pdf_bytes,
                            file_name=f"sources_{detected_topic[:30].replace(' ','_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="src_dl_pdf"
                        )
                    else:
                        st.info("Install `reportlab` for PDF: `pip install reportlab`")
            with c3:
                st.markdown("**📋 Copy Sources**")
                st.code(md_text[:2000], language="markdown")

    elif not detected_topic and search_btn:
        st.warning("Please enter a topic or upload an image.")

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="src_back"):
        st.session_state.app_mode = "chat"
        st.rerun()
