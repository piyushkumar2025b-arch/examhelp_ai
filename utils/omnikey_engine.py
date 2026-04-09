"""
omnikey_engine.py — EliteKey Orchestrator v5.0
================================================
9-key Gemini API key manager.

v5.0 fixes (two critical bugs):
  1. tried_this_round reset after full sweep → selector WAITS instead of crashing
  2. Global selection lock → concurrent threads CANNOT grab the same key simultaneously
     (was causing instant re-rate-limiting under load)
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

# ─── Rate Limits (Gemini 2.5-flash Free Tier) ─────────────────────────────────
RPM_HARD_LIMIT     = 10    # Google's actual free-tier limit
RPM_SAFE_LIMIT     = 8     # Throttle at 8 to stay below the edge
COOLDOWN_429_SEC   = 65    # After 429: 60s window + 5s buffer
COOLDOWN_ERR_SEC   = 10    # Transient errors
COOLDOWN_FATAL_SEC = 3600  # 400/401/403 → 1 hr (bad/expired key)
MAX_WAIT_FOR_KEY   = 125   # Max seconds to wait (just over 2 full windows)
GEMINI_API_BASE    = "https://generativelanguage.googleapis.com/v1beta/models"


# ─── Key Status ───────────────────────────────────────────────────────────────
class KeyStatus(Enum):
    READY    = "Ready"
    RATE_LIM = "Rate Limited"
    COOLING  = "Cooling"
    INVALID  = "Invalid"


# ─── Per-Key State Machine ────────────────────────────────────────────────────
@dataclass
class KeySlot:
    """All per-key state: usage counters, cooldown, 60s sliding RPM window."""
    key:   str
    alias: str = field(init=False)

    total_calls:      int = 0
    total_success:    int = 0
    total_errors:     int = 0
    total_429:        int = 0
    total_tokens_in:  int = 0
    total_tokens_out: int = 0

    status:         KeyStatus = KeyStatus.READY
    cooldown_until: float     = 0.0  # monotonic
    last_used:      float     = 0.0
    last_success:   float     = 0.0
    last_error_msg: str       = ""

    _rpm_window: deque    = field(default_factory=deque, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self):
        self.alias = f"Key-{self.key[-6:]}"

    # ── RPM helpers ──────────────────────────────────────────────────────────
    def _prune(self, now: float) -> None:
        cutoff = now - 60.0
        while self._rpm_window and self._rpm_window[0] < cutoff:
            self._rpm_window.popleft()

    def current_rpm(self) -> int:
        with self._lock:
            self._prune(time.monotonic())
            return len(self._rpm_window)

    def rpm_remaining(self) -> int:
        return max(0, RPM_SAFE_LIMIT - self.current_rpm())

    def rpm_reset_in(self) -> float:
        with self._lock:
            now = time.monotonic()
            self._prune(now)
            if len(self._rpm_window) < RPM_SAFE_LIMIT:
                return 0.0
            return max(0.0, (self._rpm_window[0] + 60.0) - now)

    def record_request(self) -> None:
        with self._lock:
            now = time.monotonic()
            self._prune(now)
            self._rpm_window.append(now)
            self.total_calls += 1
            self.last_used = now

    # ── Availability ─────────────────────────────────────────────────────────
    def cooldown_remaining(self, now: float = None) -> float:
        if now is None:
            now = time.monotonic()
        return max(0.0, self.cooldown_until - now)

    def time_to_ready(self, now: float = None) -> float:
        if now is None:
            now = time.monotonic()
        return max(self.cooldown_remaining(now), self.rpm_reset_in())

    def is_available(self, now: float = None) -> bool:
        if now is None:
            now = time.monotonic()
        if self.status == KeyStatus.INVALID:
            return False
        if now < self.cooldown_until:
            return False
        return self.rpm_remaining() > 0

    # ── State mutations ───────────────────────────────────────────────────────
    def mark_success(self, tokens_in: int = 0, tokens_out: int = 0) -> None:
        with self._lock:
            self.total_success    += 1
            self.last_success      = time.monotonic()
            self.total_tokens_in  += tokens_in
            self.total_tokens_out += tokens_out
            self.status            = KeyStatus.READY

    def mark_429(self, retry_after: float = 0.0) -> None:
        wait = max(retry_after + 5.0, COOLDOWN_429_SEC)
        with self._lock:
            self.total_errors  += 1
            self.total_429     += 1
            self.cooldown_until = time.monotonic() + wait
            self.status         = KeyStatus.RATE_LIM
        print(f"[OmniKey] {self.alias} rate-limited → cooling {wait:.0f}s", file=sys.stderr)

    def mark_error(self, msg: str) -> None:
        with self._lock:
            self.total_errors  += 1
            self.last_error_msg = msg[:200]
            if any(c in msg for c in ("HTTP 400", "HTTP 401", "HTTP 403")):
                self.cooldown_until = time.monotonic() + COOLDOWN_FATAL_SEC
                self.status = KeyStatus.INVALID
                print(f"[OmniKey] {self.alias} INVALID (auth). 1hr cooldown.", file=sys.stderr)
            else:
                self.cooldown_until = time.monotonic() + COOLDOWN_ERR_SEC
                self.status = KeyStatus.COOLING

    # ── Snapshot ──────────────────────────────────────────────────────────────
    def snapshot(self) -> Dict[str, Any]:
        now = time.monotonic()
        rpm = self.current_rpm()
        cd  = self.cooldown_remaining(now)
        return {
            "alias":         self.alias,
            "status":        self.status.value,
            "available":     self.is_available(now),
            "rpm_used":      rpm,
            "rpm_limit":     RPM_SAFE_LIMIT,
            "rpm_pct":       round(rpm / RPM_SAFE_LIMIT * 100, 1),
            "rpm_remaining": RPM_SAFE_LIMIT - rpm,
            "cooldown_sec":  round(cd, 1),
            "ready_in_sec":  round(self.time_to_ready(now), 1),
            "total_calls":   self.total_calls,
            "total_success": self.total_success,
            "total_429":     self.total_429,
            "total_errors":  self.total_errors,
            "success_rate":  round(self.total_success / max(self.total_calls, 1) * 100, 1),
            "last_used_ago": round(now - self.last_used, 1) if self.last_used else None,
        }


# ─── Smart Selector ───────────────────────────────────────────────────────────
class SmartSelector:
    """
    Thread-safe key selector.

    CRITICAL fix v5: _select_lock ensures only ONE thread at a time can
    evaluate + reserve a key. Without this, 12 concurrent threads all see
    the same "best" key as available and all grab it → instant re-429.

    Flow:
      1. Acquire global lock (serializes all concurrent selects)
      2. Find best available key
      3. IMMEDIATELY record_request() to consume an RPM slot
         → next thread will see reduced capacity and pick a different key
      4. Release lock → next thread runs
    """

    def __init__(self, slots: List[KeySlot]):
        self.slots = slots
        self._select_lock = threading.Lock()  # THE CRITICAL FIX

    def select(
        self,
        exclude: Set[str]  = None,
        max_wait: float    = MAX_WAIT_FOR_KEY,
    ) -> Optional[KeySlot]:
        """
        Returns the best available KeySlot with its RPM slot already reserved.
        If none immediately available, sleeps for the fastest-cooling key.
        """
        exclude  = exclude or set()
        deadline = time.monotonic() + max_wait

        while time.monotonic() < deadline:
            with self._select_lock:
                # ── Inside the lock: evaluate + reserve atomically ────────
                now        = time.monotonic()
                valid_pool = [
                    s for s in self.slots
                    if s.key not in exclude and s.status != KeyStatus.INVALID
                ]

                if not valid_pool:
                    print("[OmniKey] ✗ All keys excluded or invalid.", file=sys.stderr)
                    return None

                ready = [s for s in valid_pool if s.is_available(now)]
                if ready:
                    ready.sort(key=lambda s: (-s.rpm_remaining(), s.total_calls))
                    chosen = ready[0]
                    # Reserve the RPM slot NOW while lock is held
                    # so the next thread sees this slot as consumed
                    chosen.record_request()
                    print(
                        f"[OmniKey] → {chosen.alias} selected "
                        f"(RPM {chosen.current_rpm()}/{RPM_SAFE_LIMIT}, "
                        f"calls={chosen.total_calls})",
                        file=sys.stderr,
                    )
                    return chosen

                # All cooling — compute minimum wait outside lock
                wait_times = [s.time_to_ready(now) for s in valid_pool]
                min_wait   = min(wait_times)
                remaining  = deadline - now

            # ── Outside the lock: sleep ───────────────────────────────────
            if min_wait > remaining:
                print(
                    f"[OmniKey] ⚠ Min wait {min_wait:.0f}s > {remaining:.0f}s left. Giving up.",
                    file=sys.stderr,
                )
                return None

            sleep_for = min(min_wait + 1.0, remaining)
            print(
                f"[OmniKey] ⏳ All {len(valid_pool)} keys cooling. "
                f"Fastest ready in {min_wait:.0f}s → sleeping {sleep_for:.0f}s...",
                file=sys.stderr,
            )
            time.sleep(sleep_for)

        print("[OmniKey] ✗ Timed out waiting for a key.", file=sys.stderr)
        return None

    def status_all(self) -> List[Dict[str, Any]]:
        return [s.snapshot() for s in self.slots]


# ─── HTTP Executor ────────────────────────────────────────────────────────────
class GeminiHTTPExecutor:
    """Raw HTTPS calls to Gemini REST API — no SDK dependency."""

    def __init__(self):
        self._ssl = self._make_ssl()

    @staticmethod
    def _make_ssl():
        """Create SSL context using certifi bundle (FIX-5: secure, not global override)."""
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
            return ctx
        except ImportError:
            # certifi not installed — fall back to default (still verifies system CAs)
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
        """
        Single Gemini REST call.
        Returns (text, input_tokens, output_tokens).
        Raises RuntimeError with HTTP code prefix on failure.
        """
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


# ─── OmniKeyEngine (Singleton) ────────────────────────────────────────────────
class OmniKeyEngine:
    """
    Central orchestrator — thread-safe singleton.

    execute() strategy (v5):
      1. selector.select() atomically picks + reserves a key (lock-protected)
      2. On 429  → mark key, add to tried_this_round, try next
      3. After a full sweep (all non-fatal keys tried once) → RESET tried_this_round
         so on the next loop the selector will WAIT for the fastest cooldown
      4. fatal errors (400/401/403) → permanently excluded via fatal_excluded
      5. Never crash while valid keys exist — just wait
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
        self.slots:    List[KeySlot]      = []
        self.selector: SmartSelector      = SmartSelector([])
        self.executor: GeminiHTTPExecutor = GeminiHTTPExecutor()
        self._load_keys()
        self._ready = True

    # ── Key loading ───────────────────────────────────────────────────────────
    def _load_keys(self) -> None:
        raw: List[str] = []

        # 1. Streamlit secrets (primary for Cloud)
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                for i in range(1, 11):
                    v = st.secrets.get(f"GEMINI_API_KEY_{i}", "").strip()
                    if v and v.startswith("AIzaSy"):
                        raw.append(v)
        except Exception:
            pass

        # 2. Environment variables
        if not raw:
            for i in range(1, 11):
                v = os.environ.get(f"GEMINI_API_KEY_{i}", "").strip().strip('"\'')
                if v and v.startswith("AIzaSy"):
                    raw.append(v)

        # 3. .env file (local dev)
        if not raw:
            if os.path.exists(".env"):
                try:
                    with open(".env", "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if "GEMINI_API_KEY" in line and "=" in line:
                                _, v = line.split("=", 1)
                                v = v.strip().strip('"\'')
                                if v.startswith("AIzaSy"):
                                    raw.append(v)
                except Exception as exc:
                    print(f"[OmniKey] .env read error: {exc}", file=sys.stderr)

        # Deduplicate
        seen: Set[str] = set()
        unique: List[str] = []
        for k in raw:
            if k not in seen:
                seen.add(k)
                unique.append(k)

        self.slots    = [KeySlot(key=k) for k in unique]
        self.selector = SmartSelector(self.slots)

        n = len(self.slots)
        if n == 0:
            print(
                "[OmniKey] ⚠ No keys found! "
                "Set GEMINI_API_KEY_1…9 in .streamlit/secrets.toml",
                file=sys.stderr,
            )
        else:
            aliases = ", ".join(s.alias for s in self.slots)
            print(f"[OmniKey] ✓ Loaded {n} key(s): {aliases}", file=sys.stderr)

    def reload_keys(self) -> int:
        self.slots    = []
        self.selector = SmartSelector([])
        self._load_keys()
        return len(self.slots)

    # ── Core execute ──────────────────────────────────────────────────────────
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
        if not self.slots:
            raise RuntimeError(
                "No Gemini API keys configured. "
                "Add GEMINI_API_KEY_1…9 in .streamlit/secrets.toml."
            )

        tried_this_round: Set[str] = set()   # 429/transient errors this sweep
        fatal_excluded:   Set[str] = set()   # permanently bad keys

        max_attempts = len(self.slots) * 6
        attempts     = 0

        while attempts < max_attempts:
            attempts += 1

            # After a full sweep, reset exclusions so selector waits for cooldown
            valid_keys = {s.key for s in self.slots if s.status != KeyStatus.INVALID}
            if tried_this_round >= valid_keys and valid_keys:
                print(
                    "[OmniKey] Full sweep done — resetting exclusions, "
                    "waiting for fastest key...",
                    file=sys.stderr,
                )
                tried_this_round = set()

            # selector.select() atomically picks AND records the request
            slot = self.selector.select(
                exclude=tried_this_round | fatal_excluded,
            )

            if slot is None:
                break  # All keys dead or truly timed out

            # NOTE: record_request() was already called inside select() atomically
            # Do NOT call it again here

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
                    file=sys.stderr,
                )
                return text

            except RuntimeError as e:
                err = str(e)

                if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                    ra = GeminiHTTPExecutor._parse_retry_after(err)
                    slot.mark_429(ra)
                    tried_this_round.add(slot.key)
                    print(
                        f"[OmniKey] ⚡ {slot.alias} hit limit → "
                        f"exclusions (attempt {attempts})",
                        file=sys.stderr,
                    )
                    continue

                elif any(c in err for c in ("HTTP 400", "HTTP 401", "HTTP 403")):
                    slot.mark_error(err)
                    fatal_excluded.add(slot.key)
                    tried_this_round.add(slot.key)
                    print(f"[OmniKey] ✗ {slot.alias} → fatal. Permanently skipping.", file=sys.stderr)
                    continue

                else:
                    slot.mark_error(err)
                    tried_this_round.add(slot.key)
                    print(f"[OmniKey] ⚠ {slot.alias} → transient: {err[:80]}", file=sys.stderr)
                    continue

            except Exception as e:
                slot.mark_error(str(e))
                tried_this_round.add(slot.key)
                continue

        # Build a useful error message
        n_cool    = sum(1 for s in self.slots if s.cooldown_remaining() > 0 and s.status != KeyStatus.INVALID)
        n_invalid = sum(1 for s in self.slots if s.status == KeyStatus.INVALID)
        min_wait  = min(
            (s.cooldown_remaining() for s in self.slots if s.status != KeyStatus.INVALID),
            default=0,
        )

        if n_invalid == len(self.slots):
            msg = "⚠️ All API keys invalid. Check your keys in secrets.toml."
        elif n_cool > 0:
            msg = (
                f"⏳ All {len(self.slots)} keys are rate-limited. "
                f"Fastest recovers in ~{min_wait:.0f}s. Please wait and retry."
            )
        else:
            msg = "⚠️ All Gemini requests failed. Check your network or API keys."
        raise RuntimeError(msg)

    # ── Streaming ─────────────────────────────────────────────────────────────
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
        full  = self.execute(model=model, prompt=prompt, system=system,
                             temperature=temperature, max_tokens=max_tokens, **kwargs)
        words = full.split(" ")
        chunk: List[str] = []
        for i, word in enumerate(words):
            chunk.append(word)
            if len(chunk) >= chunk_words or i == len(words) - 1:
                yield " ".join(chunk) + (" " if i < len(words) - 1 else "")
                chunk = []

    # ── Dashboard ─────────────────────────────────────────────────────────────
    def get_status_report(self) -> Dict[str, Any]:
        now       = time.monotonic()
        snapshots = [s.snapshot() for s in self.slots]
        n_ready   = sum(1 for s in self.slots if s.is_available(now))
        n_cooling = sum(1 for s in self.slots if s.cooldown_remaining(now) > 0 and s.status != KeyStatus.INVALID)
        n_invalid = sum(1 for s in self.slots if s.status == KeyStatus.INVALID)
        return {
            "total_keys":  len(self.slots),
            "available":   n_ready,
            "cooling":     n_cooling,
            "invalid":     n_invalid,
            "total_calls": sum(s.total_calls for s in self.slots),
            "total_429":   sum(s.total_429 for s in self.slots),
            "health_pct":  round(n_ready / max(len(self.slots), 1) * 100, 1),
            "keys":        snapshots,
        }

    def get_key_status_line(self) -> str:
        r = self.get_status_report()
        return (
            f"🔑 Keys: {r['available']}/{r['total_keys']} active | "
            f"⚡ {r['total_calls']} calls | "
            f"⚠ {r['total_429']} rate-limits"
        )

    def get_dashboard_html(self) -> str:
        report = self.get_status_report()
        rows   = []
        for k in report["keys"]:
            rpm_pct   = k["rpm_pct"]
            available = k["available"]
            cd_sec    = k["cooldown_sec"]

            if not available:
                color, dot = "#e74c3c", "🔴"
            elif rpm_pct >= 80:
                color, dot = "#f39c12", "🟡"
            else:
                color, dot = "#2ecc71", "🟢"

            cd_str = f" | cools in {cd_sec:.0f}s" if cd_sec > 0 else ""
            bar_w  = max(rpm_pct, 2)

            rows.append(f"""
<div style="margin:4px 0;font-size:12px;font-family:monospace;">
  <span style="display:inline-block;width:90px;">{dot} {k['alias']}</span>
  <span style="display:inline-block;width:140px;background:#1a1a2e;border-radius:4px;overflow:hidden;vertical-align:middle;">
    <span style="display:block;width:{bar_w}%;height:12px;background:{color};border-radius:4px;transition:width 0.5s;"></span>
  </span>
  <span style="margin-left:6px;color:#aaa;">
    {k['rpm_used']}/{k['rpm_limit']} RPM · {k['total_calls']} calls · {k['success_rate']}% OK{cd_str}
  </span>
</div>""")

        keys_html = "\n".join(rows)
        r         = report
        return f"""
<div style="background:#0d0d1a;border:1px solid #2a2a4a;border-radius:8px;padding:10px 14px;margin:6px 0;">
  <div style="color:#7c83f5;font-weight:bold;font-size:13px;margin-bottom:6px;">
    🔑 OmniKey v5 — {r['available']}/{r['total_keys']} ready · {r['health_pct']}% healthy · ⚡ {r['total_429']} rate-limits
  </div>
  {keys_html}
</div>
"""

    def reset_key_cooldown(self, key_alias: str) -> bool:
        for s in self.slots:
            if s.alias == key_alias or key_alias in s.key:
                s.cooldown_until = 0.0
                s.status = KeyStatus.READY
                print(f"[OmniKey] Manual reset: {s.alias}", file=sys.stderr)
                return True
        return False

    def reset_all_cooldowns(self) -> None:
        for s in self.slots:
            if s.status != KeyStatus.INVALID:
                s.cooldown_until = 0.0
                s.status = KeyStatus.READY
        print("[OmniKey] All cooldowns reset.", file=sys.stderr)


# ─── Global Singleton ─────────────────────────────────────────────────────────
OMNI_ENGINE = OmniKeyEngine()
