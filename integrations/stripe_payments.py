# ============================================================
# INTEGRATION REMOVED — This file has been fully commented out.
# All external service integrations, API keys, and credentials
# have been stripped for security. Do not re-enable.
# ============================================================

# """
# integrations/stripe_payments.py — Stripe Checkout integration for ExamHelp AI.
# Creates checkout sessions for Pro plan upgrades.
# Webhooks should be handled server-side (FastAPI/Flask endpoint).
# """
# 
# import os
# import httpx
# from typing import Optional
# 
# def _get_secret(key: str, default: str = "") -> str:
#     try:
#         import streamlit as st
#         return st.secrets.get(key, "") or default
#     except Exception:
#         return os.getenv(key, default)
# 
# STRIPE_SECRET_KEY      = _get_secret("STRIPE_SECRET_KEY")
# STRIPE_WEBHOOK_SECRET  = _get_secret("STRIPE_WEBHOOK_SECRET")
# STRIPE_PRO_PRICE_ID    = _get_secret("STRIPE_PRO_PRICE_ID")
# STRIPE_ANNUAL_PRICE_ID = _get_secret("STRIPE_ANNUAL_PRICE_ID")
# STRIPE_SUCCESS_URL     = _get_secret("STRIPE_SUCCESS_URL", "http://localhost:8501?payment=success")
# STRIPE_CANCEL_URL      = _get_secret("STRIPE_CANCEL_URL",  "http://localhost:8501?payment=cancel")
# 
# _STRIPE_HEADERS = lambda: {
#     "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
#     "Content-Type":  "application/x-www-form-urlencoded",
# }
# 
# 
# # ── Checkout ─────────────────────────────────────────────────────────────────
# 
# def create_checkout_session(
#     price_id: str,
#     customer_email: str,
#     mode: str = "subscription",   # "subscription" | "payment"
#     metadata: Optional[dict] = None,
# ) -> dict:
#     """Create a Stripe Checkout session and return {url, session_id}."""
#     data = {
#         "mode":                          mode,
#         "line_items[0][price]":          price_id,
#         "line_items[0][quantity]":       "1",
#         "success_url":                   STRIPE_SUCCESS_URL,
#         "cancel_url":                    STRIPE_CANCEL_URL,
#         "customer_email":                customer_email,
#         "billing_address_collection":    "auto",
#         "allow_promotion_codes":         "true",
#     }
#     if metadata:
#         for k, v in metadata.items():
#             data[f"metadata[{k}]"] = str(v)
# 
#     r = httpx.post(
#         "https://api.stripe.com/v1/checkout/sessions",
#         headers=_STRIPE_HEADERS(),
#         data=data,
#         timeout=15,
#     )
#     resp = r.json()
#     return {
#         "url":        resp.get("url", ""),
#         "session_id": resp.get("id", ""),
#         "error":      resp.get("error", {}).get("message", ""),
#     }
# 
# 
# def create_billing_portal_session(customer_id: str) -> str:
#     """Return URL to Stripe customer portal for managing subscription."""
#     r = httpx.post(
#         "https://api.stripe.com/v1/billing_portal/sessions",
#         headers=_STRIPE_HEADERS(),
#         data={
#             "customer":   customer_id,
#             "return_url": STRIPE_SUCCESS_URL,
#         },
#         timeout=15,
#     )
#     return r.json().get("url", "")
# 
# 
# def get_subscription_status(customer_email: str) -> str:
#     """Check if user has an active Pro subscription. Returns 'active'|'none'."""
#     try:
#         # Find customer
#         r = httpx.get(
#             f"https://api.stripe.com/v1/customers?email={customer_email}&limit=1",
#             headers=_STRIPE_HEADERS(),
#             timeout=10,
#         )
#         customers = r.json().get("data", [])
#         if not customers:
#             return "none"
#         cid = customers[0]["id"]
# 
#         # Check subscriptions
#         r2 = httpx.get(
#             f"https://api.stripe.com/v1/subscriptions?customer={cid}&status=active&limit=1",
#             headers=_STRIPE_HEADERS(),
#             timeout=10,
#         )
#         subs = r2.json().get("data", [])
#         return "active" if subs else "none"
#     except Exception:
#         return "none"
# 
# 
# # ── Webhook verification (for server endpoint) ───────────────────────────────
# 
# def verify_webhook(payload: bytes, sig_header: str) -> Optional[dict]:
#     """
#     Verify Stripe webhook signature. Call this in your FastAPI/Flask endpoint.
#     Returns parsed event dict or None if signature invalid.
#     """
#     import hmac
#     import hashlib
#     import time
# 
#     if not STRIPE_WEBHOOK_SECRET:
#         return None
# 
#     try:
#         parts = {
#             k: v for k, v in
#             (item.split("=", 1) for item in sig_header.split(","))
#         }
#         ts    = int(parts.get("t", 0))
#         sigs  = [v for k, v in parts.items() if k == "v1"]
# 
#         signed_payload = f"{ts}.{payload.decode()}"
#         expected = hmac.new(
#             STRIPE_WEBHOOK_SECRET.encode(),
#             signed_payload.encode(),
#             hashlib.sha256
#         ).hexdigest()
# 
#         # Allow 5-minute tolerance
#         if abs(time.time() - ts) > 300:
#             return None
# 
#         if expected in sigs:
#             import json
#             return json.loads(payload)
#     except Exception:
#         pass
#     return None
# 
# 
# # ── Plans config (used by UI) ─────────────────────────────────────────────────
# 
# PLANS = {
#     "free": {
#         "name": "Free",
#         "price": "₹0",
#         "price_usd": "$0",
#         "features": [
#             "50 AI messages / day",
#             "PDF & YouTube context",
#             "Basic personas",
#             "Standard models",
#         ],
#         "cta": "Current Plan",
#         "price_id": None,
#     },
#     "pro": {
#         "name": "Pro",
#         "price": "₹499/mo",
#         "price_usd": "$6/mo",
#         "features": [
#             "Unlimited AI messages",
#             "Priority Groq + Gemini",
#             "All 40+ personas",
#             "Gmail / Drive export",
#             "Google Calendar sync",
#             "Advanced analytics",
#             "Priority support",
#         ],
#         "cta": "Upgrade to Pro →",
#         "price_id": STRIPE_PRO_PRICE_ID,
#     },
#     "annual": {
#         "name": "Pro Annual",
#         "price": "₹3,999/yr",
#         "price_usd": "$48/yr",
#         "features": [
#             "Everything in Pro",
#             "33% savings",
#             "Early feature access",
#             "Dedicated AI quota",
#         ],
#         "cta": "Best Value →",
#         "price_id": STRIPE_ANNUAL_PRICE_ID,
#     },
# }