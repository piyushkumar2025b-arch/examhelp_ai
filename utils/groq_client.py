"""
groq_client.py — Streaming Groq API client with automatic key rotation & persona support.

Uses key_manager to pick the best available key before every call,
and reports rate-limit / auth errors back so key_manager can update state.
Supports persona mode where the AI adopts a historical character's speaking style.
"""

from __future__ import annotations
import os
from typing import Generator, Optional

from groq import Groq
from utils import key_manager

# ─────────────────────────────────────────────────────────────────────────────
# System prompt — focused on high-quality, exam-ready output
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are ExamHelp, a sharp and focused AI study assistant. Your job is to help students understand, memorise, and perform well in exams.

CORE RULES:
1. Answer ONLY questions related to studying, learning, academic topics, science, mathematics, history, literature, programming, languages, or exam preparation.
2. If the user provides context (PDF text, YouTube transcript, web article), ALWAYS prioritise that content. Quote page numbers or timestamps when relevant.
3. If asked about non-academic topics (entertainment, politics, gossip, personal advice unrelated to study), politely decline and redirect.
4. Never be vague. Be direct, precise, and genuinely useful.

OUTPUT QUALITY RULES — Follow these every time:
- Use clear **headings** (##) to organise responses longer than 3 paragraphs.
- Use **bullet points** for lists of facts, steps, or items — never run them together in a paragraph.
- Use **bold** to highlight key terms, definitions, and important exam facts.
- Use numbered lists for step-by-step processes or ranked items.
- For complex topics, use this structure: Overview → Key Concepts → Examples → Exam Tips.
- When summarising, always include a "🎯 Key Exam Points" section at the end.
- When explaining a concept, always give at least one concrete real-world example.
- For maths/science, show working step-by-step with clear notation.
- Keep answers focused — don't pad with filler phrases like "Great question!" or "Certainly!".
- End long answers with a short **"💡 Remember:"** tip that captures the single most important idea.
- ALWAYS provide COMPLETE answers — never truncate, never say "I'll continue in the next message".
- If an answer is long, structure it well but include ALL the information.

TONE: Encouraging, clear, and direct. Like a smart tutor who respects the student's time."""

MODEL = "llama-3.3-70b-versatile"   # primary model
FALLBACK_MODEL = "llama-3.1-8b-instant"  # fallback
MAX_CONTEXT_CHARS = 25_000


import requests
import re
import random

def _fetch_free_api_context(query: str) -> str:
    """Uses the free public Wikipedia API to fetch factual context for the user's latest query."""
    try:
        # Very basic stopword removal to get the core entity
        clean_q = re.sub(r'\b(what|is|the|explain|how|why|who|a|an|describe|tell|me|about|calculate)\b', '', query, flags=re.IGNORECASE).strip()
        if not clean_q or len(clean_q) < 3:
            return ""
        
        # Take the first ~3 words as the search title
        search_term = " ".join(clean_q.split()[:3])
        
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exsentences": "4",
            "exlimit": "1",
            "titles": search_term,
            "explaintext": "1",
            "formatversion": "2",
            "redirects": "1"
        }
        resp = requests.get(url, params=params, timeout=1.5)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", [])
            if pages and "extract" in pages[0] and pages[0]["extract"].strip():
                return pages[0]["extract"].strip()
    except Exception:
        pass
    return ""

def _build_messages(
    history: list[dict],
    context_text: str,
) -> list[dict]:
    """Prepend context to the conversation, injecting it as a system-level document."""
    messages: list[dict] = []

    if context_text:
        trimmed = context_text[:MAX_CONTEXT_CHARS]
        source_hint = ""
        if "[Page " in trimmed:
            source_hint = " (PDF document with page markers)"
        elif "YouTube Video Transcript" in trimmed:
            source_hint = " (YouTube video transcript with timestamps)"
        elif "Web Article:" in trimmed:
            source_hint = " (web article/webpage)"

        context_block = (
            f"=== STUDY MATERIAL{source_hint} ===\n\n"
            f"{trimmed}\n\n"
            f"=== END OF STUDY MATERIAL ===\n\n"
        )
        messages.append({
            "role": "user",
            "content": context_block + "Please acknowledge you have received this study material and briefly state what it covers in 1–2 sentences."
        })
        messages.append({
            "role": "assistant",
            "content": "✅ Study material received and ready. I'll use it as my primary reference to give you accurate, source-grounded answers. Ask me anything!"
        })

    # Fetch live free context for the very last user message to make AI perfect
    last_user_msg = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)
    live_api_context = ""
    if last_user_msg:
        live_api_context = _fetch_free_api_context(last_user_msg)

    if live_api_context:
        # We silently inject the free API data right before appending the history
        messages.append({
            "role": "system",
            "content": f"[SYSTEM INJECTION: The Free Open Knowledge API has retrieved the following real-time background fact for the latest query: '{live_api_context}'. Integrate this factual baseline into your upcoming answer to increase output perfection.]"
        })

    messages.extend(history)
    return messages


def stream_chat_with_groq(
    history: list[dict],
    context_text: str = "",
    override_key: Optional[str] = None,
    model: Optional[str] = None,
    persona_prompt: str = "",
) -> Generator[str, None, None]:
    """
    Yields response text chunks as they stream from the Groq API.
    Automatically rotates through ALL available keys on failure.
    
    Args:
        persona_prompt: Additional system prompt for persona/character mode.

    Raises:
        ValueError — configuration / validation error (do not retry).
        Exception  — API error (caller should check for rate_limit / auth).
    """
    key = key_manager.get_key(override=override_key)
    if not key:
        raise ValueError("No Groq API key available. Please add one in the sidebar.")

    client = Groq(api_key=key)
    messages = _build_messages(history, context_text)
    chosen_model = model or MODEL

    # Build system prompt with optional persona
    full_system = SYSTEM_PROMPT
    if persona_prompt:
        full_system += persona_prompt

    try:
        stream = client.chat.completions.create(
            model=chosen_model,
            messages=[{"role": "system", "content": full_system}] + messages,
            max_tokens=4096,       # increased for complete responses
            temperature=0.65,
            top_p=0.9,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

        # Success — record usage
        key_manager.mark_used(key)

    except Exception as e:
        err = str(e).lower()
        if "model_not_found" in err or ("model" in err and "not" in err):
            # Fall back to smaller model
            try:
                stream = client.chat.completions.create(
                    model=FALLBACK_MODEL,
                    messages=[{"role": "system", "content": full_system}] + messages,
                    max_tokens=4096,
                    temperature=0.65,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                key_manager.mark_used(key)
                return
            except Exception:
                pass

        if "rate_limit" in err or "429" in err:
            key_manager.mark_rate_limited(key)
        elif "authentication" in err or "api_key" in err or "401" in err or "invalid" in err:
            key_manager.mark_invalid(key)
        raise  # re-raise so app.py can handle UI feedback


def chat_with_groq(
    messages: list[dict],
    json_mode: bool = False,
    override_key: Optional[str] = None,
    model: Optional[str] = MODEL,
) -> str:
    """Non-streaming chat response for tool calls (JSON or text)."""
    key = key_manager.get_key(override=override_key)
    if not key:
        raise ValueError("No Groq API key available.")

    client = Groq(api_key=key)
    try:
        response_format = {"type": "json_object"} if json_mode else {"type": "text"}
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format=response_format,
            max_tokens=2048,
            temperature=0.3 if json_mode else 0.7,
        )
        key_manager.mark_used(key)
        return completion.choices[0].message.content
    except Exception as e:
        err = str(e).lower()
        if "rate_limit" in err or "429" in err:
            key_manager.mark_rate_limited(key)
        elif "authentication" in err or "api_key" in err or "401" in err or "invalid" in err:
            key_manager.mark_invalid(key)
        raise e


def transcribe_audio(audio_bytes: bytes, override_key: Optional[str] = None) -> str:
    """Uses Groq Whisper API to transcribe audio bytes to text."""
    key = key_manager.get_key(override=override_key)
    if not key:
        raise ValueError("No Groq API key available.")
    
    client = Groq(api_key=key)
    try:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model="whisper-large-v3",
            response_format="text"
        )
        return transcription
    except Exception as e:
        err = str(e).lower()
        if "rate_limit" in err or "429" in err:
            key_manager.mark_rate_limited(key)
        elif "authentication" in err or "api_key" in err or "401" in err or "invalid" in err:
            key_manager.mark_invalid(key)
        raise ValueError(f"Transcription failed: {e}")