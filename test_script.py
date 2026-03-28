import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

print("--- Module Import Test ---")
modules = [
    "networkx",
    "gensim",
    "rank_bm25",
    "numpy",
    "unstructured",
    "pdfminer",
    "docx2txt",
    "serpapi",
    "playwright",
    "newspaper",
    "bokeh",
    "altair",
    "pydeck",
    "xgboost",
    "lightgbm",
    "annoy",
    "hnswlib",
    "passlib",
    "jose",
    "websockets"
]

for m in modules:
    try:
        __import__(m)
        print(f"✅ {m}")
    except ImportError as e:
        print(f"❌ {m}: {e}")

from ai.reasoning_engine import ReasoningEngine
print("\n--- ReasoningEngine Test ---")
try:
    G = ReasoningEngine.extract_concept_graph("Neural networks are inspired by human brains. Brains have neurons.")
    print(f"Graph nodes: {G.nodes()}")
    print("✅ ReasoningEngine works.")
except Exception as e:
    print(f"❌ ReasoningEngine failed: {e}")
