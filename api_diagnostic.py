import sys
import os
import requests
import json

# Add project root to path to test local modules
sys.path.append(os.getcwd())

from utils.query_engine import QueryEngine
from utils import key_manager
from dotenv import load_dotenv

load_dotenv()

def test_api(name, func, *args):
    print(f"Testing {name}...")
    try:
        res = func(*args)
        if res:
            print(f"✅ {name} working. Sample: {str(res)[:100]}...")
            return True
        else:
            print(f"⚠️ {name} returned empty but no error.")
            return True # Might just be no results for specific query
    except Exception as e:
        print(f"❌ {name} FAILED: {e}")
        return False

def run_diagnostic():
    print("=== ExamHelp AI API Diagnostic ===\n")
    
    results = []
    
    # 1. Groq Keys
    keys = key_manager._load_keys()
    print(f"Found {len(keys)} Groq API Keys.")
    results.append(len(keys) > 0)

    # 2. Wikipedia
    results.append(test_api("Wikipedia", QueryEngine.search_wikipedia, "Quantum Physics"))

    # 3. DuckDuckGo
    results.append(test_api("DuckDuckGo", QueryEngine.search_duckduckgo, "Latest AI news"))

    # 4. Google Books
    results.append(test_api("Google Books", QueryEngine.search_google_books, "Python Programming"))

    # 5. OpenLibrary
    results.append(test_api("OpenLibrary", QueryEngine.search_open_library, "Lord of the Rings"))

    # 6. ArXiv
    results.append(test_api("ArXiv", QueryEngine.search_arxiv, "Transformer Models"))

    # 7. StackOverflow
    results.append(test_api("StackOverflow", QueryEngine.search_stack_overflow, "python list comprehension"))

    # 8. Dictionary
    results.append(test_api("Dictionary", QueryEngine.search_dictionary, "intelligence"))

    # 9. BioRxiv
    results.append(test_api("BioRxiv", QueryEngine.search_biorxiv, "CRISPR"))

    # 10. Weather (wttr.in)
    results.append(test_api("Weather (wttr.in)", QueryEngine.get_weather, "London"))

    # 11. WorldTime
    results.append(test_api("WorldTime", QueryEngine.get_world_time, "London"))

    print("\n=== Diagnostic Complete ===")
    if all(results):
        print("ALL SYSTEMS OPERATIONAL 🟢")
    else:
        print("SOME SYSTEMS DEGRADED ⚠️ Check logs above.")

if __name__ == "__main__":
    run_diagnostic()
