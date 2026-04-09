"""
groq_client.py — Groq Provider (v2)
=====================================
v2: Groq is now a first-class provider routed through ai_engine.
    If the user enters a gsk_… key, all generate() calls go to Groq automatically.

Backward-compat stubs kept so existing callers don't break.
"""

from utils.ai_engine import generate, generate_stream


def stream_chat_with_groq(prompt: str = "", system: str = "", **kwargs):
    """Stream through whichever provider is active (routes via ai_engine)."""
    return generate_stream(prompt=prompt, system=system, **kwargs)


def chat_with_groq(prompt: str = "", system: str = "", **kwargs) -> str:
    """Generate through whichever provider is active (routes via ai_engine)."""
    return generate(prompt=prompt, system=system, **kwargs)


def transcribe_audio(*args, **kwargs) -> str:
    return "[Audio transcription unavailable]"
