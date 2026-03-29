"""
auth/login_ui.py — ExamHelp AI login screen
"""
import streamlit as st
import streamlit.components.v1 as components
from auth.supabase_auth import (
    sign_in, sign_up, reset_password, save_session,
    get_google_oauth_url, is_logged_in, handle_supabase_callback
)

# This JS runs in the Streamlit app page.
# When Supabase redirects back with #access_token in the URL hash,
# this script extracts it and puts it in the URL as ?access_token=
# so Python (Streamlit) can read it on the next render cycle.
# It uses window.parent because components.html() runs inside an iframe.
HASH_TO_PARAM_JS = """
<script>
(function() {
    function extractAndRedirect(win) {
        var hash = win.location.hash;
        if (!hash || hash.indexOf('access_token') === -1) return;
        var params = new URLSearchParams(hash.replace(/^#/, ''));
        var at = params.get('access_token');
        var rt = params.get('refresh_token') || '';
        if (at) {
            win.location.replace(
                win.location.pathname +
                '?access_token=' + encodeURIComponent(at) +
                '&refresh_token=' + encodeURIComponent(rt)
            );
        }
    }
    // Try parent window first (we're inside an iframe)
    try { extractAndRedirect(window.parent); } catch(e) {}
    // Also try current window as fallback
    try { extractAndRedirect(window); } catch(e) {}
})();
</script>
"""

AUTH_CSS = """
<style>
.stApp { background: linear-gradient(135deg, #0f0c29, #1a1040, #0d1b2a) !important; }
.auth-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 24px; padding: 2rem;
    max-width: 420px; margin: 1rem auto;
    box-shadow: 0 32px 64px rgba(0,0,0,0.4);
}
.auth-brand {
    font-size: 1.5rem; font-weight: 800; text-align: center;
    background: linear-gradient(90deg, #c8b8ff, #7c6af7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: .3rem;
}
.auth-tagline { text-align:center; color:rgba(255,255,255,0.4); font-size:.8rem; margin-bottom:1.5rem; }
.google-btn-disabled {
    display: flex; align-items: center; justify-content: center; gap: .6rem;
    width: 100%; padding: .75rem; border-radius: 12px; margin-bottom: 0.4rem;
    background: rgba(200,200,200,0.12); color: rgba(255,255,255,0.3); font-weight: 600; font-size: .9rem;
    text-decoration: none; border: 1px solid rgba(255,255,255,0.08);
    cursor: not-allowed; pointer-events: none;
}
.construction-badge {
    display: flex; align-items: center; justify-content: center; gap: .4rem;
    font-size: .72rem; color: #f0a500; background: rgba(240,165,0,0.1);
    border: 1px solid rgba(240,165,0,0.3); border-radius: 8px;
    padding: .3rem .7rem; margin-bottom: 1rem; text-align: center;
}
.guest-btn {
    display: flex; align-items: center; justify-content: center; gap: .6rem;
    width: 100%; padding: .85rem; border-radius: 12px; margin-top: 1rem;
    background: linear-gradient(135deg, rgba(124,106,247,0.25), rgba(79,142,247,0.25));
    color: #c8b8ff; font-weight: 700; font-size: .95rem;
    border: 1.5px solid rgba(124,106,247,0.5);
    cursor: pointer; text-align: center; letter-spacing: .02em;
    box-shadow: 0 0 18px rgba(124,106,247,0.15);
}
.divider {
    display:flex; align-items:center; gap:.6rem; margin:.5rem 0 1rem;
    color:rgba(255,255,255,0.3); font-size:.78rem;
}
.divider::before,.divider::after { content:''; flex:1; height:1px; background:rgba(255,255,255,0.1); }
.or-divider {
    display:flex; align-items:center; gap:.6rem; margin:.8rem 0;
    color:rgba(255,255,255,0.25); font-size:.75rem;
}
.or-divider::before,.or-divider::after { content:''; flex:1; height:1px; background:rgba(255,255,255,0.08); }
.stTextInput input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important; color: #fff !important;
}
.stButton > button {
    background: linear-gradient(135deg, #7c6af7, #4f8ef7) !important;
    border: none !important; color: white !important;
    border-radius: 10px !important; font-weight: 700 !important;
    width: 100%;
}
</style>
"""

GOOGLE_ICON = """<svg width="20" height="20" viewBox="0 0 18 18">
<path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
<path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
<path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
<path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.3z"/>
</svg>"""


def render_login_page() -> bool:

    # ── STEP 1: inject JS to convert hash → query param ──────────────────
    components.html(HASH_TO_PARAM_JS, height=0)

    # ── STEP 2: if token now in query params, log the user in ─────────────
    handle_supabase_callback()

    # ── STEP 2b: Guest bypass — set flag and rerun ────────────────────────
    if st.session_state.get("_guest_bypass"):
        return True

    # ── STEP 3: render login UI ───────────────────────────────────────────
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div class="auth-card">
            <div class="auth-brand">⚡ ExamHelp AI</div>
            <div class="auth-tagline">Your intelligent study companion · v3.0</div>
        </div>""", unsafe_allow_html=True)

        # ── Guest / Direct Access bypass button ───────────────────────────
        st.markdown('<div class="or-divider">quick access</div>', unsafe_allow_html=True)
        if st.button("⚡ Enter Without Login  →  Direct Access", key="guest_btn", use_container_width=True):
            st.session_state["_guest_bypass"] = True
            st.session_state["_guest_user"] = True
            st.rerun()
        st.markdown('<div class="or-divider">or sign in below</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Sign Up"])

        with tab1:
            # Google — disabled, under construction
            st.markdown(
                f'<div class="google-btn-disabled">'
                f'{GOOGLE_ICON} Continue with Google</div>'
                f'<div class="construction-badge">🚧 Google Sign-In is currently under construction and unavailable</div>',
                unsafe_allow_html=True
            )
            st.markdown('<div class="divider">or use email</div>', unsafe_allow_html=True)
            email = st.text_input("Email", key="si_email", placeholder="you@example.com")
            pwd   = st.text_input("Password", key="si_pwd", type="password", placeholder="••••••••")
            if st.button("Sign In →", key="si_btn"):
                if not email or not pwd:
                    st.error("Fill in all fields.")
                else:
                    with st.spinner("Signing in…"):
                        res = sign_in(email.strip(), pwd)
                    if res.get("access_token"):
                        save_session(res)
                        st.rerun()
                    else:
                        st.error(res.get("error_description") or res.get("msg") or "Sign-in failed.")

        with tab2:
            # Google — disabled, under construction
            st.markdown(
                f'<div class="google-btn-disabled">'
                f'{GOOGLE_ICON} Sign up with Google</div>'
                f'<div class="construction-badge">🚧 Google Sign-Up is currently under construction and unavailable</div>',
                unsafe_allow_html=True
            )
            st.markdown('<div class="divider">or use email</div>', unsafe_allow_html=True)
            name  = st.text_input("Full Name", key="su_name", placeholder="Ada Lovelace")
            email = st.text_input("Email", key="su_email", placeholder="you@example.com")
            pwd   = st.text_input("Password", key="su_pwd", type="password", placeholder="min 8 chars")
            pwd2  = st.text_input("Confirm", key="su_pwd2", type="password", placeholder="••••••••")
            if st.button("Create Account →", key="su_btn"):
                if not all([name, email, pwd, pwd2]):
                    st.error("Fill in all fields.")
                elif pwd != pwd2:
                    st.error("Passwords don't match.")
                elif len(pwd) < 8:
                    st.error("Password must be 8+ characters.")
                else:
                    with st.spinner("Creating account…"):
                        res = sign_up(email.strip(), pwd, name.strip())
                    if res.get("access_token"):
                        save_session(res)
                        st.rerun()
                    elif res.get("id"):
                        st.success("✅ Check your email to confirm, then sign in.")
                    else:
                        st.error(res.get("error_description") or res.get("msg") or "Sign-up failed.")

    return is_logged_in()
