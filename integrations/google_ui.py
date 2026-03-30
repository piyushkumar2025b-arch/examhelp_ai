# ============================================================
# INTEGRATION REMOVED — This file has been fully commented out.
# All external service integrations, API keys, and credentials
# have been stripped for security. Do not re-enable.
# ============================================================

# """
# integrations/google_ui.py — Streamlit UI panel for Gmail, Drive, Calendar, Maps
# Rendered inside the main app as a sidebar panel or modal section.
# """
# 
# import os
# import streamlit as st
# from integrations.google_services import (
#     GmailService, DriveService, CalendarService,
#     get_maps_embed_url, get_directions_embed_url,
#     get_google_auth_url, exchange_code_for_tokens,
# )
# 
# def _get_secret(key: str, default: str = "") -> str:
#     try:
#         return st.secrets.get(key, "") or default
#     except Exception:
#         return os.getenv(key, default)
# 
# MAPS_API_KEY = _get_secret("GOOGLE_MAPS_EMBED_KEY")
# 
# 
# # ── OAuth flow ───────────────────────────────────────────────────────────────
# 
# def handle_google_oauth_callback():
#     """
#     Call this early in app.py to catch the ?code= redirect from Google OAuth.
#     Stores tokens in session_state.
#     """
#     params = st.query_params
#     code  = params.get("code", "")
#     state = params.get("state", "")
# 
#     if code and state == "examhelp_google":
#         with st.spinner("Connecting Google account…"):
#             tokens = exchange_code_for_tokens(code)
#         if tokens.get("access_token"):
#             st.session_state["g_access_token"]  = tokens["access_token"]
#             st.session_state["g_refresh_token"] = tokens.get("refresh_token", "")
#             st.session_state["google_connected"] = True
#             # Clear code from URL
#             st.query_params.clear()
#             st.success("✅ Google account connected!")
#             st.rerun()
#         else:
#             st.error("Google auth failed. Please try again.")
# 
# 
# def is_google_connected() -> bool:
#     return bool(st.session_state.get("google_connected")
#                 and st.session_state.get("g_access_token"))
# 
# 
# def _g_token() -> str:
#     return st.session_state.get("g_access_token", "")
# 
# 
# # ── Connect button (shown in sidebar) ───────────────────────────────────────
# 
# def render_google_connect_button():
#     """Compact connect/disconnect button for sidebar."""
#     if is_google_connected():
#         st.markdown(
#             '<div style="background:rgba(72,199,142,0.12);border:1px solid '
#             'rgba(72,199,142,0.3);border-radius:10px;padding:.4rem .8rem;'
#             'font-size:.8rem;color:#48c78e;">✅ Google Connected</div>',
#             unsafe_allow_html=True,
#         )
#         if st.button("Disconnect Google", key="g_disconnect", use_container_width=True):
#             for k in ["g_access_token", "g_refresh_token", "google_connected"]:
#                 st.session_state.pop(k, None)
#             st.rerun()
#     else:
#         auth_url = get_google_auth_url(state="examhelp_google")
#         st.markdown(
#             f'<a href="{auth_url}" target="_self" style="display:block;text-align:center;'
#             'background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.14);'
#             'border-radius:10px;padding:.5rem;font-size:.82rem;color:#fff;'
#             'text-decoration:none;margin-bottom:.5rem;">'
#             '🔗 Connect Google Account</a>',
#             unsafe_allow_html=True,
#         )
# 
# 
# # ── Gmail send panel ─────────────────────────────────────────────────────────
# 
# def render_gmail_panel(prefill_body: str = ""):
#     """Full Gmail send UI — call from share/export sections."""
#     st.markdown("#### 📧 Send via Gmail")
# 
#     if not is_google_connected():
#         st.info("Connect your Google account first (sidebar).")
#         return
# 
#     gmail = GmailService(_g_token())
#     profile = gmail.get_profile()
#     from_email = profile.get("emailAddress", "your Gmail")
#     st.caption(f"Sending from: **{from_email}**")
# 
#     to_addr = st.text_input("To", placeholder="recipient@example.com", key="gmail_to")
#     subject = st.text_input("Subject", value="ExamHelp AI — Study Output", key="gmail_subj")
#     body    = st.text_area("Message", value=prefill_body, height=180, key="gmail_body")
# 
#     # Optional attachment
#     att_file = st.file_uploader("Attach file (optional)", key="gmail_attach",
#                                  type=["pdf", "docx", "pptx", "txt", "png", "jpg"])
# 
#     if st.button("📤 Send Email", key="gmail_send", use_container_width=True):
#         if not to_addr or not subject or not body:
#             st.error("Fill in To, Subject, and Message.")
#             return
#         att_bytes = att_file.read() if att_file else b""
#         att_name  = att_file.name  if att_file else ""
#         with st.spinner("Sending…"):
#             result = gmail.send_email(
#                 to=to_addr, subject=subject, body=body,
#                 attachment_bytes=att_bytes, attachment_name=att_name,
#             )
#         if result.get("id"):
#             st.success("✅ Email sent!")
#         else:
#             err = result.get("error", {}).get("message", "Unknown error")
#             st.error(f"❌ Send failed: {err}")
# 
# 
# # ── Drive panel ──────────────────────────────────────────────────────────────
# 
# def render_drive_panel(default_filename: str = "ExamHelp_Output.txt",
#                        default_content: bytes = b""):
#     """Google Drive upload UI."""
#     st.markdown("#### 📁 Save to Google Drive")
# 
#     if not is_google_connected():
#         st.info("Connect your Google account first (sidebar).")
#         return
# 
#     drive = DriveService(_g_token())
#     filename = st.text_input("File name", value=default_filename, key="drive_fname")
#     mime_map = {
#         "txt": "text/plain", "pdf": "application/pdf",
#         "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#         "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
#     }
#     ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
#     mime = mime_map.get(ext, "application/octet-stream")
# 
#     upload_file = st.file_uploader("Or upload a different file", key="drive_upload")
#     content = upload_file.read() if upload_file else default_content
# 
#     if st.button("☁️ Upload to Drive", key="drive_upload_btn", use_container_width=True):
#         if not content:
#             st.error("No content to upload.")
#             return
#         with st.spinner("Uploading…"):
#             result = drive.upload_file(filename, content, mime)
#         if result.get("id"):
#             link = result.get("webViewLink", "#")
#             st.success(f"✅ Uploaded! [Open in Drive]({link})")
#         else:
#             st.error(f"❌ Upload failed: {result.get('error', {}).get('message','?')}")
# 
#     # Recent files
#     with st.expander("📂 Recent Drive Files"):
#         with st.spinner("Loading…"):
#             files = drive.list_files(10)
#         if files:
#             for f in files:
#                 link = f.get("webViewLink", "#")
#                 st.markdown(f"- [{f['name']}]({link})")
#         else:
#             st.caption("No files found.")
# 
# 
# # ── Calendar panel ───────────────────────────────────────────────────────────
# 
# def render_calendar_panel():
#     """Google Calendar — view upcoming events and create study events."""
#     st.markdown("#### 📅 Google Calendar")
# 
#     if not is_google_connected():
#         st.info("Connect your Google account first (sidebar).")
#         return
# 
#     cal = CalendarService(_g_token())
# 
#     # Upcoming events
#     with st.expander("📋 Upcoming Events", expanded=True):
#         with st.spinner("Loading calendar…"):
#             events = cal.list_events(max_results=8)
#         if events:
#             for ev in events:
#                 start = (ev.get("start", {}).get("dateTime")
#                          or ev.get("start", {}).get("date", ""))[:16]
#                 name  = ev.get("summary", "Untitled")
#                 st.markdown(f"- **{name}** — `{start}`")
#         else:
#             st.caption("No upcoming events.")
# 
#     # Create study event
#     st.markdown("**Add Study Event**")
#     import datetime
#     ev_title   = st.text_input("Event title", "ExamHelp Study Session", key="cal_title")
#     ev_desc    = st.text_area("Description / notes", height=80, key="cal_desc")
#     ev_date    = st.date_input("Date", datetime.date.today(), key="cal_date")
#     c1, c2     = st.columns(2)
#     with c1: ev_stime = st.time_input("Start time", datetime.time(9, 0), key="cal_start")
#     with c2: ev_etime = st.time_input("End time",   datetime.time(10, 0), key="cal_end")
# 
#     if st.button("➕ Add to Calendar", key="cal_add", use_container_width=True):
#         start_dt = f"{ev_date}T{ev_stime.strftime('%H:%M:%S')}"
#         end_dt   = f"{ev_date}T{ev_etime.strftime('%H:%M:%S')}"
#         with st.spinner("Creating event…"):
#             result = cal.create_event(ev_title, ev_desc, start_dt, end_dt)
#         if result.get("id"):
#             link = result.get("htmlLink", "#")
#             st.success(f"✅ Event created! [Open in Calendar]({link})")
#         else:
#             err = result.get("error", {}).get("message", "?")
#             st.error(f"❌ Failed: {err}")
# 
# 
# # ── Maps panel ───────────────────────────────────────────────────────────────
# 
# def render_maps_panel():
#     """Google Maps embed — search + directions."""
#     st.markdown("#### 🗺️ Google Maps")
# 
#     if not MAPS_API_KEY:
#         st.warning("Set GOOGLE_MAPS_EMBED_KEY in .env to enable maps.")
#         return
# 
#     tab_search, tab_dir = st.tabs(["🔍 Search", "🧭 Directions"])
# 
#     with tab_search:
#         query = st.text_input("Search location", "VIT Chennai", key="map_search")
#         if query:
#             url = get_maps_embed_url(query, MAPS_API_KEY)
#             st.components.v1.iframe(url, height=380)
# 
#     with tab_dir:
#         c1, c2 = st.columns(2)
#         with c1: origin = st.text_input("From", "Chennai Central", key="map_from")
#         with c2: dest   = st.text_input("To", "VIT Chennai", key="map_to")
#         if origin and dest:
#             url = get_directions_embed_url(origin, dest, MAPS_API_KEY)
#             st.components.v1.iframe(url, height=380)