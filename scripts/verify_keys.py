import json
import urllib.request
import urllib.error
import ssl
import sys
import os

# ── Gemini Config ──────────────────────────────────────────
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
TEST_SUITE = [
    ("v1beta", "gemini-2.5-flash"),
    ("v1beta", "gemini-2.0-flash"),
    ("v1beta", "gemini-2.0-flash-lite"),
    ("v1",     "gemini-1.5-flash"),
]

def _make_ssl_context():
    try:
        return ssl._create_unverified_context()
    except Exception:
        return None

SSL_CTX = _make_ssl_context()

def check_key_model(key, version, model):
    base_url = f"https://generativelanguage.googleapis.com/{version}/models"
    url = f"{base_url}/{model}:generateContent?key={key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": "Say 'OK'"}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 5},
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            return True, "WORKING"
    except urllib.error.HTTPError as e:
        try: err_body = e.read().decode()
        except: err_body = ""
        
        if e.code == 429:
            if "limit: 0" in err_body: return False, "ZERO_QUOTA"
            return False, "RATE_LIMITED"
        if e.code == 404:
            print(f"(Body: {err_body[:100]}) ", end="")
            return False, "NOT_FOUND"
        if e.code == 400:
            if "API key not valid" in err_body: return False, "INVALID_KEY"
            return False, "BAD_REQUEST"
        if e.code == 403: return False, "FORBIDDEN"
        return False, f"HTTP_{e.code}"
    except Exception as e:
        print(f"({str(e)}) ", end="")
        return False, f"ERROR"

def main():
    print("Comprehensive Gemini Integrity Check")
    print("="*60)
    
    keys = []
    # (Rest of the loading logic is fine)
    # (Rest of the loading logic is fine)
    # (Rest of the loading logic is fine)
    
    # Try loading from .env first
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "GEMINI_API_KEY_" in line and "=" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        key = parts[1].strip().strip('"').strip("'")
                        if key.startswith("AIzaSy"):
                            keys.append(key)
    
    # If no keys found in .env, check secrets.toml
    if not keys and os.path.exists(".streamlit/secrets.toml"):
        with open(".streamlit/secrets.toml", "r", encoding="utf-8") as f:
            for line in f:
                if "GEMINI_API_KEY_" in line and "=" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        key = parts[1].strip().strip('"').strip("'")
                        if key.startswith("AIzaSy"):
                            keys.append(key)

    if not keys:
        print("No keys found in .env or .streamlit/secrets.toml")
        return

    print(f"Found {len(keys)} keys. Testing {len(TEST_SUITE)} endpoint/model combinations...\n")
    
    for i, key in enumerate(keys, 1):
        obs_key = f"{key[:6]}...{key[-4:]}"
        print(f"Key {i} ({obs_key}):")
        
        for version, model in TEST_SUITE:
            display = f"{version}/{model}"
            print(f"  - {display:30}: ", end="", flush=True)
            success, status = check_key_model(key, version, model)
            print(status)
        print("-" * 40)

if __name__ == "__main__":
    main()
