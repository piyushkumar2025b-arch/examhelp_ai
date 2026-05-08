import json, urllib.request, urllib.error, ssl, os
def check_key_model(key, version, model):
    base_url = f'https://generativelanguage.googleapis.com/{version}/models'
    url = f'{base_url}/{model}:generateContent?key={key}'
    body = {'contents': [{'role': 'user', 'parts': [{'text': 'OK'}]}], 'generationConfig': {'temperature':0.1, 'maxOutputTokens':4}}
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return 'WORKING'
    except urllib.error.HTTPError as e:
        body = ''
        try: body = e.read().decode()
        except: pass
        if e.code == 429:
            if 'limit: 0' in body: return 'ZERO_QUOTA'
            return 'RATE_LIMITED'
        if e.code == 404: return 'NOT_FOUND'
        if e.code == 400: return 'BAD_REQUEST'
        if e.code == 403: return 'FORBIDDEN'
        return f'HTTP_{e.code}'
    except Exception as e:
        return 'ERROR'

keys = []
if os.path.exists('.streamlit/secrets.toml'):
    with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
        for line in f:
            if 'GEMINI_API_KEY' in line and '=' in line:
                key = line.split('=')[1].strip().strip('\'" ')
                if key.startswith('AI'): keys.append(key)
if not keys:
    print('No keys found')
    exit()

models = [
    ('v1beta', 'gemini-2.5-flash'),
    ('v1beta', 'gemini-2.5-pro'),
    ('v1beta', 'gemini-2.0-flash'),
    ('v1beta', 'gemini-2.0-pro-exp-0205'),
    ('v1beta', 'gemini-2.0-flash-lite'),
    ('v1beta', 'gemini-1.5-pro'),
    ('v1', 'gemini-1.5-flash')
]

for idx, key in enumerate(keys):
    print(f'\\nKey {idx+1} ({key[:6]}...{key[-4:]}):')
    for v, m in models:
        res = check_key_model(key, v, m)
        print(f'  {m}: {res}')
