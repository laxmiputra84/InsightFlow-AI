"""
Embedding Service for InsightFlow AI RAG Pipeline.
Provides a unified embedding interface:
- Google Gemini Embeddings (models/text-embedding-004) when GEMINI_API_KEY is configured.
- Deterministic Dense Normalized Embeddings (384-dim) for offline mode, testing, and fallbacks.
Guarantees consistent unit-norm vectors for exact cosine similarity calculation.
"""
import hashlib
import math
import logging
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger("insightflow.rag.embeddings")

DEFAULT_EMBEDDING_DIM = 384


class EmbeddingService:
    """
    Unified embedding interface supporting Gemini cloud embeddings and deterministic local fallback.
    """

    @classmethod
    def get_provider_name(cls) -> str:
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            return "google-genai (text-embedding-004)"
        return "deterministic-dense-384"

    @classmethod
    def embed_query(cls, text: str) -> List[float]:
        """Generate embedding vector for search query."""
        results = cls.embed_documents([text])
        return results[0] if results else [0.0] * DEFAULT_EMBEDDING_DIM

    @classmethod
    def embed_documents(cls, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for a list of document chunks.
        """
        if not texts:
            return []

        # 1. Attempt Gemini Embeddings if API key is present
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings

                gemini_embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004",
                    google_api_key=settings.GEMINI_API_KEY.strip(),
                )
                raw_vectors = gemini_embeddings.embed_documents(texts)
                # Ensure L2 normalization for cosine similarity
                return [cls._l2_normalize(vec) for vec in raw_vectors]
            except Exception as e:
                logger.warning(
                    f"Gemini embedding API encountered an issue ({e}). Using deterministic local embedding engine."
                )

        # 2. Deterministic local dense embedding engine
        return [cls._generate_deterministic_embedding(t) for t in texts]

    @classmethod
    def _generate_deterministic_embedding(cls, text: str, dim: int = DEFAULT_EMBEDDING_DIM) -> List[float]:
        """
        Generates a deterministic, normalized dense vector based on character 3-grams and tokens.
        Preserves semantic overlap between queries and matching document chunks without external dependencies.
        """
        clean_text = text.lower().strip()
        vector = [0.0] * dim

        if not clean_text:
            return vector

        # Token & 3-gram feature extraction
        tokens = [t.strip(",.?!;:\"'()") for t in clean_text.split() if t.strip()]
        features = list(tokens)

        # Add character tri-grams
        for word in tokens:
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    features.append(word[i : i + 3])

        # Feature hashing into dense buckets
        for feat in features:
            h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if ((h >> 8) & 1) == 1 else -1.0
            vector[idx] += sign * (1.0 + 0.1 * min(len(feat), 10))

        return cls._l2_normalize(vector)

    @staticmethod
    def _l2_normalize(vector: List[float]) -> List[float]:
        """Normalizes vector to unit length (L2 norm = 1.0)."""
        squared_sum = sum(x * x for x in vector)
        if squared_sum <= 0:
            return vector
        norm = math.sqrt(squared_sum)
        return [round(x / norm, 6) for x in vector]

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """
        Computes cosine similarity between two float vectors.
        Returns value in range [-1.0, 1.0].
        """
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))

        if norm1 <= 0 or norm2 <= 0:
            return 0.0

        return round(dot_product / (norm1 * norm2), 4)
