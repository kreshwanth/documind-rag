import os
import re
from typing import List, Optional
import google.generativeai as genai
from app.config import settings
import logging
import hashlib
import numpy as np

logger = logging.getLogger("documind.embedding")

class EmbeddingService:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, dimension: Optional[int] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                logger.info("Google Gemini Embedding Service configured with API Key.")
            except Exception as e:
                logger.warning(f"Error configuring Gemini API: {e}")
        else:
            logger.info("GEMINI_API_KEY not configured. Using high-performance Semantic Feature Hashing for local embeddings.")

    def set_api_key(self, key: str):
        self.api_key = key
        settings.GEMINI_API_KEY = key
        if key:
            genai.configure(api_key=key)

    def embed_chunks(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """Generate embeddings for chunks in batches with dimension validation."""
        if not texts:
            return []

        embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            if self.api_key:
                try:
                    response = genai.embed_content(
                        model=f"models/{self.model_name}",
                        content=batch,
                        task_type="retrieval_document"
                    )
                    if "embedding" in response:
                        batch_res = response["embedding"]
                        if batch_res and isinstance(batch_res[0], list):
                            for vec in batch_res:
                                self._validate_dimension(vec)
                                embeddings.append(vec)
                        else:
                            self._validate_dimension(batch_res)
                            embeddings.append(batch_res)
                    else:
                        raise ValueError("Gemini API response did not contain 'embedding' key.")
                except Exception as e:
                    logger.warning(f"Gemini embedding batch call failed: {e}. Falling back to semantic hash vector.")
                    embeddings.extend([self._semantic_hash_embedding(t) for t in batch])
            else:
                embeddings.extend([self._semantic_hash_embedding(t) for t in batch])

        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generate a single embedding vector for a search/RAG query."""
        if self.api_key:
            try:
                response = genai.embed_content(
                    model=f"models/{self.model_name}",
                    content=query,
                    task_type="retrieval_query"
                )
                if "embedding" in response:
                    emb = response["embedding"]
                    if isinstance(emb[0], list):
                        emb = emb[0]
                    self._validate_dimension(emb)
                    return emb
            except Exception as e:
                logger.warning(f"Gemini query embedding call failed: {e}. Falling back to semantic hash vector.")
                return self._semantic_hash_embedding(query)

        return self._semantic_hash_embedding(query)

    def _validate_dimension(self, vec: List[float]):
        """Ensure vector matches configured dimension."""
        if len(vec) != self.dimension:
            logger.warning(f"Embedding dimension mismatch: expected {self.dimension}, got {len(vec)}")

    def _semantic_hash_embedding(self, text: str) -> List[float]:
        """
        High-dimensional semantic feature hashing (Murmur/SHA256 bag-of-words + subword n-grams).
        Produces meaningful cosine similarities between query terms and document passages.
        """
        STOP_WORDS = {
            'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren',
            'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
            'can', 'did', 'do', 'does', 'doing', 'don', 'down', 'during', 'each', 'few', 'for', 'from', 'further',
            'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how',
            'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself',
            'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves',
            'out', 'over', 'own', 'same', 'should', 'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs',
            'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under',
            'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom',
            'why', 'with', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves'
        }

        vec = np.zeros(self.dimension, dtype=np.float32)
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return vec.tolist()

        # Word tokens + character 3-grams
        tokens = []
        for w in words:
            weight = 0.15 if w in STOP_WORDS else 1.0
            tokens.append((w, weight))
            if len(w) >= 3 and w not in STOP_WORDS:
                for j in range(len(w) - 2):
                    tokens.append((w[j:j+3], 0.5))

        for token, weight in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[bucket] += sign * weight

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

embedding_service = EmbeddingService()

