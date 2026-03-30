# ============================================================
# INTEGRATION REMOVED — This file has been fully commented out.
# All external service integrations, API keys, and credentials
# have been stripped for security. Do not re-enable.
# ============================================================

# """
# doc_editor.py — ExamHelp AI Document Editor
# Clean, functional rich-text editor with 22+ AI-powered tools.
# """
# 
# import streamlit as st
# import base64
# import io
# import re
# import os
# import tempfile
# import json
# from utils.groq_client import chat_with_groq, transcribe_audio
# 
# try:
#     from streamlit_quill import st_quill
#     HAS_QUILL = True
# except ImportError:
#     HAS_QUILL = False
# 
# try:
#     import docx
#     HAS_DOCX = True
# except ImportError:
#     HAS_DOCX = False
# 
# # --- TOOLKIT IMPORTS (all guarded) ---
# try:
#     import wikipedia
#     HAS_WIKI = True
# except ImportError:
#     HAS_WIKI = False
# 
# try:
#     from ddgs import DDGS
#     HAS_DDGS = True
# except ImportError:
#     try:
#         from duckduckgo_search import DDGS
#         HAS_DDGS = True
#     except ImportError:
#         HAS_DDGS = False
#         DDGS = None
# 
# try:
#     from youtube_transcript_api import YouTubeTranscriptApi
#     HAS_YT = True
# except ImportError:
#     HAS_YT = False
# 
# try:
#     from sympy import sympify, latex
#     HAS_SYMPY = True
# except ImportError:
#     HAS_SYMPY = False
# 
# try:
#     from rembg import remove as rembg_remove
#     from PIL import Image
#     HAS_REMBG = True
# except ImportError:
#     HAS_REMBG = False
# 
# try:
#     import fitz
#     HAS_FITZ = True
# except ImportError:
#     HAS_FITZ = False
# 
# try:
#     import docx2txt
#     HAS_DOCX2TXT = True
# except ImportError:
#     HAS_DOCX2TXT = False
# 
# try:
#     from newspaper import Article
#     HAS_NEWS = True
# except ImportError:
#     HAS_NEWS = False
# 
# try:
#     import pytesseract
#     from PIL import Image as PILImage
#     HAS_OCR = True
# except ImportError:
#     HAS_OCR = False
# 
# try:
#     import networkx as nx
#     import matplotlib
#     matplotlib.use("Agg")
#     import matplotlib.pyplot as plt
#     HAS_NX = True
# except ImportError:
#     HAS_NX = False
# 
# try:
#     import numpy as np
#     import plotly.graph_objects as go
#     HAS_PLOT = True
# except ImportError:
#     HAS_PLOT = False
# 
# try:
#     from sklearn.feature_extraction.text import TfidfVectorizer
#     HAS_SKLEARN = True
# except ImportError:
#     HAS_SKLEARN = False
# 
# try:
#     import google.generativeai as genai
#     HAS_GEMINI = True
# except ImportError:
#     HAS_GEMINI = False
# 
# try:
#     import speech_recognition as sr
#     HAS_SR = True
# except ImportError:
#     HAS_SR = False
# 
# try:
#     from langchain.text_splitter import RecursiveCharacterTextSplitter
#     HAS_LANGCHAIN = True
# except ImportError:
#     HAS_LANGCHAIN = False
# 
# try:
#     import pypandoc
#     HAS_PANDOC = True
# except ImportError:
#     HAS_PANDOC = False
# 
# try:
#     from bs4 import BeautifulSoup
#     import requests as _requests
#     HAS_BS4 = True
# except ImportError:
#     HAS_BS4 = False
# 
# 
# def _strip_html(html_str: str) -> str:
#     """Remove HTML tags, return plain text."""
#     return re.sub(r'<[^<]+?>', '', html_str or "")
# 
# 
# def _safe_js_string(text: str) -> str:
#     """Escape text for safe embedding inside a JS string literal."""
#     text = text.replace("\\", "\\\\")
#     text = text.replace('"', '\\"')
#     text = text.replace("'", "\\'")
#     text = text.replace("\n", " ")
#     text = text.replace("\r", " ")
#     return text
# 
# 
# def render_doc_editor():
#     """Main entry point — renders the full AI document editor."""
# 
#     # ── Inject editor CSS ──────────────────────────────────────────────
#     is_dark = st.session_state.get("theme_mode", "dark") == "dark"
#     bg = "#0f0f11" if is_dark else "#f8f9fa"
#     bg2 = "#1a1a1e" if is_dark else "#ffffff"
#     bg3 = "#27272a" if is_dark else "#f1f3f4"
#     border = "#3f3f46" if is_dark else "#dadce0"
#     text_c = "#fafafa" if is_dark else "#1f1f1f"
#     text2 = "#a1a1aa" if is_dark else "#5f6368"
#     accent = "#d97706"
#     accent_bg = "rgba(217,119,6,0.08)"
#     accent_bd = "rgba(217,119,6,0.25)"
# 
#     st.markdown(f"""
# <style>
#   .editor-topbar {{
#     display: flex; align-items: center; justify-content: space-between;
#     padding: 12px 20px; border-bottom: 1px solid {border};
#     background: {bg2}; border-radius: 12px 12px 0 0; margin-bottom: 0;
#   }}
#   .editor-topbar-left {{ display: flex; align-items: center; gap: 12px; }}
#   .editor-logo {{
#     width: 36px; height: 36px; border-radius: 10px;
#     background: linear-gradient(135deg, {accent}, #f59e0b);
#     display: flex; align-items: center; justify-content: center;
#     font-size: 18px; box-shadow: 0 2px 8px rgba(217,119,6,.3);
#   }}
#   .editor-title {{ font-size: 1.1rem; font-weight: 700; color: {text_c}; letter-spacing: -.3px; }}
#   .editor-sub {{ font-size: .72rem; color: {text2}; }}
#   .editor-toolbar {{
#     background: {bg3}; border-radius: 16px; padding: 8px 16px;
#     margin: 8px 0; display: flex; align-items: center; gap: 6px;
#     flex-wrap: wrap; border: 1px solid {border};
#   }}
#   .editor-toolbar .tbtn {{
#     padding: 5px 12px; border-radius: 8px; font-size: .82rem;
#     font-weight: 500; cursor: pointer; border: 1px solid transparent;
#     background: transparent; color: {text2}; transition: all .2s ease;
#   }}
#   .editor-toolbar .tbtn:hover {{
#     background: {accent_bg}; border-color: {accent_bd}; color: {accent};
#   }}
#   .explore-panel {{
#     background: {bg2}; border: 1px solid {border}; border-radius: 12px;
#     padding: 16px; height: 900px; overflow-y: auto;
#   }}
#   .explore-panel::-webkit-scrollbar {{ width: 4px; }}
#   .explore-panel::-webkit-scrollbar-thumb {{ background: {border}; border-radius: 4px; }}
#   .tool-header {{
#     font-size: .85rem; font-weight: 600; color: {accent};
#     margin-bottom: 12px; display: flex; align-items: center; gap: 6px;
#   }}
# </style>
# """, unsafe_allow_html=True)
# 
#     # ── Session state init ─────────────────────────────────────────────
#     if "doc_content" not in st.session_state:
#         ctx = st.session_state.get("context_text", "")
#         if ctx:
#             st.session_state.doc_content = ctx.replace('\n', '<br>')
#         else:
#             st.session_state.doc_content = "<p><i>Start typing your ideas...</i></p>"
#     if "doc_title" not in st.session_state:
#         st.session_state.doc_title = "Untitled document"
#     if "explore_open" not in st.session_state:
#         st.session_state.explore_open = True
# 
#     # ── Top bar ────────────────────────────────────────────────────────
#     st.markdown(f"""
#     <div class="editor-topbar">
#         <div class="editor-topbar-left">
#             <div class="editor-logo">📝</div>
#             <div>
#                 <div class="editor-title">ExamHelp Editor</div>
#                 <div class="editor-sub">AI-Powered Document Workspace</div>
#             </div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
# 
#     # ── Action buttons row ─────────────────────────────────────────────
#     c_back, c_polish, c_fix, c_sum, c_expand, c_gap, c_txt, c_docx, c_explore = st.columns(
#         [1.2, 1, 1, 1, 1, 0.5, 1, 1, 1.5])
# 
#     with c_back:
#         if st.button("⬅️ Back to Chat", key="ed_back"):
#             st.session_state.app_mode = "chat"
#             st.rerun()
#     with c_polish:
#         if st.button("✨ Polish", key="ed_polish"):
#             st.session_state.doc_content = _run_ai_edit(
#                 "Rewrite to sound professional and academic.",
#                 st.session_state.doc_content)
#             st.rerun()
#     with c_fix:
#         if st.button("✅ Fix Grammar", key="ed_fix"):
#             st.session_state.doc_content = _run_ai_edit(
#                 "Fix all grammar and spelling errors. Keep formatting.",
#                 st.session_state.doc_content)
#             st.rerun()
#     with c_sum:
#         if st.button("📊 Summarize", key="ed_sum"):
#             st.session_state.doc_content = _run_ai_edit(
#                 "Summarize into concise bullet points.",
#                 st.session_state.doc_content)
#             st.rerun()
#     with c_expand:
#         if st.button("🧠 Expand", key="ed_expand"):
#             st.session_state.doc_content = _run_ai_edit(
#                 "Expand on the ideas with more detail and examples.",
#                 st.session_state.doc_content)
#             st.rerun()
#     with c_txt:
#         st.download_button("⬇️ TXT", data=_strip_html(st.session_state.doc_content),
#                            file_name="ExamHelp_Doc.txt", key="ed_dl_txt")
#     with c_docx:
#         if HAS_DOCX:
#             clean_text = _strip_html(st.session_state.doc_content)
#             dr = docx.Document()
#             dr.add_heading(st.session_state.doc_title, 0)
#             for line in clean_text.split('\n'):
#                 if line.strip():
#                     dr.add_paragraph(line)
#             bio = io.BytesIO()
#             dr.save(bio)
#             st.download_button("⬇️ DOCX", data=bio.getvalue(),
#                                file_name="ExamHelp_Doc.docx",
#                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#                                key="ed_dl_docx")
#         else:
#             st.button("⬇️ DOCX", disabled=True, key="ed_dl_docx_na",
#                        help="python-docx not installed")
#     with c_explore:
#         if st.button("🔍 Toggle Toolkit" if st.session_state.explore_open else "🔍 Open Toolkit",
#                       key="ed_explore"):
#             st.session_state.explore_open = not st.session_state.explore_open
#             st.rerun()
# 
#     # ── Title input ────────────────────────────────────────────────────
#     st.session_state.doc_title = st.text_input(
#         "Document Title", value=st.session_state.doc_title,
#         label_visibility="collapsed", key="ed_title_input",
#         placeholder="Document title…")
# 
#     # ── Editor + Toolkit layout ────────────────────────────────────────
#     if st.session_state.explore_open:
#         c_editor, c_tools = st.columns([5, 3])
#     else:
#         c_editor, c_tools = st.columns([8, 0.01])
# 
#     with c_editor:
#         if HAS_QUILL:
#             html = st_quill(
#                 value=st.session_state.doc_content,
#                 placeholder="Type your document here...",
#                 html=True, key="ed_quill")
#             if html and html != st.session_state.doc_content:
#                 st.session_state.doc_content = html
#         else:
#             # Fallback to text_area if quill not installed
#             plain = _strip_html(st.session_state.doc_content)
#             edited = st.text_area("Editor", value=plain, height=600,
#                                   label_visibility="collapsed", key="ed_textarea")
#             if edited != plain:
#                 st.session_state.doc_content = edited.replace('\n', '<br>')
# 
#     with c_tools:
#         if st.session_state.explore_open:
#             st.markdown('<div class="explore-panel">', unsafe_allow_html=True)
#             _render_toolkit()
#             st.markdown('</div>', unsafe_allow_html=True)
# 
# 
# def _render_toolkit():
#     """Render the 22-tool sidebar toolkit."""
#     st.markdown('<div class="tool-header">🛠️ AI Mega-Toolkit (23 Tools)</div>',
#                 unsafe_allow_html=True)
# 
#     tool_options = [
#         "1. 🌐 Web & Wiki Search",
#         "2. 📺 YouTube Transcriber",
#         "3. 🖼️ Image Finder",
#         "4. 📈 Content Analytics",
#         "5. 🗺️ Auto-Outliner",
#         "6. 💬 Chat with Document",
#         "7. 🗂️ Flashcard AI",
#         "8. 🎙️ Whisper Dictation",
#         "9. 🧮 SymPy Math Solver",
#         "10. 🪄 Magic Image Editor",
#         "11. 📥 Universal Importer",
#         "12. 🎭 Persona Rewriter",
#         "13. 📖 Article Scraper",
#         "14. 👁️ OCR Scanner",
#         "15. 🕸️ Concept Mapper",
#         "16. 📊 Plot Generator",
#         "17. 🔑 Keyword Extractor",
#         "18. 🤖 Gemini Co-Pilot",
#         "19. 🎧 Audio Transcriber",
#         "20. 📑 Text Chunker",
#         "21. 📕 EPUB Exporter",
#         "22. 🥣 HTML Scraper",
#         "23. 🔊 Read Aloud (TTS)",
#     ]
# 
#     tool_sel = st.selectbox("Select Tool:", tool_options,
#                             label_visibility="collapsed", key="ed_tool_sel")
#     st.divider()
# 
#     # ── 1. Web & Wiki Search ──────────────────────────────────────
#     if "Web & Wiki" in tool_sel:
#         q = st.text_input("Search query", key="ed_wiki_q",
#                           placeholder="Search Wikipedia & DuckDuckGo…")
#         if st.button("🔍 Search", key="ed_wiki_btn") and q:
#             if HAS_WIKI:
#                 try:
#                     st.session_state.ed_wiki_res = wikipedia.summary(q, sentences=3)
#                 except Exception:
#                     st.session_state.ed_wiki_res = None
#             if HAS_DDGS:
#                 try:
#                     st.session_state.ed_web_res = DDGS().text(q, max_results=3)
#                 except Exception:
#                     st.session_state.ed_web_res = []
# 
#         if st.session_state.get("ed_wiki_res"):
#             st.info(st.session_state.ed_wiki_res)
#             if st.button("➕ Insert Wiki Result", key="ed_wiki_ins"):
#                 st.session_state.doc_content += (
#                     f"<br><b>Wikipedia:</b> {st.session_state.ed_wiki_res}<br>")
#                 st.rerun()
# 
#         if st.session_state.get("ed_web_res"):
#             for i, r in enumerate(st.session_state.ed_web_res):
#                 st.markdown(f"**[{r.get('title', '')}]({r.get('href', '')})**")
#                 st.caption(r.get('body', '')[:120])
#                 if st.button(f"➕ Insert #{i+1}", key=f"ed_dd_ins_{i}"):
#                     st.session_state.doc_content += (
#                         f"<br><b><a href='{r.get('href', '')}'>{r.get('title', '')}</a></b>"
#                         f": {r.get('body', '')}<br>")
#                     st.rerun()
# 
#     # ── 2. YouTube Transcriber ────────────────────────────────────
#     elif "YouTube" in tool_sel:
#         if not HAS_YT:
#             st.error("❌ youtube-transcript-api not installed.")
#         else:
#             u = st.text_input("YouTube URL", key="ed_yt_url",
#                               placeholder="https://youtube.com/watch?v=…")
#             if st.button("🎬 Fetch Transcript", key="ed_yt_btn") and u:
#                 try:
#                     vid = u.split("v=")[1].split("&")[0] if "v=" in u else u.split("/")[-1].split("?")[0]
#                     transcript = YouTubeTranscriptApi.get_transcript(vid)
#                     st.session_state.ed_yt_res = " ".join(
#                         [t['text'] for t in transcript])[:2000]
#                     st.success("✅ Transcript fetched!")
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#             if st.session_state.get("ed_yt_res"):
#                 st.text_area("Preview", st.session_state.ed_yt_res[:500],
#                              height=120, disabled=True, key="ed_yt_preview")
#                 if st.button("➕ Insert Transcript", key="ed_yt_ins"):
#                     st.session_state.doc_content += (
#                         f"<br><b>Video Notes:</b><br>{st.session_state.ed_yt_res}<br>")
#                     st.rerun()
# 
#     # ── 3. Image Finder ───────────────────────────────────────────
#     elif "Image Finder" in tool_sel:
#         if not HAS_DDGS:
#             st.error("❌ DuckDuckGo search not available.")
#         else:
#             q = st.text_input("Image search", key="ed_img_q",
#                               placeholder="Search for images…")
#             if st.button("🖼️ Find Images", key="ed_img_btn") and q:
#                 try:
#                     st.session_state.ed_img_res = DDGS().images(q, max_results=4)
#                 except Exception as e:
#                     st.error(f"❌ {e}")
#                     st.session_state.ed_img_res = []
# 
#             if st.session_state.get("ed_img_res"):
#                 for i, img in enumerate(st.session_state.ed_img_res):
#                     try:
#                         st.image(img.get('image', ''), width=250)
#                     except Exception:
#                         st.caption(f"Image #{i+1} (preview unavailable)")
#                     if st.button(f"🖼️ Embed #{i+1}", key=f"ed_img_ins_{i}"):
#                         st.session_state.doc_content += (
#                             f'<br><img src="{img.get("image", "")}" '
#                             f'style="max-width:100%; border-radius:8px;"/><br>')
#                         st.rerun()
# 
#     # ── 4. Content Analytics ──────────────────────────────────────
#     elif "Analytics" in tool_sel:
#         cx = _strip_html(st.session_state.doc_content)
#         words = len(cx.split())
#         chars = len(cx)
#         sentences = len(re.split(r'[.!?]+', cx))
#         st.metric("Words", f"{words:,}")
#         st.metric("Characters", f"{chars:,}")
#         st.metric("Sentences", sentences)
#         st.metric("Reading Time", f"{max(1, words // 200)} min")
#         st.metric("Speaking Time", f"{max(1, words // 130)} min")
# 
#     # ── 5. Auto-Outliner ──────────────────────────────────────────
#     elif "Auto-Outliner" in tool_sel:
#         if st.button("📋 Generate Outline", key="ed_outline_btn"):
#             cx = _strip_html(st.session_state.doc_content)[:4000]
#             try:
#                 st.session_state.ed_outline = chat_with_groq(
#                     [{"role": "user", "content":
#                       f"Create a structured Table of Contents with numbered sections from:\n{cx}"}],
#                     override_key=st.session_state.get("manual_api_key"),
#                     model="llama-3.1-8b-instant")
#             except Exception as e:
#                 st.error(f"❌ {e}")
# 
#         if st.session_state.get("ed_outline"):
#             st.markdown(st.session_state.ed_outline)
#             if st.button("➕ Insert at Top", key="ed_outline_ins"):
#                 st.session_state.doc_content = (
#                     f"<h3>Outline</h3><p>{st.session_state.ed_outline}</p><hr>"
#                     + st.session_state.doc_content)
#                 st.rerun()
# 
#     # ── 6. Chat with Document ─────────────────────────────────────
#     elif "Chat with Document" in tool_sel:
#         q = st.text_input("Ask about your document:", key="ed_chat_q",
#                           placeholder="What is the main argument?")
#         if st.button("💬 Ask AI", key="ed_chat_btn") and q:
#             cx = _strip_html(st.session_state.doc_content)
#             try:
#                 answer = chat_with_groq(
#                     [{"role": "user", "content":
#                       f"Answer based on this document:\n\nQ: {q}\n\nDOCUMENT:\n{cx[:8000]}"}],
#                     override_key=st.session_state.get("manual_api_key"),
#                     model="llama-3.3-70b-versatile")
#                 st.info(answer)
#             except Exception as e:
#                 st.error(f"❌ {e}")
# 
#     # ── 7. Flashcard AI ───────────────────────────────────────────
#     elif "Flashcard" in tool_sel:
#         if st.button("🗂️ Generate Flashcards", key="ed_fc_btn"):
#             cx = _strip_html(st.session_state.doc_content)[:4000]
#             try:
#                 st.session_state.ed_fc = chat_with_groq(
#                     [{"role": "user", "content":
#                       f"Create 5 study flashcards (Q: and A: format) from:\n{cx}"}],
#                     override_key=st.session_state.get("manual_api_key"),
#                     model="llama-3.1-8b-instant")
#             except Exception as e:
#                 st.error(f"❌ {e}")
# 
#         if st.session_state.get("ed_fc"):
#             st.write(st.session_state.ed_fc)
#             if st.button("➕ Append Flashcards", key="ed_fc_ins"):
#                 st.session_state.doc_content += (
#                     f"<hr><h3>Flashcards</h3><p>{st.session_state.ed_fc}</p>")
#                 st.rerun()
# 
#     # ── 8. Whisper Dictation ──────────────────────────────────────
#     elif "Whisper Dictation" in tool_sel:
#         aud = st.audio_input("🎙️ Record audio", key="ed_whisper_rec")
#         if aud and st.button("📝 Transcribe", key="ed_whisper_btn"):
#             with st.spinner("Transcribing with Whisper…"):
#                 try:
#                     audio_bytes = aud.read()
#                     tx = transcribe_audio(
#                         audio_bytes,
#                         override_key=st.session_state.get("manual_api_key"))
#                     if tx and isinstance(tx, str):
#                         st.session_state.doc_content += f"<br><i>{tx}</i>"
#                         st.success("✅ Transcribed and inserted!")
#                         st.rerun()
#                     else:
#                         st.warning("No speech detected.")
#                 except Exception as e:
#                     st.error(f"❌ Transcription failed: {e}")
# 
#     # ── 9. SymPy Math Solver ──────────────────────────────────────
#     elif "Math Solver" in tool_sel:
#         if not HAS_SYMPY:
#             st.error("❌ sympy not installed.")
#         else:
#             expr = st.text_area("Enter equation:", key="ed_math_expr",
#                                 placeholder="x**2 + 2*x - 1")
#             if st.button("🧮 Solve", key="ed_math_btn") and expr:
#                 try:
#                     result = sympify(expr).doit()
#                     st.latex(latex(result))
#                     st.session_state.ed_math_result = f"{expr} = {result}"
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#             if st.session_state.get("ed_math_result"):
#                 if st.button("➕ Insert Result", key="ed_math_ins"):
#                     st.session_state.doc_content += (
#                         f"<br><b>Math:</b> {st.session_state.ed_math_result}<br>")
#                     st.rerun()
# 
#     # ── 10. Magic Image Editor ────────────────────────────────────
#     elif "Magic Image" in tool_sel:
#         if not HAS_REMBG:
#             st.error("❌ rembg not installed.")
#         else:
#             f = st.file_uploader("Upload image", ["png", "jpg", "jpeg"],
#                                  key="ed_rembg_up")
#             if f and st.button("✂️ Remove Background", key="ed_rembg_btn"):
#                 with st.spinner("Processing…"):
#                     try:
#                         img = Image.open(f)
#                         output = rembg_remove(img)
#                         bio = io.BytesIO()
#                         output.save(bio, "PNG")
#                         enc = base64.b64encode(bio.getvalue()).decode()
#                         st.session_state.doc_content += (
#                             f'<br><img src="data:image/png;base64,{enc}" '
#                             f'style="max-width:100%; border-radius:8px;"/><br>')
#                         st.success("✅ Background removed & inserted!")
#                         st.rerun()
#                     except Exception as e:
#                         st.error(f"❌ {e}")
# 
#     # ── 11. Universal Importer ────────────────────────────────────
#     elif "Universal Importer" in tool_sel:
#         f = st.file_uploader("Upload PDF, DOCX, or PPTX",
#                              ["pdf", "docx", "pptx"], key="ed_import_up")
#         if f and st.button("📥 Extract Content", key="ed_import_btn"):
#             text = ""
#             try:
#                 if f.name.endswith(".pdf") and HAS_FITZ:
#                     doc = fitz.open(stream=f.read(), filetype="pdf")
#                     text = "\n".join(page.get_text() for page in doc)
#                 elif f.name.endswith(".docx") and HAS_DOCX2TXT:
#                     text = docx2txt.process(f)
#                 else:
#                     text = f.read().decode('utf-8', 'ignore')
# 
#                 if text.strip():
#                     st.session_state.doc_content += (
#                         f"<br><b>Imported from {f.name}:</b><br>"
#                         f"{text.replace(chr(10), '<br>')}<br>")
#                     st.success(f"✅ Imported {len(text.split())} words!")
#                     st.rerun()
#                 else:
#                     st.warning("No text extracted.")
#             except Exception as e:
#                 st.error(f"❌ {e}")
# 
#     # ── 12. Persona Rewriter ──────────────────────────────────────
#     elif "Persona" in tool_sel:
#         persona = st.selectbox("Writing style:", [
#             "Academic Scholar", "Shakespeare", "Journalist",
#             "Friendly Tutor", "Technical Writer", "Pirate 🏴‍☠️"
#         ], key="ed_persona_sel")
#         if st.button("🎭 Rewrite in Style", key="ed_persona_btn"):
#             cx = _strip_html(st.session_state.doc_content)
#             try:
#                 result = chat_with_groq(
#                     [{"role": "user", "content":
#                       f"Rewrite the following text in the style of a {persona}. "
#                       f"Return clean HTML tags (<b>, <i>, <p>, <ul>, <li>). "
#                       f"Text:\n{cx[:6000]}"}],
#                     override_key=st.session_state.get("manual_api_key"),
#                     model="llama-3.3-70b-versatile")
#                 cleaned = result.replace("```html", "").replace("```", "").strip()
#                 st.session_state.doc_content = cleaned
#                 st.success(f"✅ Rewritten as {persona}!")
#                 st.rerun()
#             except Exception as e:
#                 st.error(f"❌ {e}")
# 
#     # ── 13. Article Scraper ───────────────────────────────────────
#     elif "Article Scraper" in tool_sel:
#         if not HAS_NEWS:
#             st.error("❌ newspaper3k not installed.")
#         else:
#             u = st.text_input("Article URL:", key="ed_news_url",
#                               placeholder="https://example.com/article")
#             if st.button("📖 Scrape Article", key="ed_news_btn") and u:
#                 try:
#                     a = Article(u)
#                     a.download()
#                     a.parse()
#                     st.session_state.ed_news_text = a.text
#                     st.success(f"✅ Scraped: {a.title}")
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#             if st.session_state.get("ed_news_text"):
#                 st.text_area("Preview", st.session_state.ed_news_text[:500],
#                              height=100, disabled=True, key="ed_news_preview")
#                 if st.button("➕ Insert Article", key="ed_news_ins"):
#                     st.session_state.doc_content += (
#                         f"<br><b>Article:</b><br>"
#                         f"{st.session_state.ed_news_text.replace(chr(10), '<br>')}<br>")
#                     st.rerun()
# 
#     # ── 14. OCR Scanner ───────────────────────────────────────────
#     elif "OCR Scanner" in tool_sel:
#         if not HAS_OCR:
#             st.error("❌ pytesseract not installed or Tesseract binary missing.")
#         else:
#             f = st.file_uploader("Upload text image", ["png", "jpg", "jpeg"],
#                                  key="ed_ocr_up")
#             if f and st.button("👁️ Scan Text", key="ed_ocr_btn"):
#                 try:
#                     img = PILImage.open(f)
#                     tx = pytesseract.image_to_string(img)
#                     st.session_state.ed_ocr_text = tx
#                     st.success(f"✅ Extracted {len(tx.split())} words!")
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#             if st.session_state.get("ed_ocr_text"):
#                 st.info(st.session_state.ed_ocr_text[:300])
#                 if st.button("➕ Insert OCR Text", key="ed_ocr_ins"):
#                     st.session_state.doc_content += (
#                         f"<br><b>Scanned Text:</b> {st.session_state.ed_ocr_text}<br>")
#                     st.rerun()
# 
#     # ── 15. Concept Mapper ────────────────────────────────────────
#     elif "Concept Mapper" in tool_sel:
#         if not HAS_NX:
#             st.error("❌ networkx or matplotlib not installed.")
#         else:
#             if st.button("🕸️ Generate Concept Map", key="ed_nx_btn"):
#                 cx = _strip_html(st.session_state.doc_content)
#                 words = re.findall(r'\b[A-Z][a-z]{3,}\b', cx)
#                 if len(words) < 3:
#                     words = [w for w in cx.split() if len(w) > 5][:10]
#                 else:
#                     words = list(dict.fromkeys(words))[:10]
# 
#                 G = nx.Graph()
#                 G.add_nodes_from(words[:8])
#                 for i in range(len(words[:8]) - 1):
#                     G.add_edge(words[i], words[i + 1])
#                 if len(words) > 2:
#                     G.add_edge(words[-1], words[0])
# 
#                 fig, ax = plt.subplots(figsize=(5, 4))
#                 pos = nx.spring_layout(G, seed=42)
#                 nx.draw_networkx(G, pos, ax=ax, with_labels=True,
#                                  node_color="#fbbf24", node_size=1200,
#                                  font_size=9, font_weight="bold",
#                                  edge_color="#d97706", width=2)
#                 ax.set_facecolor("none")
#                 fig.patch.set_facecolor("none")
#                 bio = io.BytesIO()
#                 plt.savefig(bio, format="png", bbox_inches="tight",
#                             transparent=True, dpi=120)
#                 plt.close(fig)
#                 enc = base64.b64encode(bio.getvalue()).decode()
#                 st.session_state.doc_content += (
#                     f'<br><img src="data:image/png;base64,{enc}" '
#                     f'style="border-radius:8px; max-width:100%;"/><br>')
#                 st.success("✅ Concept map inserted!")
#                 st.rerun()
# 
#     # ── 16. Plot Generator ────────────────────────────────────────
#     elif "Plot Generator" in tool_sel:
#         if not HAS_PLOT:
#             st.error("❌ plotly or numpy not installed.")
#         else:
#             expr = st.text_input("Math function:", key="ed_plot_expr",
#                                  value="sin(x) * exp(-0.1*x)")
#             if st.button("📊 Plot", key="ed_plot_btn") and expr:
#                 try:
#                     x = np.linspace(0, 20, 400)
#                     ns = {"x": x, "sin": np.sin, "cos": np.cos,
#                           "exp": np.exp, "tan": np.tan, "log": np.log,
#                           "sqrt": np.sqrt, "abs": np.abs,
#                           "pi": np.pi, "e": np.e}
#                     safe_expr = expr.replace("^", "**")
#                     y = eval(safe_expr, {"__builtins__": {}}, ns)
#                     fig = go.Figure(go.Scatter(x=x, y=y, name=expr))
#                     fig.update_layout(
#                         paper_bgcolor="rgba(0,0,0,0)",
#                         plot_bgcolor="rgba(0,0,0,0)",
#                         margin=dict(t=20, b=20, l=20, r=20))
#                     st.plotly_chart(fig, use_container_width=True)
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#     # ── 17. Keyword Extractor ─────────────────────────────────────
#     elif "Keyword" in tool_sel:
#         if not HAS_SKLEARN:
#             st.error("❌ scikit-learn not installed.")
#         else:
#             if st.button("🔑 Extract Keywords", key="ed_kw_btn"):
#                 try:
#                     cx = _strip_html(st.session_state.doc_content)
#                     tf = TfidfVectorizer(stop_words='english', max_features=15)
#                     tf.fit_transform([cx])
#                     kws = list(tf.get_feature_names_out())
#                     st.session_state.ed_keywords = kws
#                     st.success(f"Keywords: {', '.join(kws)}")
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#             if st.session_state.get("ed_keywords"):
#                 if st.button("➕ Insert Keywords", key="ed_kw_ins"):
#                     st.session_state.doc_content += (
#                         f"<br><i>Keywords: {', '.join(st.session_state.ed_keywords)}</i><br>")
#                     st.rerun()
# 
#     # ── 18. Gemini Co-Pilot ───────────────────────────────────────
#     elif "Gemini" in tool_sel:
#         if not HAS_GEMINI:
#             st.error("❌ google-generativeai not installed.")
#         else:
#             cmd = st.text_input("Gemini prompt:", key="ed_gemini_cmd",
#                                 value="Summarize this beautifully.")
#             if st.button("🤖 Run Gemini", key="ed_gemini_btn") and cmd:
#                 try:
#                     api_key = os.getenv("GEMINI_API_KEY", "")
#                     if not api_key:
#                         try:
#                             api_key = st.secrets.get("GEMINI_API_KEY", "")
#                         except Exception:
#                             pass
#                     if not api_key:
#                         st.error("❌ No GEMINI_API_KEY configured.")
#                     else:
#                         genai.configure(api_key=api_key)
#                         model = genai.GenerativeModel('gemini-1.5-flash')
#                         cx = _strip_html(st.session_state.doc_content)
#                         resp = model.generate_content(
#                             f"{cmd}\n\nReturn HTML for insertion.\n\nText: {cx[:6000]}")
#                         cleaned = resp.text.replace("```html", "").replace("```", "").strip()
#                         st.session_state.doc_content = cleaned
#                         st.success("✅ Gemini edit applied!")
#                         st.rerun()
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#     # ── 19. Audio File Transcriber ────────────────────────────────
#     elif "Audio" in tool_sel and "Transcriber" in tool_sel:
#         if not HAS_SR:
#             st.error("❌ speech_recognition not installed.")
#         else:
#             f = st.file_uploader("Upload .wav file", ["wav"], key="ed_sr_up")
#             if f and st.button("🎧 Transcribe", key="ed_sr_btn"):
#                 try:
#                     rc = sr.Recognizer()
#                     with sr.AudioFile(f) as src:
#                         audio = rc.record(src)
#                     text = rc.recognize_google(audio)
#                     st.session_state.ed_sr_text = text
#                     st.success("✅ Transcribed!")
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#             if st.session_state.get("ed_sr_text"):
#                 st.info(st.session_state.ed_sr_text[:300])
#                 if st.button("➕ Insert Audio Notes", key="ed_sr_ins"):
#                     st.session_state.doc_content += (
#                         f"<br><b>Audio Transcription:</b> "
#                         f"{st.session_state.ed_sr_text}<br>")
#                     st.rerun()
# 
#     # ── 20. Text Chunker ──────────────────────────────────────────
#     elif "Text Chunker" in tool_sel:
#         if not HAS_LANGCHAIN:
#             st.error("❌ langchain not installed.")
#         else:
#             chunk_size = st.slider("Chunk size (chars)", 200, 2000, 1000,
#                                    key="ed_chunk_size")
#             if st.button("📑 Chunk Document", key="ed_chunk_btn"):
#                 try:
#                     ts = RecursiveCharacterTextSplitter(
#                         chunk_size=chunk_size, chunk_overlap=100)
#                     chunks = ts.split_text(
#                         _strip_html(st.session_state.doc_content))
#                     st.success(f"✅ Split into {len(chunks)} chunks")
#                     for i, chunk in enumerate(chunks[:5]):
#                         with st.expander(f"Chunk {i+1} ({len(chunk)} chars)"):
#                             st.text(chunk[:300])
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#     # ── 21. EPUB Exporter ─────────────────────────────────────────
#     elif "EPUB" in tool_sel:
#         if not HAS_PANDOC:
#             st.error("❌ pypandoc not installed or pandoc binary missing.")
#         else:
#             if st.button("📕 Compile EPUB", key="ed_epub_btn"):
#                 try:
#                     epub = pypandoc.convert_text(
#                         st.session_state.doc_content, 'epub', format='html')
#                     st.download_button("⬇️ Download EPUB", epub,
#                                        "Document.epub", key="ed_epub_dl")
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#     # ── 22. HTML Scraper ──────────────────────────────────────────
#     elif "HTML Scraper" in tool_sel:
#         if not HAS_BS4:
#             st.error("❌ beautifulsoup4 not installed.")
#         else:
#             u = st.text_input("URL to scrape:", key="ed_bs_url",
#                               placeholder="https://example.com")
#             if st.button("🥣 Scrape Page", key="ed_bs_btn") and u:
#                 try:
#                     resp = _requests.get(u, timeout=5)
#                     soup = BeautifulSoup(resp.text, 'html.parser')
#                     st.session_state.ed_bs_text = soup.get_text()[:2000]
#                     st.success("✅ Page scraped!")
#                 except Exception as e:
#                     st.error(f"❌ {e}")
# 
#             if st.session_state.get("ed_bs_text"):
#                 st.text_area("Preview", st.session_state.ed_bs_text[:400],
#                              height=100, disabled=True, key="ed_bs_preview")
#                 if st.button("➕ Insert Scraped Data", key="ed_bs_ins"):
#                     st.session_state.doc_content += (
#                         f"<br><code>{st.session_state.ed_bs_text}</code><br>")
#                     st.rerun()
# 
#     # ── 23. Read Aloud (TTS) ──────────────────────────────────────
#     elif "Read Aloud" in tool_sel:
#         st.markdown("*Uses your browser's native speech engine.*")
#         if st.button("🔊 Read Document Aloud", key="ed_tts_btn"):
#             cx = _strip_html(st.session_state.doc_content)[:5000]
#             safe_text = _safe_js_string(cx)
#             js_code = (
#                 '<script>'
#                 'window.parent.speechSynthesis.cancel();'
#                 f'const s=new window.parent.SpeechSynthesisUtterance("{safe_text}");'
#                 's.rate=1.0;'
#                 'window.parent.speechSynthesis.speak(s);'
#                 '</script>'
#             )
#             import streamlit.components.v1 as components
#             components.html(js_code, height=0, width=0)
#             st.success("🔊 Reading aloud…")
# 
#         if st.button("⏹️ Stop Reading", key="ed_tts_stop"):
#             import streamlit.components.v1 as components
#             components.html(
#                 "<script>window.parent.speechSynthesis.cancel();</script>",
#                 height=0, width=0)
# 
# 
# def _run_ai_edit(prompt: str, content: str) -> str:
#     """Run an AI edit on the document content."""
#     with st.spinner("✨ AI is working…"):
#         try:
#             full_msg = (
#                 f"{prompt}\n\n"
#                 f"Return output in clean HTML tags (<b>, <i>, <p>, <ul>, <li>, <h2>, <h3>).\n\n"
#                 f"DOCUMENT:\n{content}")
#             result = chat_with_groq(
#                 [{"role": "user", "content": full_msg}],
#                 override_key=st.session_state.get("manual_api_key") or None,
#                 model="llama-3.3-70b-versatile")
#             return result.replace("```html", "").replace("```", "").strip()
#         except Exception as e:
#             st.error(f"❌ AI edit failed: {e}")
#             return content