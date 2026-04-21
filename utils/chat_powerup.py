"""
chat_powerup.py — Core Chat Powerup v3.0
Rating system, follow-up suggestions, auto web search trigger,
multi-modal file input (FULLY WORKING — images displayed + AI analysed),
cross-session memory, smart context injection.
"""

from __future__ import annotations
import json
import os
import hashlib
import base64
import streamlit as st
from typing import Optional, Tuple

SESSIONS_FILE = "sessions.json"

# ── 1. CROSS-SESSION MEMORY ──────────────────────────────────────────

def load_session_memory(doc_hash: str) -> list:
    """Load last 5 topics from sessions.json for a given document hash."""
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "r") as f:
                data = json.load(f)
            return data.get(doc_hash, [])
    except Exception:
        pass
    return []


def save_session_memory(doc_hash: str, topics: list):
    """Save last 5 topics discussed to sessions.json."""
    try:
        data = {}
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "r") as f:
                data = json.load(f)
        data[doc_hash] = topics[-5:]
        with open(SESSIONS_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def get_doc_hash(context_text: str) -> str:
    return hashlib.md5(context_text[:500].encode()).hexdigest()


def update_memory_with_topic(user_message: str):
    ctx = st.session_state.get("context_text", "")
    if not ctx:
        return
    doc_hash = get_doc_hash(ctx)
    topics = st.session_state.get("_session_topics", [])
    short = user_message[:80].strip()
    if short and short not in topics:
        topics.append(short)
    st.session_state["_session_topics"] = topics
    save_session_memory(doc_hash, topics)


def render_returning_user_memory():
    ctx = st.session_state.get("context_text", "")
    if not ctx:
        return
    doc_hash = get_doc_hash(ctx)
    if st.session_state.get("_memory_shown_hash") == doc_hash:
        return
    topics = load_session_memory(doc_hash)
    if topics:
        st.session_state["_memory_shown_hash"] = doc_hash
        with st.expander("🧠 Welcome back! Resume where you left off", expanded=False):
            st.caption("Your last topics with this document:")
            for t in topics[-5:]:
                if st.button(f"↩ {t}", key=f"mem_{hashlib.md5(t.encode()).hexdigest()[:6]}"):
                    st.session_state.queued_prompt = t
                    st.rerun()


# ── 2. RESPONSE RATING ───────────────────────────────────────────────

def render_rating_buttons(msg_index: int, response_content: str):
    ratings = st.session_state.get("message_ratings", {})
    current = ratings.get(msg_index)
    r1, r2, r3 = st.columns([1, 1, 10])
    with r1:
        label = "👍✓" if current == "up" else "👍"
        if st.button(label, key=f"rate_up_{msg_index}", help="Good response"):
            st.session_state.message_ratings[msg_index] = "up"
            st.toast("Thanks for the feedback! 🎉")
    with r2:
        label = "👎✓" if current == "down" else "👎"
        if st.button(label, key=f"rate_dn_{msg_index}", help="Poor response"):
            st.session_state.message_ratings[msg_index] = "down"
            st.toast("Got it — we'll improve!")


# ── 3. FOLLOW-UP SUGGESTIONS ─────────────────────────────────────────

def generate_followup_suggestions(ai_response: str, user_question: str) -> list[str]:
    cache_key = f"_followups_{hashlib.md5((ai_response[:200]+user_question).encode()).hexdigest()}"
    cached = st.session_state.get(cache_key)
    if cached:
        return cached
    try:
        from utils.ai_engine import generate
        prompt = (
            f"Based on this Q&A pair, generate exactly 3 short follow-up questions a student might ask. "
            f"Output ONLY a JSON array of 3 strings. No explanation.\n\n"
            f"Q: {user_question[:300]}\nA: {ai_response[:500]}"
        )
        resp = generate(
            messages=[{"role": "user", "content": prompt}],
            context_text="",
            max_tokens=200,
            temperature=0.7,
        )
        import re
        m = re.search(r'\[.*?\]', resp, re.DOTALL)
        if m:
            suggestions = json.loads(m.group(0))
            if isinstance(suggestions, list) and len(suggestions) >= 1:
                result = [str(s).strip() for s in suggestions[:3]]
                st.session_state[cache_key] = result
                return result
    except Exception:
        pass
    return []


def render_followup_pills(suggestions: list[str], msg_index: int):
    if not suggestions:
        return
    st.caption("💡 Suggested follow-ups:")
    cols = st.columns(len(suggestions))
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            short = suggestion[:55] + "…" if len(suggestion) > 55 else suggestion
            if st.button(short, key=f"followup_{msg_index}_{i}", use_container_width=True):
                st.session_state.queued_prompt = suggestion
                st.rerun()


# ── 4. AUTO WEB SEARCH TRIGGER ───────────────────────────────────────

def check_auto_web_search_trigger(ai_response: str) -> bool:
    triggers = [
        "i don't have current information",
        "i don't have access to real-time",
        "my knowledge cutoff",
        "i cannot access the internet",
        "as of my last update",
        "i'm not aware of recent",
        "i don't have up-to-date",
    ]
    lower = ai_response.lower()
    return any(t in lower for t in triggers)


def auto_web_search_and_append(user_question: str) -> str:
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(user_question, max_results=5):
                results.append(f"• {r.get('title', '')}: {r.get('body', '')[:200]}")
        if results:
            return "\n\n🌐 **Live Web Results:**\n" + "\n".join(results[:5])
    except Exception:
        pass
    return ""


# ── 5. MULTI-MODAL CHAT FILE INPUT (FULLY WORKING) ───────────────────

def _analyse_image_with_ai(img_bytes: bytes, mime: str, user_prompt: str = "") -> str:
    """
    Send an image to the AI engine for analysis.
    Works with Gemini (native vision) and falls back to OCR for Groq/Cerebras.
    """
    from utils.user_key_store import get_user_key

    img_b64 = base64.b64encode(img_bytes).decode()
    analysis_prompt = user_prompt or (
        "Analyse this image thoroughly. "
        "1) Describe what you see in full detail. "
        "2) Extract ALL text visible (handwriting, printed, labels). "
        "3) If it contains math/diagrams/charts, explain them. "
        "Be comprehensive — this will be used as study context."
    )

    try:
        from utils.ai_engine import generate
        result = generate(
            prompt=analysis_prompt,
            image_data=img_b64,
            image_mime=mime,
            max_tokens=1500,
        )
        if result and len(result.strip()) > 10:
            return result.strip()
    except Exception as e:
        err = str(e)
        # Groq/Cerebras don't support vision — fall back to OCR
        if "vision" in err.lower() or "image" in err.lower() or "multimodal" in err.lower() \
                or "groq" in err.lower() or "cerebras" in err.lower():
            pass  # fall through to OCR
        else:
            return f"[AI analysis failed: {err}]"

    # OCR fallback
    try:
        from utils.ocr_handler import extract_text_from_image
        ocr_text = extract_text_from_image(img_bytes)
        if ocr_text and ocr_text.strip():
            return f"[OCR extracted text]:\n{ocr_text}"
    except Exception:
        pass

    return "[Image attached — text extraction unavailable. Gemini key recommended for full vision analysis.]"


def render_chat_image_uploader() -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """
    Dedicated image uploader for the chat.
    Returns (img_bytes, mime_type, ai_analysis_text) or (None, None, None).
    Shows a live preview of the uploaded image.
    """
    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(16,185,129,0.05));
border:1px dashed rgba(99,102,241,0.3);border-radius:14px;padding:14px;margin:8px 0;">
  <div style="color:#a5b4fc;font-size:.82rem;font-weight:700;margin-bottom:8px;">
    📸 Upload Image for AI Analysis
  </div>
  <div style="color:#64748b;font-size:.73rem;">
    Supports: JPG, PNG, WEBP, GIF · Handwriting, diagrams, text, photos
  </div>
</div>
""", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload image",
        type=["jpg", "jpeg", "png", "webp", "gif"],
        key="chat_image_upload_v2",
        label_visibility="collapsed",
    )

    if not uploaded:
        return None, None, None

    img_bytes = uploaded.read()
    mime = uploaded.type or "image/jpeg"
    file_hash = hashlib.md5(img_bytes[:512]).hexdigest()[:10]
    cache_key = f"_chat_img_{file_hash}"

    # Show live image preview
    import io
    st.image(img_bytes, caption=f"📎 {uploaded.name}", use_container_width=True)

    cached = st.session_state.get(cache_key)
    if cached:
        st.success("✅ Image previously analysed — context loaded!")
        return img_bytes, mime, cached

    with st.spinner("🔍 Analysing image with AI..."):
        analysis = _analyse_image_with_ai(img_bytes, mime)

    if analysis and not analysis.startswith("[AI analysis failed"):
        st.session_state[cache_key] = analysis
        with st.expander("📋 AI Image Analysis", expanded=True):
            st.markdown(f"""
<div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.2);
border-radius:12px;padding:14px;color:#e2e8f0;font-size:.84rem;line-height:1.6;
white-space:pre-wrap;max-height:250px;overflow-y:auto;">
{analysis}
</div>""", unsafe_allow_html=True)
        st.success("✅ Image analysed! You can now ask questions about it.")
    else:
        st.warning(analysis)

    return img_bytes, mime, analysis


def render_chat_file_uploader() -> Tuple[Optional[str], Optional[str]]:
    """
    Render file uploader in the chat sidebar (PDF + Image).
    Returns (extracted_text, file_type) or (None, None).
    FULLY WORKING — uses ai_engine for images, pdf_handler for PDFs.
    """
    uploaded = st.file_uploader(
        "📎 Attach file to chat",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        key="chat_file_upload",
        label_visibility="collapsed",
        help="Attach an image or PDF to ask questions about it",
    )

    if not uploaded:
        return None, None

    file_hash = hashlib.md5(uploaded.name.encode()).hexdigest()[:8]
    cache_key = f"_chat_file_{file_hash}"

    cached = st.session_state.get(cache_key)
    if cached:
        return cached

    file_type = uploaded.type or ""
    extracted = None

    if file_type.startswith("image/"):
        img_bytes = uploaded.read()
        # Show preview
        st.image(img_bytes, caption=f"📎 {uploaded.name}", use_container_width=True)
        # AI analysis
        with st.spinner("🔍 Analysing image..."):
            extracted = _analyse_image_with_ai(img_bytes, file_type)

    elif file_type == "application/pdf":
        try:
            from utils.pdf_handler import extract_text_from_pdf
            pdf_bytes = uploaded.read()
            extracted = extract_text_from_pdf(pdf_bytes)
            if extracted:
                extracted = extracted[:4000]
                st.success(f"📄 PDF loaded: {len(extracted)} chars extracted")
        except Exception as e:
            extracted = f"[PDF attached — could not extract text: {e}]"

    result = (extracted, file_type)
    st.session_state[cache_key] = result
    return result


# ── 6. SMART CONTEXT INJECTION ───────────────────────────────────────

def get_smart_context(user_query: str, max_chunks: int = 3) -> str:
    vs = st.session_state.get("vector_store")
    if vs is not None:
        try:
            chunks = vs.search(user_query, k=max_chunks)
            if chunks:
                return "\n\n---\n\n".join(chunks)
        except Exception:
            pass
    ctx = st.session_state.get("context_text", "")
    return ctx[:3000] if ctx else ""


# ── 7. IN-CHAT IMAGE ANALYSIS WIDGET ─────────────────────────────────

def render_inline_image_ask(img_b64: str, mime: str):
    """
    Render an inline 'Ask about this image' widget after image is uploaded.
    Lets user type a specific question about the image.
    """
    st.markdown("""
<div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.2);
border-radius:12px;padding:12px;margin-top:8px;">
  <div style="color:#34d399;font-weight:700;font-size:.82rem;margin-bottom:6px;">
    🤖 Ask a specific question about this image
  </div>
</div>
""", unsafe_allow_html=True)
    question = st.text_input(
        "Your question about the image:",
        placeholder="e.g. What does the diagram show? Solve this equation.",
        key="img_inline_question",
        label_visibility="collapsed",
    )
    if st.button("🔍 Analyse", key="img_inline_ask", type="primary", use_container_width=True):
        if not question.strip():
            question = "Describe and analyse this image in detail."
        with st.spinner("Analysing..."):
            img_bytes = base64.b64decode(img_b64)
            result = _analyse_image_with_ai(img_bytes, mime, question)
        st.markdown(f"""
<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
border-radius:12px;padding:14px;margin-top:8px;color:#e2e8f0;font-size:.85rem;line-height:1.6;">
{result}
</div>""", unsafe_allow_html=True)
        # Also add to chat context
        if result:
            ctx = st.session_state.get("context_text", "")
            st.session_state["context_text"] = (ctx + "\n\n[Image Analysis]:\n" + result).strip()
