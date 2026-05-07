# 🔐 How to Set Up Google Login for ExamHelp AI

## What This Does
Adds a "Continue with Google" button on the landing page.
It's **secondary** — password login still works as before.
If Google credentials aren't configured, the button simply won't appear.

---

## Step 1 — Create a Google Cloud Project

1. Go to: **https://console.cloud.google.com**
2. Click the project dropdown (top left) → **New Project**
3. Name it: `ExamHelp AI` → **Create**
4. Make sure that project is selected

---

## Step 2 — Enable Google Identity API

1. In the left menu → **APIs & Services → Library**
2. Search for: `Google Identity` or `People API`
3. Click **"Google People API"** → **Enable**
4. Also search and enable **"OAuth2 API"** (it may already be on)

---

## Step 3 — Create OAuth 2.0 Credentials

1. In left menu → **APIs & Services → Credentials**
2. Click **+ CREATE CREDENTIALS → OAuth client ID**
3. If prompted to configure consent screen first:
   - Click **Configure Consent Screen**
   - Choose **External** → **Create**
   - App name: `ExamHelp AI`
   - User support email: your Gmail
   - Developer contact: your Gmail
   - Click **Save and Continue** through all steps
   - On the **Scopes** step, add:
     - `openid`
     - `email`
     - `profile`
   - On the **Test users** step, add your own Gmail (so it works before publishing)
   - Click **Back to Dashboard**
4. Now go back to **Credentials → + CREATE CREDENTIALS → OAuth client ID**
5. Application type: **Web application**
6. Name: `ExamHelp Web`
7. Under **Authorized redirect URIs**, click **+ ADD URI** and add:

   **For local dev:**
   ```
   http://localhost:8501
   ```

   **For Streamlit Cloud:**
   ```
   https://YOUR-APP-NAME.streamlit.app
   ```
   Replace `YOUR-APP-NAME` with your actual Streamlit Cloud app URL.

8. Click **Create**
9. A popup shows your **Client ID** and **Client Secret** — **copy both**

---

## Step 4 — Add Credentials to Streamlit Secrets

### Local development (`.streamlit/secrets.toml`):
```toml
GOOGLE_CLIENT_ID     = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "GOCSPX-your-secret-here"
GOOGLE_REDIRECT_URI  = "http://localhost:8501"
```

### Streamlit Cloud deployment:
1. Go to your app on **share.streamlit.io**
2. Click **Settings → Secrets**
3. Add:
```toml
GOOGLE_CLIENT_ID     = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "GOCSPX-your-secret-here"
GOOGLE_REDIRECT_URI  = "https://your-app.streamlit.app"
```

---

## Step 5 — Deploy / Restart

- Local: restart `streamlit run app.py`
- Cloud: it auto-deploys when you push

The Google button will appear automatically once the secrets are set.
If secrets are missing, the button silently hides itself — no errors.

---

## How It Works (Flow)

```
User clicks "Continue with Google"
    ↓
Redirected to Google's consent screen
    ↓
User picks their Google account
    ↓
Google redirects back to your app with ?code=...
    ↓
App exchanges code for access token (server-side, secure)
    ↓
App fetches user's name, email, profile picture
    ↓
passcode_verified = True  ← same flag as password login
User enters the app normally
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `redirect_uri_mismatch` | The URI in Google Console must **exactly** match `GOOGLE_REDIRECT_URI` in secrets (no trailing slash) |
| `Access blocked: app not verified` | You're in test mode — add your Gmail as a test user in the consent screen |
| Button doesn't appear | Check that all 3 secrets are set and non-empty |
| `OAuth state mismatch` | User refreshed mid-flow — just click the button again |

---

## Security Notes

- Client Secret is **never** exposed to the browser — the token exchange happens server-side in Python
- State token prevents CSRF attacks
- No user data is stored permanently — only kept in `st.session_state` for the session
