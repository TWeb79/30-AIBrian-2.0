"""
memory/hippocampus_full.py — scaffold for fuller hippocampus (DG/CA3/CA1/EC)
=======================================================================

This is an incremental scaffold providing simple interfaces for dentate gyrus
(DG), CA3 autoassociative network, CA1 comparator, and entorhinal cortex (EC).
The goal is to provide basic encode/recall hooks integrated with the existing
HippocampusSimple interface so higher-level code can switch to this when ready.

Note: This implementation is deliberately light — it stores sparse binary patterns
and performs recall by overlap. A more biologically-faithful implementation
would use LIF networks and DG pattern separation, but that is out of scope
for this patch.
"""

import numpy as np
from typing import List, Dict, Any


class HippocampusFull:
    """Simple storage of episodes across DG/CA3/CA1 pipeline.

    Episodes are stored as sparse binary neuron index lists. Recall is by
    Jaccard-like overlap scoring and returns top matches.
    """

    def __init__(self, max_episodes: int = 5000):
        self.max_episodes = max_episodes
        self.episodes: List[Dict[str, Any]] = []

    def encode(self, neuron_indices: List[int], topic: str = "", valence: float = 0.0, arousal: float = 0.0):
        data = {
            "neurons": sorted(set(int(i) for i in neuron_indices)),
            "topic": topic,
            "valence": float(valence),
            "arousal": float(arousal),
        }
        self.episodes.append(data)
        if len(self.episodes) > self.max_episodes:
            self.episodes.pop(0)

    def recall(self, neuron_indices: List[int], top_k: int = 3, min_overlap: float = 0.1):
        query = set(neuron_indices)
        scored = []
        for ep in self.episodes:
            stored = set(ep["neurons"])
            if not stored:
                continue
            # overlap ratio
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
        return {"episodes": len(self.episodes), "max_episodes": self.max_episodes}


def create_hippocampus_full(max_episodes: int = 5000) -> HippocampusFull:
    return HippocampusFull(max_episodes=max_episodes)


if __name__ == "__main__":
    h = create_hippocampus_full(100)
    h.encode([1,2,3,4], topic="greeting", valence=0.5)
    h.encode([10,20,30], topic="farewell", valence=-0.2)
    print(h.recall([1,2,3]))
