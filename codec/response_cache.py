"""
codec/response_cache.py — Similarity-Based Response Reuse
==========================================================
Before calling LLM or generating locally, checks if a semantically
similar input was seen before and reuses the cached response.

Reduces cost and latency for repeated queries.
"""

import time
import numpy as np
from typing import Optional, Dict, List, Any


class ResponseCache:
    """
    Bag-of-words cosine similarity cache.
    
    Checks before SNN simulation — returns instantly on hit (path='cached').
    Stores results from local/cached paths for future reuse.
    This is the highest-leverage cost reduction: repeated questions
    skip the entire simulation.
    """
    
    def __init__(self, max_size: int = 200, similarity_threshold: float = 0.82):
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold
        
        # Cache entries: list of (input_vector, input_text, response_text, timestamp)
        self._entries: List[tuple] = []
        
        # Global word → index mapping for vectors
        self._word_index: Dict[str, int] = {}
        self._next_idx = 0
        
        # Stats
        self._hits = 0
        self._misses = 0
    
    def _get_word_idx(self, word: str) -> int:
        if word not in self._word_index:
            self._word_index[word] = self._next_idx
            self._next_idx += 1
        return self._word_index[word]
    
    def _text_to_vector(self, text: str) -> Dict[int, float]:
        """Bag-of-words frequency vector."""
        vec: Dict[int, float] = {}
        words = text.lower().split()
        for w in words:
            # Strip punctuation
            w = w.strip(".,!?;:'\"()-")
            if len(w) < 2:
                continue
            idx = self._get_word_idx(w)
            vec[idx] = vec.get(idx, 0) + 1.0
        return vec
    
    def _cosine_similarity(self, vec_a: Dict[int, float], vec_b: Dict[int, float]) -> float:
        """Cosine similarity between two sparse vectors."""
        if not vec_a or not vec_b:
            return 0.0
        
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0
        
        dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
        norm_a = np.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = np.sqrt(sum(v * v for v in vec_b.values()))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot / (norm_a * norm_b)
    
    def lookup(self, user_text: str) -> Optional[str]:
        """
        Find the most similar cached input above threshold.
        
        Returns
        -------
        str or None
            Cached response, or None if no match
        """
        query_vec = self._text_to_vector(user_text)
        
        best_sim = 0.0
        best_response = None
        
        for cached_vec, cached_text, response_text, _ in self._entries:
            sim = self._cosine_similarity(query_vec, cached_vec)
            if sim > best_sim:
                best_sim = sim
                best_response = response_text
        
        if best_sim >= self.similarity_threshold:
            self._hits += 1
            return best_response
        
        self._misses += 1
        return None
    
    def store(self, user_text: str, response_text: str):
        """Cache a new input→response pair."""
        vec = self._text_to_vector(user_text)
        self._entries.append((vec, user_text, response_text, time.time()))
        
        # Evict oldest if over capacity
        if len(self._entries) > self.max_size:
            self._entries = self._entries[-self.max_size:]
    
    def get_size(self) -> int:
        return len(self._entries)
    
    def get_hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": len(self._entries),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.get_hit_rate(), 3),
            "similarity_threshold": self.similarity_threshold,
        }
    
    def export(self) -> List[Dict[str, Any]]:
        """Export for persistence."""
        return [
            {"input": text, "response": resp, "timestamp": ts}
            for _, text, resp, ts in self._entries
        ]
    
    def import_(self, data: List[Dict[str, Any]]):
        """Import from persistence — rebuilds vectors."""
        self._entries = []
        for d in data:
            vec = self._text_to_vector(d["input"])
            self._entries.append((vec, d["input"], d["response"], d.get("timestamp", 0.0)))


def create_response_cache(max_size: int = 200) -> ResponseCache:
    return ResponseCache(max_size)
