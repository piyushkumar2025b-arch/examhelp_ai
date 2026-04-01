"""
omnikey_engine.py — The God-Tier Gemini Key Orchestrator
=========================================================
Features:
- 9-Key High-Precision Rotation & Failover
- Token-Aware Rate Limiting (Simulated)
- Per-Key Cooldown & Error Tracking
- Instant Recovery: Switch keys mid-request on 429
- Automatic Retry-After-Delay for 429 rate limits
- Secure Loading: Zero exposure, st.secrets + .env fallback
"""

import os
import re
import sys
import time
import threading
import json
import ssl
import urllib.request
import urllib.error
import hashlib
from typing import List, Dict, Optional, Any, Iterator

# --- Configuration ---
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
RPM_LIMIT = 15      # Hard limit for free tier
RPM_SAFE = 14       # Safety buffer
COOLDOWN_SEC = 65    # Duration to wait after a 429
MAX_RETRY_PER_REQ = 9 # Try more keys before giving up (was 3)
GLOBAL_RETRY_ROUNDS = 3  # How many full rounds to attempt with cooldown waits

class KeyDiagnostics:
    """Diagnostic data for a single key."""
    def __init__(self, key: str):
        self.id = f"...{key[-6:]}"
        self.total_calls = 0
        self.success_rate = 1.0
        self.errors = 0
        self.last_used = 0.0
        self.cooldown_until = 0.0
        self.status = "Healthy"
        self.rpm_history: List[float] = []

    def to_dict(self) -> Dict[str, Any]:
        now = time.monotonic()
        remaining_cooldown = max(0.0, self.cooldown_until - now)
        return {
            "id": self.id,
            "status": "Cooling" if remaining_cooldown > 0 else "Ready",
            "cooldown": round(remaining_cooldown, 1),
            "calls": self.total_calls,
            "error_count": self.errors
        }

class OmniKeyEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OmniKeyEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized: return
        self.keys: List[str] = []
        self.stats: Dict[str, KeyDiagnostics] = {}
        self.ssl_ctx = self._make_ssl_context()
        self.load_keys()
        self._initialized = True

    def _make_ssl_context(self) -> Optional[ssl.SSLContext]:
        try:
            return ssl._create_unverified_context()
        except:
            return None

    def load_keys(self):
        """Securely load keys from all available sources."""
        found_keys = []
        
        # Source 1: Streamlit Secrets
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                for i in range(1, 11):
                    k = f"GEMINI_API_KEY_{i}"
                    val = st.secrets.get(k, "").strip()
                    if val and val.startswith("AIzaSy"):
                        found_keys.append(val)
        except:
            pass

        # Source 2: Environment Variables / .env File
        if not found_keys:
            # First check direct environment
            for i in range(1, 11):
                k = f"GEMINI_API_KEY_{i}"
                val = os.environ.get(k, "").strip().strip('"').strip("'")
                if val and val.startswith("AIzaSy"):
                    found_keys.append(val)
            
            # Then check .env file manually (if still empty)
            if not found_keys:
                try:
                    if os.path.exists(".env"):
                        with open(".env", "r") as f:
                            for line in f:
                                if "GEMINI_API_KEY" in line and "=" in line:
                                    # Very simple parser: SPLIT at first '='
                                    k, v = line.split("=", 1)
                                    v_clean = v.strip().strip('"').strip("'")
                                    if v_clean.startswith("AIzaSy"):
                                        found_keys.append(v_clean)
                except Exception as e:
                    print(f"[OmniKey] .env read error: {e}", file=sys.stderr)

        self.keys = list(dict.fromkeys(found_keys)) # Deduplicate
        self.stats = {k: KeyDiagnostics(k) for k in self.keys}
        print(f"[OmniKey] Orchestrating {len(self.keys)} Gemini keys.", file=sys.stderr)

    def get_best_key(self, exclude: set = None) -> Optional[str]:
        """Selection logic: available, not in exclude, and has lowest RPM usage."""
        exclude = exclude or set()
        now = time.monotonic()
        
        candidates = []
        for k in self.keys:
            if k in exclude: continue
            st = self.stats[k]
            
            # Clean RPM history
            st.rpm_history = [t for t in st.rpm_history if now - t < 60]
            
            if now >= st.cooldown_until and len(st.rpm_history) < RPM_SAFE:
                candidates.append(k)

        if not candidates:
            return None

        # Pick the 'freshest' key (lowest RPM usage)
        return min(candidates, key=lambda k: len(self.stats[k].rpm_history))

    def _get_shortest_cooldown(self) -> float:
        """Return the shortest remaining cooldown time across all keys."""
        now = time.monotonic()
        remaining = [self.stats[k].cooldown_until - now for k in self.keys 
                     if self.stats[k].cooldown_until > now]
        if not remaining:
            return 0
        return max(min(remaining), 0)

    @staticmethod
    def _parse_retry_delay(error_msg: str) -> float:
        """Extract retry delay from 429 error message (e.g. 'Please retry in 19.30870923s')."""
        match = re.search(r'retry in (\d+\.?\d*)\s*s', error_msg, re.IGNORECASE)
        if match:
            return float(match.group(1))
        # Also check retryDelay JSON field
        match = re.search(r'"retryDelay":\s*"(\d+)s?"', error_msg)
        if match:
            return float(match.group(1))
        return 0

    def mark_error(self, key: str, error_type: str):
        """Categorize error and adjust cooldown."""
        st = self.stats.get(key)
        if not st: return
        st.errors += 1
        
        if "429" in error_type or "quota" in error_type.lower():
            # Try to parse the actual retry delay from the error
            parsed_delay = self._parse_retry_delay(error_type)
            cooldown = max(parsed_delay + 2, COOLDOWN_SEC)  # Add 2s safety buffer
            st.cooldown_until = time.monotonic() + cooldown
            st.status = "Rate Limited"
        elif "400" in error_type or "401" in error_type:
            st.cooldown_until = time.monotonic() + 3600 # Bad key? 1 hour cooldown
            st.status = "Invalid Key"
        else:
            st.cooldown_until = time.monotonic() + 10 # Transient error

    def _acquire_key(self, tried_keys: set, attempt: int) -> Optional[str]:
        """Try to get a ready key, waiting out cooldowns if needed."""
        key = self.get_best_key(exclude=tried_keys)
        if key:
            return key

        wait_time = self._get_shortest_cooldown()
        if 0 < wait_time <= 120:
            print(f"[OmniKey] All keys cooling. Waiting {wait_time:.0f}s...", file=sys.stderr)
            time.sleep(wait_time + 1)
            tried_keys.clear()
            return self.get_best_key()

        if attempt < MAX_RETRY_PER_REQ - 1:
            time.sleep(2)
            tried_keys.clear()
        return None

    def _handle_429_wait(self, err_str: str) -> None:
        """If the error is a short-delay 429, sleep before next attempt."""
        if "429" not in err_str:
            return
        retry_delay = self._parse_retry_delay(err_str)
        if 0 < retry_delay <= 30:
            print(f"[OmniKey] 429 hit, waiting {retry_delay:.0f}s before next attempt...", file=sys.stderr)
            time.sleep(retry_delay + 1)

    def _between_round_wait(self, round_num: int, tried_keys: set) -> None:
        """Wait between retry rounds to let quotas partially recover."""
        if round_num >= GLOBAL_RETRY_ROUNDS - 1:
            return
        wait_time = self._get_shortest_cooldown()
        actual_wait = min(wait_time + 1, 65) if wait_time > 0 else 5
        print(f"[OmniKey] Round {round_num + 1} exhausted. Waiting {actual_wait:.0f}s before retry...", file=sys.stderr)
        time.sleep(actual_wait)
        tried_keys.clear()

    def execute(self, model: str, prompt: str, system: str = "", **kwargs) -> str:
        """The core execution loop with transparent failover and retry-after-delay."""
        tried_keys: set = set()
        last_exception: Optional[Exception] = None

        for round_num in range(GLOBAL_RETRY_ROUNDS):
            for attempt in range(MAX_RETRY_PER_REQ):
                key = self._acquire_key(tried_keys, attempt)
                if not key:
                    continue

                st = self.stats[key]
                st.total_calls += 1
                st.rpm_history.append(time.monotonic())

                try:
                    return self._raw_request(key, model, prompt, system, **kwargs)
                except Exception as e:
                    err_str = str(e)
                    self.mark_error(key, err_str)
                    tried_keys.add(key)
                    last_exception = e
                    self._handle_429_wait(err_str)

            self._between_round_wait(round_num, tried_keys)

        raise last_exception or RuntimeError("Exhausted all available Gemini keys or all are in cooldown.")

    def _raw_request(self, key: str, model: str, prompt: str, system: str, **kwargs) -> str:
        url = f"{GEMINI_API_BASE}/{model}:generateContent?key={key}"
        
        parts = []
        if kwargs.get("image_b64"):
            parts.append({
                "inline_data": {
                    "mime_type": kwargs.get("image_mime", "image/jpeg"),
                    "data": kwargs.get("image_b64")
                }
            })
        parts.append({"text": prompt})

        body = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 4096),
            }
        }
        if system:
            body["system_instruction"] = {"parts": [{"text": system}]}

        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=60, context=self.ssl_ctx) as resp:
                res_data = json.loads(resp.read())
                
                candidates = res_data.get("candidates", [])
                if not candidates:
                    block = res_data.get("promptFeedback", {}).get("blockReason", "Unknown")
                    raise ValueError(f"Content blocked: {block}")
                
                parts_out = candidates[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts_out)

        except urllib.error.HTTPError as e:
            msg = ""
            try: msg = e.read().decode()
            except: pass
            raise RuntimeError(f"HTTP {e.code}: {msg}")
        except Exception as e:
            print(f"[OmniKey] Raw request failed: {str(e)}", file=sys.stderr)
            raise RuntimeError(f"Request failed: {str(e)}")

    def get_status_report(self) -> Dict[str, Any]:
        return {
            "total_keys": len(self.keys),
            "available": sum(1 for k in self.keys if time.monotonic() >= self.stats[k].cooldown_until),
            "active_diagnostics": [st.to_dict() for st in self.stats.values()]
        }

# Global Singleton Instance
OMNI_ENGINE = OmniKeyEngine()
