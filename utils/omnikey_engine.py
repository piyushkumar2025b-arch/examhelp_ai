"""
omnikey_engine.py — Single-Key Gemini Executor v6.0
=====================================================
v6.0 BREAKING CHANGE: 9-key rotation system RETIRED.
The system now runs through exactly ONE user-supplied Gemini key stored in
st.session_state via user_key_store.py.

All 9-key rotation code is preserved below but commented out so it can be
restored if ever needed.

Public interface is unchanged:
  OMNI_ENGINE.execute(...)
  OMNI_ENGINE.execute_stream(...)
  OMNI_ENGINE.get_status_report()
  OMNI_ENGINE.get_key_status_line()
  OMNI_ENGINE.get_dashboard_html()
  OMNI_ENGINE.reset_all_cooldowns()
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterator, List, Optional, Tuple

# -- Rate Limits (Gemini 2.5-flash Free Tier) --
RPM_HARD_LIMIT     = 10
RPM_SAFE_LIMIT     = 8
COOLDOWN_429_SEC   = 65
COOLDOWN_ERR_SEC   = 10
COOLDOWN_FATAL_SEC = 3600
GEMINI_API_BASE    = "https://generativelanguage.googleapis.com/v1beta/models"


# -- HTTP Executor (unchanged) --
class GeminiHTTPExecutor:
    """Raw HTTPS calls to Gemini REST API - no SDK dependency."""

    def __init__(self):
        self._ssl = self._make_ssl()

    @staticmethod
    def _make_ssl():
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
            return ctx
        except ImportError:
            try:
                return ssl.create_default_context()
            except Exception:
                return None
        except Exception:
            return None

    @staticmethod
    def _parse_retry_after(text: str) -> float:
        m = re.search(r"retry[_ ]?(?:after|in)[:\s]+(\d+\.?\d*)\s*s", text, re.I)
        if m:
            return float(m.group(1))
        m = re.search(r'"retryDelay":\s*"(\d+)s?"', text)
        if m:
            return float(m.group(1))
        return 0.0

    def call(
        self,
        key: str,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        image_b64: str = "",
        image_mime: str = "image/jpeg",
    ) -> Tuple[str, int, int]:
        url   = f"{GEMINI_API_BASE}/{model}:generateContent?key={key}"
        parts: List[Dict] = []
        if image_b64:
            parts.append({"inline_data": {"mime_type": image_mime, "data": image_b64}})
        parts.append({"text": prompt})

        body: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system:
            body["system_instruction"] = {"parts": [{"text": system}]}

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=90, context=self._ssl) as resp:
                raw        = json.loads(resp.read())
                candidates = raw.get("candidates", [])
                if not candidates:
                    block = raw.get("promptFeedback", {}).get("blockReason", "Unknown")
                    raise RuntimeError(f"Content blocked: {block}")
                parts_out = candidates[0].get("content", {}).get("parts", [])
                text      = "".join(p.get("text", "") for p in parts_out)
                usage     = raw.get("usageMetadata", {})
                return text, usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0)

        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode(errors="replace")
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code}: {body_text}")

        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")

        except RuntimeError:
            raise

        except Exception as e:
            raise RuntimeError(f"Unexpected: {e}")


# -- OmniKeyEngine - Single-Key Mode --
class OmniKeyEngine:
    """
    Single-key Gemini executor (v6.0).
    Reads the user key from st.session_state via user_key_store.
    The 9-key rotation machinery is preserved but commented out at the bottom.
    """
    _instance: Optional["OmniKeyEngine"] = None
    _init_lock = threading.Lock()

    def __new__(cls) -> "OmniKeyEngine":
        with cls._init_lock:
            if cls._instance is None:
                obj = super().__new__(cls)
                obj._ready = False
                cls._instance = obj
        return cls._instance

    def __init__(self):
        if self._ready:
            return
        self.executor = GeminiHTTPExecutor()
        self._lock          = threading.Lock()
        self._total_calls   = 0
        self._total_success = 0
        self._total_429     = 0
        self._total_tok_in  = 0
        self._total_tok_out = 0
        self._ready = True

    def _get_key(self) -> str:
        """Fetch the user-supplied Gemini key from session state."""
        try:
            from utils.user_key_store import get_user_key
            key, provider = get_user_key()
            if key and provider == "gemini":
                return key
        except Exception:
            pass
        raise RuntimeError(
            "No Gemini API key set. "
            "Please enter your Gemini API key in the sidebar to continue."
        )

    def execute(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        image_b64: str = "",
        image_mime: str = "image/jpeg",
        **_kwargs,
    ) -> str:
        key = self._get_key()

        with self._lock:
            self._total_calls += 1

        try:
            text, tok_in, tok_out = self.executor.call(
                key=key,
                model=model,
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
                image_b64=image_b64,
                image_mime=image_mime,
            )
            with self._lock:
                self._total_success += 1
                self._total_tok_in  += tok_in
                self._total_tok_out += tok_out
            print(
                f"[OmniKey v6] success (model={model}, in={tok_in}, out={tok_out})",
                file=sys.stderr,
            )
            return text, tok_in + tok_out

        except RuntimeError as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                with self._lock:
                    self._total_429 += 1
                raise RuntimeError(
                    "Your Gemini key has hit its rate limit. "
                    "Please wait ~60 seconds and try again."
                )
            elif any(c in err for c in ("HTTP 400", "HTTP 401", "HTTP 403")):
                raise RuntimeError(
                    "Your Gemini API key is invalid or has been revoked. "
                    "Please enter a valid key in the sidebar."
                )
            raise

    def execute_stream(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        chunk_words: int = 5,
        **kwargs,
    ) -> Iterator[str]:
        full  = self.execute(
            model=model, prompt=prompt, system=system,
            temperature=temperature, max_tokens=max_tokens, **kwargs
        )
        words = full.split(" ")
        chunk: List[str] = []
        for i, word in enumerate(words):
            chunk.append(word)
            if len(chunk) >= chunk_words or i == len(words) - 1:
                yield " ".join(chunk) + (" " if i < len(words) - 1 else "")
                chunk = []

    def get_status_report(self) -> Dict[str, Any]:
        with self._lock:
            sr = round(self._total_success / max(self._total_calls, 1) * 100, 1)
            return {
                "total_keys":  1,
                "available":   1,
                "cooling":     0,
                "invalid":     0,
                "total_calls": self._total_calls,
                "total_429":   self._total_429,
                "health_pct":  100.0,
                "keys": [{
                    "alias":         "User-Key",
                    "status":        "Ready",
                    "available":     True,
                    "rpm_used":      0,
                    "rpm_limit":     RPM_SAFE_LIMIT,
                    "rpm_pct":       0.0,
                    "rpm_remaining": RPM_SAFE_LIMIT,
                    "cooldown_sec":  0,
                    "ready_in_sec":  0,
                    "total_calls":   self._total_calls,
                    "total_success": self._total_success,
                    "total_429":     self._total_429,
                    "total_errors":  0,
                    "success_rate":  sr,
                    "last_used_ago": None,
                }],
            }

    def get_key_status_line(self) -> str:
        with self._lock:
            return (
                f"1 key active | "
                f"{self._total_calls} calls | "
                f"{self._total_429} rate-limits"
            )

    def get_dashboard_html(self) -> str:
        with self._lock:
            sr = round(self._total_success / max(self._total_calls, 1) * 100, 1)
            calls = self._total_calls
            rl    = self._total_429
        return (
            '<div style="background:#0d0d1a;border:1px solid #2a2a4a;'
            'border-radius:8px;padding:10px 14px;margin:6px 0;">'
            '<div style="color:#7c83f5;font-weight:bold;font-size:13px;margin-bottom:6px;">'
            "Single-Key Mode (v6) - User API Key Active"
            "</div>"
            '<div style="font-size:12px;font-family:monospace;color:#aaa;">'
            f"User-Key | {calls} calls | {sr}% success | {rl} rate-limits"
            "</div></div>"
        )

    def reset_all_cooldowns(self) -> None:
        """No-op in single-key mode."""
        print("[OmniKey v6] reset_all_cooldowns called (no-op in single-key mode).", file=sys.stderr)

    @property
    def slots(self):
        """Backward-compat shim for ai_engine.get_token_usage_summary()."""
        return [_FakeSlot(self._total_tok_in, self._total_tok_out)]


class _FakeSlot:
    def __init__(self, tok_in: int, tok_out: int):
        self.total_tokens_in  = tok_in
        self.total_tokens_out = tok_out


# -- Global Singleton --
OMNI_ENGINE = OmniKeyEngine()
