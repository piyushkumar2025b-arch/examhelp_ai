import sys
import json
import streamlit as st

# Setup minimal env
st.session_state = {}

from utils.query_engine import QueryEngine
from utils.app_controller import AppController
from chat.share import ChatShare
from utils.web_handler import scrape_web_page

try:
    print('1. Testing DuckDuckGo...')
    ddg = QueryEngine.search_duckduckgo('Einstein', max_results=1)
    print(f'   DDG OK: {len(ddg) > 0}')
    
    print('2. Testing Wikipedia...')
    wiki = QueryEngine.search_wikipedia('Relativity', max_results=1)
    print(f'   WIKI OK: {len(wiki) > 0}')
    
    print('3. Testing Math Eval...')
    m = AppController.evaluate_expression('10 + 20 * 2')
    print(f'   MATH OK: {m == "50"} ({m})')
    
    print('4. Testing Chat Serializer...')
    link = ChatShare.generate_share_link([{"role": "user", "content": "test"}])
    print(f'   SERIALIZER OK: {len(link) > 5}')

    print('5. Testing Web Scraper Fallback...')
    scraped, title = scrape_web_page("https://example.com")
    print(f'   SCRAPER OK: {len(scraped) > 5}')
    
    print('ALL ESSENTIAL APIS OK')
except Exception as e:
    import traceback
    traceback.print_exc()
