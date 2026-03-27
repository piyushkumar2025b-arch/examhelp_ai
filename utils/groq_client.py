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
# System prompt — locked to study topics
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are ExamHelp, a focused AI study assistant.

RULES:
1. Answer ONLY questions related to studying, learning, academic topics,
   science, mathematics, history, literature, programming, or exam preparation.
2. If the user provides context (PDF text, YouTube transcript, web article),
   prioritize information from that context in your answers.
3. If asked about non-academic topics (e.g. entertainment, politics, gossip),
   politely decline and redirect to study topics.
4. Be concise but thorough. Use bullet points and headings where helpful.
5. When summarising, highlight key concepts likely to appear in exams.
6. Always be encouraging and supportive."""

MODEL = "llama-3.1-8b-instant"
MAX_CONTEXT_CHARS = 12_000


def _build_messages(
    history: list[dict],
    context_text: str,
) -> list[dict]:
    """Prepend context to the first user message if context exists."""
    messages: list[dict] = []

    if context_text:
        trimmed = context_text[:MAX_CONTEXT_CHARS]
        context_block = (
            f"=== STUDY MATERIAL (use this as your primary reference) ===\n\n"
            f"{trimmed}\n\n"
            f"=== END OF STUDY MATERIAL ===\n\n"
        )
        # Inject context as a leading user turn followed by an ack
        messages.append({"role": "user", "content": context_block + "Please acknowledge you have received this study material."})
        messages.append({"role": "assistant", "content": "Understood. I have read and stored your study material and will use it to answer your questions accurately."})

    messages.extend(history)
    return messages


def stream_chat_with_groq(
    history: list[dict],
    context_text: str = "",
    override_key: Optional[str] = None,
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

    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
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
        if "rate_limit" in err or "429" in err:
            key_manager.mark_rate_limited(key)
        elif "authentication" in err or "api_key" in err or "401" in err or "invalid" in err:
            key_manager.mark_invalid(key)
        raise  # re-raise so app.py can handle UI feedback
