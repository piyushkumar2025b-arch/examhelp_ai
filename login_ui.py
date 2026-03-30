# ============================================================
# INTEGRATION REMOVED — This file has been fully commented out.
# All external service integrations, API keys, and credentials
# have been stripped for security. Do not re-enable.
# ============================================================

# """
# auth/login_ui.py — ExamHelp AI login screen with guest bypass
# """
# import streamlit as st
# from auth.supabase_auth import (
#     sign_in, sign_up, reset_password, save_session, is_logged_in
# )
# 
# def render_login_page() -> bool:
# 
#     # ── GUEST BYPASS ──────────────────────────────────────────────────────
#     if st.query_params.get("guest") == "1":
#         st.session_state["sb_user"]          = {"id": "guest", "email": "guest@examhelp.ai"}
#         st.session_state["sb_access_token"]  = "guest"
#         st.session_state["sb_refresh_token"] = ""
#         st.session_state["logged_in"]        = True
#         st.query_params.clear()
#         st.rerun()
# 
#     st.markdown("""
#     <style>
#     .stApp { background: linear-gradient(135deg, #0f0c29, #1a1040, #0d1b2a) !important; }
#     .stButton > button {
#         background: linear-gradient(135deg, #7c6af7, #4f8ef7) !important;
#         border: none !important; color: white !important;
#         border-radius: 10px !important; font-weight: 700 !important;
#     }
#     .guest-btn {
#         display:block; text-align:center; padding:.6rem 1rem;
#         background: rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.2);
#         border-radius:10px; color:rgba(255,255,255,0.7); text-decoration:none;
#         font-size:.85rem; margin-top:.5rem;
#     }
#     .guest-btn:hover { background:rgba(255,255,255,0.14); color:white; }
#     .stTextInput input {
#         background: rgba(255,255,255,0.07) !important;
#         border: 1px solid rgba(255,255,255,0.15) !important;
#         border-radius: 10px !important; color: #fff !important;
#     }
#     </style>
#     """, unsafe_allow_html=True)
# 
#     _, col, _ = st.columns([1, 2, 1])
#     with col:
#         st.markdown("## ⚡ ExamHelp AI")
#         st.caption("Your intelligent study companion · v3.0")
#         st.divider()
# 
#         tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Sign Up"])
# 
#         with tab1:
#             email = st.text_input("Email", key="si_email", placeholder="you@example.com")
#             pwd   = st.text_input("Password", key="si_pwd", type="password", placeholder="••••••••")
#             if st.button("Sign In →", key="si_btn", use_container_width=True):
#                 if not email or not pwd:
#                     st.error("Fill in all fields.")
#                 else:
#                     with st.spinner("Signing in…"):
#                         res = sign_in(email.strip(), pwd)
#                     if res.get("access_token"):
#                         save_session(res)
#                         st.rerun()
#                     else:
#                         st.error(res.get("error_description") or "Sign-in failed.")
# 
#             st.markdown("---")
#             st.markdown(
#                 '<a href="?guest=1" target="_self" class="guest-btn">🚀 Continue as Guest (No signup needed)</a>',
#                 unsafe_allow_html=True
#             )
# 
#         with tab2:
#             name  = st.text_input("Full Name", key="su_name", placeholder="Ada Lovelace")
#             email = st.text_input("Email", key="su_email", placeholder="you@example.com")
#             pwd   = st.text_input("Password", key="su_pwd", type="password", placeholder="min 8 chars")
#             pwd2  = st.text_input("Confirm", key="su_pwd2", type="password", placeholder="••••••••")
#             if st.button("Create Account →", key="su_btn", use_container_width=True):
#                 if not all([name, email, pwd, pwd2]):
#                     st.error("Fill in all fields.")
#                 elif pwd != pwd2:
#                     st.error("Passwords don't match.")
#                 elif len(pwd) < 8:
#                     st.error("Password must be 8+ characters.")
#                 else:
#                     with st.spinner("Creating account…"):
#                         res = sign_up(email.strip(), pwd, name.strip())
#                     if res.get("access_token"):
#                         save_session(res)
#                         st.rerun()
#                     elif res.get("id"):
#                         st.success("✅ Check your email to confirm, then sign in.")
#                     else:
#                         st.error(res.get("error_description") or "Sign-up failed.")
# 
#             st.markdown("---")
#             st.markdown(
#                 '<a href="?guest=1" target="_self" class="guest-btn">🚀 Continue as Guest (No signup needed)</a>',
#                 unsafe_allow_html=True
#             )
# 
#     return is_logged_in()