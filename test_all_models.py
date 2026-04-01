import json, urllib.request, ssl, os

models_to_test = [
    ('v1beta', 'gemini-1.5-flash'),
    ('v1', 'gemini-1.5-flash'),
    ('v1beta', 'gemini-1.5-flash-8b'),
    ('v1beta', 'gemini-1.5-pro'),
    ('v1beta', 'gemini-2.0-flash'),
    ('v1beta', 'gemini-2.0-flash-lite-preview-02-05'),
]

key = None
if os.path.exists('.streamlit/secrets.toml'):
    with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
        for line in f:
            if 'GEMINI_API_KEY' in line and '=' in line:
                key = line.split('=')[1].strip().strip('\'" ')
                if key.startswith('AI'):
                    break

if not key:
    print('No key found')
    exit()

print(f'Testing with key starting {key[:6]}...')

for v, m in models_to_test:
    url = f'https://generativelanguage.googleapis.com/{v}/models/{m}:generateContent?key={key}'
    body = {'contents': [{'role': 'user', 'parts': [{'text': 'hi'}]}], 'generationConfig': {'maxOutputTokens':4}}
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            print(f'SUCCESS: {m}')
    except urllib.error.HTTPError as e:
        body = ''
        try: body = e.read().decode()
        except: pass
        if e.code == 429: print(f'QUOTA/RATE_LIMIT: {m}')
        elif e.code == 404: print(f'NOT_FOUND: {m}')
        else: print(f'HTTP {e.code}: {m}')
    except Exception as e:
        print(f'ERROR: {m} - {e}')
