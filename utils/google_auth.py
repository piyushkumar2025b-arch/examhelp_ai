"""
utils/google_auth.py
Google OAuth 2.0 login for ExamHelp AI.

Setup instructions are in HOW_TO_SETUP_GOOGLE_AUTH.md

This module:
  - Builds the Google OAuth authorize URL
  - Handles the ?code= callback and exchanges for tokens
  - Fetches the user's profile (name, email, picture)
  - Stores user info in st.session_state
  - Is entirely OPTIONAL — password login still works if not configured
"""

import streamlit as st
import urllib.parse
import urllib.request
import json
import secrets
import time

# ─── Read credentials from Streamlit secrets (safe no-ops if missing) ────────
def _get_cfg():
    try:
        cid    = st.secrets.get("GOOGLE_CLIENT_ID", "")
        csec   = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
        redir  = st.secrets.get("GOOGLE_REDIRECT_URI", "")
        return cid, csec, redir
    except Exception:
        return "", "", ""

def google_oauth_configured() -> bool:
    cid, csec, redir = _get_cfg()
    return bool(cid and csec and redir)

# ─── Build the Google Login URL ───────────────────────────────────────────────
def get_google_login_url() -> str:
    cid, _, redir = _get_cfg()
    if not cid or not redir:
        return ""
    # Store a random state token to prevent CSRF
    state = secrets.token_urlsafe(16)
    st.session_state["google_oauth_state"] = state
    params = urllib.parse.urlencode({
        "client_id":     cid,
        "redirect_uri":  redir,
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "online",
        "prompt":        "select_account",
    })
    return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

# ─── Exchange code → token → user profile ────────────────────────────────────
def _exchange_code_for_token(code: str) -> dict:
    cid, csec, redir = _get_cfg()
    payload = urllib.parse.urlencode({
        "code":          code,
        "client_id":     cid,
        "client_secret": csec,
        "redirect_uri":  redir,
        "grant_type":    "authorization_code",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def _get_user_info(access_token: str) -> dict:
    req = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

# ─── Call this ONCE at the top of app.py to catch the redirect ───────────────
def handle_google_callback():
    """
    Checks st.query_params for ?code= & ?state=.
    If found and valid, exchanges for user profile and sets session state.
    Call this before any page rendering.
    """
    if not google_oauth_configured():
        return
    
    params = st.query_params
    code  = params.get("code",  "")
    state = params.get("state", "")
    
    if not code:
        return
    
    # Validate state
    expected_state = st.session_state.get("google_oauth_state", "")
    if state != expected_state:
        st.session_state["google_auth_error"] = "OAuth state mismatch — possible CSRF. Please try again."
        st.query_params.clear()
        return

    # Exchange code for token
    token_data = _exchange_code_for_token(code)
    if "error" in token_data:
        st.session_state["google_auth_error"] = f"Token exchange failed: {token_data['error']}"
        st.query_params.clear()
        return

    access_token = token_data.get("access_token", "")
    if not access_token:
        st.session_state["google_auth_error"] = "No access token received."
        st.query_params.clear()
        return

    # Fetch user profile
    user = _get_user_info(access_token)
    if "error" in user:
        st.session_state["google_auth_error"] = f"Profile fetch failed: {user['error']}"
        st.query_params.clear()
        return

    # ✅ All good — mark user as verified
    st.session_state["passcode_verified"]     = True
    st.session_state["google_user"]           = {
        "name":    user.get("name", "User"),
        "email":   user.get("email", ""),
        "picture": user.get("picture", ""),
    }
    st.session_state["google_auth_error"]     = ""
    st.session_state.pop("google_oauth_state", None)

    # Clear the ?code= params from URL
    st.query_params.clear()
    st.rerun()

# ─── Render the Google Sign-In button ─────────────────────────────────────────
def render_google_login_button():
    """
    Renders a styled Google Sign-In button.
    Returns True if clicked (redirect to Google happens via st.markdown link).
    Safe no-op if credentials not configured.
    """
    if not google_oauth_configured():
        return

    login_url = get_google_login_url()
    if not login_url:
        return

    error = st.session_state.get("google_auth_error", "")
    if error:
        st.error(f"Google login failed: {error}")

    # The button is a styled anchor — clicking it navigates to Google's consent screen
    st.markdown(f"""
    <div style="margin-top:10px;">
      <div style="
        display:flex;align-items:center;gap:0;
        font-family:'Rajdhani',sans-serif;
        font-size:12px;color:rgba(255,255,255,0.3);
        letter-spacing:3px;text-transform:uppercase;
        text-align:center;justify-content:center;
        margin-bottom:10px;
      ">
        <span style="flex:1;height:1px;background:rgba(255,255,255,0.08);display:inline-block;"></span>
        &nbsp; OR &nbsp;
        <span style="flex:1;height:1px;background:rgba(255,255,255,0.08);display:inline-block;"></span>
      </div>
      <a href="{login_url}" target="_self" style="text-decoration:none;">
        <div style="
          display:flex;align-items:center;justify-content:center;gap:12px;
          background:rgba(255,255,255,0.06);
          border:1px solid rgba(255,255,255,0.12);
          border-radius:10px;
          padding:11px 20px;
          cursor:pointer;
          transition:all 0.2s ease;
          font-family:'Rajdhani',sans-serif;
          font-size:15px;font-weight:600;
          color:rgba(255,255,255,0.85);
          letter-spacing:0.3px;
        "
        onmouseover="this.style.background='rgba(255,255,255,0.1)';this.style.borderColor='rgba(255,255,255,0.25)';"
        onmouseout="this.style.background='rgba(255,255,255,0.06)';this.style.borderColor='rgba(255,255,255,0.12)';"
        >
          <svg width="20" height="20" viewBox="0 0 48 48">
            <path fill="#4285F4" d="M44.5 20H24v8.5h11.9C34.4 33.6 29.8 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 6 1.1 8.1 3l6-6C34.6 5.1 29.6 3 24 3 12.4 3 3 12.4 3 24s9.4 21 21 21c10.9 0 20.3-7.9 20.3-21 0-1.4-.1-2.7-.3-4z"/>
            <path fill="#34A853" d="M6.3 14.7l7 5.1C15.1 16.1 19.2 13 24 13c3.1 0 6 1.1 8.1 3l6-6C34.6 5.1 29.6 3 24 3c-7.6 0-14.2 4.5-17.7 11.7z"/>
            <path fill="#FBBC05" d="M24 45c5.8 0 10.7-1.9 14.3-5.2l-6.6-5.4C29.8 36.1 27 37 24 37c-5.8 0-10.6-3.4-12.2-8.3l-6.9 5.4C8.1 40.7 15.5 45 24 45z"/>
            <path fill="#EA4335" d="M44.5 20H24v8.5h11.9c-.8 2.3-2.3 4.2-4.3 5.6l6.6 5.4C42 36.1 44.5 30.5 44.5 24c0-1.4-.1-2.7-.3-4z"/>
          </svg>
          Continue with Google
        </div>
      </a>
      <div style="
        margin-top:8px;text-align:center;
        font-size:11px;color:rgba(255,255,255,0.2);
        font-family:'Space Mono',monospace;letter-spacing:1px;
      ">Secondary option — password above still works</div>
    </div>
    """, unsafe_allow_html=True)
