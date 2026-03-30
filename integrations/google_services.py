# ============================================================
# INTEGRATION REMOVED — This file has been fully commented out.
# All external service integrations, API keys, and credentials
# have been stripped for security. Do not re-enable.
# ============================================================

# """
# integrations/google_services.py — Gmail, Drive, Calendar, Maps
# All services flow through Google OAuth tokens stored in Supabase session.
# """
# 
# import os
# import base64
# import json
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from email.mime.base import MIMEBase
# from email import encoders
# from typing import Optional
# import httpx
# 
# def _get_secret(key: str, default: str = "") -> str:
#     try:
#         import streamlit as st
#         return st.secrets.get(key, "") or default
#     except Exception:
#         return os.getenv(key, default)
# 
# GOOGLE_CLIENT_ID     = _get_secret("GOOGLE_CLIENT_ID")
# GOOGLE_CLIENT_SECRET = _get_secret("GOOGLE_CLIENT_SECRET")
# GOOGLE_REDIRECT_URI  = _get_secret("GOOGLE_REDIRECT_URI", "http://localhost:8501")
# 
# SCOPES = " ".join([
#     "https://www.googleapis.com/auth/gmail.send",
#     "https://www.googleapis.com/auth/drive.file",
#     "https://www.googleapis.com/auth/calendar",
#     "https://www.googleapis.com/auth/userinfo.email",
#     "openid",
# ])
# 
# 
# # ── OAuth helpers ────────────────────────────────────────────────────────────
# 
# def get_google_auth_url(state: str = "examhelp") -> str:
#     """Build OAuth consent URL with all required scopes."""
#     params = (
#         f"https://accounts.google.com/o/oauth2/v2/auth"
#         f"?client_id={GOOGLE_CLIENT_ID}"
#         f"&redirect_uri={GOOGLE_REDIRECT_URI}"
#         f"&response_type=code"
#         f"&scope={SCOPES.replace(' ', '+')}"
#         f"&access_type=offline"
#         f"&prompt=consent"
#         f"&state={state}"
#     )
#     return params
# 
# 
# def exchange_code_for_tokens(code: str) -> dict:
#     """Exchange authorization code for access + refresh tokens."""
#     r = httpx.post(
#         "https://oauth2.googleapis.com/token",
#         data={
#             "code": code,
#             "client_id": GOOGLE_CLIENT_ID,
#             "client_secret": GOOGLE_CLIENT_SECRET,
#             "redirect_uri": GOOGLE_REDIRECT_URI,
#             "grant_type": "authorization_code",
#         },
#         timeout=15,
#     )
#     return r.json()
# 
# 
# def refresh_google_token(refresh_token: str) -> dict:
#     r = httpx.post(
#         "https://oauth2.googleapis.com/token",
#         data={
#             "client_id": GOOGLE_CLIENT_ID,
#             "client_secret": GOOGLE_CLIENT_SECRET,
#             "refresh_token": refresh_token,
#             "grant_type": "refresh_token",
#         },
#         timeout=15,
#     )
#     return r.json()
# 
# 
# # ── Gmail ────────────────────────────────────────────────────────────────────
# 
# class GmailService:
#     def __init__(self, access_token: str):
#         self.token = access_token
#         self._headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json",
#         }
# 
#     def send_email(
#         self,
#         to: str,
#         subject: str,
#         body: str,
#         body_html: Optional[str] = None,
#         attachment_name: str = "",
#         attachment_bytes: bytes = b"",
#     ) -> dict:
#         """Send email via Gmail API."""
#         msg = MIMEMultipart("alternative")
#         msg["to"]      = to
#         msg["subject"] = subject
# 
#         msg.attach(MIMEText(body, "plain"))
#         if body_html:
#             msg.attach(MIMEText(body_html, "html"))
# 
#         if attachment_bytes and attachment_name:
#             part = MIMEBase("application", "octet-stream")
#             part.set_payload(attachment_bytes)
#             encoders.encode_base64(part)
#             part.add_header("Content-Disposition", f'attachment; filename="{attachment_name}"')
#             msg.attach(part)
# 
#         raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
#         r = httpx.post(
#             "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
#             headers=self._headers,
#             json={"raw": raw},
#             timeout=20,
#         )
#         return r.json()
# 
#     def get_profile(self) -> dict:
#         r = httpx.get(
#             "https://gmail.googleapis.com/gmail/v1/users/me/profile",
#             headers=self._headers,
#             timeout=10,
#         )
#         return r.json()
# 
# 
# # ── Google Drive ─────────────────────────────────────────────────────────────
# 
# class DriveService:
#     def __init__(self, access_token: str):
#         self.token = access_token
#         self._auth = {"Authorization": f"Bearer {access_token}"}
# 
#     def upload_file(
#         self,
#         filename: str,
#         content: bytes,
#         mime_type: str = "application/octet-stream",
#         folder_id: Optional[str] = None,
#     ) -> dict:
#         """Upload a file to Drive, returns {id, name, webViewLink}."""
#         metadata = {"name": filename}
#         if folder_id:
#             metadata["parents"] = [folder_id]
# 
#         import io
#         r = httpx.post(
#             "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
#             headers=self._auth,
#             files={
#                 "metadata": (None, json.dumps(metadata), "application/json"),
#                 "file":     (filename, io.BytesIO(content), mime_type),
#             },
#             timeout=30,
#         )
#         return r.json()
# 
#     def create_folder(self, name: str, parent_id: Optional[str] = None) -> dict:
#         metadata = {
#             "name": name,
#             "mimeType": "application/vnd.google-apps.folder",
#         }
#         if parent_id:
#             metadata["parents"] = [parent_id]
#         r = httpx.post(
#             "https://www.googleapis.com/drive/v3/files?fields=id,name",
#             headers={**self._auth, "Content-Type": "application/json"},
#             json=metadata,
#             timeout=10,
#         )
#         return r.json()
# 
#     def list_files(self, page_size: int = 10) -> list:
#         r = httpx.get(
#             f"https://www.googleapis.com/drive/v3/files?pageSize={page_size}"
#             f"&fields=files(id,name,mimeType,modifiedTime,webViewLink)",
#             headers=self._auth,
#             timeout=10,
#         )
#         return r.json().get("files", [])
# 
# 
# # ── Google Calendar ──────────────────────────────────────────────────────────
# 
# class CalendarService:
#     def __init__(self, access_token: str):
#         self.token = access_token
#         self._headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json",
#         }
# 
#     def create_event(
#         self,
#         title: str,
#         description: str,
#         start_dt: str,   # ISO 8601 e.g. "2025-06-01T10:00:00"
#         end_dt: str,
#         timezone: str = "Asia/Kolkata",
#         calendar_id: str = "primary",
#     ) -> dict:
#         body = {
#             "summary": title,
#             "description": description,
#             "start": {"dateTime": start_dt, "timeZone": timezone},
#             "end":   {"dateTime": end_dt,   "timeZone": timezone},
#         }
#         r = httpx.post(
#             f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
#             headers=self._headers,
#             json=body,
#             timeout=10,
#         )
#         return r.json()
# 
#     def list_events(self, max_results: int = 10, calendar_id: str = "primary") -> list:
#         import datetime
#         now = datetime.datetime.utcnow().isoformat() + "Z"
#         r = httpx.get(
#             f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
#             f"?maxResults={max_results}&orderBy=startTime&singleEvents=true&timeMin={now}",
#             headers=self._headers,
#             timeout=10,
#         )
#         return r.json().get("items", [])
# 
#     def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
#         r = httpx.delete(
#             f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
#             headers=self._headers,
#             timeout=10,
#         )
#         return r.status_code == 204
# 
# 
# # ── Google Maps (Embed only — no server secret needed) ───────────────────────
# 
# def get_maps_embed_url(query: str, maps_api_key: str) -> str:
#     """Return an embed URL for Google Maps iframe."""
#     import urllib.parse
#     q = urllib.parse.quote(query)
#     return (
#         f"https://www.google.com/maps/embed/v1/search"
#         f"?key={maps_api_key}&q={q}"
#     )
# 
# 
# def get_directions_embed_url(origin: str, destination: str, maps_api_key: str) -> str:
#     import urllib.parse
#     o = urllib.parse.quote(origin)
#     d = urllib.parse.quote(destination)
#     return (
#         f"https://www.google.com/maps/embed/v1/directions"
#         f"?key={maps_api_key}&origin={o}&destination={d}"
#     )