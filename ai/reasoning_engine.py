"""reasoning_engine.py — Concept extraction and relevance ranking."""

import re
from collections import Counter

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    nx = None
    HAS_NX = False

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    BM25Okapi = None
    HAS_BM25 = False

try:
    import numpy as np
    HAS_NP = True
except ImportError:
    np = None
    HAS_NP = False


def _extract_keywords(text: str, ratio: float = 0.2) -> str:
    """Extract keywords using simple frequency analysis."""
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    stopwords = {'this', 'that', 'with', 'from', 'they', 'have', 'been', 'were',
                 'will', 'would', 'could', 'should', 'their', 'there', 'about',
                 'which', 'when', 'what', 'your', 'also', 'into', 'more', 'than'}
    filtered = [w for w in words if w not in stopwords]
    count = Counter(filtered)
    n = max(1, int(len(count) * ratio))
    return ' '.join([w for w, _ in count.most_common(n)])


class ReasoningEngine:
    """Advanced AI Reasoning Engine for concept extraction and relevance mapping."""

    @staticmethod
    def extract_concept_graph(text: str):
        """Extract a concept graph. Returns nx.Graph or None if networkx unavailable."""
        if not HAS_NX:
            return None
        G = nx.Graph()
        lines = text.split('.')
        for line in lines[:20]:
            words = [w.strip().lower() for w in line.split() if len(w.strip()) > 4]
            for i in range(len(words) - 1):
                G.add_edge(words[i], words[i + 1])
        return G

    @staticmethod
    def rank_relevance(query: str, documents: list) -> list:
        """Rank documents by relevance to query using BM25 or fallback."""
        if not documents:
            return []

        # BM25 ranking if available
        if HAS_BM25 and HAS_NP:
            try:
                tokenized_corpus = [doc.lower().split() for doc in documents]
                bm25 = BM25Okapi(tokenized_corpus)
                tokenized_query = query.lower().split()
                doc_scores = bm25.get_scores(tokenized_query)
                top_indices = np.argsort(doc_scores)[::-1]
                return [documents[i] for i in top_indices if doc_scores[i] > 0]
            except Exception:
                pass

        # Keyword overlap fallback
        query_terms = set(re.findall(r'\b\w{4,}\b', query.lower()))
        scored = []
        for doc in documents:
            doc_terms = set(re.findall(r'\b\w{4,}\b', doc.lower()))
            score = len(query_terms & doc_terms)
            if score > 0:
                scored.append((score, doc))
        scored.sort(reverse=True)
        return [doc for _, doc in scored]

    @staticmethod
    def extract_keywords(text: str, ratio: float = 0.2) -> str:
        return _extract_keywords(text, ratio)


def humanize_text(text: str) -> str:
    return text.replace("Assistant:", "").strip()
