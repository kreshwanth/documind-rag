import os
from typing import List, Optional
import google.generativeai as genai
from app.config import settings
import logging
import hashlib
import numpy as np

logger = logging.getLogger("documind.gemini")

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.embedding_model = getattr(settings, "EMBEDDING_MODEL", "text-embedding-004")
        self.generative_model_name = getattr(settings, "LLM_MODEL", "gemini-1.5-flash")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.generative_model_name)
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY is not configured. Real AI calls will fallback to deterministic mock/offline mode.")

    def get_embeddings_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Generate embeddings for a list of texts in batches.
        Returns a list of 768-dimensional float vectors.
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            if self.api_key:
                try:
                    response = genai.embed_content(
                        model=f"models/{self.embedding_model}",
                        content=batch,
                        task_type="retrieval_document"
                    )
                    # response['embedding'] is a list of embeddings
                    if "embedding" in response:
                        batch_embeds = response["embedding"]
                        # Handle single vs multiple responses
                        if batch_embeds and isinstance(batch_embeds[0], list):
                            all_embeddings.extend(batch_embeds)
                        else:
                            all_embeddings.append(batch_embeds)
                    else:
                        raise ValueError("No embedding field in Gemini API response")
                except Exception as e:
                    logger.error(f"Error calling Gemini Embedding API: {e}. Generating fallback embedding.")
                    all_embeddings.extend([self._generate_pseudo_embedding(t) for t in batch])
            else:
                # Deterministic pseudo-embedding for testing/offline mode
                all_embeddings.extend([self._generate_pseudo_embedding(t) for t in batch])

        return all_embeddings

    def get_query_embedding(self, query: str) -> List[float]:
        """Generate a single 768-dimensional embedding for a search/RAG query."""
        if self.api_key:
            try:
                response = genai.embed_content(
                    model=f"models/{self.embedding_model}",
                    content=query,
                    task_type="retrieval_query"
                )
                if "embedding" in response:
                    emb = response["embedding"]
                    if isinstance(emb[0], list):
                        return emb[0]
                    return emb
            except Exception as e:
                logger.error(f"Error generating query embedding: {e}")
                return self._generate_pseudo_embedding(query)

        return self._generate_pseudo_embedding(query)

    def generate_grounded_answer(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generate a strictly grounded response using Gemini LLM.
        """
        if self.api_key:
            try:
                generation_config = genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.95,
                    max_output_tokens=2048,
                )
                
                # Check if system instruction is supported
                if system_instruction:
                    model = genai.GenerativeModel(
                        model_name=self.generative_model_name,
                        system_instruction=system_instruction
                    )
                else:
                    model = self.model or genai.GenerativeModel(self.generative_model_name)
                    
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"Error generating content via Gemini: {e}")
                return f"I encountered an error communicating with the AI service: {str(e)}"

        # Offline / Mock response mode when no API key is provided
        return "I could not find sufficient information in the uploaded documents to answer this question."

    def _generate_pseudo_embedding(self, text: str, dimension: int = 768) -> List[float]:
        """
        Generate a deterministic normalized pseudo-embedding based on SHA-256 seed.
        Used for local unit tests without requiring live API credits.
        """
        seed = int(hashlib.sha256(text.encode('utf-8')).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        vec = rng.randn(dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

gemini_service = GeminiService()
