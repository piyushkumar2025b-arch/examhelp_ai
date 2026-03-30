# ExamHelp AI — Setup Guide

> ⚠️ **IMPORTANT**: All external integrations (Supabase, Stripe, Google OAuth, Cloudflare) 
> have been **permanently removed** from this project. The files are commented out and must 
> not be re-enabled. All previously exposed API keys have been revoked.

---

## Prerequisites

- Python 3.9+
- A Streamlit account (for deployment)
- New Groq and/or Gemini API keys (generate fresh ones — old ones are revoked)

---

## Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Adding New API Keys (after revoking exposed ones)

In `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY_1 = "YOUR_NEW_GROQ_KEY"
GEMINI_API_KEY_1 = "YOUR_NEW_GEMINI_KEY"
```

**Never** commit this file to git. It is already in `.gitignore`.

---

## Removed Integrations

The following integrations have been fully disabled and commented out:

| Integration | Files | Status |
|---|---|---|
| Supabase (Auth/DB) | `supabase_auth.py`, `auth/` | ❌ Removed |
| Stripe (Payments) | `integrations/stripe_*.py` | ❌ Removed |
| Google (OAuth/Maps) | `integrations/google_*.py` | ❌ Removed |
| Cloudflare Pages | `cloudflare/` | ❌ Removed |
