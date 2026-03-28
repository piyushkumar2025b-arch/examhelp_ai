"""vector_store.py — RAG-ready in-memory vector store using FAISS + sentence-transformers.
Gracefully degrades to keyword search if dependencies are not available.
"""

from __future__ import annotations
import re
from typing import List

try:
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer
    _HAS_VECTOR = True
except ImportError:
    np = None
    faiss = None
    SentenceTransformer = None
    _HAS_VECTOR = False


class VectorStore:
    """Dual-mode vector/keyword store for study material retrieval."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.documents: List[str] = []
        self.index = None
        self.model = None

        if _HAS_VECTOR:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:
                pass  # Fall back to keyword mode

    def add_documents(self, docs: List[str]):
        """Chunk and index documents."""
        # Chunk into ~300-word segments
        for doc in docs:
            words = doc.split()
            for i in range(0, len(words), 300):
                chunk = " ".join(words[i:i + 300])
                if chunk.strip():
                    self.documents.append(chunk)

        if self.model and _HAS_VECTOR and self.documents:
            try:
                embeddings = self.model.encode(self.documents, show_progress_bar=False)
                embeddings = np.array(embeddings).astype("float32")
                if self.index is None:
                    dim = embeddings.shape[1]
                    self.index = faiss.IndexFlatL2(dim)
                self.index.add(embeddings)
            except Exception:
                self.index = None  # Fall back to keyword mode

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Return top-k relevant document chunks."""
        if not self.documents:
            return []

        # Vector search
        if self.model and self.index is not None and _HAS_VECTOR:
            try:
                q_emb = self.model.encode([query], show_progress_bar=False)
                q_emb = np.array(q_emb).astype("float32")
                distances, indices = self.index.search(q_emb, min(top_k, len(self.documents)))
                return [self.documents[i] for i in indices[0] if 0 <= i < len(self.documents)]
            except Exception:
                pass

        # Keyword fallback — simple BM25-like term overlap
        query_terms = set(re.findall(r'\b\w{4,}\b', query.lower()))
        scored = []
        for doc in self.documents:
            doc_terms = set(re.findall(r'\b\w{4,}\b', doc.lower()))
            score = len(query_terms & doc_terms)
            if score > 0:
                scored.append((score, doc))
        scored.sort(reverse=True)
        return [doc for _, doc in scored[:top_k]]

    def is_active(self) -> bool:
        return bool(self.documents)

    def clear(self):
        self.documents = []
        self.index = None
