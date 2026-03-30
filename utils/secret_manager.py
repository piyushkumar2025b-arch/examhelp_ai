"""
secret_manager.py — CENTRALIZED API Key Vault v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE SINGLE SOURCE OF TRUTH for every API key in ExamHelp AI.

SECURITY RULES:
  1. NO key is EVER hardcoded anywhere in source code
  2. ALL keys are loaded from .env / st.secrets / environment variables ONLY
  3. Keys are NEVER displayed in UI, logs, or error messages
  4. This file itself contains ZERO actual key values
  5. Status displays show only last 4 chars masked: …xxxx

KEY HIERARCHY:
  .env file (local)
    → st.secrets (Streamlit Cloud)
      → os.environ (fallback)

USAGE:
  from utils.secret_manager import get_groq_key, get_gemini_key, get_service_key
  key = get_groq_key()          # Auto-rotated Groq key
  key = get_gemini_key()        # Auto-rotated Gemini key
  key = get_service_key("GNEWS_API_KEY")  # Any other service key
"""

from __future__ import annotations
import os
import threading
from typing import Optional, Dict, List

# ══════════════════════════════════════════════════════════════
# PHASE 1: Load .env BEFORE anything else
# ══════════════════════════════════════════════════════════════

def _force_load_env():
    """Bulletproof .env loader — works even without python-dotenv."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return
    except ImportError:
        pass
    # Manual fallback
    import pathlib
    for env_path in [
        pathlib.Path(__file__).resolve().parent.parent / ".env",
        pathlib.Path.cwd() / ".env",
    ]:
        if env_path.is_file():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if key and value and key not in os.environ:
                        os.environ[key] = value
            except Exception:
                pass
            break

_force_load_env()

# Streamlit availability
try:
    import streamlit as st
    _HAS_ST = True
except ImportError:
    _HAS_ST = False

_lock = threading.RLock()


# ══════════════════════════════════════════════════════════════
# PHASE 2: Core key loading — env + secrets, NEVER hardcoded
# ══════════════════════════════════════════════════════════════

def _get_secret(name: str) -> str:
    """Get a secret from st.secrets first, then os.environ. NEVER a hardcode."""
    val = ""
    if _HAS_ST:
        try:
            val = st.secrets.get(name, "") or ""
        except Exception:
            pass
    if not val:
        val = os.getenv(name, "") or ""
    return val.strip()


def _load_numbered_keys(prefix: str, max_count: int = 20) -> List[str]:
    """Load keys like PREFIX_1, PREFIX_2, ..., PREFIX_N."""
    keys: List[str] = []
    for i in range(1, max_count + 1):
        val = _get_secret(f"{prefix}_{i}")
        if val and val not in keys:
            keys.append(val)
    # Fallback: try PREFIX without number
    if not keys:
        val = _get_secret(prefix)
        if val:
            keys.append(val)
    return keys


# ══════════════════════════════════════════════════════════════
# PHASE 3: Key pools — loaded once at module init
# ══════════════════════════════════════════════════════════════

# Groq keys (main LLM backbone)
GROQ_KEYS: List[str] = _load_numbered_keys("GROQ_API_KEY", 20)

# Gemini keys (vision, debugger, fallback LLM)
GEMINI_KEYS: List[str] = _load_numbered_keys("GEMINI_API_KEY", 10)

# Dedicated debugger Gemini keys (separate pool)
GEMINI_DEBUG_KEYS: List[str] = _load_numbered_keys("GEMINI_DEBUG_KEY", 5)

# Service-specific keys (loaded on demand)
_SERVICE_CACHE: Dict[str, str] = {}


# ══════════════════════════════════════════════════════════════
# PHASE 4: Public API — retrieve keys safely
# ══════════════════════════════════════════════════════════════

def get_groq_key(override: Optional[str] = None) -> Optional[str]:
    """Get the best available Groq key via key_manager rotation."""
    if override and override.strip():
        return override.strip()
    from utils import key_manager
    return key_manager.get_key()


def get_gemini_key(override: Optional[str] = None) -> Optional[str]:
    """Get the best available Gemini key via gemini_key_manager rotation."""
    if override and override.strip():
        return override.strip()
    from utils import gemini_key_manager as gkm
    return gkm.get_key()


def get_gemini_keys_list() -> List[str]:
    """Get all available Gemini keys (for modules that do their own rotation)."""
    return list(GEMINI_KEYS)


def get_gemini_debug_keys() -> List[str]:
    """Get dedicated Gemini debug keys + fallback to main pool."""
    keys = list(GEMINI_DEBUG_KEYS)
    # Add main Gemini keys as fallback
    for k in GEMINI_KEYS:
        if k not in keys:
            keys.append(k)
    return keys


def get_service_key(name: str) -> str:
    """
    Get any service key by env var name.
    Only caches non-empty values so keys added later are found.
    """
    with _lock:
        cached = _SERVICE_CACHE.get(name)
        if cached:  # Only return cache if non-empty
            return cached
        val = _get_secret(name)
        if val:  # Only cache non-empty values
            _SERVICE_CACHE[name] = val
        return val


# ══════════════════════════════════════════════════════════════
# PHASE 5: Status & diagnostics (SAFE — never exposes full keys)
# ══════════════════════════════════════════════════════════════

def mask_key(key: str) -> str:
    """Mask a key for safe display: '…xxxx'"""
    if not key or len(key) < 8:
        return "…(empty)"
    return f"…{key[-4:]}"


def get_key_status() -> Dict:
    """Get a safe status summary of all key pools."""
    return {
        "groq_total": len(GROQ_KEYS),
        "groq_keys": [mask_key(k) for k in GROQ_KEYS],
        "gemini_total": len(GEMINI_KEYS),
        "gemini_keys": [mask_key(k) for k in GEMINI_KEYS],
        "gemini_debug_total": len(GEMINI_DEBUG_KEYS),
        "services": {
            "GNEWS_API_KEY": "✅" if get_service_key("GNEWS_API_KEY") else "❌",
            "GOOGLE_MAPS_EMBED_KEY": "✅" if get_service_key("GOOGLE_MAPS_EMBED_KEY") else "❌",
            "PEXELS_API_KEY": "✅" if get_service_key("PEXELS_API_KEY") else "❌",
            "PIXABAY_API_KEY": "✅" if get_service_key("PIXABAY_API_KEY") else "❌",
            "NEWSDATA_API_KEY": "✅" if get_service_key("NEWSDATA_API_KEY") else "❌",
        },
    }


def validate_all_keys() -> Dict[str, bool]:
    """Validate all required keys exist without exposing values."""
    status = {}

    # Check Groq — flat keys GROQ_API_KEY_1 .. N
    groq_ok = False
    for i in range(1, 21):
        if _get_secret(f"GROQ_API_KEY_{i}"):
            groq_ok = True
            break
    if not groq_ok and _get_secret("GROQ_API_KEY"):
        groq_ok = True
    status["groq"] = groq_ok

    # Check Gemini — flat keys GEMINI_API_KEY_1 .. N
    gemini_ok = False
    for i in range(1, 11):
        if _get_secret(f"GEMINI_API_KEY_{i}"):
            gemini_ok = True
            break
    if not gemini_ok and _get_secret("GEMINI_API_KEY"):
        gemini_ok = True
    status["gemini"] = gemini_ok

    # Other optional services
    status["serpapi"] = bool(_get_secret("SERPAPI_KEY"))
    status["wolfram"] = bool(_get_secret("WOLFRAM_APP_ID"))
    status["unsplash"] = bool(_get_secret("UNSPLASH_ACCESS_KEY"))

    return status


# ══════════════════════════════════════════════════════════════
# PHASE 6: Gemini direct-call helper (best model, key rotation)
# ══════════════════════════════════════════════════════════════

# Best Gemini models (ranked by capability, verified March 2026):
GEMINI_BEST_MODEL   = "gemini-2.0-flash"                 # Fast, 1M context, most reliable
GEMINI_FLASH_MODEL  = "gemini-1.5-flash"                 # Proven stable fallback
GEMINI_LITE_MODEL   = "gemini-1.5-flash-8b"              # Fastest stable fallback

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def call_gemini(
    prompt: str,
    system: str = "",
    model: str = None,
    max_tokens: int = 8192,
    temperature: float = 0.7,
    image_data: Optional[str] = None,
    image_mime: str = "image/jpeg",
) -> Optional[str]:
    """
    Call Gemini API directly with automatic key rotation.
    Uses the best available model by default.
    
    Args:
        prompt: User prompt text
        system: System instruction
        model: Model override (defaults to GEMINI_BEST_MODEL)
        max_tokens: Max output tokens
        temperature: Generation temperature
        image_data: Base64-encoded image data (for vision)
        image_mime: MIME type of image
    
    Returns:
        Generated text, or None on failure
    """
    import requests as req

    chosen_model = model or GEMINI_BEST_MODEL
    keys = get_gemini_keys_list()
    
    if not keys:
        return None

    for key in keys:
        try:
            url = f"{_GEMINI_BASE_URL}/{chosen_model}:generateContent?key={key}"
            
            # Build content parts
            parts = [{"text": prompt}]
            if image_data:
                parts.append({"inline_data": {"mime_type": image_mime, "data": image_data}})
            
            payload = {
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            }
            
            # Add system instruction if provided
            if system:
                payload["system_instruction"] = {"parts": [{"text": system}]}
            
            resp = req.post(url, json=payload, timeout=60)
            
            if resp.status_code == 429:
                continue  # Rate limited, try next key
            if resp.status_code == 400:
                # Model not available, try fallback
                if chosen_model != GEMINI_FLASH_MODEL:
                    url = f"{_GEMINI_BASE_URL}/{GEMINI_FLASH_MODEL}:generateContent?key={key}"
                    resp = req.post(url, json=payload, timeout=60)
                    if resp.status_code != 200:
                        continue
                else:
                    continue
            
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                continue
            
            parts_out = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts_out).strip()
            
            if text:
                # Mark key as used in gemini_key_manager if available
                try:
                    from utils import gemini_key_manager as gkm
                    gkm.mark_used(key)
                except Exception:
                    pass
                return text
                
        except Exception:
            continue
    
    return None
