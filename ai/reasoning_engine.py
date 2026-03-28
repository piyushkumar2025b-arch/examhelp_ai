import networkx as nx
from gensim.summarization import keywords # Note: gensim 3.x vs 4.x keywords behavior differs
from rank_bm25 import BM25Okapi
import numpy as np

class ReasoningEngine:
    """Advanced AI Reasoning Engine for concept extraction and relevance mapping."""
    
    @staticmethod
    def extract_concept_graph(text: str) -> nx.Graph:
        """Build a graph of related concepts from the text."""
        G = nx.Graph()
        # Simplified concept extraction
        lines = text.split('.')
        for line in lines[:20]: # Limit for performance
            words = [w.strip().lower() for w in line.split() if len(w.strip()) > 4]
            for i in range(len(words)-1):
                G.add_edge(words[i], words[i+1])
        return G

    @staticmethod
    def rank_relevance(query: str, documents: list[str]) -> list[str]:
        """Rank documents by relevance using BM25."""
        if not documents: return []
        tokenized_corpus = [doc.lower().split() for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.lower().split()
        doc_scores = bm25.get_scores(tokenized_query)
        top_indices = np.argsort(doc_scores)[::-1]
        return [documents[i] for i in top_indices if doc_scores[i] > 0]

def humanize_text(text: str) -> str:
    """Post-processing to make AI text feel more natural (placeholder for now)."""
    return text.replace("Assistant:", "").strip()
