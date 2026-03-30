"""
groq_client.py — REMOVED
=========================
Groq integration has been permanently removed.
All functions delegate to Gemini via ai_engine.
"""

from utils.ai_engine import generate, generate_stream

def stream_chat_with_groq(prompt: str = "", system: str = "", **kwargs):
    return generate_stream(prompt=prompt, system=system)

def chat_with_groq(prompt: str = "", system: str = "", **kwargs) -> str:
    return generate(prompt=prompt, system=system)

def transcribe_audio(*args, **kwargs) -> str:
    return "[Audio transcription unavailable — Groq removed]"
