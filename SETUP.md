# ExamHelp AI v3.1 - Comprehensive Setup & Deployment Guide

Welcome to ExamHelp AI v3.1! This guide will walk you through setting up the complete infrastructure for the platform, which includes Supabase (Auth & Database), Google Cloud (Integrations), Stripe (Payments), Streamlit Cloud (App Hosting), and Cloudflare Pages (Landing Page).

Follow these steps in exactly this order for the fastest, error-free setup.

---

## Step 1: Supabase Setup (Database & Authentication)
Supabase handles user accounts, secure sessions, and profile data.

1. **Create a Project:**
   - Go to [Supabase](https://supabase.com/) and create a new project.
   - Save your **Project URL** and **anon public key** (found in Project Settings -> API).

2. **Initialize Database:**
   - Go to the **SQL Editor** in the left sidebar.
   - Click "New Query" and paste the contents of `supabase_setup.sql` (located in the root of the project).
   - Click **Run**. This will create the `user_profiles` and `study_sessions` tables, set up Row Level Security (RLS) policies, and create the auto-profile trigger.

3. **Configure Authentication:**
   - Go to Authentication -> Providers.
   - Enable **Email** provider.
   - Enable **Google** provider (you will add the Client ID and Secret in Step 2).
   - Go to Authentication -> URL Configuration.
   - Set the **Site URL** to your future Streamlit URL (e.g., `https://examhelp-ai.streamlit.app`).

---

## Step 2: Google Cloud Setup (OAuth & G-Suite Integrations)
This enables Google Sign-in, Gmail, Drive, Calendar, and Maps functionality.

1. **Create a Project:**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.

2. **Enable Required APIs:**
   - Navigate to **APIs & Services -> Library**.
   - Search for and **Enable** the following 4 APIs:
     1. Gmail API
     2. Google Drive API
     3. Google Calendar API
     4. Maps Embed API

3. **Configure OAuth Consent Screen:**
   - Go to **APIs & Services -> OAuth consent screen**.
   - Choose **External** and fill out the required app details (name, support email).
   - Add scopes (or leave default for now, Streamlit app requests scopes dynamically).
   - Add your own email as a Test User if publishing status is "Testing".

4. **Create OAuth Credentials:**
   - Go to **Credentials -> Create Credentials -> OAuth client ID**.
   - Application type: **Web application**.
   - **Authorized redirect URIs:**
     - Add your Streamlit app URL (e.g., `https://examhelp-ai.streamlit.app/`)
     - Add `http://localhost:8501/` for local testing.
   - Click Create. Copy your **Client ID** and **Client Secret**.
   - *(Go back to Supabase and paste these into the Google Provider settings!)*

5. **Get Maps API Key:**
   - Go to **Credentials -> Create Credentials -> API key**.
   - Save this key (this is your `GOOGLE_MAPS_API_KEY`).

---

## Step 3: Stripe Setup (Payments & Subscriptions)
Stripe handles user upgrades from Free to Pro/Ultra plans.

1. **Create a Stripe Account:**
   - Go to [Stripe](https://stripe.com/) and sign up or switch to Test Mode for development.

2. **Create Products & Prices:**
   - Go to **Products -> Add Product**.
   - Create the **ExamHelp Pro** plan:
     - Pricing model: Standard pricing, Recurring, Monthly.
     - Price: e.g., $9.99/month.
     - Save and copy the **Price ID** (looks like `price_xxxxxxxx`).
   - Create the **ExamHelp Ultra** plan:
     - Pricing model: Standard pricing, Recurring, Monthly.
     - Price: e.g., $19.99/month.
     - Save and copy the **Price ID**.

3. **Get API Keys:**
   - Go to **Developers -> API keys**.
   - Copy your **Publishable key** and **Secret key**.

---

## Step 4: Streamlit Cloud Deployment (The Main App)
Deploy the Python backend and UI interface.

1. **Deploy the App:**
   - Push your entire `examhelp_ai` codebase to a GitHub repository.
   - Go to [Streamlit Community Cloud](https://share.streamlit.io/) and click "New app".
   - Select your repo, branch, and set the Main file path to `app.py`.
   - Click **Deploy!**

2. **Configure Secrets:**
   - Once deployed (or while it's building), go to **App Settings -> Secrets**.
   - Paste the following TOML structure and fill in your keys:

   ```toml
   [supabase]
   url = "https://your-project.supabase.co"
   key = "your-anon-public-key"

   [google]
   client_id = "your-google-client-id.apps.googleusercontent.com"
   client_secret = "your-google-client-secret"
   redirect_uri = "https://your-app-url.streamlit.app"
   maps_api_key = "AIzaSy..."

   [stripe]
   public_key = "pk_test_..."
   secret_key = "sk_test_..."
   price_id_pro = "price_..."
   price_id_ultra = "price_..."

   [api_keys]
   # Add your LLM / other API keys here
   GROQ_API_KEY = "gsk_..."
   GEMINI_API_KEY = "AIza..."
   ```

   - Save the secrets. The app will reboot automatically.

---

## Step 5: Cloudflare Pages (The Landing Page)
Deploy the high-converting frontend marketing site.

1. **Deploy the Folder:**
   - In Cloudflare dashboard, go to **Workers & Pages -> Create application -> Pages**.
   - Connect your GitHub repo, OR choose **Direct Upload** and upload the `cloudflare/` folder.

2. **Configure Routing & Connect to App:**
   - Before uploading (or by editing in GitHub), open `cloudflare/index.html`.
   - Search for `#APP_URL#` or the Streamlit app link, and replace it with your actual Streamlit URL (e.g., `https://examhelp-ai.streamlit.app`).
   - The `_redirects` file handles routing automatically.
   - Deploy the site.

---

## Verification ✅
1. Visit your **Cloudflare landing page**. Click "Get Started" or "Login".
2. You should route to the **Streamlit Login UI**.
3. Sign up via Email or Google OAuth (OAuth redirects to Google and back).
4. Once authenticated, the sidebar should show your Profile Chip and the "Google Suite" integrations.
5. Click **Plans & Pricing** to view the Stripe integration.

**Congratulations! ExamHelp AI v3.1 is now fully live and integrated.**
