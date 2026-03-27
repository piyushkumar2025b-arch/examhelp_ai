"""
groq_client.py — Streaming Groq API client with automatic key rotation.

Uses key_manager to pick the best available key before every call,
and reports rate-limit / auth errors back so key_manager can update state.
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

TONE: Encouraging, clear, and direct. Like a smart tutor who respects the student's time."""

MODEL = "llama-3.3-70b-versatile"   # upgraded for better output quality
FALLBACK_MODEL = "llama-3.1-8b-instant"
MAX_CONTEXT_CHARS = 25_000           # increased to support larger documents


def _build_messages(
    history: list[dict],
    context_text: str,
) -> list[dict]:
    """Prepend context to the conversation, injecting it as a system-level document."""
    messages: list[dict] = []

    if context_text:
        trimmed = context_text[:MAX_CONTEXT_CHARS]
        # Count sources/type hints for better AI framing
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

    messages.extend(history)
    return messages


def stream_chat_with_groq(
    history: list[dict],
    context_text: str = "",
    override_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Yields response text chunks as they stream from the Groq API.

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

    try:
        stream = client.chat.completions.create(
            model=chosen_model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            max_tokens=2048,       # increased for richer responses
            temperature=0.65,      # slightly lower for more precise answers
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
        if "model_not_found" in err or "model" in err and "not" in err:
            # Fall back to smaller model
            try:
                stream = client.chat.completions.create(
                    model=FALLBACK_MODEL,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                    max_tokens=2048,
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