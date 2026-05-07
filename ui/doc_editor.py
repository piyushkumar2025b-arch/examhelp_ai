"""
ui/doc_editor.py — ExamHelp AI Document Editor (rebuilt)
Rich text editor powered by Claude AI via Anthropic API.
No external auth required — uses the app's configured AI client.
"""
from __future__ import annotations
import streamlit as st
import json, re, base64, io, os

try:
    from docx import Document as _DocxDoc
    from docx.shared import Pt
    _DOCX = True
except ImportError:
    _DOCX = False


# ─── tiny AI helper ───────────────────────────────────────────────────────────
def _ai(prompt: str, max_tokens: int = 800) -> str:
    try:
        from utils.ai_engine import generate
        return generate(prompt, max_tokens=max_tokens)
    except Exception:
        try:
            from utils.groq_client import chat_with_groq
            return chat_with_groq([{"role": "user", "content": prompt}])
        except Exception as e:
            return f"[AI unavailable: {e}]"


# ─── CSS ──────────────────────────────────────────────────────────────────────
_CSS = """
<style>
.de-hero{background:linear-gradient(135deg,#0d0d1a 0%,#1a1a2e 100%);
  border:1px solid #3730a3;border-radius:18px;padding:28px 24px 22px;
  margin-bottom:20px;text-align:center;}
.de-hero h2{background:linear-gradient(90deg,#818cf8,#c084fc,#38bdf8);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  font-size:1.8rem;font-weight:800;margin:0 0 6px;}
.de-hero p{color:#94a3b8;font-size:.9rem;margin:0;}
.de-btn{background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;
  border:none;border-radius:10px;padding:8px 18px;cursor:pointer;
  font-size:.85rem;font-weight:600;transition:opacity .2s;}
.de-btn:hover{opacity:.85;}
.de-toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;
  background:#0f0f1e;border:1px solid #1e1e3a;border-radius:12px;
  padding:10px 14px;margin-bottom:14px;}
.de-stat{background:#1e1e3a;border-radius:8px;padding:6px 14px;
  color:#a5b4fc;font-size:.8rem;font-weight:600;}
</style>
"""


def render_doc_editor():
    """Full AI Document Editor — no Quill, no external deps."""
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("""
<div class="de-hero">
  <h2>✍️ AI Document Editor</h2>
  <p>Write, edit & refine documents with built-in AI tools — export to TXT or DOCX</p>
</div>
""", unsafe_allow_html=True)

    # ── state ──────────────────────────────────────────────────────────────────
    if "de_content" not in st.session_state:
        st.session_state.de_content = ""
    if "de_history" not in st.session_state:
        st.session_state.de_history = []
    if "de_title" not in st.session_state:
        st.session_state.de_title = "Untitled Document"

    # ── toolbar row ────────────────────────────────────────────────────────────
    st.markdown('<div class="de-toolbar">', unsafe_allow_html=True)
    tc1, tc2, tc3, tc4 = st.columns([3,1,1,1])
    with tc1:
        new_title = st.text_input("📄 Document Title", value=st.session_state.de_title,
                                   key="de_title_input", label_visibility="collapsed")
        if new_title != st.session_state.de_title:
            st.session_state.de_title = new_title
    with tc2:
        wc = len(st.session_state.de_content.split()) if st.session_state.de_content else 0
        st.markdown(f'<div class="de-stat">📝 {wc} words</div>', unsafe_allow_html=True)
    with tc3:
        cc = len(st.session_state.de_content)
        st.markdown(f'<div class="de-stat">🔤 {cc} chars</div>', unsafe_allow_html=True)
    with tc4:
        lc = st.session_state.de_content.count("\n") + 1 if st.session_state.de_content else 0
        st.markdown(f'<div class="de-stat">📏 {lc} lines</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── main editor ────────────────────────────────────────────────────────────
    content = st.text_area(
        "Document Content",
        value=st.session_state.de_content,
        height=380,
        key="de_main_editor",
        placeholder="Start writing your document here...\n\nTip: Use the AI tools below to enhance your writing.",
        label_visibility="collapsed",
    )
    if content != st.session_state.de_content:
        # save undo snapshot
        if st.session_state.de_content:
            st.session_state.de_history.append(st.session_state.de_content)
            if len(st.session_state.de_history) > 20:
                st.session_state.de_history.pop(0)
        st.session_state.de_content = content

    # ── AI tools ───────────────────────────────────────────────────────────────
    st.markdown("### 🤖 AI Writing Tools")
    tabs = st.tabs(["✨ Improve", "📝 Generate", "🔧 Transform", "📊 Analyse", "💾 Export"])

    # TAB 1 — IMPROVE
    with tabs[0]:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✨ Improve Writing", use_container_width=True, key="de_improve"):
                if st.session_state.de_content:
                    with st.spinner("AI polishing…"):
                        res = _ai(f"Improve the writing quality of this text. Fix grammar, clarity and flow. Return only the improved text:\n\n{st.session_state.de_content}")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = res; st.rerun()
                else:
                    st.warning("Write something first!")
        with col_b:
            if st.button("📖 Fix Grammar", use_container_width=True, key="de_grammar"):
                if st.session_state.de_content:
                    with st.spinner("Fixing grammar…"):
                        res = _ai(f"Fix all grammar, spelling and punctuation errors. Return only the corrected text:\n\n{st.session_state.de_content}")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = res; st.rerun()
        col_c, col_d = st.columns(2)
        with col_c:
            if st.button("🎯 Make Concise", use_container_width=True, key="de_concise"):
                if st.session_state.de_content:
                    with st.spinner("Trimming…"):
                        res = _ai(f"Make this text more concise and clear. Preserve all key information. Return only the result:\n\n{st.session_state.de_content}")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = res; st.rerun()
        with col_d:
            if st.button("💼 Formal Tone", use_container_width=True, key="de_formal"):
                if st.session_state.de_content:
                    with st.spinner("Adjusting tone…"):
                        res = _ai(f"Rewrite in a formal professional tone. Return only the text:\n\n{st.session_state.de_content}")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = res; st.rerun()
        if st.session_state.de_history:
            if st.button("↩️ Undo Last Change", key="de_undo"):
                st.session_state.de_content = st.session_state.de_history.pop()
                st.rerun()

    # TAB 2 — GENERATE
    with tabs[1]:
        gen_prompt = st.text_input("Describe what to generate:", placeholder="e.g. Introduction for a report on climate change", key="de_gen_prompt")
        g1, g2 = st.columns(2)
        with g1:
            if st.button("✍️ Generate Text", use_container_width=True, key="de_gen"):
                if gen_prompt:
                    with st.spinner("Generating…"):
                        res = _ai(f"Write the following. Return only the text, no preamble:\n{gen_prompt}")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = (st.session_state.de_content + "\n\n" + res).strip()
                    st.rerun()
        with g2:
            if st.button("📋 Generate Outline", use_container_width=True, key="de_outline"):
                if gen_prompt:
                    with st.spinner("Outlining…"):
                        res = _ai(f"Create a detailed document outline for: {gen_prompt}\nReturn a numbered outline with subpoints.")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = (st.session_state.de_content + "\n\n" + res).strip()
                    st.rerun()
        if st.button("📝 Continue Writing", use_container_width=True, key="de_continue"):
            if st.session_state.de_content:
                with st.spinner("Continuing…"):
                    res = _ai(f"Continue writing this document naturally for 2-3 more paragraphs:\n\n{st.session_state.de_content}")
                st.session_state.de_history.append(st.session_state.de_content)
                st.session_state.de_content = st.session_state.de_content + "\n\n" + res
                st.rerun()

    # TAB 3 — TRANSFORM
    with tabs[2]:
        t1, t2 = st.columns(2)
        with t1:
            if st.button("📋 → Bullet Points", use_container_width=True, key="de_bullets"):
                if st.session_state.de_content:
                    with st.spinner("Converting…"):
                        res = _ai(f"Convert this to clear bullet points. Return only the bullets:\n\n{st.session_state.de_content}")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = res; st.rerun()
        with t2:
            if st.button("📜 → Paragraphs", use_container_width=True, key="de_paras"):
                if st.session_state.de_content:
                    with st.spinner("Converting…"):
                        res = _ai(f"Convert these bullet points / notes into flowing paragraphs:\n\n{st.session_state.de_content}")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = res; st.rerun()
        t3, t4 = st.columns(2)
        with t3:
            if st.button("🌐 Translate (EN→Hindi)", use_container_width=True, key="de_hindi"):
                if st.session_state.de_content:
                    with st.spinner("Translating…"):
                        res = _ai(f"Translate to Hindi. Return only the Hindi text:\n\n{st.session_state.de_content}")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = res; st.rerun()
        with t4:
            if st.button("📧 → Email Format", use_container_width=True, key="de_email"):
                if st.session_state.de_content:
                    with st.spinner("Formatting…"):
                        res = _ai(f"Reformat as a professional email with subject, greeting, body and sign-off:\n\n{st.session_state.de_content}")
                    st.session_state.de_history.append(st.session_state.de_content)
                    st.session_state.de_content = res; st.rerun()

    # TAB 4 — ANALYSE
    with tabs[3]:
        if st.button("🔍 Full Analysis", use_container_width=True, key="de_analyse"):
            if st.session_state.de_content:
                with st.spinner("Analysing…"):
                    res = _ai(f"""Analyse this document and return a JSON object with these keys:
"tone" (formal/informal/academic/creative), "readability" (easy/medium/hard),
"key_topics" (list of 3-5 topics), "strengths" (list of 3), 
"improvements" (list of 3), "summary" (1 sentence).
Return only valid JSON, no markdown.

TEXT:
{st.session_state.de_content[:3000]}""")
                try:
                    s = res.find("{"); e = res.rfind("}") + 1
                    analysis = json.loads(res[s:e])
                    st.success("Analysis Complete!")
                    a1, a2 = st.columns(2)
                    with a1:
                        st.markdown(f"**🎭 Tone:** {analysis.get('tone','–')}")
                        st.markdown(f"**📖 Readability:** {analysis.get('readability','–')}")
                        st.markdown(f"**📋 Summary:** {analysis.get('summary','–')}")
                        st.markdown("**🏷️ Topics:**")
                        for t in analysis.get("key_topics", []):
                            st.markdown(f"  • {t}")
                    with a2:
                        st.markdown("**✅ Strengths:**")
                        for s2 in analysis.get("strengths", []):
                            st.markdown(f"  • {s2}")
                        st.markdown("**💡 Improvements:**")
                        for i in analysis.get("improvements", []):
                            st.markdown(f"  • {i}")
                except Exception:
                    st.info(res)
            else:
                st.warning("Write something first!")

    # TAB 5 — EXPORT
    with tabs[4]:
        e1, e2, e3 = st.columns(3)
        with e1:
            txt_bytes = st.session_state.de_content.encode("utf-8")
            st.download_button("⬇️ Download TXT", txt_bytes,
                               file_name=f"{st.session_state.de_title}.txt",
                               mime="text/plain", use_container_width=True, key="de_dl_txt")
        with e2:
            md_bytes = f"# {st.session_state.de_title}\n\n{st.session_state.de_content}".encode("utf-8")
            st.download_button("⬇️ Download MD", md_bytes,
                               file_name=f"{st.session_state.de_title}.md",
                               mime="text/markdown", use_container_width=True, key="de_dl_md")
        with e3:
            if _DOCX:
                doc = _DocxDoc()
                doc.add_heading(st.session_state.de_title, 0)
                for para in st.session_state.de_content.split("\n"):
                    doc.add_paragraph(para)
                buf = io.BytesIO(); doc.save(buf); buf.seek(0)
                st.download_button("⬇️ Download DOCX", buf.getvalue(),
                                   file_name=f"{st.session_state.de_title}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   use_container_width=True, key="de_dl_docx")
            else:
                st.info("Install python-docx for DOCX export")
        if st.button("🗑️ Clear Document", use_container_width=True, key="de_clear"):
            st.session_state.de_history.append(st.session_state.de_content)
            st.session_state.de_content = ""
            st.rerun()

    if st.button("💬 Back to Chat", use_container_width=True, key="de_back"):
        st.session_state.app_mode = "chat"; st.rerun()
