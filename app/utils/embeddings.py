from sentence_transformers import SentenceTransformer
from typing import List


class LocalHuggingFaceEmbeddings:
    """Simple wrapper for SentenceTransformer to work with LangChain/Chroma."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
