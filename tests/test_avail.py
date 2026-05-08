import json, urllib.request, ssl, os

models = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-flash-latest']
keys = []
with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    for line in f:
        if 'GEMINI_API_KEY' in line and '=' in line:
            k = line.split('=')[1].strip().strip('\'" ')
            if k.startswith('AI'): keys.append(k)

for m in models:
    works = False
    for i, k in enumerate(keys[:3]):
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}'
        req = urllib.request.Request(url, data=b'{"contents":[{"role":"user","parts":[{"text":"hi"}]}]}', headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=10, context=ssl._create_unverified_context()) as r:
                print(f'{m} -> WORKING on key {i+1}')
                works = True
                break
        except urllib.error.HTTPError as e:
            pass
    if not works: print(f'{m} -> FAIL on all 3 keys (rate limited / quota)')

