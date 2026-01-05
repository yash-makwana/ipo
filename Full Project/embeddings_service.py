# embeddings_service_local.py
# LOCAL VERSION: Uses sentence-transformers instead of Vertex AI
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingsService:
    """Service for generating text embeddings using local sentence-transformers"""
    
    def __init__(self):
        """Initialize local embedding model"""
        # Use a lightweight, high-quality model
        # all-MiniLM-L6-v2 is fast and works well for semantic search
        model_name = "all-MiniLM-L6-v2"
        print(f"🔄 Loading local embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print(f"✅ Embeddings service initialized (Local Model: {model_name})")
    
    def get_embedding(self, text):
        """Alias for backward compatibility"""
        return self.generate_single_embedding(text)
    
    def get_embeddings(self, texts, batch_size=5):
        """Alias for backward compatibility"""
        return self.generate_embeddings(texts, batch_size=batch_size)
    
    def generate_embeddings(self, texts, batch_size=5):
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing (ignored for local, processes all at once)
        
        Returns:
            List of embedding vectors (numpy arrays)
        """
        if not texts:
            return []
        
        try:
            # sentence-transformers is already optimized for batching
            embeddings = self.model.encode(
                texts,
                batch_size=32,  # Use efficient batch size
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Convert to list of numpy arrays for compatibility
            return [np.array(emb) for emb in embeddings]
            
        except Exception as e:
            print(f"❌ Embedding generation error: {e}")
            # Return zero vectors as fallback
            dim = 384  # all-MiniLM-L6-v2 dimension
            return [np.zeros(dim) for _ in texts]
    
    def generate_single_embedding(self, text):
        """
        Generate embedding for a single text
        
        Args:
            text: Text string
        
        Returns:
            numpy array of embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            dim = 384
            return np.zeros(dim)
        
        try:
            embedding = self.model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return np.array(embedding)
            
        except Exception as e:
            print(f"❌ Single embedding error: {e}")
            dim = 384
            return np.zeros(dim)


# Singleton instance
_embeddings_service = None

def get_embeddings_service():
    """Get or create singleton EmbeddingsService instance"""
    global _embeddings_service
    
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    
    return _embeddings_service
