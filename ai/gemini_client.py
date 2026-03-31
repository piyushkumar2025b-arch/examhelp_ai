"""
ai/gemini_client.py — Clean stub
All Gemini calls are handled by utils/ai_engine.py (9-key rotation, retry, streaming).
This file exists for backwards compatibility only.
"""
from utils.ai_engine import generate, generate_stream, vision_generate, json_generate

def call_gemini(prompt: str, system: str = "", **kwargs) -> str:
    return generate(prompt=prompt, system=system)

def stream_gemini(prompt: str, system: str = "", **kwargs):
    return generate_stream(prompt=prompt, system=system)

def vision_call(prompt: str, image_b64: str, **kwargs) -> str:
    return vision_generate(prompt=prompt, image_b64=image_b64)
