import networkx as nx
from rank_bm25 import BM25Okapi
import numpy as np
import re
from collections import Counter

# gensim.summarization was removed in gensim 4.x — replaced with simple keyword extraction
def _extract_keywords(text: str, ratio: float = 0.2) -> str:
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
    def extract_concept_graph(text: str) -> nx.Graph:
        G = nx.Graph()
        lines = text.split('.')
        for line in lines[:20]:
            words = [w.strip().lower() for w in line.split() if len(w.strip()) > 4]
            for i in range(len(words) - 1):
                G.add_edge(words[i], words[i + 1])
        return G

    @staticmethod
    def rank_relevance(query: str, documents: list) -> list:
        if not documents:
            return []
        tokenized_corpus = [doc.lower().split() for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.lower().split()
        doc_scores = bm25.get_scores(tokenized_query)
        top_indices = np.argsort(doc_scores)[::-1]
        return [documents[i] for i in top_indices if doc_scores[i] > 0]

    @staticmethod
    def extract_keywords(text: str, ratio: float = 0.2) -> str:
        return _extract_keywords(text, ratio)


def humanize_text(text: str) -> str:
    return text.replace("Assistant:", "").strip()
