import requests
import toml
import os

try:
    secrets = toml.load('.streamlit/secrets.toml')
    groq_key = secrets.get('GROQ_API_KEY_1')
    gemini_key = secrets.get('GEMINI_API_KEY_1')
except Exception as e:
    print(f"Error loading secrets: {e}")
    exit(1)

print(f"Testing Groq Key: {groq_key[:10]}...")
headers = {
    "Authorization": f"Bearer {groq_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "llama-3.1-8b-instant",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
}
try:
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    print("Groq Response Status:", resp.status_code)
    print("Groq Response Body:", resp.text)
except Exception as e:
    print("Groq Request failed", e)

print(f"\nTesting Gemini Key: {gemini_key[:10]}...")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
try:
    resp2 = requests.post(url, headers={"Content-Type": "application/json"}, json={"contents": [{"parts": [{"text": "Hello"}]}]})
    print("Gemini Response Status:", resp2.status_code)
    print("Gemini Response Body:", resp2.text)
except Exception as e:
    print("Gemini Request failed", e)
