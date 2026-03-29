"""
auth/supabase_auth.py — Supabase Auth integration for ExamHelp AI
"""

import os
import streamlit as st
from typing import Optional
import httpx

def _get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets.get(key, "") or default
    except Exception:
        return os.getenv(key, default)

SUPABASE_URL     = _get_secret("SUPABASE_URL")
SUPABASE_ANON_KEY = _get_secret("SUPABASE_ANON_KEY")

def _headers():
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    }

def _auth_headers(access_token: str) -> dict:
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


# ── Core Auth ────────────────────────────────────────────────────────────────

def sign_up(email: str, password: str, full_name: str = "") -> dict:
    r = httpx.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers=_headers(),
        json={"email": email, "password": password, "data": {"full_name": full_name}},
        timeout=10,
    )
    return r.json()


def sign_in(email: str, password: str) -> dict:
    r = httpx.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers=_headers(),
        json={"email": email, "password": password},
        timeout=10,
    )
    return r.json()


def sign_out(access_token: str) -> bool:
    try:
        httpx.post(f"{SUPABASE_URL}/auth/v1/logout", headers=_auth_headers(access_token), timeout=10)
    except Exception:
        pass
    return True


def refresh_token(refresh_tok: str) -> dict:
    r = httpx.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
        headers=_headers(),
        json={"refresh_token": refresh_tok},
        timeout=10,
    )
    return r.json()


def reset_password(email: str) -> bool:
    try:
        httpx.post(f"{SUPABASE_URL}/auth/v1/recover", headers=_headers(), json={"email": email}, timeout=10)
        return True
    except Exception:
        return False


def get_user(access_token: str) -> Optional[dict]:
    try:
        r = httpx.get(f"{SUPABASE_URL}/auth/v1/user", headers=_auth_headers(access_token), timeout=10)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


# ── Google OAuth URL ─────────────────────────────────────────────────────────

def get_google_oauth_url() -> str:
    """
    Build the Supabase Google OAuth URL.
    redirect_to must point back to the app so Supabase sends the session there.
    """
    base = _get_secret("SUPABASE_REDIRECT_URL", "http://localhost:8501")
    return (
        f"{SUPABASE_URL}/auth/v1/authorize"
        f"?provider=google"
        f"&redirect_to={base}"
        f"&scopes=openid%20email%20profile"
    )


# ── Session ──────────────────────────────────────────────────────────────────

def save_session(data: dict):
    st.session_state["sb_user"]          = data.get("user")
    st.session_state["sb_access_token"]  = data.get("access_token")
    st.session_state["sb_refresh_token"] = data.get("refresh_token")
    st.session_state["logged_in"]        = True


def clear_session():
    for k in ["sb_user", "sb_access_token", "sb_refresh_token", "logged_in"]:
        st.session_state.pop(k, None)


def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in") and st.session_state.get("sb_access_token"))


def current_user() -> Optional[dict]:
    return st.session_state.get("sb_user")


def current_token() -> Optional[str]:
    return st.session_state.get("sb_access_token")


def try_refresh():
    rt = st.session_state.get("sb_refresh_token")
    if rt:
        data = refresh_token(rt)
        if data.get("access_token"):
            save_session(data)


# ── THE REAL CALLBACK HANDLER ────────────────────────────────────────────────

def handle_supabase_callback():
    """
    After Google login, Supabase redirects back to the app with the session
    encoded as a URL hash fragment: #access_token=...&refresh_token=...
    
    Browsers don't send hash fragments to the server, so we use a JS redirect
    to convert the hash into query params (?access_token=...) that Streamlit
    can read server-side.
    
    This function checks for ?access_token= in the URL and logs the user in.
    It must be called AFTER st.markdown(HASH_REDIRECT_JS) has been rendered.
    """
    params = st.query_params
    access_token  = params.get("access_token", "")
    refresh_tok   = params.get("refresh_token", "")

    if not access_token:
        return

    # Validate token by fetching user
    user = get_user(access_token)
    if user and user.get("id"):
        st.session_state["sb_user"]          = user
        st.session_state["sb_access_token"]  = access_token
        st.session_state["sb_refresh_token"] = refresh_tok
        st.session_state["logged_in"]        = True
        st.query_params.clear()
        st.rerun()
    else:
        # Token invalid — clear URL silently
        st.query_params.clear()


# ── Profile ──────────────────────────────────────────────────────────────────

def upsert_profile(access_token: str, user_id: str, updates: dict) -> bool:
    try:
        r = httpx.post(
            f"{SUPABASE_URL}/rest/v1/user_profiles",
            headers={**_auth_headers(access_token), "Prefer": "resolution=merge-duplicates"},
            json={"id": user_id, **updates},
            timeout=10,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


def get_profile(access_token: str, user_id: str) -> Optional[dict]:
    try:
        r = httpx.get(
            f"{SUPABASE_URL}/rest/v1/user_profiles?id=eq.{user_id}&select=*",
            headers=_auth_headers(access_token),
            timeout=10,
        )
        data = r.json()
        return data[0] if data else {}
    except Exception:
        return {}
