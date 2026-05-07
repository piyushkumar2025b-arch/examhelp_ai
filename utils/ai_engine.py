"""
ai_engine.py — High-Level AI Orchestration v5.0
=================================================
v5.0: 18-provider multi-key system.

Supported providers (18 total):
  gemini, groq, cerebras,                          ← original 3
  openai, anthropic, mistral, cohere, together,    ← new batch 1
  perplexity, openrouter, fireworks, replicate,    ← new batch 2
  huggingface, sambanova, nvidia, deepseek,        ← new batch 3
  ai21, xai                                        ← new batch 4

All providers use OpenAI-compatible /v1/chat/completions EXCEPT:
  gemini   → native Gemini REST (via OmniKeyEngine)
  replicate → polling REST
  huggingface → Inference API

Vision (image input) is supported for:
  gemini, openai, anthropic, nvidia, replicate
"""
# Providers that support vision/image input
_VISION_CAPABLE_PROVIDERS = {"gemini", "openai", "anthropic", "nvidia", "replicate", "openrouter", "together"}

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import ssl
import sys
import time
import threading
import urllib.error
import urllib.request
from typing import Dict, Iterator, List, Optional

from utils.omnikey_engine import OMNI_ENGINE
from utils.prompts import get_engine_config

# ── Model defaults ────────────────────────────────────────────────────────────
GEMINI_MODELS    = ["gemini-2.5-flash"]
GROQ_MODEL       = "llama-3.3-70b-versatile"
CEREBRAS_MODEL   = "llama3.3-70b"
OPENAI_MODEL     = "gpt-4o-mini"
ANTHROPIC_MODEL  = "claude-3-haiku-20240307"
MISTRAL_MODEL    = "mistral-small-latest"
COHERE_MODEL     = "command-r"
TOGETHER_MODEL   = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
PERPLEXITY_MODEL = "llama-3.1-sonar-small-128k-online"
OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
FIREWORKS_MODEL  = "accounts/fireworks/models/llama-v3p1-8b-instruct"
REPLICATE_MODEL  = "meta/meta-llama-3-8b-instruct"
HUGGINGFACE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
SAMBANOVA_MODEL  = "Meta-Llama-3.3-70B-Instruct"
NVIDIA_MODEL     = "meta/llama-3.1-8b-instruct"
DEEPSEEK_MODEL   = "deepseek-chat"
AI21_MODEL       = "jamba-1.5-mini"
XAI_MODEL        = "grok-beta"

# ── API endpoints ─────────────────────────────────────────────────────────────
_ENDPOINTS = {
    "openai":      "https://api.openai.com/v1/chat/completions",
    "anthropic":   "https://api.anthropic.com/v1/messages",
    "mistral":     "https://api.mistral.ai/v1/chat/completions",
    "cohere":      "https://api.cohere.ai/v2/chat",
    "together":    "https://api.together.xyz/v1/chat/completions",
    "perplexity":  "https://api.perplexity.ai/chat/completions",
    "openrouter":  "https://openrouter.ai/api/v1/chat/completions",
    "fireworks":   "https://api.fireworks.ai/inference/v1/chat/completions",
    "sambanova":   "https://api.sambanova.ai/v1/chat/completions",
    "nvidia":      "https://integrate.api.nvidia.com/v1/chat/completions",
    "deepseek":    "https://api.deepseek.com/v1/chat/completions",
    "ai21":        "https://api.ai21.com/studio/v1/chat/completions",
    "xai":         "https://api.x.ai/v1/chat/completions",
    "groq":        "https://api.groq.com/openai/v1/chat/completions",
    "cerebras":    "https://api.cerebras.ai/v1/chat/completions",
    "huggingface": "https://api-inference.huggingface.co/models/{model}",
    "replicate":   "https://api.replicate.com/v1/models/{model}/predictions",
}

# ── In-memory cache ───────────────────────────────────────────────────────────
_mem_cache: Dict[str, str] = {}
_cache_lock = threading.Lock()
_CACHE_MAX = 400


def _cache_key(prompt: str, system: str) -> str:
    return hashlib.md5(f"{prompt}::{system}".encode()).hexdigest()

def _cache_get(k: str) -> Optional[str]:
    with _cache_lock:
        return _mem_cache.get(k)

def _cache_set(k: str, v: str) -> None:
    with _cache_lock:
        if len(_mem_cache) >= _CACHE_MAX:
            for old_k in list(_mem_cache.keys())[:50]:
                _mem_cache.pop(old_k, None)
        _mem_cache[k] = v


# ── SSL context ───────────────────────────────────────────────────────────────
_ssl_ctx = None
_ssl_lock = threading.Lock()

def _ssl() -> Optional[ssl.SSLContext]:
    global _ssl_ctx
    with _ssl_lock:
        if _ssl_ctx is None:
            try:
                import certifi
                _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                try:
                    _ssl_ctx = ssl.create_default_context()
                except Exception:
                    _ssl_ctx = None
    return _ssl_ctx


# ── HTTP helpers ──────────────────────────────────────────────────────────────
_COMMON_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/124 Safari/537.36"
)

def _post_json(url: str, body: dict, headers: dict, timeout: int = 90) -> dict:
    """POST JSON and return parsed response dict."""
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": _COMMON_UA, **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl()) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode(errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code}: {body_text[:400]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def _extract_openai_text(raw: dict) -> str:
    """Extract text from OpenAI-compatible response."""
    choices = raw.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    raise RuntimeError(f"Unexpected response format: {str(raw)[:200]}")


# ── Provider-specific callers ────────────────────────────────────────────────

def _call_openai_compat(
    key: str, url: str, model: str,
    prompt: str, system: str = "",
    temperature: float = 0.7, max_tokens: int = 4096,
    image_b64: str = "", image_mime: str = "image/jpeg",
) -> str:
    """Generic OpenAI-compatible endpoint caller (covers most providers)."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})

    if image_b64:
        # Vision message
        messages.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_b64}"}},
                {"type": "text", "text": prompt},
            ]
        })
    else:
        messages.append({"role": "user", "content": prompt})

    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    raw = _post_json(url, body, {"Authorization": f"Bearer {key}"})
    return _extract_openai_text(raw)


def _call_anthropic(
    key: str, model: str,
    prompt: str, system: str = "",
    temperature: float = 0.7, max_tokens: int = 4096,
    image_b64: str = "", image_mime: str = "image/jpeg",
) -> str:
    """Anthropic Messages API."""
    url = _ENDPOINTS["anthropic"]
    content: list = []
    if image_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": image_mime, "data": image_b64},
        })
    content.append({"type": "text", "text": prompt})

    body: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        body["system"] = system
    if temperature != 1.0:
        body["temperature"] = temperature

    raw = _post_json(url, body, {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    })
    content_out = raw.get("content", [])
    if content_out:
        return content_out[0].get("text", "")
    raise RuntimeError(f"Anthropic: empty response — {str(raw)[:200]}")


def _call_cohere(
    key: str, model: str,
    prompt: str, system: str = "",
    temperature: float = 0.7, max_tokens: int = 4096,
) -> str:
    """Cohere Chat API v2."""
    url = _ENDPOINTS["cohere"]
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    raw = _post_json(url, body, {"Authorization": f"Bearer {key}"})
    # Cohere v2 response
    msg = raw.get("message", {})
    ct = msg.get("content", [])
    if ct:
        return ct[0].get("text", "")
    # Fallback for older format
    return raw.get("text", str(raw)[:200])


def _call_huggingface(
    key: str, model: str,
    prompt: str, system: str = "",
    max_tokens: int = 2048,
) -> str:
    """HuggingFace Inference API."""
    url = f"https://api-inference.huggingface.co/models/{model}"
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    body = {
        "inputs": full_prompt,
        "parameters": {"max_new_tokens": min(max_tokens, 2048), "return_full_text": False},
    }
    raw = _post_json(url, body, {"Authorization": f"Bearer {key}"}, timeout=60)
    if isinstance(raw, list) and raw:
        return raw[0].get("generated_text", "")
    if isinstance(raw, dict):
        return raw.get("generated_text", str(raw)[:200])
    return str(raw)[:500]


def _call_replicate(
    key: str, model: str,
    prompt: str, system: str = "",
    max_tokens: int = 2048,
) -> str:
    """Replicate predictions API (polling)."""
    url = f"https://api.replicate.com/v1/models/{model}/predictions"
    input_dict: dict = {"prompt": prompt, "max_new_tokens": max_tokens}
    if system:
        input_dict["system_prompt"] = system

    # Create prediction
    raw = _post_json(url, {"input": input_dict}, {"Authorization": f"Token {key}"})
    prediction_id = raw.get("id")
    if not prediction_id:
        raise RuntimeError(f"Replicate: no prediction ID — {str(raw)[:200]}")

    # Poll for result
    poll_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
    for _ in range(30):
        time.sleep(2)
        req = urllib.request.Request(
            poll_url,
            headers={"Authorization": f"Token {key}", "User-Agent": _COMMON_UA},
        )
        with urllib.request.urlopen(req, timeout=30, context=_ssl()) as resp:
            status_data = json.loads(resp.read())
        status = status_data.get("status")
        if status == "succeeded":
            output = status_data.get("output", "")
            if isinstance(output, list):
                return "".join(output)
            return str(output)
        elif status in ("failed", "canceled"):
            raise RuntimeError(f"Replicate prediction {status}: {status_data.get('error', '')}")
    raise RuntimeError("Replicate: prediction timed out after 60s")


# ── Prompt helpers ────────────────────────────────────────────────────────────

def _build_prompt(messages: list, context_text: str, prompt: str) -> str:
    turns: List[str] = []
    if context_text:
        turns.append(f"Context:\n{context_text}")
    for m in messages:
        role    = m.get("role", "user")
        content = m.get("content", "")
        turns.append(f"{role.capitalize()}: {content}")
    return "\n".join(turns)


def _apply_engine_config(
    engine_name: str, system: str, temperature: float, max_tokens: int, kwargs: dict
) -> tuple:
    cfg = get_engine_config(engine_name)
    out_system = (system + "\n\n" if system else "") + cfg["system"]
    out_temp   = kwargs.get("temperature", cfg["temperature"])
    out_tokens = kwargs.get("max_tokens",  cfg["max_tokens"])
    return out_system, out_temp, out_tokens


# ── Provider routing ───────────────────────────────────────────────────────────

def _get_provider_and_key():
    """Return (key, provider) from user_key_store, or raise."""
    try:
        from utils.user_key_store import get_user_key
        key, provider = get_user_key()
        if key and provider:
            return key, provider
    except Exception:
        pass
    raise RuntimeError(
        "No API key set. Please enter your API key in the **sidebar** to continue.\n\n"
        "Supported: Gemini, Groq, Cerebras, OpenAI, Anthropic, Mistral, Cohere, "
        "Together AI, Perplexity, OpenRouter, Fireworks, Replicate, HuggingFace, "
        "SambaNova, NVIDIA NIM, DeepSeek, AI21, xAI Grok."
    )


def _route_call(
    key: str,
    provider: str,
    prompt: str,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    model: str = "",
    image_data: str = "",
    image_mime: str = "image/jpeg",
) -> str:
    """Route the call to the correct provider backend."""

    # ── Vision guard: strip image if provider doesn't support it ─────────────
    if image_data and provider not in _VISION_CAPABLE_PROVIDERS:
        raise RuntimeError(
            f"Vision AI is not supported by your current provider ({provider}). "
            f"Please switch to Gemini, OpenAI, Anthropic, or another vision-capable provider in Settings."
        )

    # ── Gemini ───────────────────────────────────────────────────────────────
    if provider == "gemini":
        model_name = model or GEMINI_MODELS[0]
        return OMNI_ENGINE.execute(
            model=model_name, prompt=prompt, system=system,
            temperature=temperature, max_tokens=max_tokens,
            image_b64=image_data, image_mime=image_mime,
        )

    # ── Anthropic (special format) ────────────────────────────────────────────
    if provider == "anthropic":
        return _call_anthropic(
            key=key, model=model or ANTHROPIC_MODEL,
            prompt=prompt, system=system,
            temperature=temperature, max_tokens=max_tokens,
            image_b64=image_data if image_data else "",
            image_mime=image_mime,
        )

    # ── Cohere (special format) ───────────────────────────────────────────────
    if provider == "cohere":
        return _call_cohere(
            key=key, model=model or COHERE_MODEL,
            prompt=prompt, system=system,
            temperature=temperature, max_tokens=max_tokens,
        )

    # ── HuggingFace (special format) ─────────────────────────────────────────
    if provider == "huggingface":
        return _call_huggingface(
            key=key, model=model or HUGGINGFACE_MODEL,
            prompt=prompt, system=system, max_tokens=max_tokens,
        )

    # ── Replicate (polling) ───────────────────────────────────────────────────
    if provider == "replicate":
        return _call_replicate(
            key=key, model=model or REPLICATE_MODEL,
            prompt=prompt, system=system, max_tokens=max_tokens,
        )

    # ── All OpenAI-compatible providers ──────────────────────────────────────
    _model_defaults = {
        "groq":       GROQ_MODEL,
        "cerebras":   CEREBRAS_MODEL,
        "openai":     OPENAI_MODEL,
        "mistral":    MISTRAL_MODEL,
        "together":   TOGETHER_MODEL,
        "perplexity": PERPLEXITY_MODEL,
        "openrouter": OPENROUTER_MODEL,
        "fireworks":  FIREWORKS_MODEL,
        "sambanova":  SAMBANOVA_MODEL,
        "nvidia":     NVIDIA_MODEL,
        "deepseek":   DEEPSEEK_MODEL,
        "ai21":       AI21_MODEL,
        "xai":        XAI_MODEL,
    }

    endpoint = _ENDPOINTS.get(provider)
    if not endpoint:
        raise RuntimeError(f"Unknown provider: {provider}")

    chosen_model = model or _model_defaults.get(provider, "default")

    # OpenRouter needs extra headers
    extra_headers: dict = {}
    if provider == "openrouter":
        extra_headers["HTTP-Referer"] = "https://examhelp.ai"
        extra_headers["X-Title"] = "ExamHelp AI"

    return _call_openai_compat(
        key=key, url=endpoint, model=chosen_model,
        prompt=prompt, system=system,
        temperature=temperature, max_tokens=max_tokens,
        image_b64=image_data if image_data else "",
        image_mime=image_mime,
    )


# ── Core generate() ───────────────────────────────────────────────────────────

def generate(
    prompt: str = "",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    image_data: str = "",
    image_mime: str = "image/jpeg",
    messages: list = None,
    context_text: str = "",
    model: str = "",
    **kwargs,
) -> str:
    """
    Generate a response using whichever provider key the user has entered.
    Automatically routes to the correct backend (18 providers supported).
    """
    if messages:
        prompt = _build_prompt(messages, context_text, prompt)

    engine_name = kwargs.get("engine_name")
    if engine_name:
        system, temperature, max_tokens = _apply_engine_config(
            engine_name, system, temperature, max_tokens, kwargs
        )

    persona_prompt = kwargs.get("persona_prompt", "")
    if persona_prompt:
        system = (system + "\n\n" if system else "") + persona_prompt

    # Cache check (skip for vision)
    if not image_data:
        ck = _cache_key(prompt, system)
        cached = _cache_get(ck)
        if cached:
            return cached

    key, provider = _get_provider_and_key()
    result = _route_call(
        key=key, provider=provider,
        prompt=prompt, system=system,
        temperature=temperature, max_tokens=max_tokens,
        model=model, image_data=image_data, image_mime=image_mime,
    )

    if not result:
        raise RuntimeError("No response received from the AI provider.")

    if not image_data:
        _cache_set(_cache_key(prompt, system), result)

    # Live usage tracking
    try:
        from utils.api_key_ui import track_api_call
        track_api_call(prompt=prompt, response=result)
    except Exception:
        pass

    return result


# ── Streaming generate ────────────────────────────────────────────────────────

def generate_stream(
    prompt: str = "",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    image_data: str = "",
    image_mime: str = "image/jpeg",
    messages: list = None,
    context_text: str = "",
    chunk_words: int = 6,
    **kwargs,
) -> Iterator[str]:
    """Yields word-chunks for smooth Streamlit streaming."""
    if messages:
        prompt = _build_prompt(messages, context_text, prompt)

    engine_name = kwargs.get("engine_name")
    if engine_name:
        system, temperature, max_tokens = _apply_engine_config(
            engine_name, system, temperature, max_tokens, kwargs
        )

    persona_prompt = kwargs.get("persona_prompt", "")
    if persona_prompt:
        system = (system + "\n\n" if system else "") + persona_prompt

    key, provider = _get_provider_and_key()

    # Gemini has native streaming via OmniKeyEngine
    if provider == "gemini":
        yield from OMNI_ENGINE.execute_stream(
            model=GEMINI_MODELS[0],
            prompt=prompt, system=system,
            temperature=temperature, max_tokens=max_tokens,
            image_b64=image_data, image_mime=image_mime,
            chunk_words=chunk_words,
        )
        return

    # All other providers: call full generate() and chunk
    full = generate(
        prompt=prompt, system=system,
        temperature=temperature, max_tokens=max_tokens,
        image_data=image_data, image_mime=image_mime,
        model=kwargs.get("model", ""),
    )
    words = full.split(" ")
    chunk: List[str] = []
    for i, word in enumerate(words):
        chunk.append(word)
        if len(chunk) >= chunk_words or i == len(words) - 1:
            yield " ".join(chunk) + (" " if i < len(words) - 1 else "")
            chunk = []


# ── Convenience wrappers ──────────────────────────────────────────────────────

def quick_generate(prompt: str, system: str = "", **kwargs) -> str:
    return generate(prompt=prompt, system=system, max_tokens=2048, **kwargs)


def vision_generate(prompt: str, image_b64: str, mime: str = "image/jpeg", **kwargs) -> str:
    """Generate response from image + prompt. Works with Gemini and OpenAI/Anthropic."""
    return generate(prompt=prompt, image_data=image_b64, image_mime=mime, **kwargs)


def json_generate(prompt: str, system: str = "", **kwargs) -> str:
    import re as _re
    kwargs.pop("json_mode", None)

    def _extract_and_validate(raw: str) -> Optional[str]:
        fence_match = _re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if fence_match:
            candidate = fence_match.group(1).strip()
        else:
            candidate = None
            for start_char in ("{", "["):
                idx = raw.find(start_char)
                if idx != -1:
                    candidate = raw[idx:].rstrip()
                    break
        if candidate is None:
            return None
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            return None

    json_system = (
        (system + "\n\n" if system else "") +
        "IMPORTANT: Respond with ONLY valid JSON. No markdown, no preamble, no explanation."
    )
    raw = generate(prompt=prompt, system=json_system, temperature=0.2, **kwargs)
    result = _extract_and_validate(raw)
    if result:
        return result

    strict_system = "Return ONLY a raw JSON object. No text before or after it. No markdown."
    try:
        raw2 = generate(prompt=prompt, system=strict_system, temperature=0.1, **kwargs)
        result2 = _extract_and_validate(raw2)
        if result2:
            return result2
    except Exception:
        pass
    return raw


def generate_with_retry(prompt: str, max_retries: int = 3, **kwargs) -> str:
    delay = 1.0
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return generate(prompt=prompt, **kwargs)
        except RuntimeError as e:
            err_str = str(e)
            if any(kw in err_str for kw in ("rate limit", "wait", "invalid", "revoked", "No API key")):
                raise
            last_err = e
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
    raise last_err or RuntimeError("generate_with_retry: all retries exhausted.")


def batch_generate(prompts: List[str], **kwargs) -> List[str]:
    results: List[str] = [""] * len(prompts)

    def _task(idx: int, p: str) -> None:
        try:
            results[idx] = generate(prompt=p, **kwargs)
        except Exception as e:
            results[idx] = f"[Error: {str(e)[:100]}]"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(_task, i, p) for i, p in enumerate(prompts)]
        concurrent.futures.wait(futures)

    return results


# ── Status & Admin ────────────────────────────────────────────────────────────

def get_pool_status() -> dict:
    return OMNI_ENGINE.get_status_report()


def get_capacity_summary() -> str:
    return OMNI_ENGINE.get_key_status_line()


def get_dashboard_html() -> str:
    return OMNI_ENGINE.get_dashboard_html()


def reset_all_keys() -> None:
    OMNI_ENGINE.reset_all_cooldowns()


def get_token_usage_summary() -> dict:
    total_in  = sum(s.total_tokens_in  for s in OMNI_ENGINE.slots)
    total_out = sum(s.total_tokens_out for s in OMNI_ENGINE.slots)
    cost = (total_in / 1_000_000 * 0.075) + (total_out / 1_000_000 * 0.30)
    return {
        "total_in":           total_in,
        "total_out":          total_out,
        "estimated_cost_usd": round(cost, 6),
    }


# ── Backward-compat stubs ─────────────────────────────────────────────────────

def stream_chat_with_groq(*args, **kwargs) -> Iterator[str]:
    return generate_stream(**kwargs)


def chat_with_groq(*args, **kwargs) -> str:
    return generate(**kwargs)
