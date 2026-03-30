import urllib.request
import urllib.error
import json
import re
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

groq_key = None
gemini_key = None

try:
    with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
        content = f.read()
        groq_match = re.search(r'GROQ_API_KEY_1\s*=\s*"([^"]+)"', content)
        gemini_match = re.search(r'GEMINI_API_KEY_1\s*=\s*"([^"]+)"', content)
        if groq_match: groq_key = groq_match.group(1)
        if gemini_match: gemini_key = gemini_match.group(1)
except Exception as e:
    print(f"Error loading secrets: {e}")
    exit(1)

print(f"Testing Groq Key: {str(groq_key)[:10]}...")
url_groq = "https://api.groq.com/openai/v1/chat/completions"
data_groq = json.dumps({
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
}).encode("utf-8")
headers_groq = {
    "Authorization": f"Bearer {groq_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}
req_groq = urllib.request.Request(url_groq, data=data_groq, headers=headers_groq)
try:
    with urllib.request.urlopen(req_groq) as response:
        print("Groq Response Status:", response.status)
        print("Groq Response Body:", response.read().decode("utf-8")[:100], "...")
except urllib.error.URLError as e:
    print("Groq Request failed:", getattr(e, 'reason', e))
    if hasattr(e, 'read'):
        print("Body:", e.read().decode("utf-8"))

print(f"\nTesting Gemini Key: {str(gemini_key)[:10]}...")
url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
data_gemini = json.dumps({"contents": [{"parts": [{"text": "Hello"}]}]}).encode("utf-8")
req_gemini = urllib.request.Request(url_gemini, data=data_gemini, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req_gemini) as response:
        print("Gemini Response Status:", response.status)
        print("Gemini Response Body:", response.read().decode("utf-8")[:100], "...")
except urllib.error.URLError as e:
    print("Gemini Request failed:", getattr(e, 'reason', e))
    if hasattr(e, 'read'):
        print("Body:", e.read().decode("utf-8"))
