# ============================================================
# INTEGRATION REMOVED — This file has been fully commented out.
# All external service integrations, API keys, and credentials
# have been stripped for security. Do not re-enable.
# ============================================================

# """
# auth/supabase_auth.py — Supabase Auth for ExamHelp AI
# """
# import os
# import streamlit as st
# from typing import Optional
# import httpx
# 
# def _get_secret(key: str, default: str = "") -> str:
#     try:
#         return st.secrets.get(key, "") or default
#     except Exception:
#         return os.getenv(key, default)
# 
# SUPABASE_URL      = _get_secret("SUPABASE_URL")
# SUPABASE_ANON_KEY = _get_secret("SUPABASE_ANON_KEY")
# 
# def _headers():
#     return {
#         "apikey": SUPABASE_ANON_KEY,
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
#     }
# 
# def _auth_headers(access_token: str) -> dict:
#     return {
#         "apikey": SUPABASE_ANON_KEY,
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {access_token}",
#     }
# 
# def sign_up(email: str, password: str, full_name: str = "") -> dict:
#     r = httpx.post(f"{SUPABASE_URL}/auth/v1/signup", headers=_headers(),
#         json={"email": email, "password": password, "data": {"full_name": full_name}}, timeout=10)
#     return r.json()
# 
# def sign_in(email: str, password: str) -> dict:
#     r = httpx.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", headers=_headers(),
#         json={"email": email, "password": password}, timeout=10)
#     return r.json()
# 
# def sign_out(access_token: str) -> bool:
#     try:
#         httpx.post(f"{SUPABASE_URL}/auth/v1/logout", headers=_auth_headers(access_token), timeout=10)
#     except Exception:
#         pass
#     return True
# 
# def refresh_token(refresh_tok: str) -> dict:
#     r = httpx.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token", headers=_headers(),
#         json={"refresh_token": refresh_tok}, timeout=10)
#     return r.json()
# 
# def reset_password(email: str) -> bool:
#     try:
#         httpx.post(f"{SUPABASE_URL}/auth/v1/recover", headers=_headers(),
#             json={"email": email}, timeout=10)
#         return True
#     except Exception:
#         return False
# 
# def get_user(access_token: str) -> Optional[dict]:
#     try:
#         r = httpx.get(f"{SUPABASE_URL}/auth/v1/user",
#             headers=_auth_headers(access_token), timeout=10)
#         return r.json() if r.status_code == 200 else None
#     except Exception:
#         return None
# 
# def get_google_oauth_url() -> str:
#     """
#     Supabase Google OAuth URL.
#     After Google login, Supabase redirects to redirect_to with #access_token in hash.
#     We point redirect_to to our app — the app's JS extracts the token from the hash.
#     """
#     base = _get_secret("SUPABASE_REDIRECT_URL", "http://localhost:8501")
#     return (
#         f"{SUPABASE_URL}/auth/v1/authorize"
#         f"?provider=google"
#         f"&redirect_to={base}"
#         f"&scopes=openid%20email%20profile"
#     )
# 
# def save_session(data: dict):
#     st.session_state["sb_user"]          = data.get("user")
#     st.session_state["sb_access_token"]  = data.get("access_token")
#     st.session_state["sb_refresh_token"] = data.get("refresh_token")
#     st.session_state["logged_in"]        = True
# 
# def clear_session():
#     for k in ["sb_user", "sb_access_token", "sb_refresh_token", "logged_in"]:
#         st.session_state.pop(k, None)
# 
# def is_logged_in() -> bool:
#     return bool(st.session_state.get("logged_in") and st.session_state.get("sb_access_token"))
# 
# def current_user() -> Optional[dict]:
#     return st.session_state.get("sb_user")
# 
# def current_token() -> Optional[str]:
#     return st.session_state.get("sb_access_token")
# 
# def try_refresh():
#     rt = st.session_state.get("sb_refresh_token")
#     if rt:
#         data = refresh_token(rt)
#         if data.get("access_token"):
#             save_session(data)
# 
# def handle_supabase_callback():
#     """
#     Reads ?access_token= from URL (placed there by JS after hash extraction).
#     """
#     access_token = st.query_params.get("access_token", "")
#     refresh_tok  = st.query_params.get("refresh_token", "")
#     if not access_token:
#         return
#     user = get_user(access_token)
#     if user and user.get("id"):
#         st.session_state["sb_user"]          = user
#         st.session_state["sb_access_token"]  = access_token
#         st.session_state["sb_refresh_token"] = refresh_tok
#         st.session_state["logged_in"]        = True
#         st.query_params.clear()
#         st.rerun()
#     else:
#         st.query_params.clear()
# 
# def upsert_profile(access_token: str, user_id: str, updates: dict) -> bool:
#     try:
#         r = httpx.post(f"{SUPABASE_URL}/rest/v1/user_profiles",
#             headers={**_auth_headers(access_token), "Prefer": "resolution=merge-duplicates"},
#             json={"id": user_id, **updates}, timeout=10)
#         return r.status_code in (200, 201)
#     except Exception:
#         return False
# 
# def get_profile(access_token: str, user_id: str) -> Optional[dict]:
#     try:
#         r = httpx.get(f"{SUPABASE_URL}/rest/v1/user_profiles?id=eq.{user_id}&select=*",
#             headers=_auth_headers(access_token), timeout=10)
#         data = r.json()
#         return data[0] if data else {}
#     except Exception:
#         return {}