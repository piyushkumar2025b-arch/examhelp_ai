"""
auth/login_ui.py — Login/signup screen for ExamHelp AI.
"""

import streamlit as st
import streamlit.components.v1 as components
from auth.supabase_auth import (
    sign_in, sign_up, reset_password, save_session,
    get_google_oauth_url, is_logged_in, current_user,
    handle_supabase_callback
)

# ── CRITICAL: JS that converts URL hash → query params ───────────────────────
# Supabase returns: https://yourapp.com/#access_token=xxx&refresh_token=yyy
# Streamlit CANNOT read hash fragments (they never reach the server).
# This JS detects the hash and redirects to: ?access_token=xxx&refresh_token=yyy
# which Streamlit CAN read. This must be injected BEFORE handle_supabase_callback().

HASH_REDIRECT_JS = """
<script>
(function() {
    // components.html runs inside an iframe, so we use window.parent to access the real page
    var targetWindow = window.parent || window;
    var hash = targetWindow.location.hash;
    if (hash && hash.indexOf('access_token') !== -1) {
        var params = new URLSearchParams(hash.replace(/^#/, ''));
        var at = params.get('access_token');
        var rt = params.get('refresh_token') || '';
        if (at) {
            var newUrl = targetWindow.location.pathname + '?access_token=' + encodeURIComponent(at) + '&refresh_token=' + encodeURIComponent(rt);
            targetWindow.location.replace(newUrl);
        }
    }
})();
</script>
"""

AUTH_CSS = """
<style>
section[data-testid="stMain"] { background: linear-gradient(135deg, #0f0c29 0%, #1a1040 50%, #0d1b2a 100%) !important; }
.auth-card {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.13);
  border-radius: 24px;
  padding: 2.5rem 2rem;
  max-width: 420px; width: 100%;
  box-shadow: 0 32px 64px rgba(0,0,0,0.4);
  margin: 2rem auto;
}
.auth-brand { font-size: 1.5rem; font-weight: 800;
  background: linear-gradient(90deg, #c8b8ff, #7c6af7);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.auth-tagline { font-size: .75rem; color: rgba(255,255,255,0.45);
  text-align: center; margin-bottom: 1.6rem; }
.google-btn {
  display: flex; align-items: center; justify-content: center; gap: .65rem;
  width: 100%; padding: .75rem 1rem; border-radius: 12px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.2);
  color: #fff; font-size: .9rem; font-weight: 600; cursor: pointer;
  text-decoration: none; transition: background .2s; margin-bottom: 1.2rem;
}
.google-btn:hover { background: rgba(255,255,255,0.15); color: #fff; }
.auth-divider {
  display: flex; align-items: center; gap: .8rem;
  margin: .5rem 0 1rem; color: rgba(255,255,255,0.3); font-size: .78rem;
}
.auth-divider::before, .auth-divider::after {
  content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.1);
}
.stTextInput > div > div > input {
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 10px !important; color: #fff !important;
}
.stButton > button {
  border-radius: 12px !important; font-weight: 700 !important;
  background: linear-gradient(135deg, #7c6af7, #4f8ef7) !important;
  border: none !important; color: #fff !important;
}
.auth-footer { text-align: center; margin-top: 1.5rem;
  font-size: .72rem; color: rgba(255,255,255,0.25); }
</style>
"""

LOGO_SVG = """
<svg viewBox="0 0 24 24" width="32" height="32" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white" opacity="0.9"/>
  <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
  <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>
</svg>"""

GOOGLE_SVG = """<svg width="18" height="18" viewBox="0 0 18 18"><path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"/><path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 0 1-7.18-2.54H1.83v2.07A8 8 0 0 0 8.98 17z"/><path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 0 1 0-3.04V5.41H1.83a8 8 0 0 0 0 7.18l2.67-2.07z"/><path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 0 0 1.83 5.4L4.5 7.49a4.77 4.77 0 0 1 4.48-3.3z"/></svg>"""


def render_login_page() -> bool:
    """
    Step 1: Inject JS to convert URL hash → query params (runs in browser).
    Step 2: handle_supabase_callback() reads ?access_token= and logs user in.
    Step 3: If not logged in, show the login UI.
    """

    # STEP 1 — Inject JS hash converter using components.html (executes properly, not sandboxed)
    components.html(HASH_REDIRECT_JS, height=0)

    # STEP 2 — Check if Supabase just redirected back with a token
    handle_supabase_callback()

    # STEP 3 — If still not logged in, show the login form
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="auth-card">
      <div style="display:flex;align-items:center;gap:.75rem;justify-content:center;margin-bottom:.5rem;">
        <div style="width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,#7c6af7,#4f8ef7);
          display:flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(124,106,247,0.4);">
          {LOGO_SVG}
        </div>
        <span class="auth-brand">ExamHelp AI</span>
      </div>
      <div class="auth-tagline">Your intelligent study companion · v3.0</div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Sign Up"])

        # ── SIGN IN ──────────────────────────────────────────────────────────
        with tab1:
            google_url = get_google_oauth_url()
            st.markdown(
                f'<a href="{google_url}" target="_self" class="google-btn">'
                f'{GOOGLE_SVG} &nbsp; Continue with Google</a>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="auth-divider">or sign in with email</div>', unsafe_allow_html=True)

            email_in = st.text_input("Email", placeholder="you@example.com", key="signin_email")
            pass_in  = st.text_input("Password", type="password", placeholder="••••••••", key="signin_pass")

            col_btn, col_fp = st.columns([2, 1])
            with col_btn:
                signin_btn = st.button("Sign In →", use_container_width=True, key="signin_btn")
            with col_fp:
                forgot = st.button("Forgot?", key="forgot_btn", use_container_width=True)

            if signin_btn:
                if not email_in or not pass_in:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Signing in…"):
                        result = sign_in(email_in.strip(), pass_in)
                    if result.get("access_token"):
                        save_session(result)
                        st.success("✅ Signed in!")
                        st.rerun()
                    else:
                        msg = result.get("error_description") or result.get("msg") or "Sign-in failed."
                        st.error(f"❌ {msg}")

            if forgot:
                fp_email = st.text_input("Enter your email to reset:", key="fp_email")
                if fp_email and st.button("Send Reset Email", key="send_reset"):
                    reset_password(fp_email.strip())
                    st.success("📧 Reset email sent — check your inbox.")

        # ── SIGN UP ──────────────────────────────────────────────────────────
        with tab2:
            google_url = get_google_oauth_url()
            st.markdown(
                f'<a href="{google_url}" target="_self" class="google-btn">'
                f'{GOOGLE_SVG} &nbsp; Sign up with Google</a>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="auth-divider">or sign up with email</div>', unsafe_allow_html=True)

            name_su  = st.text_input("Full Name", placeholder="Ada Lovelace", key="signup_name")
            email_su = st.text_input("Email", placeholder="you@example.com", key="signup_email")
            pass_su  = st.text_input("Password (min 8 chars)", type="password", placeholder="••••••••", key="signup_pass")
            pass_su2 = st.text_input("Confirm Password", type="password", placeholder="••••••••", key="signup_pass2")

            if st.button("Create Account →", use_container_width=True, key="signup_btn"):
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
                            st.success("🎉 Account created!")
                            st.rerun()
                        else:
                            st.success("📧 Check your email to confirm, then sign in.")
                    else:
                        msg = result.get("error_description") or result.get("msg") or result.get("message", "Sign-up failed.")
                        st.error(f"❌ {msg}")

        st.markdown("""
        <div class="auth-footer">© 2025 ExamHelp AI · Powered by Groq + Gemini · Secured by Supabase</div>
        """, unsafe_allow_html=True)

    return is_logged_in()
