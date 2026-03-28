"""plugin_registry.py — High-Signal Modular API Service Registry.

This module maps educational domains to specific high-value API providers.
It allows the system to scale to 60+ APIs by loading only what is needed.
"""

# ==============================
# API DOMAIN MAP (60+ CAPACITY)
# ==============================
PLUGIN_REGISTRY = {
    # 📚 1. KNOWLEDGE & SEARCH
    "knowledge": ["wikipedia", "duckduckgo", "google_search", "wikidata", "encyclopedia_britannica"],
    
    # 🎓 2. COURSES & ACADEMY
    "courses": ["khan_academy", "coursera", "mit_ocw", "stanford_online", "edx"],
    
    # 📖 3. LITERATURE & BOOKS
    "literature": ["google_books", "open_library", "gutenberg", "internet_archive"],
    
    # 🧪 4. SCIENCE & RESEARCH
    "science": ["arxiv", "pubmed", "crossref", "semantic_scholar", "biorxiv"],
    
    # 🧮 5. COMPUTATION & LOGIC
    "math": ["wolfram_alpha", "sympy", "mathjs", "scipy"],
    
    # 🌍 6. LEXICON & LANGUAGE
    "language": ["dictionary_api", "wordnik", "oxford", "merriam_webster", "datamuse"],
    
    # 🧑💻 7. COMPETITIVE CODING
    "contests": ["codeforces", "atcoder", "leetcode", "codechef"],
    
    # 🖼️ 8. VISUAL & MULTIMEDIA
    "visual": ["unsplash", "pexels", "pixabay", "wikimedia_commons"],
    
    # 📄 9. GENERATORS (LOCAL)
    "generators": ["reportlab_pdf", "pptx_slide", "docx_word", "markdown_html"]
}

def get_best_provider(domain: str) -> str:
    """Returns the primary active provider for a domain."""
    return PLUGIN_REGISTRY.get(domain, ["unknown"])[0]

def get_substitutes(domain: str) -> list:
    """Returns fallback providers if the primary is down/rate-limited."""
    return PLUGIN_REGISTRY.get(domain, [])[1:]
