"""
ai_engine.py — ZERO-DOWNTIME Unified AI Router v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE BRAIN that routes every AI call across ExamHelp.

ARCHITECTURE:
  ┌──────────────────────────────────────────────────┐
  │  ANY FEATURE (chat, humaniser, notes, etc.)      │
  │       calls ai_engine.generate(prompt, ...)      │
  └──────────────┬───────────────────────────────────┘
                 │
  ┌──────────────▼───────────────────────────────────┐
  │        UNIFIED AI ROUTER (this file)             │
  │                                                  │
  │  ┌─────────┐  instant   ┌─────────┐  instant    │
  │  │ Groq    │──switch──▶│ Groq    │──switch──▶  │
  │  │ Key #1  │           │ Key #2  │          ... │
  │  └─────────┘           └─────────┘              │
  │       │ all Groq exhausted                       │
  │       ▼                                          │
  │  ┌─────────┐  instant   ┌─────────┐             │
  │  │ Gemini  │──switch──▶│ Gemini  │──▶ ...      │
  │  │ Key #1  │           │ Key #2  │              │
  │  └─────────┘           └─────────┘              │
  └──────────────────────────────────────────────────┘

KEY PRINCIPLES:
  1. INSTANT switch — zero delay on rate limit (no sleep/wait)
  2. Groq first (faster), auto-cascade to Gemini
  3. Per-key sliding window tracking (RPM, TPM, RPD)
  4. Pre-emptive switching BEFORE hitting the wall
  5. Every key is milked to its absolute maximum
  6. Single function for ALL AI calls across the platform

RATE-LIMIT STRATEGY:
  - On 429 → mark key with cooldown → INSTANTLY try next key
  - On auth error → mark key DEAD for 24h → next key
  - On model error → try fallback model on SAME key → then next key
  - On network error → short penalty → next key
  - All keys exhausted → cascade to Gemini pool
  - ALL pools exhausted → raise clear error
"""

from __future__ import annotations
import os, time, threading, math, re, json
from collections import deque
from typing import Optional, Generator, Dict, Any, List, Tuple
from dataclasses import dataclass, field

# ══════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════

# Groq model hierarchy (best → fallback)
GROQ_MODELS = [
    "llama-4-scout-17b-16e-instruct",  # 30K TPM, 500K TPD — BEST
    "llama-3.3-70b-versatile",          # 12K TPM — secondary
    "llama-3.1-8b-instant",             # 6K TPM — fast fallback
]

# Gemini model hierarchy (best → fallback)
GEMINI_MODELS = [
    "gemini-2.5-flash-preview-04-17",   # Best capability
    "gemini-2.0-flash",                 # Fast, 1M context
    "gemini-2.0-flash-lite",            # Fastest
]

# Groq limits per key
GROQ_RPM  = 30
GROQ_RPD  = 1_000
GROQ_TPM  = 30_000
GROQ_TPD  = 500_000

# Gemini limits per key
GEMINI_RPM = 15
GEMINI_RPD = 1_500

# Pre-emptive switch thresholds (switch BEFORE hitting wall)
GROQ_SWITCH_RPM  = 4     # switch when < 4 RPM remaining
GROQ_SWITCH_TPM  = 4_000 # switch when < 4K TPM remaining
GEMINI_SWITCH_RPM = 3    # switch when < 3 RPM remaining

# Timing
RATE_LIMIT_COOLDOWN = 65.0   # seconds to cooldown after 429
DEAD_KEY_COOLDOWN = 86_400.0 # 24h for auth failures
ERROR_PENALTY_BASE = 5.0     # seconds penalty per consecutive error
WINDOW = 60.0                # sliding window for RPM/TPM

# Gemini API
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


# ══════════════════════════════════════════════════════════════
# KEY STATE TRACKING
# ══════════════════════════════════════════════════════════════

@dataclass
class KeyState:
    """Real-time state tracker for a single API key."""
    key: str
    provider: str  # "groq" or "gemini"
    
    # Rate tracking
    rpm_log: deque = field(default_factory=deque)      # timestamps of requests in window
    tpm_log: deque = field(default_factory=deque)      # (timestamp, tokens) in window
    rpd_used: int = 0
    tpd_used: int = 0
    
    # Timing
    cooldown_until: float = 0.0
    day_reset_at: float = 0.0
    last_used: float = 0.0
    last_error: float = 0.0
    
    # Health
    consecutive_errors: int = 0
    total_uses: int = 0
    total_errors: int = 0
    rate_limit_hits: int = 0
    total_tokens: int = 0
    is_dead: bool = False
    
    def __post_init__(self):
        import datetime
        # Set day reset (midnight UTC for Groq, midnight PT for Gemini)
        now_utc = datetime.datetime.utcnow()
        if self.provider == "gemini":
            # Midnight Pacific = 8AM UTC
            self.day_reset_at = (now_utc + datetime.timedelta(days=1)).replace(
                hour=8, minute=0, second=0, microsecond=0).timestamp()
        else:
            self.day_reset_at = (now_utc + datetime.timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0).timestamp()


class KeyPool:
    """Thread-safe pool of API keys with instant rotation."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._groq_keys: List[KeyState] = []
        self._gemini_keys: List[KeyState] = []
        self._initialized = False
    
    def _ensure_init(self):
        """Lazy initialization — load keys on first use."""
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            self._load_all_keys()
            self._initialized = True
    
    def _load_all_keys(self):
        """Load all keys from secret_manager."""
        from utils.secret_manager import GROQ_KEYS, GEMINI_KEYS
        
        self._groq_keys = [KeyState(key=k, provider="groq") for k in GROQ_KEYS]
        self._gemini_keys = [KeyState(key=k, provider="gemini") for k in GEMINI_KEYS]
    
    # ── Sliding window helpers ────────────────────────────────
    
    def _prune_window(self, log: deque, now: float, is_tuple: bool = False):
        """Remove expired entries from sliding window."""
        cutoff = now - WINDOW
        while log:
            ts = log[0][0] if is_tuple else log[0]
            if ts < cutoff:
                log.popleft()
            else:
                break
    
    def _rpm_used(self, ks: KeyState, now: float) -> int:
        self._prune_window(ks.rpm_log, now)
        return len(ks.rpm_log)
    
    def _tpm_used(self, ks: KeyState, now: float) -> int:
        self._prune_window(ks.tpm_log, now, is_tuple=True)
        return sum(t for _, t in ks.tpm_log)
    
    def _daily_reset(self, ks: KeyState, now: float):
        if now >= ks.day_reset_at:
            ks.rpd_used = 0
            ks.tpd_used = 0
            import datetime
            ks.day_reset_at = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).replace(
                hour=(8 if ks.provider == "gemini" else 0),
                minute=0, second=0, microsecond=0
            ).timestamp()
    
    # ── Health score (0.0 = unavailable, 1.0 = fully healthy) ─
    
    def _health_score(self, ks: KeyState, now: float) -> float:
        """Calculate key health 0.0-1.0. 0.0 means DO NOT USE."""
        if ks.is_dead:
            return 0.0
        if ks.cooldown_until > now:
            return 0.0
        
        self._daily_reset(ks, now)
        
        if ks.provider == "groq":
            rpm_rem = GROQ_RPM - self._rpm_used(ks, now)
            tpm_rem = GROQ_TPM - self._tpm_used(ks, now)
            rpd_rem = GROQ_RPD - ks.rpd_used
            
            if rpm_rem < GROQ_SWITCH_RPM:
                return 0.0
            if tpm_rem < GROQ_SWITCH_TPM:
                return 0.0
            if rpd_rem < 10:
                return 0.0
            
            score = (
                0.35 * (rpm_rem / GROQ_RPM) +
                0.35 * (tpm_rem / GROQ_TPM) +
                0.20 * (rpd_rem / GROQ_RPD) +
                0.10 * ((GROQ_TPD - ks.tpd_used) / GROQ_TPD)
            )
        else:  # gemini
            rpm_rem = GEMINI_RPM - self._rpm_used(ks, now)
            rpd_rem = GEMINI_RPD - ks.rpd_used
            
            if rpm_rem < GEMINI_SWITCH_RPM:
                return 0.0
            if rpd_rem < 5:
                return 0.0
            
            score = 0.5 * (rpm_rem / GEMINI_RPM) + 0.5 * (rpd_rem / GEMINI_RPD)
        
        # Health penalty for consecutive errors
        if ks.consecutive_errors > 0:
            score *= math.exp(-0.5 * ks.consecutive_errors)
        
        return max(0.0, min(1.0, score))
    
    # ── Key selection (INSTANT — zero delay) ──────────────────
    
    def get_best_key(self, provider: str = "groq", exclude: set = None) -> Optional[KeyState]:
        """Get the healthiest key for a provider. O(n) scan — instant."""
        self._ensure_init()
        now = time.time()
        exclude = exclude or set()
        
        with self._lock:
            pool = self._groq_keys if provider == "groq" else self._gemini_keys
            candidates = [ks for ks in pool if ks.key not in exclude]
            
            if not candidates:
                return None
            
            # Sort by health score (highest first)
            scored = [(self._health_score(ks, now), ks) for ks in candidates]
            scored.sort(key=lambda x: -x[0])
            
            # Return best healthy key
            if scored[0][0] > 0:
                return scored[0][1]
            
            # All scored 0 — find one that's in cooldown but closest to recovery
            cooling = [ks for ks in candidates if not ks.is_dead and ks.cooldown_until > now]
            if cooling:
                return min(cooling, key=lambda ks: ks.cooldown_until)
            
            # All dead — return any non-dead key
            alive = [ks for ks in candidates if not ks.is_dead]
            if alive:
                return alive[0]
            
            return None
    
    # ── State mutations ───────────────────────────────────────
    
    def mark_success(self, ks: KeyState, tokens: int = 0):
        """Mark a successful API call."""
        now = time.time()
        with self._lock:
            ks.rpm_log.append(now)
            ks.rpd_used += 1
            ks.total_uses += 1
            ks.last_used = now
            ks.consecutive_errors = 0  # Reset on success!
            if tokens > 0:
                ks.tpm_log.append((now, tokens))
                ks.tpd_used += tokens
                ks.total_tokens += tokens
    
    def mark_rate_limited(self, ks: KeyState, retry_after: float = 0):
        """Mark key as rate-limited — instant cooldown, move to next."""
        now = time.time()
        cooldown = max(retry_after + 2.0, RATE_LIMIT_COOLDOWN) if retry_after > 0 else RATE_LIMIT_COOLDOWN
        with self._lock:
            ks.cooldown_until = now + cooldown
            ks.rate_limit_hits += 1
            ks.total_errors += 1
            ks.consecutive_errors = min(ks.consecutive_errors + 1, 10)
            ks.last_error = now
            # Clear windows so score resets naturally after cooldown
            ks.rpm_log.clear()
            ks.tpm_log.clear()
    
    def mark_auth_failed(self, ks: KeyState):
        """Mark key as permanently dead (invalid key)."""
        now = time.time()
        with self._lock:
            ks.is_dead = True
            ks.cooldown_until = now + DEAD_KEY_COOLDOWN
            ks.consecutive_errors = 99
            ks.total_errors += 1
            ks.last_error = now
    
    def mark_error(self, ks: KeyState):
        """Mark a generic error — short penalty."""
        now = time.time()
        with self._lock:
            ks.consecutive_errors = min(ks.consecutive_errors + 1, 10)
            ks.total_errors += 1
            ks.last_error = now
            penalty = min(ERROR_PENALTY_BASE * ks.consecutive_errors, 60.0)
            ks.cooldown_until = max(ks.cooldown_until, now + penalty)
    
    def reset_all(self):
        """Emergency reset — clear all cooldowns."""
        with self._lock:
            for ks in self._groq_keys + self._gemini_keys:
                ks.cooldown_until = 0.0
                ks.consecutive_errors = 0
                ks.rpm_log.clear()
                ks.tpm_log.clear()
                ks.is_dead = False
    
    # ── Status (safe — never shows full keys) ─────────────────
    
    def get_status(self) -> Dict:
        """Get complete pool status for diagnostics."""
        self._ensure_init()
        now = time.time()
        
        def _key_info(ks: KeyState) -> Dict:
            score = self._health_score(ks, now)
            if ks.is_dead:
                status = "⛔ DEAD"
            elif ks.cooldown_until > now:
                remaining = ks.cooldown_until - now
                status = f"⏳ {remaining:.0f}s"
            elif score > 0.7:
                status = f"🟢 {score*100:.0f}%"
            elif score > 0.3:
                status = f"🟡 {score*100:.0f}%"
            elif score > 0:
                status = f"🟠 {score*100:.0f}%"
            else:
                status = "🔴 exhausted"
            
            return {
                "id": f"…{ks.key[-4:]}",
                "status": status,
                "score": round(score, 3),
                "rpm": f"{self._rpm_used(ks, now)}/{GROQ_RPM if ks.provider == 'groq' else GEMINI_RPM}",
                "rpd": f"{ks.rpd_used}/{GROQ_RPD if ks.provider == 'groq' else GEMINI_RPD}",
                "uses": ks.total_uses,
                "errors": ks.total_errors,
                "rl_hits": ks.rate_limit_hits,
                "tokens": f"{ks.total_tokens:,}",
            }
        
        with self._lock:
            groq_avail = sum(1 for ks in self._groq_keys if self._health_score(ks, now) > 0)
            gemini_avail = sum(1 for ks in self._gemini_keys if self._health_score(ks, now) > 0)
            
            return {
                "groq": {
                    "total": len(self._groq_keys),
                    "available": groq_avail,
                    "keys": [_key_info(ks) for ks in self._groq_keys],
                },
                "gemini": {
                    "total": len(self._gemini_keys),
                    "available": gemini_avail,
                    "keys": [_key_info(ks) for ks in self._gemini_keys],
                },
                "total_capacity": {
                    "groq_rpm": len(self._groq_keys) * GROQ_RPM,
                    "groq_tpm": len(self._groq_keys) * GROQ_TPM,
                    "gemini_rpm": len(self._gemini_keys) * GEMINI_RPM,
                },
            }


# Global singleton
_pool = KeyPool()


# ══════════════════════════════════════════════════════════════
# ERROR CLASSIFICATION
# ══════════════════════════════════════════════════════════════

def _classify_error(err_str: str) -> str:
    """Classify an error for routing decisions."""
    e = err_str.lower()
    if "rate_limit" in e or "429" in e or "too many" in e or "rate limit" in e:
        return "rate_limit"
    if "authentication" in e or "api_key" in e or "401" in e or "invalid api key" in e or "unauthorized" in e:
        return "auth"
    if "model_not_found" in e or ("model" in e and "not" in e and "found" in e):
        return "model_not_found"
    if "context_length" in e or ("token" in e and "exceed" in e):
        return "context_length"
    if "connection" in e or "timeout" in e or "network" in e:
        return "network"
    if "overload" in e or "503" in e or "service_unavailable" in e or "capacity" in e or "529" in e:
        return "overload"
    return "unknown"


def _parse_retry_after(err_str: str) -> float:
    """Extract retry-after seconds from error message."""
    m = re.search(r'try again in ([0-9.]+)s', err_str, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r'retry.after[\"\s:]+([0-9.]+)', err_str, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return 0.0


# ══════════════════════════════════════════════════════════════
# GROQ CALL ENGINE
# ══════════════════════════════════════════════════════════════

def _call_groq(
    messages: list,
    system_prompt: str,
    model: str,
    max_tokens: int,
    temperature: float,
    json_mode: bool,
    stream: bool,
) -> Tuple[Any, KeyState]:
    """
    Try ALL Groq keys. Instant rotation on any failure.
    Returns (result, key_state) or raises if all exhausted.
    """
    from groq import Groq
    
    tried: set = set()
    last_err = None
    max_attempts = len(_pool._groq_keys) * 3  # Try each key up to 3 times
    
    for _attempt in range(max_attempts):
        ks = _pool.get_best_key("groq", exclude=tried)
        if not ks:
            break
        
        # If we've tried this key and all others are tried, stop
        if ks.key in tried and len(tried) >= len(_pool._groq_keys):
            break
        tried.add(ks.key)
        
        client = Groq(api_key=ks.key)
        
        # Try primary model, then fallbacks
        models_to_try = [model] if model else [GROQ_MODELS[0]]
        
        for try_model in models_to_try:
            try:
                fmt = {"type": "json_object"} if json_mode and not stream else {"type": "text"}
                kwargs = dict(
                    model=try_model,
                    messages=[{"role": "system", "content": system_prompt}] + messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                )
                if not stream:
                    kwargs["response_format"] = fmt
                
                completion = client.chat.completions.create(stream=stream, **kwargs)
                
                if stream:
                    # Return the stream object — caller handles iteration
                    return completion, ks
                
                # Non-streaming: extract result
                tokens = 0
                try:
                    tokens = completion.usage.total_tokens or 0
                except Exception:
                    pass
                
                text = completion.choices[0].message.content
                _pool.mark_success(ks, tokens)
                return text, ks
                
            except Exception as e:
                err_str = str(e)
                last_err = e
                etype = _classify_error(err_str)
                
                if etype == "rate_limit":
                    retry_after = _parse_retry_after(err_str)
                    _pool.mark_rate_limited(ks, retry_after)
                    break  # INSTANT switch to next key (break model loop)
                
                elif etype == "auth":
                    _pool.mark_auth_failed(ks)
                    break  # Key is dead, next key
                
                elif etype == "model_not_found":
                    # Try fallback models on SAME key
                    for fb_model in GROQ_MODELS[1:]:
                        if fb_model != try_model:
                            try:
                                kwargs["model"] = fb_model
                                completion = client.chat.completions.create(stream=stream, **kwargs)
                                if stream:
                                    return completion, ks
                                tokens = 0
                                try:
                                    tokens = completion.usage.total_tokens or 0
                                except Exception:
                                    pass
                                text = completion.choices[0].message.content
                                _pool.mark_success(ks, tokens)
                                return text, ks
                            except Exception:
                                continue
                    _pool.mark_error(ks)
                    break
                
                elif etype == "overload":
                    _pool.mark_rate_limited(ks, retry_after=15.0)
                    break
                
                elif etype == "network":
                    _pool.mark_error(ks)
                    break
                
                else:
                    _pool.mark_error(ks)
                    break
    
    if last_err:
        raise last_err
    raise RuntimeError("All Groq keys exhausted")


# ══════════════════════════════════════════════════════════════
# GEMINI CALL ENGINE
# ══════════════════════════════════════════════════════════════

def _call_gemini(
    prompt: str,
    system_prompt: str = "",
    model: str = None,
    max_tokens: int = 8192,
    temperature: float = 0.7,
    image_data: str = None,
    image_mime: str = "image/jpeg",
) -> Tuple[str, KeyState]:
    """
    Try ALL Gemini keys with instant rotation.
    Returns (text, key_state) or raises if all exhausted.
    """
    import requests as req
    
    chosen_model = model or GEMINI_MODELS[0]
    tried: set = set()
    last_err = None
    
    for _attempt in range(len(_pool._gemini_keys) * len(GEMINI_MODELS)):
        ks = _pool.get_best_key("gemini", exclude=tried)
        if not ks:
            break
        if ks.key in tried and len(tried) >= len(_pool._gemini_keys):
            break
        tried.add(ks.key)
        
        # Try each model in priority order
        for try_model in ([chosen_model] + [m for m in GEMINI_MODELS if m != chosen_model]):
            try:
                url = f"{GEMINI_API_BASE}/{try_model}:generateContent?key={ks.key}"
                
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
                if system_prompt:
                    payload["system_instruction"] = {"parts": [{"text": system_prompt}]}
                
                resp = req.post(url, json=payload, timeout=60)
                
                if resp.status_code == 429:
                    _pool.mark_rate_limited(ks, retry_after=60.0)
                    break  # INSTANT switch to next key
                
                if resp.status_code == 403 or resp.status_code == 401:
                    _pool.mark_auth_failed(ks)
                    break
                
                if resp.status_code == 400:
                    # Model might not exist — try next model
                    continue
                
                if resp.status_code == 503 or resp.status_code == 529:
                    _pool.mark_rate_limited(ks, retry_after=15.0)
                    break
                
                resp.raise_for_status()
                data = resp.json()
                candidates = data.get("candidates", [])
                
                if not candidates:
                    continue
                
                parts_out = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts_out).strip()
                
                if text:
                    _pool.mark_success(ks)
                    return text, ks
                    
            except Exception as e:
                last_err = e
                etype = _classify_error(str(e))
                if etype == "rate_limit":
                    _pool.mark_rate_limited(ks)
                    break
                elif etype == "auth":
                    _pool.mark_auth_failed(ks)
                    break
                else:
                    _pool.mark_error(ks)
                    continue
    
    if last_err:
        raise last_err
    raise RuntimeError("All Gemini keys exhausted")


# ══════════════════════════════════════════════════════════════
# PUBLIC API — THE SINGLE ENTRY POINT FOR ALL AI CALLS
# ══════════════════════════════════════════════════════════════

def generate(
    prompt: str = "",
    messages: list = None,
    system_prompt: str = "",
    model: str = None,
    provider: str = "auto",
    max_tokens: int = 8192,
    temperature: float = 0.7,
    json_mode: bool = False,
    image_data: str = None,
    image_mime: str = "image/jpeg",
) -> str:
    """
    THE universal AI call function. Routes to the best available key/provider.
    
    Args:
        prompt: Simple text prompt (for Gemini-style calls)
        messages: Chat messages list [{"role": "user", "content": "..."}]
        system_prompt: Custom system instructions
        model: Specific model override
        provider: "groq", "gemini", or "auto" (tries Groq then Gemini)
        max_tokens: Maximum output tokens
        temperature: Generation temperature
        json_mode: Return JSON-formatted response
        image_data: Base64 image data (forces Gemini)
        image_mime: Image MIME type
    
    Returns:
        Generated text string
    
    Raises:
        RuntimeError: If ALL keys across ALL providers are exhausted
    """
    _pool._ensure_init()
    
    # Image data requires Gemini (has vision)
    if image_data:
        provider = "gemini"
    
    # Build messages from prompt if not provided
    if not messages and prompt:
        messages = [{"role": "user", "content": prompt}]
    elif not messages:
        raise ValueError("Either prompt or messages must be provided")
    
    # AUTO: Try Groq first (faster), fall back to Gemini
    if provider == "auto":
        # Try Groq
        try:
            text, _ = _call_groq(
                messages=messages,
                system_prompt=system_prompt or "You are a helpful AI assistant.",
                model=model or GROQ_MODELS[0],
                max_tokens=max_tokens,
                temperature=temperature,
                json_mode=json_mode,
                stream=False,
            )
            if isinstance(text, str) and text.strip():
                return text
        except Exception:
            pass  # Fall through to Gemini
        
        # Groq exhausted — cascade to Gemini
        try:
            prompt_text = "\n\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
                for m in messages
            )
            text, _ = _call_gemini(
                prompt=prompt_text,
                system_prompt=system_prompt,
                model=None,  # Use best available
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return text
        except Exception as e:
            raise RuntimeError(f"All AI providers exhausted. Groq + Gemini all rate-limited. Try again in ~60s. Error: {e}")
    
    elif provider == "groq":
        text, _ = _call_groq(
            messages=messages,
            system_prompt=system_prompt or "You are a helpful AI assistant.",
            model=model or GROQ_MODELS[0],
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=json_mode,
            stream=False,
        )
        return text
    
    elif provider == "gemini":
        prompt_text = prompt or "\n\n".join(
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in messages
        )
        text, _ = _call_gemini(
            prompt=prompt_text,
            system_prompt=system_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            image_data=image_data,
            image_mime=image_mime,
        )
        return text
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'auto', 'groq', or 'gemini'.")


def generate_stream(
    messages: list,
    system_prompt: str = "",
    model: str = None,
    max_tokens: int = 8192,
    temperature: float = 0.65,
    persona_prompt: str = "",
    context_text: str = "",
) -> Generator[str, None, None]:
    """
    Streaming version of generate(). Currently Groq-only with Gemini non-stream fallback.
    
    Yields text chunks as they arrive. On rate limit, instantly switches keys
    and continues streaming from the next key — user sees no interruption.
    """
    _pool._ensure_init()
    
    full_system = system_prompt
    if persona_prompt:
        full_system = (full_system + "\n\n" + persona_prompt) if full_system else persona_prompt
    if not full_system:
        full_system = "You are a helpful AI assistant."
    
    # Build context-aware messages
    built_messages = list(messages)
    if context_text:
        ctx_trimmed = context_text[:28_000]
        built_messages = [
            {"role": "user", "content": f"=== STUDY MATERIAL ===\n\n{ctx_trimmed}\n\n=== END ===\n\nPlease acknowledge you received this."},
            {"role": "assistant", "content": "✅ Study material received. I will answer grounded in this material."},
        ] + built_messages
    
    tried_keys: set = set()
    last_err = None
    
    # Try Groq keys for streaming
    for _attempt in range(len(_pool._groq_keys) * 2):
        ks = _pool.get_best_key("groq", exclude=tried_keys)
        if not ks:
            break
        if ks.key in tried_keys and len(tried_keys) >= len(_pool._groq_keys):
            break
        tried_keys.add(ks.key)
        
        try:
            from groq import Groq
            client = Groq(api_key=ks.key)
            
            use_model = model or GROQ_MODELS[0]
            stream_obj = client.chat.completions.create(
                stream=True,
                model=use_model,
                messages=[{"role": "system", "content": full_system}] + built_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
            )
            
            total_tokens = 0
            word_count = 0
            
            for chunk in stream_obj:
                # Try to get usage from final chunk
                try:
                    if chunk.usage:
                        total_tokens = chunk.usage.total_tokens or total_tokens
                except Exception:
                    pass
                
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    word_count += len(delta.split())
                    yield delta
            
            # Estimate tokens if API didn't report
            if total_tokens == 0:
                total_tokens = int(word_count * 1.4)
            
            _pool.mark_success(ks, total_tokens)
            return  # Stream complete!
            
        except Exception as e:
            err_str = str(e)
            last_err = e
            etype = _classify_error(err_str)
            
            if etype == "rate_limit":
                _pool.mark_rate_limited(ks, _parse_retry_after(err_str))
                continue  # INSTANT switch — no sleep!
            elif etype == "auth":
                _pool.mark_auth_failed(ks)
                continue
            elif etype == "overload":
                _pool.mark_rate_limited(ks, 15.0)
                continue
            else:
                _pool.mark_error(ks)
                continue
    
    # All Groq keys exhausted — Gemini non-streaming fallback
    try:
        prompt_text = "\n\n".join(
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in built_messages
        )
        text, _ = _call_gemini(
            prompt=prompt_text,
            system_prompt=full_system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        # Simulate streaming by yielding in chunks
        words = text.split()
        chunk_size = 5
        for i in range(0, len(words), chunk_size):
            yield " ".join(words[i:i+chunk_size])
            if i + chunk_size < len(words):
                yield " "
        return
    except Exception as e:
        last_err = e
    
    if last_err:
        raise last_err
    raise RuntimeError("All AI keys exhausted across Groq + Gemini. Wait ~60s for cooldowns to expire.")


# ══════════════════════════════════════════════════════════════
# CONVENIENCE SHORTCUTS
# ══════════════════════════════════════════════════════════════

def quick_generate(prompt: str, system: str = "") -> str:
    """Fastest possible generation — auto-routed, no frills."""
    return generate(prompt=prompt, system_prompt=system)


def vision_generate(prompt: str, image_b64: str, mime: str = "image/jpeg") -> str:
    """Vision call using Gemini (only provider with vision)."""
    return generate(prompt=prompt, provider="gemini", image_data=image_b64, image_mime=mime)


def json_generate(prompt: str, system: str = "") -> str:
    """Generate structured JSON output."""
    return generate(prompt=prompt, system_prompt=system, json_mode=True, temperature=0.2)


# ══════════════════════════════════════════════════════════════
# STATUS & DIAGNOSTICS
# ══════════════════════════════════════════════════════════════

def get_pool_status() -> Dict:
    """Get full pool status (safe — never shows key values)."""
    return _pool.get_status()


def reset_all_keys():
    """Emergency reset — clear all cooldowns and errors."""
    _pool.reset_all()


def get_capacity_summary() -> str:
    """Human-readable capacity summary."""
    status = _pool.get_status()
    g = status["groq"]
    m = status["gemini"]
    return (
        f"🔑 Groq: {g['available']}/{g['total']} keys ready | "
        f"💎 Gemini: {m['available']}/{m['total']} keys ready | "
        f"⚡ Total capacity: {status['total_capacity']['groq_rpm']}+{status['total_capacity']['gemini_rpm']} RPM"
    )
