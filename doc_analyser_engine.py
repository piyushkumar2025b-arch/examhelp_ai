"""
doc_analyser_engine.py
Smart Document Analyser — Upload PDF / Image / TXT and ask AI:
  "What's good here?", "What should I add?", "Where should I improve?"
Uses Gemini Vision for images, PyMuPDF for PDFs, plain read for text.
"""

import io
import base64
import streamlit as st
# [REMOVED — integration/key stripped] from utils.groq_client import chat_with_groq
from utils.pdf_handler import extract_text_from_pdf

# ── Try optional deps ────────────────────────────────────────────────────────
try:
# [REMOVED — integration/key stripped]     from ai.gemini_client import analyze_image_with_gemini, gemini_available
    _HAS_GEMINI = True
except Exception:
    _HAS_GEMINI = False

try:
    from utils.ocr_handler import extract_text_from_image
    _HAS_OCR = True
except Exception:
    _HAS_OCR = False

# ── Supported types ──────────────────────────────────────────────────────────
PDF_TYPES  = ["application/pdf"]
IMAGE_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"]
TEXT_TYPES  = ["text/plain", "text/csv", "text/markdown"]

ACCEPTED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "webp", "txt", "csv", "md"]

# ── System prompt ────────────────────────────────────────────────────────────
ANALYSER_SYSTEM = """You are an expert document reviewer and advisor. 
The user will share content extracted from their uploaded file (PDF, image, or text document).
Your job is to:
1. Identify WHAT IS GOOD — strengths, clear sections, strong points
2. Identify WHAT IS MISSING or WEAK — gaps, vague areas, things that need more detail
3. Give SPECIFIC SUGGESTIONS — exact things to add, where to add them, and WHY
4. Be HONEST and CONSTRUCTIVE — like a smart mentor reviewing the work

Format your response with clear sections:
✅ **What's Good**
⚠️ **What Needs Work**
➕ **What to Add & Where**
💡 **Quick Wins**

Be specific, practical, and actionable. Reference actual content from the document in your feedback.
"""

CHAT_SYSTEM = """You are an expert document reviewer and advisor. 
The user has uploaded a document and you have already reviewed it.
The document content is provided at the start of the conversation.
Answer follow-up questions about the document specifically and helpfully.
Reference actual content from the document when relevant.
Be practical, direct, and constructive."""

# ── Quick prompt suggestions ─────────────────────────────────────────────────
QUICK_PROMPTS = [
    "Give me a full detailed review — what's good, what's weak, what's missing.",
    "What are the 3 most critical improvements needed?",
    "Rate this document out of 10 with specific justification.",
    "What's missing compared to industry best practices?",
    "Identify all structural and logical gaps.",
    "Summarise the key points concisely.",
    "What would an expert reviewer say about this?",
    "How can I make this stand out from average work?",
    "What's the strongest part of this document?",
    "Give specific line-by-line improvement suggestions.",
]


def _extract_content(uploaded_file) -> tuple[str, str, bytes | None]:
    """
    Returns (extracted_text, file_type_label, raw_bytes_or_None)
    file_type_label: "pdf" | "image" | "text"
    """
    name = uploaded_file.name.lower()
    mime = uploaded_file.type or ""
    raw  = uploaded_file.read()

    if name.endswith(".pdf") or "pdf" in mime:
        text = extract_text_from_pdf(io.BytesIO(raw))
        return text, "pdf", raw

    if any(name.endswith(ext) for ext in ["png","jpg","jpeg","webp","gif"]) or "image" in mime:
        return "", "image", raw

    # Text / CSV / Markdown
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = str(raw)
    return text, "text", raw


def _analyse_with_ai(content_text: str, file_type: str,
                     raw_bytes: bytes | None, user_prompt: str,
                     model: str) -> str:
    """Run the analysis — vision for images, text for everything else."""

    if file_type == "image":
        if not raw_bytes:
            return "❌ Could not read image bytes."

        if _HAS_GEMINI and gemini_available():
            full_prompt = (
                f"{ANALYSER_SYSTEM}\n\n"
                f"The user uploaded an image. Analyse it carefully.\n\n"
                f"User question: {user_prompt}"
            )
            return analyze_image_with_gemini(raw_bytes, "image/png", full_prompt)

        elif _HAS_OCR:
            ocr_text = extract_text_from_image(raw_bytes)
            if ocr_text.startswith("Error:"):
                return (
                    "⚠️ Gemini Vision is unavailable and OCR could not extract text from this image.\n\n"
                    f"OCR detail: {ocr_text}\n\n"
                    "Please configure Gemini API keys for full image analysis."
                )
            content_text = ocr_text
        else:
            return (
                "⚠️ Image analysis requires either **Gemini Vision** (recommended) or **Tesseract OCR**.\n\n"
                "- Add Gemini API keys in `.streamlit/secrets.toml` for best results\n"
                "- Or install: `pip install pytesseract pillow` + Tesseract binary"
            )

    # ── Text / PDF path ──────────────────────────────────────────────────────
    if not content_text or content_text.startswith("Error"):
        return f"❌ Could not extract content from the file.\n\nDetail: {content_text}"

    # Truncate to avoid token overflow
    excerpt = content_text[:12000]
    if len(content_text) > 12000:
        excerpt += "\n\n[... content truncated for length ...]"

    messages = [
        {
            "role": "user",
            "content": (
                f"Here is the content extracted from the uploaded document:\n\n"
                f"---\n{excerpt}\n---\n\n"
                f"User question: {user_prompt}"
            )
        }
    ]

    return chat_with_groq(
        messages=messages,
        system_prompt=ANALYSER_SYSTEM,
        model=model,
    )


def render_doc_analyser():
    """Main render function — called from app.py."""

    is_dark = st.session_state.get("theme_mode", "dark") == "dark"
    surface  = "#1a1525" if is_dark else "#ffffff"
    surface2 = "#231d2f" if is_dark else "#f3eeff"
    border   = "#2e2740" if is_dark else "#e2d4f5"
    txt      = "#f0eaf8" if is_dark else "#1a0d2e"
    muted    = "#9585b0" if is_dark else "#7c5fa0"
    accent   = "#a78bfa"
    user_bub = "linear-gradient(135deg,#3d2b6b,#4a2f7a)"
    ai_bub   = surface2

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&family=Rajdhani:wght@300;400;600;700&display=swap');

    .da-header {{
        position: relative;
        background: linear-gradient(135deg, {surface}, rgba(15,23,42,0.95));
        border: 1px solid rgba(167,139,250,0.2);
        border-radius: 22px;
        padding: 24px 28px;
        margin-bottom: 18px;
        overflow: hidden;
        backdrop-filter: blur(20px);
        box-shadow: 0 0 60px rgba(167,139,250,0.07), 0 20px 60px rgba(0,0,0,0.35);
    }}
    .da-header::after {{
        content: '';
        position: absolute; top: -1px; left: 10%; right: 10%; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(167,139,250,0.5), rgba(96,165,250,0.4), transparent);
    }}
    .da-title {{
        font-family: 'Orbitron', monospace;
        font-size: 1.25rem; font-weight: 900; letter-spacing: 1px;
        background: linear-gradient(90deg, #a78bfa, #60a5fa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }}
    .da-sub {{ font-family: 'Rajdhani', sans-serif; font-size: 0.85rem; color: {muted}; margin-top: 4px; letter-spacing: 0.3px; }}

    .da-badge {{
        display: inline-flex; align-items: center;
        font-family: 'Space Mono', monospace;
        font-size: 0.68rem; font-weight: 700; letter-spacing: 1px;
        padding: 4px 12px; border-radius: 100px;
        background: rgba(167,139,250,0.1);
        border: 1px solid rgba(167,139,250,0.25);
        color: {accent}; margin: 3px;
        transition: all 0.2s ease;
    }}
    .da-badge:hover {{ background: rgba(167,139,250,0.2); border-color: rgba(167,139,250,0.45); }}

    .da-file-box {{
        background: {surface2};
        border: 2px dashed rgba(167,139,250,0.3);
        border-radius: 18px;
        padding: 36px 24px;
        text-align: center;
        margin-bottom: 16px;
        transition: all 0.25s ease;
        position: relative; overflow: hidden;
    }}
    .da-file-box:hover {{ border-color: {accent}; transform: translateY(-2px); box-shadow: 0 8px 30px rgba(167,139,250,0.1); }}

    .da-bubble-ai {{
        background: {ai_bub};
        border: 1px solid {border};
        border-left: 3px solid {accent};
        border-radius: 0 18px 18px 18px;
        padding: 16px 20px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.92rem;
        color: {txt};
        line-height: 1.7;
        margin-bottom: 6px;
        transition: box-shadow 0.2s ease;
        animation: daIn 0.35s cubic-bezier(0.16,1,0.3,1) both;
    }}
    .da-bubble-ai:hover {{ box-shadow: 0 4px 20px rgba(167,139,250,0.15); }}
    @keyframes daIn {{ from{{opacity:0;transform:translateY(8px);}} to{{opacity:1;transform:none;}} }}
    .da-bubble-user {{
        background: {user_bub};
        border: 1px solid rgba(139,92,246,.3);
        border-right: 3px solid rgba(139,92,246,0.7);
        border-radius: 18px 0 18px 18px;
        padding: 14px 20px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.92rem;
        color: #f0eaf8;
        line-height: 1.65;
        margin-bottom: 6px;
        text-align: right;
        animation: daIn 0.3s ease both;
    }}
    .da-meta {{
        font-family: 'Space Mono', monospace;
        font-size: 0.65rem; color: {muted}; margin-bottom: 14px; letter-spacing: 1px;
    }}
    .da-meta-right {{ text-align: right; }}

    .da-typing {{
        display: inline-flex; gap: 5px; align-items: center;
        padding: 10px 18px; border-radius: 18px;
        background: {surface2}; border: 1px solid {border};
        border-left: 3px solid {accent}; margin-bottom: 10px;
    }}
    .da-dot {{
        width: 7px; height: 7px; border-radius: 50%;
        background: {accent};
        animation: da-blink 1.2s ease-in-out infinite;
    }}
    .da-dot:nth-child(2){{animation-delay:.2s}}
    .da-dot:nth-child(3){{animation-delay:.4s}}
    @keyframes da-blink{{0%,80%,100%{{transform:translateY(0);opacity:0.4;}} 40%{{transform:translateY(-5px);opacity:1;}}}}
    .da-qchip-grid {{
        display: grid; grid-template-columns: repeat(auto-fill, minmax(200px,1fr));
        gap: 8px; margin: 12px 0;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="da-header">
        <div class="da-title">📎 Smart Document Analyser</div>
        <div class="da-sub">
            Upload any document. AI reviews it — what's strong, what's weak, what's missing and exactly where to fix it.
        </div>
        <div style="margin-top:10px;">
            <span class="da-badge">📄 PDF</span>
            <span class="da-badge">🖼️ PNG / JPG</span>
            <span class="da-badge">📝 TXT / MD</span>
            <span class="da-badge">📊 CSV</span>
            <span class="da-badge">🌐 WEBP</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Back button ───────────────────────────────────────────────────────────
    col_back, col_clear = st.columns([1, 1])
    with col_back:
        if st.button("← Back to Chat", key="da_back", use_container_width=True):
            st.session_state.app_mode = "chat"
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear & Start Over", key="da_clear", use_container_width=True):
            for k in ["da_messages", "da_content_text", "da_file_type",
                      "da_raw_bytes", "da_file_name", "da_analysed"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("---")

    # ── Init session state ────────────────────────────────────────────────────
    if "da_messages"     not in st.session_state: st.session_state.da_messages     = []
    if "da_content_text" not in st.session_state: st.session_state.da_content_text = ""
    if "da_file_type"    not in st.session_state: st.session_state.da_file_type    = ""
    if "da_raw_bytes"    not in st.session_state: st.session_state.da_raw_bytes    = None
    if "da_file_name"    not in st.session_state: st.session_state.da_file_name    = ""
    if "da_analysed"     not in st.session_state: st.session_state.da_analysed     = False

    model = st.session_state.get("model_choice", "llama-3.3-70b-versatile")

    # ── File uploader ─────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "📂 Drop your file here",
        type=ACCEPTED_EXTENSIONS,
        key="da_uploader",
        help="Supports PDF, PNG, JPG, WEBP, TXT, CSV, MD",
        label_visibility="collapsed",
    )

    if uploaded:
        # Only re-extract if it's a new file
        if uploaded.name != st.session_state.da_file_name:
            with st.spinner("📖 Reading your file…"):
                text, ftype, raw = _extract_content(uploaded)
                st.session_state.da_content_text = text
                st.session_state.da_file_type    = ftype
                st.session_state.da_raw_bytes    = raw
                st.session_state.da_file_name    = uploaded.name
                st.session_state.da_messages     = []
                st.session_state.da_analysed     = False

        fname = st.session_state.da_file_name
        ftype = st.session_state.da_file_type

        # File info strip
        type_emoji = {"pdf": "📄", "image": "🖼️", "text": "📝"}.get(ftype, "📎")
        word_count = len(st.session_state.da_content_text.split()) if st.session_state.da_content_text else 0
        wc_str = f"~{word_count:,} words extracted" if ftype != "image" else "Image loaded"
        st.success(f"{type_emoji} **{fname}** · {ftype.upper()} · {wc_str}")

        # ── Auto full review on first upload ─────────────────────────────────
        if not st.session_state.da_analysed:
            st.markdown("### 🔍 Quick Start — Full Review")
            if st.button("✨ Analyse this document now!", key="da_auto_review",
                         use_container_width=True, type="primary"):
                _run_analysis("Give me a full detailed review — what's good, what's weak, what should I add and where exactly.", model)

        # ── Quick prompt chips ────────────────────────────────────────────────
        if not st.session_state.da_analysed:
            st.markdown("**Or pick a quick question:**")
            cols = st.columns(2)
            for i, qp in enumerate(QUICK_PROMPTS[:6]):
                with cols[i % 2]:
                    if st.button(qp, key=f"da_qp_{i}", use_container_width=True):
                        _run_analysis(qp, model)
                        st.rerun()

        # ── Chat history ──────────────────────────────────────────────────────
        if st.session_state.da_messages:
            st.markdown("---")
            st.markdown("### 💬 Review Conversation")
            for msg in st.session_state.da_messages:
                is_user = msg["role"] == "user"
                if is_user:
                    st.markdown(
                        f'<div class="da-bubble-user">{msg["content"]}</div>'
                        f'<div class="da-meta da-meta-right">You</div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div class="da-bubble-ai">{msg["content"]}</div>'
                        f'<div class="da-meta">📎 Document AI</div>',
                        unsafe_allow_html=True)

        # ── Follow-up input ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("**Ask a follow-up question about this document:**")

        with st.form(key="da_form", clear_on_submit=True):
            user_q = st.text_area(
                "Your question",
                placeholder="e.g. What section needs the most improvement? What should I add in the conclusion?",
                height=80,
                label_visibility="collapsed"
            )
            col_send, col_more = st.columns([2, 1])
            with col_send:
                send = st.form_submit_button("🔍 Analyse", use_container_width=True, type="primary")
            with col_more:
                full_review = st.form_submit_button("✨ Full Review", use_container_width=True)

        if send and user_q.strip():
            _run_analysis(user_q.strip(), model)
            st.rerun()

        if full_review:
            _run_analysis(
                "Give me a comprehensive review — what's good, what's weak, what should I add and exactly where to add it.",
                model
            )
            st.rerun()

        # ── More quick prompts when chat is active ────────────────────────────
        if st.session_state.da_analysed:
            st.markdown("**Quick follow-ups:**")
            cols2 = st.columns(4)
            remaining = [q for q in QUICK_PROMPTS
                         if q not in [m["content"] for m in st.session_state.da_messages]]
            for i, qp in enumerate(remaining[:4]):
                with cols2[i % 4]:
                    if st.button(qp, key=f"da_fup_{i}", use_container_width=True):
                        _run_analysis(qp, model)
                        st.rerun()

    else:
        # ── No file uploaded yet ──────────────────────────────────────────────
        st.markdown("""
        <div class="da-file-box">
            <div style="font-size:3rem;margin-bottom:12px;">📎</div>
            <div style="font-size:1rem;font-weight:600;margin-bottom:6px;">Upload your document above</div>
            <div style="font-size:0.8rem;color:#9585b0;">
                PDF · PNG · JPG · WEBP · TXT · CSV · Markdown<br><br>
                The AI will tell you <strong>what's good</strong>, <strong>what's missing</strong>,
                and <strong>exactly what to add and where</strong>.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Examples of what it can do ────────────────────────────────────────
        st.markdown("### 💡 What can you analyse?")
        examples = [
            ("📄", "Resume / CV", "Get specific feedback on gaps, formatting, missing skills sections"),
            ("📋", "Assignment / Essay", "Find weak arguments, missing citations, structure issues"),
            ("🖼️", "Screenshot / Image", "Review UI designs, handwritten notes, diagrams"),
            ("📊", "CSV / Data file", "Spot missing columns, data quality issues, what to add"),
            ("📝", "Project Proposal", "Check completeness, missing sections, what experts expect"),
            ("🎓", "Study Notes", "Find gaps, what topics to add, how to structure better"),
        ]
        cols = st.columns(3)
        for i, (emoji, title, desc) in enumerate(examples):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:{surface2};border:1px solid {border};
                     border-radius:12px;padding:14px;margin-bottom:10px;">
                    <div style="font-size:1.5rem">{emoji}</div>
                    <div style="font-size:.85rem;font-weight:700;color:{txt};margin:6px 0 4px">{title}</div>
                    <div style="font-size:.72rem;color:{muted}">{desc}</div>
                </div>
                """, unsafe_allow_html=True)


def _run_analysis(prompt: str, model: str):
    """Run AI analysis and append to da_messages."""
    content_text = st.session_state.da_content_text
    file_type    = st.session_state.da_file_type
    raw_bytes    = st.session_state.da_raw_bytes

    st.session_state.da_messages.append({"role": "user", "content": prompt})

    with st.spinner("🔍 Analysing your document…"):
        # For follow-up messages, include history for context
        if len(st.session_state.da_messages) > 1 and file_type != "image":
            # Build full conversation with document context embedded in first message
            excerpt = content_text[:10000]
            history = []
            for i, msg in enumerate(st.session_state.da_messages):
                if i == 0:
                    history.append({
                        "role": "user",
                        "content": (
                            f"Document content:\n---\n{excerpt}\n---\n\n"
                            f"Question: {msg['content']}"
                        )
                    })
                else:
                    history.append(msg)
            reply = chat_with_groq(
                messages=history,
                system_prompt=CHAT_SYSTEM,
                model=model,
            )
        else:
            reply = _analyse_with_ai(content_text, file_type, raw_bytes, prompt, model)

    st.session_state.da_messages.append({"role": "assistant", "content": reply})
    st.session_state.da_analysed = True
