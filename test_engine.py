import sys
import os
from utils import ai_engine

def test():
    print("Testing ai_engine.generate()...")
    try:
        res = ai_engine.generate(prompt="Hello, are you there?", system="Be helpful.")
        print(f"SUCCESS: {res[:50]}...")
    except Exception as e:
        print(f"ULTIMATE FAILURE: {str(e)}")

if __name__ == "__main__":
    test()
