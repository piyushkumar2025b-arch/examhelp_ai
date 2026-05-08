import json, urllib.request, ssl, os
with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    key = None
    for line in f:
        if 'GEMINI_API_KEY' in line and '=' in line:
            key = line.split('=')[1].strip().strip('\'" ')
            if key.startswith('AI'): break

if not key: exit()

url = f'https://generativelanguage.googleapis.com/v1beta/models?key={key}'
ctx = ssl._create_unverified_context()
try:
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read().decode())
        models = [m['name'].replace('models/', '') for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        print('Available models:', ', '.join(models))
except Exception as e:
    print('Error:', e)
