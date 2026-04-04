"""
memory/hippocampus_spiking.py — lightweight spiking-inspired hippocampus scaffold
==========================================================================

Provides a moderately richer hippocampus interface using a small DG/CA3/CA1
pipeline. This is still a scaffold: encoding stores sparse patterns and uses
simple pattern separation (DG random projection) and autoassociative lookup
in CA3 via overlap scoring. The interface matches HippocampusSimple so it can
be swapped into OSCENBrain.

This is intentionally small and deterministic enough for unit tests.
"""

import numpy as np
from typing import List, Dict, Any
import time


class HippocampusSpiking:
    def __init__(self, max_episodes: int = 5000, dg_size: int = 1024, seed: int = 42):
        self.max_episodes = max_episodes
        self.episodes: List[Dict[str, Any]] = []
        self.dg_size = dg_size
        self.rng = np.random.default_rng(seed)
        # random projection matrix for DG pattern separation (binary masks)
        self._proj_masks = [self.rng.choice(dg_size, size=max(1, dg_size//20), replace=False) for _ in range(10)]

    def _dg_separate(self, neuron_indices: List[int]) -> List[int]:
        # Simple deterministic separation: hash neuron ids and flip through masks
        out = set()
        for n in neuron_indices:
            h = (hash(n) & 0xffffffff)
            mask = self._proj_masks[h % len(self._proj_masks)]
            # pick one index from mask based on hash
            idx = mask[h % mask.size]
            out.add(int(idx))
        return sorted(out)

    def encode(self, neuron_indices: List[int], topic: str = "", valence: float = 0.0, arousal: float = 0.0):
        if not neuron_indices:
            return
        dg_pattern = self._dg_separate(list(neuron_indices))
        ep = {
            "neurons": dg_pattern,
            "timestamp": time.time(),
            "topic": topic,
            "valence": float(valence),
            "arousal": float(arousal),
        }
        self.episodes.append(ep)
        if len(self.episodes) > self.max_episodes:
            self.episodes.pop(0)

    def recall(self, neuron_indices: List[int], top_k: int = 3, min_overlap: float = 0.1):
        if not neuron_indices or not self.episodes:
            return []
        query = set(self._dg_separate(list(neuron_indices)))
        scored = []
        for ep in self.episodes:
            stored = set(ep.get("neurons", []))
            if not stored:
                continue
            ov = len(query & stored) / max(1, len(stored))
            if ov >= min_overlap:
                scored.append((ov, ep))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:top_k]]

    def import_(self, data: List[Dict[str, Any]]):
        self.episodes = data[-self.max_episodes :]

    def export(self) -> List[Dict[str, Any]]:
        return list(self.episodes)

    def get_statistics(self) -> Dict[str, Any]:
        return {"episodes": len(self.episodes), "dg_size": self.dg_size}


def create_hippocampus_spiking(max_episodes: int = 5000, dg_size: int = 1024) -> HippocampusSpiking:
    return HippocampusSpiking(max_episodes=max_episodes, dg_size=dg_size)


if __name__ == "__main__":
    h = create_hippocampus_spiking(100)
    h.encode([1,2,3,4], topic="hello", valence=0.3)
    print(h.recall([1,2,3]))
