import numpy as np
from typing import Dict, Optional
import hashlib


class SemanticCache:
    """Cache s sémantickým vyhledáváním pro rychlejší odpovědi"""

    def __init__(self, similarity_threshold: float = 0.95):
        self.cache: Dict[str, Dict] = {}
        self.threshold = similarity_threshold

    def _get_key(self, question: str) -> str:
        """Vytvoří hash klíč pro otázku"""
        return hashlib.md5(question.encode()).hexdigest()

    def add(self, question: str, embedding: list, response: Dict):
        """Přidá odpověď do cache"""
        key = self._get_key(question)
        self.cache[key] = {
            "question": question,
            "embedding": embedding,
            "response": response
        }

    def get(self, question: str, embedding: list) -> Optional[Dict]:
        """Zkusí najít podobnou otázku v cache"""
        if not self.cache:
            return None

        query_emb = np.array(embedding)

        for key, cached in self.cache.items():
            cached_emb = np.array(cached["embedding"])

            # Cosine similarity
            similarity = np.dot(query_emb, cached_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(cached_emb)
            )

            if similarity >= self.threshold:
                return {
                    **cached["response"],
                    "from_cache": True,
                    "cache_similarity": float(similarity)
                }

        return None

    def clear(self):
        """Vymaže cache"""
        self.cache.clear()

    def size(self) -> int:
        """Vrátí počet položek v cache"""
        return len(self.cache)
