import streamlit as st
import base64
import io
import re
import os
import tempfile
from utils.groq_client import chat_with_groq
from streamlit_quill import st_quill

try: import docx; HAS_DOCX = True
except ImportError: HAS_DOCX = False

# --- MEGA TOOLKIT IMPORTS ---
try: import wikipedia; HAS_WIKI = True
except ImportError: HAS_WIKI = False

try: from duckduckgo_search import DDGS; HAS_DDGS = True
except ImportError: HAS_DDGS = False

try: from youtube_transcript_api import YouTubeTranscriptApi; HAS_YT = True
except ImportError: HAS_YT = False

try: from sympy import sympify, latex; HAS_SYMPY = True
except ImportError: HAS_SYMPY = False

try: from rembg import remove; from PIL import Image; HAS_REMBG = True
except ImportError: HAS_REMBG = False

try: import fitz; HAS_FITZ = True
except ImportError: HAS_FITZ = False

try: import docx2txt; HAS_DOCX2TXT = True
except ImportError: HAS_DOCX2TXT = False

try: from newspaper import Article; HAS_NEWS = True
except ImportError: HAS_NEWS = False

try: import pytesseract; HAS_OCR = True
except ImportError: HAS_OCR = False

try: import networkx as nx; import matplotlib.pyplot as plt; HAS_NX = True
except ImportError: HAS_NX = False

try: import numpy as np; import plotly.graph_objects as go; HAS_PLOT = True
except ImportError: HAS_PLOT = False

try: from sklearn.feature_extraction.text import TfidfVectorizer; HAS_SKLEARN = True
except ImportError: HAS_SKLEARN = False

try: import google.generativeai as genai; HAS_GEMINI = True
except ImportError: HAS_GEMINI = False

try: import speech_recognition as sr; HAS_SR = True
except ImportError: HAS_SR = False

try: from langchain.text_splitter import RecursiveCharacterTextSplitter; HAS_LANGCHAIN = True
except ImportError: HAS_LANGCHAIN = False

try: import pypandoc; HAS_PANDOC = True
except ImportError: HAS_PANDOC = False

try: from bs4 import BeautifulSoup; import requests; HAS_BS4 = True
except ImportError: HAS_BS4 = False

try: import pyttsx3; HAS_TTS = True
except ImportError: HAS_TTS = False


def render_doc_editor():
    # Inject Google Docs UI
    st.markdown("""
<style>
.stApp { background-color: #f8f9fa !important; }
.main .block-container { max-width: 100% !important; padding: 0 !important; }
[data-testid="stSidebar"] { display: none !important; }
header { display: none !important; }

.gdocs-topbar { background: #f8f9fa; display: flex; align-items: center; justify-content: space-between; padding: 12px 20px 8px 16px; font-family: 'Roboto', 'Arial', sans-serif;}
.gdocs-topbar-left { display: flex; align-items: center; gap: 8px; }
.gdocs-icon { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin-right: 4px; }
.gdocs-title-area { display: flex; flex-direction: column; }
.gdocs-title-row { display: flex; align-items: center; gap: 8px; }
.gdocs-doc-title-input { font-size: 18px; font-weight: 400; color: #1f1f1f; border: 1px solid transparent; border-radius: 4px; padding: 1px 6px; margin-left: -6px; font-family: 'Arial', sans-serif; outline: none; width: 300px; background: transparent;}
.gdocs-doc-title-input:hover { border-color: #e0e0e0; }
.gdocs-doc-title-input:focus { border-color: #1a73e8; background: white; }
.gdocs-doc-icons { color: #444746; display: flex; gap: 12px; font-size: 18px; margin-top: -2px; cursor: pointer; }
.menu-list { color: #444746; font-size: 14px; display: flex; gap: 14px; margin-top: 1px; margin-left: 2px; }
.menu-list span { cursor: pointer; padding: 3px 7px; border-radius: 4px; }
.menu-list span:hover { background: #e8eaed; }

.gdocs-topbar-right { display: flex; align-items: center; gap: 16px; }
.hist-icon, .video-icon { font-size: 20px; cursor: pointer; color: #5f6368; }
.comment-icon { font-size: 20px; cursor: pointer; color: #5f6368; display: flex; align-items: center; justify-content: center; background: #e8f0fe; width: 32px; height: 32px; border-radius: 50%; }
.share-btn { background: #c2e7ff; color: #001d35; border: none; padding: 8px 24px; border-radius: 20px; font-weight: 500; font-size: 14px; display: flex; align-items: center; gap: 8px; cursor: pointer;}
.share-btn:hover { background: #b1dcfb; box-shadow: 0 1px 3px rgba(0,0,0,0.15); }
.avatar { width: 34px; height: 34px; border-radius: 50%; background: #9c27b0; color: white; display: flex; align-items: center; justify-content: center; font-weight: 500; font-size: 16px; }

.gdocs-format-bar { background: #edf2fa; border-radius: 24px; padding: 6px 16px; margin: 4px 16px; display: flex; align-items: center; gap: 12px; font-size: 15px; color: #444746; overflow-x: auto; scrollbar-width: none;}
.gdocs-format-bar::-webkit-scrollbar { display: none; }
.toolbar-divider { width: 1px; height: 20px; background: #c7c7c7; margin: 0 4px; }
.toolbar-btn { cursor: pointer; padding: 4px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
.toolbar-btn:hover { background: #dfe3eb; }

div.stButton > button { background-color: transparent !important; border: 1px solid #dadce0 !important; border-radius: 4px !important; color: #1a73e8 !important; padding: 2px 10px !important; font-size: 13px !important;}
div.stButton > button:hover { background-color: #f8f9fa !important; }
.explore-sidebar { background: white; border-radius: 8px; border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 20px; height: 1100px; overflow-y: auto;}
</style>
""", unsafe_allow_html=True)

    if "doc_content" not in st.session_state:
        if st.session_state.get("context_text"): st.session_state.doc_content = st.session_state.context_text.replace('\n', '<br>')
        else: st.session_state.doc_content = "<p><i>Start typing your ideas...</i></p>"
    if "doc_title" not in st.session_state: st.session_state.doc_title = "Untitled document"
    if "explore_open" not in st.session_state: st.session_state.explore_open = True

    # --- 1. TOP BAR ---
    st.markdown(f"""
    <div class="gdocs-topbar">
        <div class="gdocs-topbar-left">
            <div class="gdocs-icon"><svg width="40" height="40" viewBox="0 0 40 40"><path fill="#4285f4" d="M25.8 4H11C9.9 4 9 4.9 9 6v28c0 1.1.9 2 2 2h22c1.1 0 2-.9 2-2V11.2L25.8 4z"></path><path fill="#1967d2" d="M25.8 4v7.2h7.2L25.8 4z"></path><path fill="#e8f0fe" d="M14 26h14v-2H14v2zm0-5h14v-2H14v2zm0-5h10v-2H14v2z"></path></svg></div>
            <div class="gdocs-title-area">
                <div class="gdocs-title-row"><input type="text" class="gdocs-doc-title-input" value="{st.session_state.doc_title}" id="doc_title" /><div class="gdocs-doc-icons">⭐ 📁 ☁️</div></div>
                <div class="menu-list"><span>File</span><span>Edit</span><span>View</span><span>Insert</span><span>Format</span><span>Tools</span><span>Extensions</span><span>Help</span></div>
            </div>
        </div>
        <div class="gdocs-topbar-right">
            <span class="hist-icon">🕒</span><span class="comment-icon">💬</span><span class="video-icon">📹</span>
            <button class="share-btn">🔒 Share</button><div class="avatar">U</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. FORMATTING TOOLBAR & AI BAR ---
    st.markdown("""
    <div class="gdocs-format-bar">
        <span class="toolbar-btn">↩️</span><span class="toolbar-btn">↪️</span><span class="toolbar-btn">🖨️</span><span class="toolbar-btn">A✅</span><span class="toolbar-btn">🖌️</span>
        <div class="toolbar-divider"></div><span class="toolbar-btn">100% ▾</span>
        <div class="toolbar-divider"></div><span class="toolbar-btn">Normal text ▾</span>
        <div class="toolbar-divider"></div><span class="toolbar-btn">Arial ▾</span>
        <div class="toolbar-divider"></div><span class="toolbar-btn">−</span><span style="border:1px solid #dadce0; padding:2px 8px; border-radius:4px;">11</span><span class="toolbar-btn">+</span>
        <div class="toolbar-divider"></div><span class="toolbar-btn" style="font-weight:bold; font-family:serif;">B</span><span class="toolbar-btn" style="font-style:italic; font-family:serif;">I</span><span class="toolbar-btn" style="text-decoration:underline; font-family:serif;">U</span><span class="toolbar-btn" style="color:#202124"><u>A</u></span><span class="toolbar-btn" style="background:#fefedc;border:1px solid #c7c7c7;padding:2px 8px;">🖍️</span>
        <div class="toolbar-divider"></div><span class="toolbar-btn">🔗</span><span class="toolbar-btn">💬</span><span class="toolbar-btn">🖼️</span>
        <div class="toolbar-divider"></div><span class="toolbar-btn">⬅️</span><span class="toolbar-btn">⏫</span><span class="toolbar-btn">✅</span><span class="toolbar-btn">1.</span><span class="toolbar-btn">•</span><span class="toolbar-btn">⬅️</span><span class="toolbar-btn">➡️</span>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c_gap, c6, c7, c8 = st.columns([1.2, 1, 1, 1, 1, 1.5, 1, 1, 1.5])
    with c1:
        if st.button("⬅️ App / Chat"): st.session_state.app_mode = "chat"; st.rerun()
    with c2:
        if st.button("✨ Polish"): st.session_state.doc_content = _run_ai_edit("Rewrite to sound professional and academic.", st.session_state.doc_content)
    with c3:
        if st.button("✅ Fix Text"): st.session_state.doc_content = _run_ai_edit("Fix all grammar errors.", st.session_state.doc_content)
    with c4:
        if st.button("📊 Summarize"): st.session_state.doc_content = _run_ai_edit("Summarize into bullet points.", st.session_state.doc_content)
    with c5:
        if st.button("🧠 Expand"): st.session_state.doc_content = _run_ai_edit("Expand on this detail.", st.session_state.doc_content)
    with c6:
        st.download_button("⬇️ TXT", data=st.session_state.doc_content, file_name="Doc.txt")
    with c7:
        if HAS_DOCX:
            clean_text = re.sub('<[^<]+?>', '', st.session_state.doc_content)
            dr = docx.Document(); dr.add_heading("Exported Doc", 0)
            for line in clean_text.split('\\n'): dr.add_paragraph(line)
            bio = io.BytesIO(); dr.save(bio)
            st.download_button("⬇️ DOCX", data=bio.getvalue(), file_name="Doc.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with c8:
        if st.button("🔍 Explore APIs"): st.session_state.explore_open = not st.session_state.explore_open; st.rerun()

    # --- 3. EDITOR & EXPLORE ---
    st.markdown('<div style="background:#f8f9fa; padding-bottom:50px;">', unsafe_allow_html=True)
    if st.session_state.explore_open: c_l, c_c, c_e = st.columns([0.1, 5, 2.8])
    else: c_l, c_c, c_e = st.columns([1, 6, 1])

    with c_c:
        st.markdown('<style> .element-container iframe { background: white !important; box-shadow: 0 1px 3px rgba(0,0,0,0.12) !important; min-height:1000px !important; margin:20px auto; padding:60px 80px; } </style>', unsafe_allow_html=True)
        html = st_quill(value=st.session_state.doc_content, placeholder="Type your document here...", html=True, key="q")
        if html and html != st.session_state.doc_content: st.session_state.doc_content = html

    with c_e:
        if st.session_state.explore_open:
            st.markdown('<div class="explore-sidebar">', unsafe_allow_html=True)
            st.markdown("### 🌐 API Mega-Toolkit (22 Tools)")
            
            opts = [
                "1. 🌐 Web & Wiki Search", "2. 📺 YouTube Transcriber", "3. 🖼️ Native Image Finder",
                "4. 📈 Content Analytics", "5. 🗺️ Auto-Outliner", "6. 💬 Chat w/ Document",
                "7. 🗂️ Flashcard AI", "8. 🎙️ Whisper Dictation", "9. 🧮 SymPy Math Solver",
                "10. 🪄 Magic Image Editor", "11. 📥 Universal Importer", "12. 🎭 Persona Engine",
                "13. 📖 Article Scraper", "14. 👁️ OCR Scanner", "15. 🕸️ Concept Mapper",
                "16. 📊 Plot Generator", "17. 🔑 Keyword Extractor", "18. 🤖 Gemini Co-Pilot",
                "19. 🎧 Audio File Transcriber", "20. 📑 Text Chunker", "21. 📕 EPUB Exporter",
                "22. 🥣 Raw HTML Scraper", "23. 🔊 Read Aloud (TTS)"
            ]
            
            tool_sel = st.selectbox("Select Core Toolkit API:", opts, label_visibility="collapsed")
            st.divider()

            if "Web & Wiki" in tool_sel:
                q = st.text_input("DuckDuckGo/Wiki Search")
                if st.button("Search") and q:
                    if HAS_WIKI:
                        try: st.session_state.wiki_res = wikipedia.summary(q, sentences=3)
                        except: st.session_state.wiki_res = None
                    if HAS_DDGS: st.session_state.web_res = DDGS().text(q, max_results=3)
                if st.session_state.get("wiki_res"):
                    st.info(st.session_state.wiki_res)
                    if st.button("➕ Insert Wiki", key="w1"):
                        st.session_state.doc_content += f"<br><b>Wiki:</b> {st.session_state.wiki_res}<br>"; st.rerun()
                if st.session_state.get("web_res"):
                    for i, r in enumerate(st.session_state.web_res):
                        st.markdown(f"**[{r['title']}]({r['href']})**\\n{r['body'][:100]}...")
                        if st.button(f"➕ Insert #{i+1}", key=f"dd_{i}"):
                            st.session_state.doc_content += f"<br><b><a href='{r['href']}'>{r['title']}</a></b>: {r['body']}<br>"; st.rerun()
                            
            elif "YouTube" in tool_sel:
                if not HAS_YT: st.error("youtube-transcript-api missing.")
                else:
                    u = st.text_input("YouTube URL")
                    if st.button("Fetch") and u:
                        v = u.split("v=")[1].split("&")[0] if "v=" in u else u.split("/")[-1].split("?")[0]
                        st.session_state.yt_res = " ".join([t['text'] for t in YouTubeTranscriptApi.get_transcript(v)])[:1500]
                    if st.session_state.get("yt_res"):
                        st.success("Transcribed!")
                        if st.button("➕ Insert"): st.session_state.doc_content += f"<br><b>Video Notes:</b><br>{st.session_state.yt_res}<br>"; st.rerun()

            elif "Image Finder" in tool_sel:
                if not HAS_DDGS: st.error("duckduckgo proxy missing.")
                else:
                    q = st.text_input("Search DuckDuckGo Images")
                    if st.button("Search") and q: st.session_state.img_res = DDGS().images(q, max_results=4)
                    if st.session_state.get("img_res"):
                        for i, img in enumerate(st.session_state.img_res):
                            st.image(img['image'])
                            if st.button(f"🖼️ Embed #{i+1}", key=f"im_{i}"): 
                                st.session_state.doc_content += f'<br><img src="{img["image"]}" style="max-width:100%; border-radius:8px;"/><br>'; st.rerun()
            
            elif "Analytics" in tool_sel:
                cx = re.sub('<[^<]+?>', '', st.session_state.doc_content)
                words = len(cx.split()); st.metric("Words", words); st.metric("Chars", len(cx))
                st.metric("Reading Time", f"{max(1, words//200)} min")

            elif "Auto-Outliner" in tool_sel:
                if st.button("Generate Layout"):
                    cx = re.sub('<[^<]+?>', '', st.session_state.doc_content)[:4000]
                    st.session_state.outl = chat_with_groq([{"role":"user","content":f"Make Table of Contents from:\\n{cx}"}], override_key=st.session_state.get("manual_api_key"), model="llama-3.1-8b-instant")
                if st.session_state.get("outl"):
                    st.markdown(st.session_state.outl)
                    if st.button("➕ Append Top"): st.session_state.doc_content = f"<h3>Outline</h3><p>{st.session_state.outl}</p><hr>" + st.session_state.doc_content; st.rerun()

            elif "Chat w/ Document" in tool_sel:
                q = st.text_input("Ask doc:")
                if st.button("Ask Groq") and q:
                    cx = re.sub('<[^<]+?>', '', st.session_state.doc_content)
                    st.info(chat_with_groq([{"role":"user","content":f"Answer based on DOC:\\n\\nQ: {q}\\nDOC: {cx}"}], override_key=st.session_state.get("manual_api_key"), model="llama-3.3-70b-versatile"))

            elif "Flashcard AI" in tool_sel:
                if st.button("Extract Q&A"):
                    cx = re.sub('<[^<]+?>', '', st.session_state.doc_content)[:4000]
                    st.session_state.fc = chat_with_groq([{"role":"user","content":f"Make 5 flashcards from this text:\\n{cx}"}], override_key=st.session_state.get("manual_api_key"), model="llama-3.1-8b-instant")
                if st.session_state.get("fc"):
                    st.write(st.session_state.fc)
                    if st.button("➕ Append Bottom"): st.session_state.doc_content += f"<hr><h3>Flashcards</h3><p>{st.session_state.fc}</p>"; st.rerun()

            elif "Whisper Dictation" in tool_sel:
                aud = st.audio_input("Record")
                if aud and st.button("Transcribe"):
                    from utils.groq_client import get_groq_client, MODEL_WHISPER
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                        t.write(aud.getvalue()); t_p = t.name
                    with open(t_p, "rb") as f: tx = get_groq_client(st.session_state.get("manual_api_key")).audio.transcriptions.create(file=(t_p, f.read()), model=MODEL_WHISPER).text
                    os.unlink(t_p); st.session_state.doc_content += f"<br><i>{tx}</i>"; st.rerun()

            elif "Math Solver" in tool_sel:
                if not HAS_SYMPY: st.error("sympy missing.")
                else:
                    expr = st.text_area("Equation")
                    if st.button("Solve") and expr:
                        try: 
                            r = sympify(expr).doit(); st.latex(latex(r))
                            if st.button("➕ Append"): st.session_state.doc_content += f"<br><b>Math:</b> {expr} = {r}<br>"; st.rerun()
                        except Exception as e: st.error(e)

            elif "Magic Image Editor" in tool_sel:
                if not HAS_REMBG: st.error("rembg framework missing.")
                else:
                    f = st.file_uploader("Upload Image", ["png","jpg"])
                    if f and st.button("Remove BG"):
                        o = remove(Image.open(f)); bio = io.BytesIO(); o.save(bio, "PNG")
                        st.session_state.doc_content += f'<br><img src="data:image/png;base64,{base64.b64encode(bio.getvalue()).decode()}" style="max-width:100%; border-radius:8px;"/><br>'; st.rerun()

            elif "Universal Importer" in tool_sel:
                f = st.file_uploader("Upload PPTX, PDF, DOCX", ["pdf","docx","pptx"])
                if f and st.button("Extract Data"):
                    text = ""
                    if f.name.endswith(".pdf") and HAS_FITZ: text = "\\n".join(p.get_text() for p in fitz.open(stream=f.read(), filetype="pdf"))
                    elif f.name.endswith(".docx") and HAS_DOCX2TXT: text = docx2txt.process(f)
                    else: text = f.read().decode('utf-8', 'ignore')
                    st.session_state.doc_content += f"<br><b>File Extract:</b><br>{text.replace('\\n','<br>')}<br>"; st.rerun()

            elif "Persona Engine" in tool_sel:
                vp = st.selectbox("Role", ["Shakespeare", "Pirate", "Harvard Scholar"])
                if st.button("Rewrite"):
                    cx = re.sub('<[^<]+?>', '', st.session_state.doc_content)
                    ans = chat_with_groq([{"role":"user","content":f"Rewrite as {vp}. Return HTML only. Text: {cx}"}], override_key=st.session_state.get("manual_api_key"), model="llama-4-scout-17b-16e-instruct")
                    st.session_state.doc_content = ans.replace("```html","").replace("```","").strip(); st.rerun()

            elif "Article Scraper" in tool_sel:
                if not HAS_NEWS: st.error("newspaper3k missing")
                else:
                    u = st.text_input("Raw URL")
                    if st.button("Scrape") and u:
                        a = Article(u); a.download(); a.parse(); st.session_state.news_t = a.text; st.success("Scraped!")
                    if st.session_state.get("news_t"):
                        if st.button("➕ Append"): st.session_state.doc_content += f"<br><b>Article:</b><br>{st.session_state.news_t.replace('\\n','<br>')}<br>"; st.rerun()

            elif "OCR Scanner" in tool_sel:
                if not HAS_OCR: st.error("pytesseract missing or inactive on OS.")
                else:
                    f = st.file_uploader("Upload Text Image", ["png","jpg"])
                    if f and st.button("Scan Text"):
                        try:
                            tx = pytesseract.image_to_string(Image.open(f)); st.info(tx); st.session_state.ocr_t = tx
                        except Exception as e: st.error(e)
                    if st.session_state.get("ocr_t"):
                        if st.button("➕ Append OCR"): st.session_state.doc_content += f"<br><b>Scanned Image:</b> {st.session_state.ocr_t}<br>"; st.rerun()

            elif "Concept Mapper" in tool_sel:
                if not HAS_NX: st.error("networkx mapping disabled.")
                else:
                    if st.button("Generate Topic Graph"):
                        G = nx.Graph()
                        G.add_nodes_from(["Concepts", "Ideas", "Research", "Analysis", "Data"])
                        G.add_edges_from([("Concepts", "Ideas"), ("Research", "Data"), ("Analysis", "Concepts"), ("Data", "Analysis")])
                        fig, ax = plt.subplots(figsize=(4, 4))
                        nx.draw_networkx(G, ax=ax, with_labels=True, node_color="#c2e7ff", node_size=1500, font_size=10, font_weight="bold", edge_color="#1a73e8")
                        bio = io.BytesIO(); plt.savefig(bio, format="png"); plt.close(fig)
                        enc = base64.b64encode(bio.getvalue()).decode()
                        st.session_state.doc_content += f'<br><img src="data:image/png;base64,{enc}" style="border-radius:8px;"/><br>'; st.rerun()

            elif "Plot Generator" in tool_sel:
                if not HAS_PLOT: st.error("plotly disabled.")
                else:
                    expr = st.text_input("Math Function", "sin(x) * exp(-0.1*x)")
                    if st.button("Plot Graph") and expr:
                        x = np.linspace(0, 20, 400); y = eval(expr, {"x":x, "sin":np.sin, "exp":np.exp, "cos":np.cos})
                        st.plotly_chart(go.Figure(go.Scatter(x=x, y=y)))
                        bio = io.BytesIO(); go.Figure(go.Scatter(x=x, y=y)).write_image(bio, format="png")
                        st.session_state.plt_img = bio.getvalue()
                    if st.session_state.get("plt_img"):
                        if st.button("➕ Inject Graph"): st.session_state.doc_content += f'<br><img src="data:image/png;base64,{base64.b64encode(st.session_state.plt_img).decode()}"/><br>'; st.rerun()

            elif "Keyword Extractor" in tool_sel:
                if not HAS_SKLEARN: st.error("scikit-learn down.")
                else:
                    if st.button("Analyze Vocab"):
                        tf = TfidfVectorizer(stop_words='english', max_features=10)
                        tf.fit_transform([re.sub('<[^<]+?>', '', st.session_state.doc_content)])
                        st.session_state.kw = list(tf.get_feature_names_out())
                        st.success(f"Keywords: {', '.join(st.session_state.kw)}")
                    if st.session_state.get("kw"):
                        if st.button("➕ Inject"): st.session_state.doc_content += f"<br><i>Keywords: {', '.join(st.session_state.kw)}</i><br>"; st.rerun()

            elif "Gemini Co-Pilot" in tool_sel:
                if not HAS_GEMINI: st.error("google.generativeai interface missing.")
                else:
                    cmd = st.text_input("Gemini Prompt", "Summarize this beautifully.")
                    if st.button("Run Gemini Edit") and cmd:
                        genai.configure(api_key=getattr(st.secrets, "GEMINI_API_KEY", ""))
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        cx = re.sub('<[^<]+?>', '', st.session_state.doc_content)
                        st.session_state.doc_content = model.generate_content(f"{cmd} (Return HTML only for insertion based on this: {cx})").text.replace("```html","").replace("```","").strip(); st.rerun()

            elif "Audio File Transcriber" in tool_sel:
                if not HAS_SR: st.error("speech_recognition disabled.")
                else:
                    f = st.file_uploader("Upload .wav", ["wav"])
                    if f and st.button("Transcribe Audio"):
                        rc = sr.Recognizer()
                        try:
                            with sr.AudioFile(f) as src: a = rc.record(src)
                            st.session_state.sr_t = rc.recognize_google(a); st.success("Transcribed!")
                        except Exception as e: st.error(str(e))
                    if st.session_state.get("sr_t"):
                        if st.button("➕ Append Audio Notes"): st.session_state.doc_content += f"<br><b>Audio File:</b> {st.session_state.sr_t}<br>"; st.rerun()

            elif "Text Chunker" in tool_sel:
                if not HAS_LANGCHAIN: st.error("Langchain core missing.")
                else:
                    if st.button("Process Document Hierarchy"):
                        ts = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                        chunks = ts.split_text(re.sub('<[^<]+?>', '', st.session_state.doc_content))
                        st.info(f"Split document into {len(chunks)} chunks cleanly.")

            elif "EPUB Exporter" in tool_sel:
                if not HAS_PANDOC: st.error("pypandoc or OS pandoc binary missing. Re-route to standard PDF output if necessary.")
                else:
                    if st.button("Compile EPUB File"):
                        epub = pypandoc.convert_text(st.session_state.doc_content, 'epub', format='html')
                        st.download_button("⬇️ Download E-Book", epub, "Document.epub")

            elif "Raw HTML Scraper" in tool_sel:
                if not HAS_BS4: st.error("beautifulsoup4 not found.")
                else:
                    u = st.text_input("Raw URL")
                    if st.button("Scrape Data") and u:
                        rs = requests.get(u, timeout=5).text; st.session_state.bs_t = BeautifulSoup(rs, 'html.parser').get_text()[:2000]
                        st.success("Scraped HTML Structure!")
                    if st.session_state.get("bs_t"):
                        if st.button("➕ Append DOM Data"): st.session_state.doc_content += f"<br><code>{st.session_state.bs_t}</code><br>"; st.rerun()

            elif "Read Aloud (TTS)" in tool_sel:
                st.markdown("*Use the pyttsx3 module to generate an audio reading of your document.*")
                if not HAS_TTS: st.error("pyttsx3 missing or OS audio drivers unavailable.")
                else:
                    if st.button("Generate Audio"):
                        with st.spinner("Generating speech format..."):
                            try:
                                engine = pyttsx3.init()
                                cx = re.sub('<[^<]+?>', '', st.session_state.doc_content)
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t: t_p = t.name
                                engine.save_to_file(cx[:5000], t_p)
                                engine.runAndWait()
                                with open(t_p, "rb") as f: st.session_state.tts_audio = f.read()
                                os.unlink(t_p); st.success("Audio generated!")
                            except Exception as e: st.error(f"TTS Error: {e}")
                    if st.session_state.get("tts_audio"):
                        st.audio(st.session_state.tts_audio, format="audio/wav")

            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def _run_ai_edit(prompt, content):
    with st.spinner("✨ AI is working its magic..."):
        full_msg = f"{prompt}\\nProvide output strictly in HTML tags (<b>, <i>, <p>, <ul>) matching rich text.\\n\\nDOCUMENT:\\n{content}"
        messages = [{"role": "user", "content": full_msg}]
        result = chat_with_groq(messages, override_key=st.session_state.get("manual_api_key") or None, model="llama-4-scout-17b-16e-instruct")
        return result.replace("```html", "").replace("```", "").strip()
