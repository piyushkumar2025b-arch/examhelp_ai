"""
auth/login_ui.py — Beautiful glassmorphic login/signup screen for ExamHelp AI.
Renders BEFORE main app when user is not authenticated.
"""

import streamlit as st
from auth.supabase_auth import (
    sign_in, sign_up, reset_password, save_session,
    get_google_oauth_url, is_logged_in, current_user
)


# ── CSS ──────────────────────────────────────────────────────────────────────

AUTH_CSS = """
<style>
/* ── Auth page base ── */
.auth-wrapper {
  display: flex; flex-direction: column; align-items: center;
  min-height: 100vh; padding: 2rem 1rem;
  background: linear-gradient(135deg, #0f0c29 0%, #1a1040 50%, #0d1b2a 100%);
}

/* ── Floating card ── */
.auth-card {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.13);
  border-radius: 24px;
  padding: 2.5rem 2rem;
  max-width: 420px; width: 100%;
  box-shadow: 0 32px 64px rgba(0,0,0,0.4), 0 0 80px rgba(124,106,247,0.12);
}

/* ── Logo area ── */
.auth-logo {
  display: flex; align-items: center; gap: .75rem;
  justify-content: center; margin-bottom: 1.8rem;
}
.auth-logo-icon {
  width: 48px; height: 48px; border-radius: 14px;
  background: linear-gradient(135deg, #7c6af7, #4f8ef7);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8px 24px rgba(124,106,247,0.4);
}
.auth-logo-icon svg { width: 28px; height: 28px; }
.auth-brand { font-size: 1.5rem; font-weight: 800;
  background: linear-gradient(90deg, #c8b8ff, #7c6af7);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.auth-tagline { font-size: .75rem; color: rgba(255,255,255,0.45);
  text-align: center; margin-top: -.3rem; margin-bottom: 1.6rem; letter-spacing:.04em; }

/* ── Tabs ── */
.auth-tabs { display: flex; gap: .5rem; margin-bottom: 1.6rem;
  background: rgba(255,255,255,0.05); border-radius: 12px; padding: .25rem; }
.auth-tab { flex: 1; text-align: center; padding: .5rem;
  border-radius: 9px; cursor: pointer; font-size: .85rem; font-weight: 600;
  color: rgba(255,255,255,0.45); transition: all .2s; }
.auth-tab.active {
  background: linear-gradient(135deg, #7c6af7, #4f8ef7);
  color: #fff; box-shadow: 0 4px 12px rgba(124,106,247,0.35); }

/* ── Google btn ── */
.google-btn {
  display: flex; align-items: center; justify-content: center; gap: .65rem;
  width: 100%; padding: .7rem 1rem; border-radius: 12px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14);
  color: #fff; font-size: .88rem; font-weight: 600; cursor: pointer;
  text-decoration: none; transition: background .2s;
  margin-bottom: 1.2rem;
}
.google-btn:hover { background: rgba(255,255,255,0.13); }

/* ── OR divider ── */
.auth-divider {
  display: flex; align-items: center; gap: .8rem;
  margin: .8rem 0 1.2rem; color: rgba(255,255,255,0.28); font-size: .78rem;
}
.auth-divider::before, .auth-divider::after {
  content: ''; flex: 1; height: 1px;
  background: rgba(255,255,255,0.1);
}

/* ── Error / success chips ── */
.auth-error { background: rgba(255,80,80,0.12); border: 1px solid rgba(255,80,80,0.3);
  color: #ff7070; border-radius: 10px; padding: .55rem .9rem;
  font-size: .82rem; margin-bottom: .8rem; }
.auth-success { background: rgba(72,199,142,0.12); border: 1px solid rgba(72,199,142,0.3);
  color: #48c78e; border-radius: 10px; padding: .55rem .9rem;
  font-size: .82rem; margin-bottom: .8rem; }

/* ── Feature pills ── */
.feature-pills { display: flex; flex-wrap: wrap; gap: .4rem;
  justify-content: center; margin-top: 2rem; }
.feature-pill { background: rgba(124,106,247,0.12);
  border: 1px solid rgba(124,106,247,0.25); border-radius: 20px;
  padding: .3rem .75rem; font-size: .72rem; color: rgba(200,184,255,0.8); }

/* ── Footer ── */
.auth-footer { text-align: center; margin-top: 1.5rem;
  font-size: .72rem; color: rgba(255,255,255,0.25); }

/* ── Make Streamlit inputs blend in ── */
section[data-testid="stMain"] { background: transparent !important; }
.stTextInput > div > div > input {
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 10px !important; color: #fff !important;
}
.stTextInput > div > div > input:focus {
  border-color: rgba(124,106,247,0.6) !important;
  box-shadow: 0 0 0 2px rgba(124,106,247,0.18) !important;
}
.stButton > button {
  border-radius: 12px !important; font-weight: 700 !important;
  background: linear-gradient(135deg, #7c6af7, #4f8ef7) !important;
  border: none !important; color: #fff !important;
  box-shadow: 0 4px 16px rgba(124,106,247,0.35) !important;
  transition: transform .15s !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; }
</style>
"""

LOGO_SVG = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white" opacity="0.9"/>
  <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2"
    stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
  <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2"
    stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>
</svg>"""


def render_login_page() -> bool:
    """
    Renders the full-screen auth UI.
    Returns True when the user successfully authenticates (triggers main app reload).
    """

    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    # ── Card ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;justify-content:center;margin-top:2rem;">
      <div style="width:420px;max-width:100%;">
        <div class="auth-card">
          <div class="auth-logo">
            <div class="auth-logo-icon">{LOGO_SVG}</div>
            <span class="auth-brand">ExamHelp AI</span>
          </div>
          <div class="auth-tagline">Your intelligent study companion · v3.0</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Centered column ──────────────────────────────────────────────────────
    _, col, _ = st.columns([1, 2, 1])

    with col:
        # Tab state
        if "auth_tab" not in st.session_state:
            st.session_state.auth_tab = "login"

        tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Sign Up"])

        # ── SIGN IN ──────────────────────────────────────────────────────────
        with tab1:
            st.markdown("#### Welcome back")

            google_url = get_google_oauth_url()
            st.markdown(
                f'<a href="{google_url}" target="_self" class="google-btn">'
                '🌐 Continue with Google</a>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="auth-divider">or sign in with email</div>',
                        unsafe_allow_html=True)

            email_in = st.text_input("Email", placeholder="you@example.com",
                                     key="signin_email")
            pass_in  = st.text_input("Password", type="password",
                                     placeholder="••••••••", key="signin_pass")

            col_btn, col_fp = st.columns([2, 1])
            with col_btn:
                signin_btn = st.button("Sign In →", use_container_width=True,
                                       key="signin_btn")
            with col_fp:
                forgot = st.button("Forgot?", key="forgot_btn",
                                   use_container_width=True)

            if signin_btn:
                if not email_in or not pass_in:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Signing in…"):
                        result = sign_in(email_in.strip(), pass_in)
                    if result.get("access_token"):
                        save_session(result)
                        st.success("✅ Signed in! Loading…")
                        st.rerun()
                    else:
                        msg = result.get("error_description") or result.get("msg") or "Sign-in failed."
                        st.error(f"❌ {msg}")

            if forgot:
                fp_email = st.text_input("Enter your email to reset:",
                                         key="fp_email")
                if fp_email and st.button("Send Reset Email", key="send_reset"):
                    reset_password(fp_email.strip())
                    st.success("📧 Reset email sent — check your inbox.")

        # ── SIGN UP ──────────────────────────────────────────────────────────
        with tab2:
            st.markdown("#### Create account")

            google_url = get_google_oauth_url()
            st.markdown(
                f'<a href="{google_url}" target="_self" class="google-btn">'
                '🌐 Sign up with Google</a>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="auth-divider">or sign up with email</div>',
                        unsafe_allow_html=True)

            name_su  = st.text_input("Full Name", placeholder="Ada Lovelace",
                                     key="signup_name")
            email_su = st.text_input("Email", placeholder="you@example.com",
                                     key="signup_email")
            pass_su  = st.text_input("Password (min 8 chars)", type="password",
                                     placeholder="••••••••", key="signup_pass")
            pass_su2 = st.text_input("Confirm Password", type="password",
                                     placeholder="••••••••", key="signup_pass2")

            signup_btn = st.button("Create Account →", use_container_width=True,
                                   key="signup_btn")

            if signup_btn:
                if not all([name_su, email_su, pass_su, pass_su2]):
                    st.error("Please fill in all fields.")
                elif len(pass_su) < 8:
                    st.error("Password must be at least 8 characters.")
                elif pass_su != pass_su2:
                    st.error("Passwords do not match.")
                else:
                    with st.spinner("Creating account…"):
                        result = sign_up(email_su.strip(), pass_su, name_su.strip())
                    if result.get("id") or result.get("access_token"):
                        if result.get("access_token"):
                            save_session(result)
                            st.success("🎉 Account created! Loading…")
                            st.rerun()
                        else:
                            st.success("📧 Check your email to confirm, then sign in.")
                    else:
                        msg = (result.get("error_description")
                               or result.get("msg")
                               or result.get("message", "Sign-up failed."))
                        st.error(f"❌ {msg}")

        # ── Feature pills ────────────────────────────────────────────────────
        st.markdown("""
        <div class="feature-pills">
          <span class="feature-pill">📚 AI Study Chat</span>
          <span class="feature-pill">📧 Gmail Export</span>
          <span class="feature-pill">📁 Google Drive</span>
          <span class="feature-pill">📅 Calendar</span>
          <span class="feature-pill">🗺️ Maps</span>
          <span class="feature-pill">💳 Stripe</span>
        </div>
        <div class="auth-footer">
          © 2025 ExamHelp AI · Powered by Groq + Gemini · Secured by Supabase
        </div>
        """, unsafe_allow_html=True)

    return is_logged_in()
