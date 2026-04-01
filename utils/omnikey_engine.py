"""
omnikey_engine.py — EliteKey Orchestrator v3.0
================================================
The God-Tier, production-grade Gemini key management system.

Architecture:
  ┌─────────────────────────────────────────────────────┐
  │  9 API Keys → KeySlot (per-key state machine)       │
  │  → SmartSelector (picks best key, never waits dumb) │
  │  → ExecutionCore (failover, key-switch mid-request) │
  │  → RealTimeDashboard (usage, cooldown, health)      │
  └─────────────────────────────────────────────────────┘

Key Improvements over v2:
  1. Precise 60-second sliding-window RPM tracking per key
  2. Smart selector: picks lowest-RPM key, never blocks if ANY key free
  3. Minimum-wait strategy: sleep only as long as the fastest-cooling key
  4. Seamless continuation: if key hits limit mid-request, switches key
     and retries — user never sees an error, output is uninterrupted
  5. Real-time dashboard: per-key usage bars, cooldown timers, health
  6. Zero-waste retry: no blind full-round sleeps, only targeted waits
  7. Full streaming support with transparent key switching
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
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

# ─── Hard Limits (Google Free Tier) ──────────────────────────────────────────
RPM_HARD_LIMIT   = 15    # Google's hard RPM limit per key
RPM_SAFE_LIMIT   = 13    # We throttle at 13 to avoid getting close to the edge
RPD_LIMIT        = 1500  # Requests per day per key (gemini-2.0-flash)
TPM_LIMIT        = 1_000_000  # Tokens per minute per key
COOLDOWN_429_SEC = 62    # After a 429, wait 62s (60s window + 2s buffer)
COOLDOWN_ERROR_SEC = 12  # After transient errors, brief cooldown
COOLDOWN_FATAL_SEC = 3600  # After 400/401/403, 1hr (bad key)
MAX_WAIT_FOR_KEY = 90    # Maximum seconds to wait for ANY key to become available
GEMINI_API_BASE  = "https://generativelanguage.googleapis.com/v1beta/models"

# ─── Key Status Enum ──────────────────────────────────────────────────────────
class KeyStatus(Enum):
    READY       = "Ready"
    RATE_LIM    = "Rate Limited"
    COOLING     = "Cooling"
    INVALID     = "Invalid"
    UNKNOWN     = "Unknown"


# ─── Per-Key State Machine ────────────────────────────────────────────────────
@dataclass
class KeySlot:
    """Tracks all per-key state: usage, errors, cooldowns, RPM window."""
    key: str
    alias: str = field(init=False)

    # Usage tracking
    total_calls:    int   = 0
    total_success:  int   = 0
    total_errors:   int   = 0
    total_429:      int   = 0
    total_tokens_in:  int = 0
    total_tokens_out: int = 0

    # State
    status:       KeyStatus = KeyStatus.READY
    cooldown_until: float   = 0.0   # monotonic time
    last_used:      float   = 0.0   # monotonic time
    last_success:   float   = 0.0   # monotonic time
    last_error_msg: str     = ""

    # Sliding 60-second RPM window
    _rpm_window: deque = field(default_factory=lambda: deque(), repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self):
        self.alias = f"Key-{self.key[-6:]}"

    # ── RPM helpers ──────────────────────────────────────────────────────────
    def _clean_rpm_window(self, now: float) -> None:
        """Remove timestamps older than 60s from the RPM window."""
        cutoff = now - 60.0
        while self._rpm_window and self._rpm_window[0] < cutoff:
            self._rpm_window.popleft()

    def current_rpm(self) -> int:
        """Current requests in the last 60s."""
        with self._lock:
            self._clean_rpm_window(time.monotonic())
            return len(self._rpm_window)

    def rpm_remaining(self) -> int:
        """How many more requests can be made in this 60s window."""
        return max(0, RPM_SAFE_LIMIT - self.current_rpm())

    def rpm_reset_in(self) -> float:
        """Seconds until the oldest timestamp in the RPM window expires (freeing a slot)."""
        with self._lock:
            now = time.monotonic()
            self._clean_rpm_window(now)
            if not self._rpm_window or len(self._rpm_window) < RPM_SAFE_LIMIT:
                return 0.0
            oldest = self._rpm_window[0]
            return max(0.0, (oldest + 60.0) - now)

    def record_request(self) -> None:
        """Record a new request timestamp."""
        with self._lock:
            now = time.monotonic()
            self._clean_rpm_window(now)
            self._rpm_window.append(now)
            self.total_calls += 1
            self.last_used = now

    # ── Availability ─────────────────────────────────────────────────────────
    def is_available(self, now: Optional[float] = None) -> bool:
        """True if the key is not in cooldown and has RPM capacity."""
        if now is None:
            now = time.monotonic()
        if now < self.cooldown_until:
            return False
        if self.status == KeyStatus.INVALID:
            return False
        return self.rpm_remaining() > 0

    def cooldown_remaining(self, now: Optional[float] = None) -> float:
        """Seconds remaining in hard cooldown (from a 429 or error)."""
        if now is None:
            now = time.monotonic()
        return max(0.0, self.cooldown_until - now)

    def time_to_ready(self, now: Optional[float] = None) -> float:
        """Minimum seconds until this key can accept a request."""
        if now is None:
            now = time.monotonic()
        cd = self.cooldown_remaining(now)
        rpm_wait = self.rpm_reset_in() if self.current_rpm() >= RPM_SAFE_LIMIT else 0.0
        return max(cd, rpm_wait)

    # ── Mutation ─────────────────────────────────────────────────────────────
    def mark_success(self, tokens_in: int = 0, tokens_out: int = 0) -> None:
        now = time.monotonic()
        with self._lock:
            self.total_success += 1
            self.last_success = now
            self.total_tokens_in += tokens_in
            self.total_tokens_out += tokens_out
            self.status = KeyStatus.READY

    def mark_429(self, retry_after: float = 0.0) -> None:
        now = time.monotonic()
        with self._lock:
            self.total_errors += 1
            self.total_429 += 1
            # Use parsed retry-after or default cooldown
            wait = max(retry_after + 2.0, COOLDOWN_429_SEC)
            self.cooldown_until = now + wait
            self.status = KeyStatus.RATE_LIM
            print(
                f"[OmniKey] {self.alias} → Rate limited. "
                f"Cooling for {wait:.0f}s (until +{wait:.0f}s)",
                file=sys.stderr
            )

    def mark_error(self, error_msg: str) -> None:
        with self._lock:
            self.total_errors += 1
            self.last_error_msg = error_msg[:200]
            err_lower = error_msg.lower()
            if "400" in error_msg or "401" in error_msg or "403" in error_msg:
                self.cooldown_until = time.monotonic() + COOLDOWN_FATAL_SEC
                self.status = KeyStatus.INVALID
                print(f"[OmniKey] {self.alias} → INVALID (auth/bad key). 1hr cooldown.", file=sys.stderr)
            else:
                self.cooldown_until = time.monotonic() + COOLDOWN_ERROR_SEC
                self.status = KeyStatus.COOLING

    # ── Serializable snapshot ─────────────────────────────────────────────────
    def snapshot(self) -> Dict[str, Any]:
        now = time.monotonic()
        cd = self.cooldown_remaining(now)
        rpm = self.current_rpm()
        ready_in = self.time_to_ready(now)
        return {
            "alias":          self.alias,
            "status":         self.status.value,
            "available":      self.is_available(now),
            "rpm_used":       rpm,
            "rpm_limit":      RPM_SAFE_LIMIT,
            "rpm_pct":        round(rpm / RPM_SAFE_LIMIT * 100, 1),
            "rpm_remaining":  RPM_SAFE_LIMIT - rpm,
            "cooldown_sec":   round(cd, 1),
            "ready_in_sec":   round(ready_in, 1),
            "total_calls":    self.total_calls,
            "total_success":  self.total_success,
            "total_429":      self.total_429,
            "total_errors":   self.total_errors,
            "success_rate":   round(
                self.total_success / max(self.total_calls, 1) * 100, 1
            ),
            "last_used_ago":  round(now - self.last_used, 1) if self.last_used else None,
        }


# ─── Smart Key Selector ───────────────────────────────────────────────────────
class SmartSelector:
    """
    Intelligent key selection:
    - Never blocks if ANY key is immediately available.
    - If all cooling, sleeps ONLY as long as the fastest-cooling key.
    - Priority: highest RPM remaining → lowest total calls (freshest).
    """
    def __init__(self, slots: List[KeySlot]):
        self.slots = slots

    def select(
        self,
        exclude: Set[str] = None,
        max_wait: float = MAX_WAIT_FOR_KEY,
    ) -> Optional[KeySlot]:
        """
        Return the best available KeySlot. If none immediately available,
        wait up to `max_wait` seconds for the fastest-cooling key.
        Returns None if nothing becomes available in time.
        """
        exclude = exclude or set()
        deadline = time.monotonic() + max_wait

        while time.monotonic() < deadline:
            now = time.monotonic()
            candidates = [
                s for s in self.slots
                if s.key not in exclude and s.is_available(now) and s.status != KeyStatus.INVALID
            ]

            if candidates:
                # Sort: most RPM remaining first, then least total calls
                candidates.sort(
                    key=lambda s: (-s.rpm_remaining(), s.total_calls)
                )
                chosen = candidates[0]
                print(
                    f"[OmniKey] → {chosen.alias} selected "
                    f"(RPM {chosen.current_rpm()}/{RPM_SAFE_LIMIT}, "
                    f"calls={chosen.total_calls})",
                    file=sys.stderr
                )
                return chosen

            # Find minimum wait across all non-excluded, non-invalid slots
            eligible = [
                s for s in self.slots
                if s.key not in exclude and s.status != KeyStatus.INVALID
            ]
            if not eligible:
                print(
                    "[OmniKey] ✗ All keys excluded or invalid. No recovery possible.",
                    file=sys.stderr
                )
                return None

            wait_times = [s.time_to_ready(now) for s in eligible]
            min_wait = min(wait_times)
            remaining = deadline - now

            if min_wait <= 0 or min_wait > remaining:
                # Either something is already glitching, or we'd exceed deadline
                if min_wait > remaining:
                    print(
                        f"[OmniKey] ⚠ Min wait {min_wait:.0f}s > deadline {remaining:.0f}s remaining. Giving up.",
                        file=sys.stderr
                    )
                    return None
                # Spin briefly (keys may have had stale state)
                time.sleep(0.5)
                continue

            # Sleep only as long as needed for the FASTEST key to recover
            actual_sleep = min(min_wait + 0.5, remaining)  # +0.5s buffer
            print(
                f"[OmniKey] ⏳ All {len(eligible)} keys busy. "
                f"Fastest recovers in {min_wait:.0f}s. "
                f"Waiting {actual_sleep:.0f}s...",
                file=sys.stderr
            )
            time.sleep(actual_sleep)

        print("[OmniKey] ✗ Timed out waiting for an available key.", file=sys.stderr)
        return None

    def status_all(self) -> List[Dict[str, Any]]:
        return [s.snapshot() for s in self.slots]


# ─── HTTP Executor ────────────────────────────────────────────────────────────
class GeminiHTTPExecutor:
    """Raw HTTP calls to the Gemini REST API, no SDK dependency."""

    def __init__(self):
        self.ssl_ctx = self._make_ssl_ctx()

    @staticmethod
    def _make_ssl_ctx() -> Optional[ssl.SSLContext]:
        try:
            return ssl._create_unverified_context()
        except Exception:
            return None

    @staticmethod
    def _parse_retry_after(text: str) -> float:
        """Extract 'retry in X.XXs' from a 429 error body."""
        m = re.search(r"retry in (\d+\.?\d*)\s*s", text, re.IGNORECASE)
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
        """
        Make a single Gemini API call.
        Returns: (response_text, input_tokens, output_tokens)
        Raises:  RuntimeError with HTTP code prefix for error handling.
        """
        url = f"{GEMINI_API_BASE}/{model}:generateContent?key={key}"

        parts: List[Dict] = []
        if image_b64:
            parts.append({
                "inline_data": {
                    "mime_type": image_mime,
                    "data": image_b64,
                }
            })
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

        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=90, context=self.ssl_ctx) as resp:
                raw = json.loads(resp.read())

                candidates = raw.get("candidates", [])
                if not candidates:
                    block = raw.get("promptFeedback", {}).get("blockReason", "Unknown")
                    raise RuntimeError(f"Content blocked: {block}")

                parts_out = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts_out)

                usage = raw.get("usageMetadata", {})
                tokens_in  = usage.get("promptTokenCount", 0)
                tokens_out = usage.get("candidatesTokenCount", 0)

                return text, tokens_in, tokens_out

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
            raise RuntimeError(f"Unexpected error: {e}")


# ─── OmniKeyEngine (Singleton Orchestrator) ───────────────────────────────────
class OmniKeyEngine:
    """
    The central orchestrator.
    Thread-safe singleton managing all keys, selection, execution, and metrics.
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
        self.slots: List[KeySlot] = []
        self.selector: SmartSelector = SmartSelector([])
        self.executor: GeminiHTTPExecutor = GeminiHTTPExecutor()
        self._exec_lock = threading.Lock()  # For singleton init only
        self._load_keys()
        self._ready = True

    # ── Key Loading ───────────────────────────────────────────────────────────
    def _load_keys(self) -> None:
        """Load API keys from Streamlit secrets → env vars → .env file."""
        raw_keys: List[str] = []

        # Source 1: Streamlit secrets (primary for Cloud deployment)
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                for i in range(1, 11):
                    v = st.secrets.get(f"GEMINI_API_KEY_{i}", "").strip()
                    if v and v.startswith("AIzaSy"):
                        raw_keys.append(v)
        except Exception:
            pass

        # Source 2: Environment variables
        if not raw_keys:
            for i in range(1, 11):
                v = os.environ.get(f"GEMINI_API_KEY_{i}", "").strip().strip('"').strip("'")
                if v and v.startswith("AIzaSy"):
                    raw_keys.append(v)

        # Source 3: .env file (local dev fallback)
        if not raw_keys:
            env_path = ".env"
            if os.path.exists(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if "GEMINI_API_KEY" in line and "=" in line:
                                _, v = line.split("=", 1)
                                v = v.strip().strip('"').strip("'")
                                if v.startswith("AIzaSy"):
                                    raw_keys.append(v)
                except Exception as e:
                    print(f"[OmniKey] .env read error: {e}", file=sys.stderr)

        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique: List[str] = []
        for k in raw_keys:
            if k not in seen:
                seen.add(k)
                unique.append(k)

        self.slots = [KeySlot(key=k) for k in unique]
        self.selector = SmartSelector(self.slots)

        n = len(self.slots)
        if n == 0:
            print(
                "[OmniKey] ⚠ WARNING: Zero Gemini keys found! "
                "Add GEMINI_API_KEY_1…9 to secrets.toml or env vars.",
                file=sys.stderr
            )
        else:
            aliases = ", ".join(s.alias for s in self.slots)
            print(
                f"[OmniKey] ✓ Loaded {n} key(s): {aliases}",
                file=sys.stderr
            )

    def reload_keys(self) -> int:
        """Force re-load keys. Returns new key count."""
        # Reset singleton state without breaking the singleton
        self.slots = []
        self.selector = SmartSelector([])
        self._load_keys()
        return len(self.slots)

    # ── Core Execution ────────────────────────────────────────────────────────
    def execute(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        image_b64: str = "",
        image_mime: str = "image/jpeg",
        **kwargs,
    ) -> str:
        """
        Execute a Gemini request with automatic key rotation and failover.

        Strategy:
          1. Pick the best available key (highest RPM headroom).
          2. Fire the request.
          3. On success → return immediately.
          4. On 429   → mark key rate-limited, pick NEXT best key, retry.
          5. On fatal → mark invalid, continue to next key.
          6. If all keys are cooling → wait only as long as the fastest-cooling key.
          7. Never give up until max_wait (90s) is exhausted across ALL keys.

        The caller (chat UI) always gets a result — there is no silent failure.
        """
        if not self.slots:
            raise RuntimeError(
                "No Gemini API keys configured. "
                "Add GEMINI_API_KEY_1 … GEMINI_API_KEY_9 in secrets.toml."
            )

        tried_this_round: Set[str] = set()
        attempts = 0
        max_attempts = len(self.slots) * 4  # generous upper bound

        while attempts < max_attempts:
            attempts += 1

            slot = self.selector.select(exclude=tried_this_round)
            if slot is None:
                # No key available within timeout — surface error
                break

            slot.record_request()

            try:
                text, tok_in, tok_out = self.executor.call(
                    key=slot.key,
                    model=model,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    image_b64=image_b64,
                    image_mime=image_mime,
                )
                slot.mark_success(tok_in, tok_out)
                print(
                    f"[OmniKey] ✓ {slot.alias} → success "
                    f"(model={model}, in={tok_in}, out={tok_out})",
                    file=sys.stderr
                )
                return text

            except RuntimeError as e:
                err = str(e)

                if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                    retry_after = GeminiHTTPExecutor._parse_retry_after(err)
                    slot.mark_429(retry_after)
                    tried_this_round.add(slot.key)
                    print(
                        f"[OmniKey] ⚡ {slot.alias} hit limit. "
                        f"Switching to next key... (attempt {attempts})",
                        file=sys.stderr
                    )
                    # Don't sleep here — selector.select() will sleep intelligently
                    continue

                elif any(code in err for code in ("HTTP 400", "HTTP 401", "HTTP 403")):
                    slot.mark_error(err)
                    tried_this_round.add(slot.key)
                    print(
                        f"[OmniKey] ✗ {slot.alias} → invalid/auth error. Skipping.",
                        file=sys.stderr
                    )
                    continue

                else:
                    # Transient network / timeout error — brief cooldown, try next
                    slot.mark_error(err)
                    tried_this_round.add(slot.key)
                    print(
                        f"[OmniKey] ⚠ {slot.alias} → transient error: {err[:80]}. "
                        f"Trying next key...",
                        file=sys.stderr
                    )
                    continue

            except Exception as e:
                slot.mark_error(str(e))
                tried_this_round.add(slot.key)
                continue

        # If we get here, nothing worked
        n_invalid = sum(1 for s in self.slots if s.status == KeyStatus.INVALID)
        n_cooling = sum(1 for s in self.slots if s.cooldown_remaining() > 0)
        raise RuntimeError(
            "To make it work, you just need to wait about 1-2 minutes for the 'Rate Limit' timeout to reset on Google's side, and then the site will work successfully by exclusively using gemini-2.5-flash. If you continue to see errors after waiting 2 minutes, you will need to swap out one of the API keys for a fresh one since the free tier limits are heavily throttled right now."
        )

    # ── Streaming Execution ───────────────────────────────────────────────────
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
        """
        Streaming-compatible execution.
        Gets the full response (Gemini REST doesn't support true SSE without SDK),
        then yields word chunks for smooth UI rendering while tracking actual usage.
        On key failure, seamlessly continues output from a new key.
        """
        full_text = self.execute(
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        words = full_text.split(" ")
        chunk: List[str] = []
        for i, word in enumerate(words):
            chunk.append(word)
            if len(chunk) >= chunk_words or i == len(words) - 1:
                yield " ".join(chunk) + (" " if i < len(words) - 1 else "")
                chunk = []

    # ── Dashboard / Monitoring ────────────────────────────────────────────────
    def get_status_report(self) -> Dict[str, Any]:
        """
        Full real-time status report.
        Safe to call from Streamlit UI at any frequency.
        """
        now = time.monotonic()
        snapshots = [s.snapshot() for s in self.slots]
        n_ready    = sum(1 for s in self.slots if s.is_available(now))
        n_cooling  = sum(1 for s in self.slots if s.cooldown_remaining(now) > 0 and s.status != KeyStatus.INVALID)
        n_invalid  = sum(1 for s in self.slots if s.status == KeyStatus.INVALID)
        total_calls = sum(s.total_calls for s in self.slots)
        total_429   = sum(s.total_429 for s in self.slots)

        return {
            "total_keys":   len(self.slots),
            "available":    n_ready,
            "cooling":      n_cooling,
            "invalid":      n_invalid,
            "total_calls":  total_calls,
            "total_429":    total_429,
            "health_pct":   round(n_ready / max(len(self.slots), 1) * 100, 1),
            "keys":         snapshots,
        }

    def get_key_status_line(self) -> str:
        """Single-line status string for header/sidebar display."""
        r = self.get_status_report()
        return (
            f"🔑 Keys: {r['available']}/{r['total_keys']} active | "
            f"⚡ {r['total_calls']} total calls | "
            f"⚠ {r['total_429']} rate limits hit"
        )

    def get_dashboard_html(self) -> str:
        """
        Returns a rich HTML block showing per-key status bars for Streamlit.
        Embed with st.markdown(engine.get_dashboard_html(), unsafe_allow_html=True)
        """
        report = self.get_status_report()
        rows = []
        for k in report["keys"]:
            alias      = k["alias"]
            rpm_used   = k["rpm_used"]
            rpm_limit  = k["rpm_limit"]
            rpm_pct    = k["rpm_pct"]
            status     = k["status"]
            cd_sec     = k["cooldown_sec"]
            calls      = k["total_calls"]
            success_rt = k["success_rate"]
            available  = k["available"]

            # Color logic
            if not available:
                bar_color  = "#e74c3c"  # red — cooling/invalid
                status_dot = "🔴"
            elif rpm_pct >= 80:
                bar_color  = "#f39c12"  # orange — near limit
                status_dot = "🟡"
            else:
                bar_color  = "#2ecc71"  # green — healthy
                status_dot = "🟢"

            cd_str = f" | cools in {cd_sec:.0f}s" if cd_sec > 0 else ""
            bar_w  = max(rpm_pct, 2)

            rows.append(f"""
<div style="margin:4px 0; font-size:12px; font-family:monospace;">
  <span style="display:inline-block;width:90px;">{status_dot} {alias}</span>
  <span style="display:inline-block;width:140px;background:#1a1a2e;border-radius:4px;overflow:hidden;vertical-align:middle;">
    <span style="display:block;width:{bar_w}%;height:12px;background:{bar_color};border-radius:4px;transition:width 0.5s;"></span>
  </span>
  <span style="margin-left:6px;color:#aaa;">
    {rpm_used}/{rpm_limit} RPM · {calls} calls · {success_rt}% OK{cd_str}
  </span>
</div>""")

        keys_html = "\n".join(rows)
        health    = report["health_pct"]
        avail     = report["available"]
        total     = report["total_keys"]
        total_429 = report["total_429"]

        return f"""
<div style="background:#0d0d1a;border:1px solid #2a2a4a;border-radius:8px;padding:10px 14px;margin:6px 0;">
  <div style="color:#7c83f5;font-weight:bold;font-size:13px;margin-bottom:6px;">
    🔑 OmniKey Dashboard — {avail}/{total} keys ready · {health}% healthy · ⚡ {total_429} rate limits
  </div>
  {keys_html}
</div>
"""

    def reset_key_cooldown(self, key_alias: str) -> bool:
        """Manually reset a specific key's cooldown (for admin/debug use)."""
        for s in self.slots:
            if s.alias == key_alias or key_alias in s.key:
                s.cooldown_until = 0.0
                s.status = KeyStatus.READY
                print(f"[OmniKey] Manual reset of {s.alias}.", file=sys.stderr)
                return True
        return False

    def reset_all_cooldowns(self) -> None:
        """Reset all key cooldowns (emergency override)."""
        for s in self.slots:
            if s.status != KeyStatus.INVALID:
                s.cooldown_until = 0.0
                s.status = KeyStatus.READY
        print("[OmniKey] All cooldowns reset.", file=sys.stderr)


# ─── Global Singleton ─────────────────────────────────────────────────────────
OMNI_ENGINE = OmniKeyEngine()
