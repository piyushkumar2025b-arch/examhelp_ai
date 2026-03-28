"""
gemini_client.py — Uncrashable Gemini client with 7-key rotation.

ARCHITECTURE
============
  7 Gemini keys (each from a separate GCP project = separate quota)
  Model: gemini-1.5-flash  (15 RPM, 1500 RPD, 1M TPM — most generous free tier)
  Fallback model: gemini-2.5-flash-lite  (15 RPM, 1000 RPD)

  REQUEST FLOW:
  1. gemini_key_manager picks key with most RPM + RPD headroom
  2. Call via REST (no SDK dependency)
  3. On 429 -> parse Retry-After -> hard cooldown -> next key instantly
  4. All 7 exhausted -> raise -> app.py falls back to Groq

  COMBINED CAPACITY (7 keys x gemini-1.5-flash free tier):
    RPM: 7 x 15 = 105 requests/min
    RPD: 7 x 1500 = 10,500 requests/day
"""

from __future__ import annotations
import time, json, base64, re
import requests
from typing import Generator, Optional

from utils import gemini_key_manager as gkm

FAST_MODEL    = "gemini-1.5-flash"
FALLBACK_MODEL = "gemini-2.5-flash-lite" 
VISION_MODEL  = "gemini-1.5-flash"
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

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


def _parse_retry_after(resp: requests.Response) -> Optional[float]:
    """Extract Retry-After seconds from a 429 Gemini response."""
    try:
        ra = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
        if ra: return float(ra) + 1.0
        # Try body
        body = resp.json()
        details = body.get("error", {}).get("details", [])
        for d in details:
            if d.get("@type","").endswith("RetryInfo"):
                delay = d.get("retryDelay","0s").rstrip("s")
                return float(delay) + 1.0
    except Exception:
        pass
    return None


def _build_contents(messages: list[dict], context_text: str = "") -> list[dict]:
    contents = []
    if context_text:
        trimmed = context_text[:25_000]
        contents.append({"role":"user","parts":[{"text":
            f"=== STUDY MATERIAL ===\n\n{trimmed}\n\n=== END ===\n\nAcknowledge receipt."}]})
        contents.append({"role":"model","parts":[{"text":
            "✅ Study material received. Ready to provide precise answers."}]})
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        content = msg["content"]
        if isinstance(content, str):
            contents.append({"role":role,"parts":[{"text":content}]})
        elif isinstance(content, list):
            parts = []
            for p in content:
                if p.get("type") == "text":
                    parts.append({"text": p["text"]})
                elif p.get("type") == "image_url":
                    url = p["image_url"]["url"]
                    if url.startswith("data:"):
                        header, b64 = url.split(",",1)
                        mime = header.split(":")[1].split(";")[0]
                        parts.append({"inline_data":{"mime_type":mime,"data":b64}})
                    else:
                        parts.append({"text":f"[Image: {url}]"})
            contents.append({"role":role,"parts":parts})
    return contents


def _call_gemini(key: str, model: str, contents: list[dict],
                 system_instruction: str, json_mode: bool = False,
                 stream: bool = False, max_tokens: int = 4096,
                 temperature: float = 0.65) -> requests.Response:
    endpoint = "streamGenerateContent" if stream else "generateContent"
    url = f"{_BASE_URL}/{model}:{endpoint}?key={key}"
    if stream: url += "&alt=sse"
    body = {
        "system_instruction": {"parts":[{"text":system_instruction}]},
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
        headers={"Content-Type":"application/json"},
        stream=stream, timeout=60,
    )


def _parse_text(resp_json: dict) -> str:
    try: return resp_json["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError): return ""


# ── Public: non-streaming ─────────────────────────────────────────────────────

def chat_with_gemini(
    messages: list[dict],
    context_text: str = "",
    json_mode: bool = False,
    override_key: Optional[str] = None,
    model: Optional[str] = None,
    use_pro: bool = False,
) -> str:
    chosen_model = model or FAST_MODEL
    contents = _build_contents(messages, context_text)
    tried: set[str] = set()
    last_err: Optional[Exception] = None

    for _attempt in range(gkm.MAX_RETRIES):
        if not tried and override_key:
            key = override_key
        else:
            key = gkm.get_next_key(exclude_keys=tried) or gkm.get_key()

        if not key: break
        if key in tried and len(tried) >= gkm.total_keys(): break
        tried.add(key)

        try:
            resp = _call_gemini(key, chosen_model, contents, SYSTEM_PROMPT,
                                json_mode=json_mode, stream=False,
                                max_tokens=2048 if json_mode else 8192,
                                temperature=0.3 if json_mode else 0.65)

            if resp.status_code == 200:
                gkm.mark_used(key)
                return _parse_text(resp.json())

            if resp.status_code == 429:
                retry_after = _parse_retry_after(resp)
                gkm.mark_rate_limited(key, retry_after=retry_after)
                continue

            if resp.status_code in (503, 529):
                gkm.mark_rate_limited(key, retry_after=15.0)
                continue

            if resp.status_code in (400, 401, 403):
                gkm.mark_invalid(key)
                continue

            last_err = ValueError(f"Gemini HTTP {resp.status_code}")
            continue

        except requests.exceptions.Timeout:
            last_err = TimeoutError("Gemini timed out")
            continue
        except Exception as e:
            last_err = e
            continue

    # All Gemini keys failed — raise so app.py's tiered fallback handles it
    if last_err:
        raise last_err
    raise ValueError("All Gemini API keys exhausted.")


# ── Public: streaming ─────────────────────────────────────────────────────────

def stream_chat_with_gemini(
    history: list[dict],
    context_text: str = "",
    override_key: Optional[str] = None,
    model: Optional[str] = None,
    persona_prompt: str = "",
    use_pro: bool = False,
) -> Generator[str, None, None]:
    chosen_model = model or FAST_MODEL
    sys_prompt = SYSTEM_PROMPT + ("\n\n" + persona_prompt if persona_prompt else "")
    contents = _build_contents(history, context_text)
    tried: set[str] = set()
    last_err: Optional[Exception] = None

    for _attempt in range(gkm.MAX_RETRIES):
        if not tried and override_key:
            key = override_key
        else:
            key = gkm.get_next_key(exclude_keys=tried) or gkm.get_key()

        if not key: break
        if key in tried and len(tried) >= gkm.total_keys(): break
        tried.add(key)

        try:
            resp = _call_gemini(key, chosen_model, contents, sys_prompt,
                                json_mode=False, stream=True,
                                max_tokens=8192, temperature=0.65)

            if resp.status_code == 429:
                retry_after = _parse_retry_after(resp)
                gkm.mark_rate_limited(key, retry_after=retry_after)
                continue

            if resp.status_code in (503, 529):
                gkm.mark_rate_limited(key, retry_after=15.0)
                continue

            if resp.status_code in (400, 401, 403):
                gkm.mark_invalid(key)
                continue

            if resp.status_code != 200:
                last_err = ValueError(f"Gemini HTTP {resp.status_code}")
                continue

            gkm.mark_used(key)
            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line: continue
                if raw_line.startswith("data:"):
                    json_str = raw_line[5:].strip()
                    if json_str == "[DONE]": break
                    try:
                        chunk = json.loads(json_str)
                        text = (chunk.get("candidates",[{}])[0]
                                .get("content",{}).get("parts",[{}])[0]
                                .get("text",""))
                        if text: yield text
                    except json.JSONDecodeError:
                        continue
            return  # success

        except requests.exceptions.Timeout:
            last_err = TimeoutError("Gemini stream timed out")
            continue
        except GeneratorExit:
            return
        except Exception as e:
            last_err = e
            continue

    # All Gemini keys failed — raise so app.py's tiered fallback handles it
    if last_err:
        raise last_err
    raise ValueError("All Gemini streaming keys exhausted.")


# ── Vision ────────────────────────────────────────────────────────────────────

def analyze_image_with_gemini(image_bytes: bytes, mime_type: str,
                               prompt: str, override_key: Optional[str] = None) -> str:
    b64 = base64.b64encode(image_bytes).decode()
    messages = [{"role":"user","content":[
        {"type":"image_url","image_url":{"url":f"data:{mime_type};base64,{b64}"}},
        {"type":"text","text":prompt},
    ]}]
    return chat_with_gemini(messages, json_mode=False,
                            override_key=override_key, model=VISION_MODEL)


def gemini_available() -> bool:
    return gkm.available_keys_count() > 0

def gemini_status() -> str:
    avail = gkm.available_keys_count()
    total = gkm.total_keys()
    if total == 0: return "❌ No Gemini keys configured"
    if avail == 0: return f"⏳ All {total} Gemini keys on cooldown"
    return f"✅ Gemini: {avail}/{total} keys ready"
