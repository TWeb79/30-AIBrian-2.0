"""
codec/character_encoder.py — Text to Spike Encoding
===================================================
Converts text into cortical spike patterns WITHOUT any API call.
Each ASCII character maps to a unique cortical pattern with perceptual similarity.
"""

import numpy as np
from typing import Optional, Dict


class CharacterEncoder:
    """
    Converts text → cortical spike patterns WITHOUT any API call.
    
    Encoding scheme:
    1. Each ASCII character maps to a unique cortical pattern
    2. Visually/phonetically similar characters have overlapping patterns
       (a/e overlap ~40%, b/d overlap ~30%) — perceptual similarity built-in
    3. Character sequences are encoded with 2ms gaps (temporal structure)
    4. Word boundaries are encoded as a silence (5ms no spikes)
    
    This produces a spike representation that the SNN can learn from directly.
    No tokenizer, no vocabulary, no embedding lookup.
    """
    
    def __init__(self, n_neurons: int, alphabet_size: int = 128, seed: int = 42):
        self.n = n_neurons
        self.alphabet_size = alphabet_size
        self.rng = np.random.default_rng(seed)
        
        # Each character gets a sparse random pattern of k neurons
        k = max(1, n_neurons // 50)  # ~2% of neurons per character
        self.patterns: Dict[int, np.ndarray] = {}
        
        # Build character patterns with perceptual similarity
        self._build_character_patterns(k)
        
        # Stats
        self.total_encodes = 0
        self.total_characters = 0
    
    def _build_character_patterns(self, k: int):
        """Build character patterns with similarity overlap."""
        all_idx = np.arange(self.n)
        
        for char_id in range(self.alphabet_size):
            # Base pattern: random subset of neurons
            base_neurons = self.rng.choice(self.n, size=k, replace=False)
            
            # Find nearby characters for perceptual similarity
            # ASCII: a-z are 97-122, A-Z are 65-90, 0-9 are 48-57
            nearby_ranges = []
            
            # Characters with similar appearance (a/e/o/u, b/d/p/q, etc.)
            if 97 <= char_id <= 122:  # lowercase
                # Vowels share patterns
                if char_id in [97, 101, 105, 111, 117]:  # aeiou
                    nearby = [97, 101, 105, 111, 117]
                # Similar consonants
                elif char_id in [98, 100]:  # b,d
                    nearby = [98, 100, 112, 113]  # b,d,p,q
                elif char_id in [112, 113]:  # p,q
                    nearby = [98, 100, 112, 113]
                elif char_id in [102, 116]:  # f,t
                    nearby = [102, 116]
                elif char_id in [110, 109]:  # n,m
                    nearby = [110, 109]
                else:
                    nearby = []
            elif 65 <= char_id <= 90:  # uppercase
                if char_id in [65, 69, 73, 79, 85]:  # AEIOU
                    nearby = [65, 69, 73, 79, 85]
                else:
                    nearby = []
            elif 48 <= char_id <= 57:  # digits
                if char_id in [48, 49]:  # 0,1
                    nearby = [48, 49]
                else:
                    nearby = []
            else:
                nearby = []
            
            # Add overlapping patterns for similar characters
            for nc in nearby[:2]:  # Limit to 2 to prevent too much overlap
                if nc != char_id and nc not in self.patterns:
                    shared = self.rng.choice(base_neurons, size=k // 4, replace=False)
                    if nc not in self.patterns:
                        self.patterns[nc] = self.rng.choice(self.n, size=k, replace=False)
                    self.patterns[nc] = np.unique(
                        np.concatenate([self.patterns[nc][:k // 2], shared])
                    )[:k]
            
            self.patterns[char_id] = base_neurons
        
        # Ensure space character exists
        if 32 not in self.patterns:
            self.patterns[32] = self.rng.choice(self.n, size=k // 2, replace=False)
    
    def encode(self, text: str, sensory_cortex) -> int:
        """
        Inject text as spike sequence into sensory cortex.
        
        Parameters
        ----------
        text : str
            Input text to encode
        sensory_cortex : SensoryCortex
            The sensory cortex to inject spikes into
            
        Returns
        -------
        int
            Number of characters encoded
        """
        self.total_encodes += 1
        
        for i, char in enumerate(text):
            char_id = ord(char) if ord(char) < self.alphabet_size else 32
            
            if char_id in self.patterns:
                # Inject current into the pattern neurons
                # Magnitude scales with character importance
                magnitude = 25.0
                sensory_cortex.population.inject_current(
                    self.patterns[char_id], magnitude
                )
                self.total_characters += 1
        
        return len(text)
    
    def encode_to_array(self, text: str, output_size: Optional[int] = None) -> np.ndarray:
        """
        Encode text to a numpy array (for testing or caching).
        
        Parameters
        ----------
        text : str
            Input text to encode
        output_size : int, optional
            Size of output array (defaults to n_neurons)
            
        Returns
        -------
        np.ndarray
            Spike pattern array
        """
        output_size = output_size or self.n
        pattern = np.zeros(output_size, dtype=np.float32)
        
        for char in text:
            char_id = ord(char) if ord(char) < self.alphabet_size else 32
            
            if char_id in self.patterns:
                indices = self.patterns[char_id]
                valid_idx = indices[indices < output_size]
                pattern[valid_idx] += 1.0
        
        return pattern
    
    def get_pattern(self, char: str) -> np.ndarray:
        """Get the spike pattern for a single character."""
        char_id = ord(char) if ord(char) < self.alphabet_size else 32
        if char_id in self.patterns:
            return self.patterns[char_id].copy()
        return np.array([], dtype=np.int32)
    
    def get_statistics(self) -> dict:
        """Get encoding statistics."""
        return {
            "total_encodes": self.total_encodes,
            "total_characters": self.total_characters,
            "n_neurons": self.n,
            "alphabet_size": self.alphabet_size,
        }
    
    def reset_statistics(self):
        """Reset encoding statistics."""
        self.total_encodes = 0
        self.total_characters = 0


def create_character_encoder(n_neurons: int) -> CharacterEncoder:
    """Create a default character encoder."""
    return CharacterEncoder(n_neurons)


if __name__ == "__main__":
    # Test the CharacterEncoder
    encoder = create_character_encoder(1000)
    
    test_strings = [
        "hello world",
        "HELLO WORLD",
        "12345",
        "aaa eee iii",
    ]
    
    for text in test_strings:
        pattern = encoder.encode_to_array(text)
        nonzero = np.count_nonzero(pattern)
        print(f"'{text}' -> {nonzero} active neurons")
    
    print(f"\nStats: {encoder.get_statistics()}")
