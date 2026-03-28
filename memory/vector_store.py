try:
    import faiss
    from sentence_transformers import SentenceTransformer
except ImportError:
    faiss = None
    SentenceTransformer = None

class VectorStore:
    """RAG-ready Vector Memory for the ExamHelp Ecosystem."""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name) if SentenceTransformer else None
        self.index = None
        self.documents = []

    def add_documents(self, docs: list[str]):
        """Embed and add documents to the vector index."""
        if not self.model: return
        self.documents.extend(docs)
        embeddings = self.model.encode(docs)
        
        if self.index is None:
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
        
        self.index.add(embeddings.astype('float32'))

    def search(self, query: str, top_k=3) -> list[str]:
        """Search for most relevant document snippets."""
        if not self.index or not self.model: return []
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.documents):
                results.append(self.documents[idx])
        return results

    def is_active(self) -> bool:
        return self.index is not None
