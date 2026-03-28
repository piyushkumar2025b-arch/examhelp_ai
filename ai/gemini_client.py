"""
gemini_client.py — Google Gemini API client with full 7-key rotation + Groq fallback.

ARCHITECTURE
============
Primary path  → Gemini (gemini-1.5-flash  /  gemini-1.5-pro)
  ↓ on 429 / quota     → rotate to next Gemini key (up to 7x)
  ↓ all Gemini down    → fall through to Groq (groq_client.py)

Features
────────
• Streaming and non-streaming text generation
• Vision / multimodal (image + text) via Gemini's vision models
• Structured JSON output
• Automatic key rotation on rate-limit or auth error
• Token/request accounting fed back to gemini_key_manager
• Transparent Groq fallback — callers never see the switch

Models
──────
FAST_MODEL  = gemini-1.5-flash  (default — fast, cheap, 1M ctx)
PRO_MODEL   = gemini-1.5-pro    (complex tasks)
VISION_MODEL= gemini-1.5-flash  (multimodal)
"""

from __future__ import annotations
import time
import json
import base64
import requests
from typing import Generator, Optional

from utils import gemini_key_manager as gkm
from utils import key_manager            # Groq fallback

# ── Models ────────────────────────────────────────────────────────────────────
FAST_MODEL   = "gemini-1.5-flash"
PRO_MODEL    = "gemini-1.5-pro"
VISION_MODEL = "gemini-1.5-flash"

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


# ── System prompt (mirrors Groq's for seamless fallback) ─────────────────────
SYSTEM_PROMPT = """\
You are ExamHelp AI, a GOD-LEVEL Study Architect and Academic Reasoning Engine.

TRANSFORMATION PROTOCOL — DEEP-THINK MODE:
1. AXIOMATIC EXPLANATION: Start every complex topic from first principles.
2. LONG-FORM SCHOLARSHIP: For academic queries provide 4-8 comprehensive paragraphs.
3. VISUAL MANIFEST (MANDATORY): If a concept is spatial/physical/geometric, append:
   ---
   VISUAL_MANIFEST: {"query": "specific image search terms", "caption": "technical description"}
   ---
4. SOURCE-SYNC: If [STUDY MATERIAL] context is provided, explicitly reference it.

RESPONSE ARCHITECTURE:
## 🧠 Conceptual Axioms
## 🔍 Logic & Deep-Dive
## 🛠️ Procedural Steps
## 🧪 Real-World Proof
## 🎯 Exam Strategy

TONE: Intellectually elite, authoritative, exhaustive.\
"""


# ── Low-level REST helpers ────────────────────────────────────────────────────

def _build_contents(messages: list[dict], context_text: str = "") -> list[dict]:
    """Convert OpenAI-style messages → Gemini contents array."""
    contents = []

    if context_text:
        trimmed = context_text[:25_000]
        contents.append({
            "role": "user",
            "parts": [{"text": f"=== STUDY MATERIAL ===\n\n{trimmed}\n\n=== END ===\n\nAcknowledge receipt."}]
        })
        contents.append({
            "role": "model",
            "parts": [{"text": "✅ Study material received. Ready to provide precise, source-grounded answers."}]
        })

    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        content = msg["content"]
        if isinstance(content, str):
            contents.append({"role": role, "parts": [{"text": content}]})
        elif isinstance(content, list):
            parts = []
            for part in content:
                if part.get("type") == "text":
                    parts.append({"text": part["text"]})
                elif part.get("type") == "image_url":
                    url = part["image_url"]["url"]
                    if url.startswith("data:"):
                        header, b64 = url.split(",", 1)
                        mime = header.split(":")[1].split(";")[0]
                        parts.append({"inline_data": {"mime_type": mime, "data": b64}})
                    else:
                        parts.append({"text": f"[Image: {url}]"})
            contents.append({"role": role, "parts": parts})

    return contents


def _call_gemini(
    key: str,
    model: str,
    contents: list[dict],
    system_instruction: str,
    json_mode: bool = False,
    stream: bool = False,
    max_tokens: int = 4096,
    temperature: float = 0.65,
) -> requests.Response:
    """Raw REST call to Gemini generateContent / streamGenerateContent."""
    endpoint = "streamGenerateContent" if stream else "generateContent"
    url = f"{_BASE_URL}/{model}:{endpoint}?key={key}"
    if stream:
        url += "&alt=sse"

    body: dict = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
            "topP": 0.9,
        }
    }
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"

    return requests.post(
        url, json=body,
        headers={"Content-Type": "application/json"},
        stream=stream,
        timeout=60,
    )


def _parse_text(resp_json: dict) -> str:
    try:
        return resp_json["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return ""


# ── Public: non-streaming ─────────────────────────────────────────────────────

def chat_with_gemini(
    messages: list[dict],
    context_text: str = "",
    json_mode: bool = False,
    override_key: Optional[str] = None,
    model: Optional[str] = None,
    use_pro: bool = False,
) -> str:
    """
    Non-streaming Gemini call with automatic key rotation.
    Falls back to Groq automatically if all Gemini keys fail.
    """
    chosen_model = model or (PRO_MODEL if use_pro else FAST_MODEL)
    contents     = _build_contents(messages, context_text)
    tried: set[str] = set()
    last_err: Optional[Exception] = None

    for attempt in range(gkm.MAX_RETRIES):
        key = (
            (override_key if attempt == 0 and override_key else None)
            or gkm.get_next_key(exclude_key=next(iter(tried), None))
            or gkm.get_key()
        )
        if not key:
            break
        if key in tried and len(tried) >= gkm.total_keys():
            break
        tried.add(key)

        try:
            resp = _call_gemini(
                key, chosen_model, contents,
                system_instruction=SYSTEM_PROMPT,
                json_mode=json_mode,
                stream=False,
                max_tokens=2048 if json_mode else 4096,
                temperature=0.3 if json_mode else 0.65,
            )

            if resp.status_code == 200:
                gkm.mark_used(key)
                data = resp.json()
                return _parse_text(data)

            if resp.status_code == 429:
                gkm.mark_rate_limited(key)
                time.sleep(0.5)
                continue

            if resp.status_code in (400, 401, 403):
                gkm.mark_invalid(key)
                continue

            # Other HTTP error — try next key
            last_err = ValueError(f"Gemini HTTP {resp.status_code}: {resp.text[:200]}")
            continue

        except requests.exceptions.Timeout:
            last_err = TimeoutError("Gemini request timed out")
            continue
        except Exception as e:
            last_err = e
            continue

    # ── Groq fallback ──────────────────────────────────────────────────────────
    from utils.groq_client import chat_with_groq
    return chat_with_groq(messages, json_mode=json_mode)


# ── Public: streaming ─────────────────────────────────────────────────────────

def stream_chat_with_gemini(
    history: list[dict],
    context_text: str = "",
    override_key: Optional[str] = None,
    model: Optional[str] = None,
    persona_prompt: str = "",
    use_pro: bool = False,
) -> Generator[str, None, None]:
    """
    Streaming Gemini call — yields text chunks.
    On full failure falls through to Groq streaming automatically.
    """
    chosen_model = model or (PRO_MODEL if use_pro else FAST_MODEL)
    sys_prompt   = SYSTEM_PROMPT + ("\n\n" + persona_prompt if persona_prompt else "")
    contents     = _build_contents(history, context_text)
    tried: set[str] = set()
    last_err: Optional[Exception] = None

    for attempt in range(gkm.MAX_RETRIES):
        key = (
            (override_key if attempt == 0 and override_key else None)
            or gkm.get_next_key(exclude_key=next(iter(tried), None))
            or gkm.get_key()
        )
        if not key:
            break
        if key in tried and len(tried) >= gkm.total_keys():
            break
        tried.add(key)

        try:
            resp = _call_gemini(
                key, chosen_model, contents,
                system_instruction=sys_prompt,
                json_mode=False,
                stream=True,
                max_tokens=4096,
                temperature=0.65,
            )

            if resp.status_code == 429:
                gkm.mark_rate_limited(key)
                time.sleep(0.5)
                continue

            if resp.status_code in (400, 401, 403):
                gkm.mark_invalid(key)
                continue

            if resp.status_code != 200:
                last_err = ValueError(f"Gemini HTTP {resp.status_code}")
                continue

            # Stream SSE lines
            gkm.mark_used(key)
            buffer = ""
            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                if raw_line.startswith("data:"):
                    json_str = raw_line[5:].strip()
                    if json_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(json_str)
                        text = (
                            chunk.get("candidates", [{}])[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        if text:
                            yield text
                    except json.JSONDecodeError:
                        continue
            return  # success — done

        except requests.exceptions.Timeout:
            last_err = TimeoutError("Gemini stream timed out")
            continue
        except GeneratorExit:
            return
        except Exception as e:
            last_err = e
            continue

    # ── Groq streaming fallback ────────────────────────────────────────────────
    from utils.groq_client import stream_chat_with_groq
    yield from stream_chat_with_groq(
        history,
        context_text=context_text,
        persona_prompt=persona_prompt,
    )


# ── Public: vision / multimodal ───────────────────────────────────────────────

def analyze_image_with_gemini(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    override_key: Optional[str] = None,
) -> str:
    """
    Send an image + text prompt to Gemini Vision.
    Returns the analysis text.
    """
    b64 = base64.b64encode(image_bytes).decode()
    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            {"type": "text", "text": prompt},
        ]
    }]
    return chat_with_gemini(
        messages,
        json_mode=False,
        override_key=override_key,
        model=VISION_MODEL,
    )


# ── Status helpers ────────────────────────────────────────────────────────────

def gemini_available() -> bool:
    """True if at least one Gemini key is ready right now."""
    return gkm.available_keys_count() > 0


def gemini_status() -> str:
    """One-line human-readable status."""
    avail = gkm.available_keys_count()
    total = gkm.total_keys()
    if total == 0:
        return "❌ No Gemini keys configured"
    if avail == 0:
        return f"⏳ All {total} Gemini keys on cooldown — using Groq fallback"
    return f"✅ Gemini: {avail}/{total} keys ready"
