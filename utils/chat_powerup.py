"""
chat_powerup.py — Core Chat Powerup v2.0
Rating system, follow-up suggestions, auto web search trigger,
multi-modal file input, cross-session memory, smart context injection.
"""

from __future__ import annotations
import json
import os
import hashlib
import base64
import streamlit as st
from typing import Optional

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
        data[doc_hash] = topics[-5:]  # keep last 5 only
        with open(SESSIONS_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def get_doc_hash(context_text: str) -> str:
    return hashlib.md5(context_text[:500].encode()).hexdigest()


def update_memory_with_topic(user_message: str):
    """Extract topic from user message and persist to session memory."""
    ctx = st.session_state.get("context_text", "")
    if not ctx:
        return
    doc_hash = get_doc_hash(ctx)
    topics = st.session_state.get("_session_topics", [])
    # Use first 80 chars of user message as topic
    short = user_message[:80].strip()
    if short and short not in topics:
        topics.append(short)
    st.session_state["_session_topics"] = topics
    save_session_memory(doc_hash, topics)


def render_returning_user_memory():
    """Show a memory banner if returning user has prior session topics."""
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
    """Render thumbs up/down rating buttons for an AI response."""
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
    """Generate 3 follow-up question suggestions using 8B model in same call."""
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
            model="llama-3.1-8b-instant",
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
    """Render clickable pill buttons for follow-up suggestions."""
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
    """Check if AI response indicates it lacks current information."""
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
    """Run DuckDuckGo search and return formatted results as context."""
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


# ── 5. MULTI-MODAL CHAT FILE INPUT ────────────────────────────────────

def render_chat_file_uploader() -> tuple[Optional[str], Optional[str]]:
    """
    Render file uploader in the chat sidebar.
    Returns (extracted_text, file_type) or (None, None).
    """
    uploaded = st.file_uploader(
        "📎 Attach file to chat",
        type=["jpg", "jpeg", "png", "pdf"],
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

    file_type = uploaded.type
    extracted = None

    if file_type.startswith("image/"):
        # Send to Gemini vision
        try:
            img_bytes = uploaded.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            from utils.secret_manager import call_gemini
            extracted = call_gemini(
                prompt="Describe this image in detail and extract all text visible in it.",
                image_data=img_b64,
                image_mime=file_type,
                max_tokens=1000,
            )
            if not extracted:
                # Fallback to OCR
                from utils.ocr_handler import extract_text_from_image
                extracted = extract_text_from_image(img_bytes)
        except Exception as e:
            extracted = f"[Image attached — could not extract text: {e}]"

    elif file_type == "application/pdf":
        try:
            from utils.pdf_handler import extract_text_from_pdf
            pdf_bytes = uploaded.read()
            extracted = extract_text_from_pdf(pdf_bytes)
            if extracted:
                extracted = extracted[:3000]  # limit context
        except Exception as e:
            extracted = f"[PDF attached — could not extract text: {e}]"

    result = (extracted, file_type)
    st.session_state[cache_key] = result
    return result


# ── 6. SMART CONTEXT INJECTION (top-3 vector chunks) ────────────────

def get_smart_context(user_query: str, max_chunks: int = 3) -> str:
    """
    Retrieve top-k relevant chunks from vector store instead of full context_text.
    Falls back to truncated context_text if vector store unavailable.
    """
    vs = st.session_state.get("vector_store")
    if vs is not None:
        try:
            chunks = vs.search(user_query, k=max_chunks)
            if chunks:
                return "\n\n---\n\n".join(chunks)
        except Exception:
            pass

    # Fallback: return first 3000 chars of context
    ctx = st.session_state.get("context_text", "")
    return ctx[:3000] if ctx else ""
