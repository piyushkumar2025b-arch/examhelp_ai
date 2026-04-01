import urllib.request, ssl, sys, re, json
import time

def test_model():
    with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
        keys = re.findall(r'GEMINI_API_KEY_\d+\s*=\s*["\']([^"\']+)', f.read())
    
    if not keys: return
    
    for k in keys:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={k}'
        body = {'contents': [{'role': 'user', 'parts': [{'text': 'OK'}]}], 'generationConfig': {'temperature':0.1, 'maxOutputTokens':4}}
        data = json.dumps(body).encode()
        try:
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
                print(f"Key {k[:6]} SUCCESS")
                return
        except urllib.error.HTTPError as e:
            try: err = e.read().decode()
            except: err = str(e)
            print(f"Key {k[:6]} ERR: {err.strip()}")
        except Exception as e:
            print(f"Key {k[:6]} ERR: {e}")
test_model()
