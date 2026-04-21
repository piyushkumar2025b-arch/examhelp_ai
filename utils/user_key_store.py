"""
user_key_store.py — Multi-Provider API Key Manager v2.0
=========================================================
Supports 18 providers (was 3):

ORIGINAL:
  Gemini   : AIzaSy…
  Groq     : gsk_…
  Cerebras : csk-…

NEW (15 additions):
  OpenAI         : sk-…
  Anthropic      : sk-ant-…
  Mistral        : key from mistral.ai (no fixed prefix — stored explicitly)
  Cohere         : co_…
  Together AI    : …  (no fixed prefix)
  DeepSeek       : sk-…  (same prefix as OpenAI, differentiated by user label)
  Perplexity     : pplx-…
  OpenRouter     : sk-or-…
  Fireworks AI   : fw_…
  Replicate      : r8_…
  HuggingFace    : hf_…
  AI21 Labs      : …
  Anyscale       : esecret_…
  Sambanova      : samba_…
  Nvidia NIM     : nvapi_…

Storage: session_state only, never on disk.

Public API (unchanged):
  set_user_key(raw, provider_hint=None) → provider
  get_user_key()  → (key, provider) or (None, None)
  clear_user_key()
  detect_provider(raw, hint=None) → str | None
  has_key()       → bool
  get_all_stored_keys()  → list[dict]  NEW
  set_multi_keys(keys_dict) → None  NEW
"""

from __future__ import annotations
import streamlit as st
from typing import Optional, Tuple, List, Dict


# ── Provider registry ──────────────────────────────────────────────────────────

PROVIDER_REGISTRY: Dict[str, Dict] = {
    "gemini": {
        "label": "Google Gemini",
        "icon": "✨",
        "color": "#4285f4",
        "model": "gemini-2.5-flash",
        "prefix": ["AIzaSy"],
        "hint": "aistudio.google.com",
        "free": True,
        "supports_vision": True,
    },
    "groq": {
        "label": "Groq",
        "icon": "⚡",
        "color": "#f55036",
        "model": "llama-3.3-70b-versatile",
        "prefix": ["gsk_"],
        "hint": "console.groq.com",
        "free": True,
        "supports_vision": False,
    },
    "cerebras": {
        "label": "Cerebras",
        "icon": "🚀",
        "color": "#ff6b35",
        "model": "llama3.3-70b",
        "prefix": ["csk-"],
        "hint": "cloud.cerebras.ai",
        "free": True,
        "supports_vision": False,
    },
    "openai": {
        "label": "OpenAI",
        "icon": "🤖",
        "color": "#10a37f",
        "model": "gpt-4o-mini",
        "prefix": ["sk-proj-", "sk-"],
        "hint": "platform.openai.com",
        "free": False,
        "supports_vision": True,
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "icon": "🔮",
        "color": "#c96442",
        "model": "claude-3-haiku-20240307",
        "prefix": ["sk-ant-"],
        "hint": "console.anthropic.com",
        "free": False,
        "supports_vision": True,
    },
    "mistral": {
        "label": "Mistral AI",
        "icon": "🌬️",
        "color": "#ff7000",
        "model": "mistral-small-latest",
        "prefix": [],
        "hint": "console.mistral.ai",
        "free": False,
        "supports_vision": False,
    },
    "cohere": {
        "label": "Cohere",
        "icon": "🧠",
        "color": "#39a7a3",
        "model": "command-r",
        "prefix": ["co_"],
        "hint": "dashboard.cohere.com",
        "free": True,
        "supports_vision": False,
    },
    "together": {
        "label": "Together AI",
        "icon": "🤝",
        "color": "#0ea5e9",
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "prefix": [],
        "hint": "api.together.xyz",
        "free": True,
        "supports_vision": False,
    },
    "perplexity": {
        "label": "Perplexity AI",
        "icon": "🔭",
        "color": "#20b2aa",
        "model": "llama-3.1-sonar-small-128k-online",
        "prefix": ["pplx-"],
        "hint": "perplexity.ai/settings/api",
        "free": False,
        "supports_vision": False,
    },
    "openrouter": {
        "label": "OpenRouter",
        "icon": "🔀",
        "color": "#8b5cf6",
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "prefix": ["sk-or-"],
        "hint": "openrouter.ai/keys",
        "free": True,
        "supports_vision": False,
    },
    "fireworks": {
        "label": "Fireworks AI",
        "icon": "🎆",
        "color": "#ef4444",
        "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "prefix": ["fw_"],
        "hint": "fireworks.ai",
        "free": True,
        "supports_vision": False,
    },
    "replicate": {
        "label": "Replicate",
        "icon": "♾️",
        "color": "#f59e0b",
        "model": "meta/meta-llama-3-8b-instruct",
        "prefix": ["r8_"],
        "hint": "replicate.com",
        "free": False,
        "supports_vision": True,
    },
    "huggingface": {
        "label": "Hugging Face",
        "icon": "🤗",
        "color": "#ff9d00",
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "prefix": ["hf_"],
        "hint": "huggingface.co/settings/tokens",
        "free": True,
        "supports_vision": False,
    },
    "sambanova": {
        "label": "SambaNova",
        "icon": "🧬",
        "color": "#e11d48",
        "model": "Meta-Llama-3.3-70B-Instruct",
        "prefix": ["samba_"],
        "hint": "cloud.sambanova.ai",
        "free": True,
        "supports_vision": False,
    },
    "nvidia": {
        "label": "NVIDIA NIM",
        "icon": "🟢",
        "color": "#76b900",
        "model": "meta/llama-3.1-8b-instruct",
        "prefix": ["nvapi-"],
        "hint": "build.nvidia.com",
        "free": True,
        "supports_vision": True,
    },
    "deepseek": {
        "label": "DeepSeek",
        "icon": "🔍",
        "color": "#2563eb",
        "model": "deepseek-chat",
        "prefix": [],  # manual selection required (shares sk- with OpenAI)
        "hint": "platform.deepseek.com",
        "free": False,
        "supports_vision": False,
    },
    "ai21": {
        "label": "AI21 Labs",
        "icon": "💎",
        "color": "#7c3aed",
        "model": "jamba-1.5-mini",
        "prefix": [],
        "hint": "studio.ai21.com",
        "free": True,
        "supports_vision": False,
    },
    "xai": {
        "label": "xAI Grok",
        "icon": "𝕏",
        "color": "#ffffff",
        "model": "grok-beta",
        "prefix": ["xai-"],
        "hint": "console.x.ai",
        "free": False,
        "supports_vision": False,
    },
}

# ── Session state keys ─────────────────────────────────────────────────────────

_KEY_SS   = "_user_api_key"
_PROV_SS  = "_user_api_provider"
_MULTI_SS = "_multi_api_keys"   # dict: {provider: key}


# ── Provider detection ────────────────────────────────────────────────────────

def detect_provider(raw: str, hint: Optional[str] = None) -> Optional[str]:
    """
    Auto-detect provider from key prefix.
    If hint is given (provider name), validate and return it.
    Falls back to None (user must specify via hint) for ambiguous keys.
    """
    key = raw.strip()

    # Explicit hint takes priority (for e.g. DeepSeek/OpenAI ambiguity)
    if hint and hint in PROVIDER_REGISTRY:
        return hint

    # Check prefixes — specific first
    ordered = [
        "anthropic", "groq", "cerebras", "gemini",
        "openrouter", "fireworks", "replicate",
        "huggingface", "sambanova", "nvidia",
        "perplexity", "cohere", "xai",
    ]
    for prov in ordered:
        meta = PROVIDER_REGISTRY.get(prov, {})
        for prefix in meta.get("prefix", []):
            if key.startswith(prefix):
                return prov

    # OpenAI sk- prefix (after ruling out sk-ant- and sk-or-)
    if key.startswith("sk-"):
        return "openai"

    return None


# ── Primary key (single-key mode) ────────────────────────────────────────────

def set_user_key(raw: str, provider_hint: Optional[str] = None) -> str:
    """
    Store user API key after auto-detecting provider.
    Returns detected provider name. Raises ValueError if unknown.
    """
    key = raw.strip()
    provider = detect_provider(key, hint=provider_hint)
    if provider is None:
        raise ValueError(
            "Unrecognised API key format. Please select your provider from the dropdown "
            "and paste your key, or use a key with a known prefix:\n"
            "• Gemini: AIzaSy…  • Groq: gsk_…  • Cerebras: csk-…\n"
            "• OpenAI: sk-…     • Anthropic: sk-ant-…  • OpenRouter: sk-or-…\n"
            "• HuggingFace: hf_… • Perplexity: pplx-… • Fireworks: fw_…\n"
            "• NVIDIA: nvapi-… • Replicate: r8_… • Cohere: co_…\n"
            "• SambaNova: samba_… • xAI: xai-…\n\n"
            "For Mistral, Together, DeepSeek, AI21: select provider manually."
        )
    st.session_state[_KEY_SS]  = key
    st.session_state[_PROV_SS] = provider

    # Also store in multi-key dict
    _ensure_multi()
    st.session_state[_MULTI_SS][provider] = key
    return provider


def get_user_key() -> Tuple[Optional[str], Optional[str]]:
    """Return (api_key, provider) or (None, None)."""
    key  = st.session_state.get(_KEY_SS)
    prov = st.session_state.get(_PROV_SS)
    if key and prov:
        return key, prov
    return None, None


def clear_user_key() -> None:
    st.session_state.pop(_KEY_SS,  None)
    st.session_state.pop(_PROV_SS, None)


def has_key() -> bool:
    key, _ = get_user_key()
    return bool(key)


# ── Multi-key management ──────────────────────────────────────────────────────

def _ensure_multi():
    if _MULTI_SS not in st.session_state:
        st.session_state[_MULTI_SS] = {}


def set_multi_keys(keys_dict: Dict[str, str]) -> None:
    """Store multiple provider keys at once. {provider_name: api_key}"""
    _ensure_multi()
    for prov, key in keys_dict.items():
        if prov in PROVIDER_REGISTRY and key.strip():
            st.session_state[_MULTI_SS][prov] = key.strip()


def get_key_for_provider(provider: str) -> Optional[str]:
    """Retrieve stored key for a specific provider."""
    _ensure_multi()
    return st.session_state[_MULTI_SS].get(provider)


def get_all_stored_keys() -> List[Dict]:
    """Return list of all stored provider keys with metadata."""
    _ensure_multi()
    result = []
    for prov, key in st.session_state[_MULTI_SS].items():
        if key and prov in PROVIDER_REGISTRY:
            meta = PROVIDER_REGISTRY[prov]
            result.append({
                "provider": prov,
                "label": meta["label"],
                "icon": meta["icon"],
                "color": meta["color"],
                "key_masked": f"…{key[-4:]}",
                "model": meta["model"],
                "is_primary": (prov == st.session_state.get(_PROV_SS)),
            })
    return result


def set_primary_provider(provider: str) -> bool:
    """Switch primary AI provider (must have a stored key)."""
    _ensure_multi()
    key = st.session_state[_MULTI_SS].get(provider)
    if not key:
        return False
    st.session_state[_KEY_SS]  = key
    st.session_state[_PROV_SS] = provider
    return True
