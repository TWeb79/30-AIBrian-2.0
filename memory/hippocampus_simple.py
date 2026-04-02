"""
memory/hippocampus_simple.py — Simplified Hippocampus
=====================================================
One-shot episodic encoding. Stores concept patterns at key moments
(high salience, user feedback). Recalls similar past episodes
when a partial cue is presented.

v0.2: CA3 attractor only (no full DG/CA1/EC).
v0.4: Full hippocampal circuit.
"""

import time
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Set


@dataclass
class Episode:
    """A single episodic memory."""
    neuron_ids: List[int]
    timestamp: float
    topic: str = ""
    valence: float = 0.0
    response_text: str = ""
    arousal: float = 0.0


class HippocampusSimple:
    """
    Simplified hippocampal circuit for episodic memory.
    
    Encoding: one-shot — store the active concept pattern + metadata.
    Recall: pattern completion — find episodes with highest neuron overlap
            to the current cue pattern.
    
    Capacity: max_episodes (default 1000). Oldest pruned on overflow.
    """
    
    def __init__(self, max_episodes: int = 1000):
        self.max_episodes = max_episodes
        self.episodes: List[Episode] = []
        self._encode_count = 0
        self._recall_count = 0
        self._recall_hits = 0
    
    def encode(
        self,
        neuron_ids: List[int],
        topic: str = "",
        valence: float = 0.0,
        response_text: str = "",
        arousal: float = 0.0,
    ):
        """
        One-shot encoding of a spike pattern as an episode.
        
        Parameters
        ----------
        neuron_ids : list[int]
            Active concept neuron IDs
        topic : str
            Topic label (first word or keyword)
        valence : float
            Emotional valence at encoding time
        response_text : str
            What was said in response
        arousal : float
            Arousal level at encoding time
        """
        if not neuron_ids:
            return
        
        episode = Episode(
            neuron_ids=list(neuron_ids),
            timestamp=time.time(),
            topic=topic,
            valence=valence,
            response_text=response_text,
            arousal=arousal,
        )
        
        self.episodes.append(episode)
        self._encode_count += 1
        
        # Prune oldest if over capacity
        if len(self.episodes) > self.max_episodes:
            self.episodes = self.episodes[-self.max_episodes:]
    
    def recall(
        self,
        cue_neuron_ids: Set[int],
        top_k: int = 3,
        min_overlap: float = 0.15,
    ) -> List[Episode]:
        """
        Pattern completion: partial cue → find similar episodes.
        
        Parameters
        ----------
        cue_neuron_ids : set[int]
            Currently active concept neuron IDs
        top_k : int
            Max episodes to return
        min_overlap : float
            Minimum Jaccard similarity to return a result
            
        Returns
        -------
        list[Episode]
            Most similar episodes, best first
        """
        self._recall_count += 1
        
        if not cue_neuron_ids or not self.episodes:
            return []
        
        scored = []
        for ep in self.episodes:
            ep_set = set(ep.neuron_ids)
            if not ep_set:
                continue
            # Jaccard similarity
            intersection = len(cue_neuron_ids & ep_set)
            union = len(cue_neuron_ids | ep_set)
            similarity = intersection / union if union > 0 else 0.0
            
            if similarity >= min_overlap:
                scored.append((ep, similarity))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        if scored:
            self._recall_hits += 1
        
        return [ep for ep, _ in scored[:top_k]]
    
    def get_recent(self, n: int = 5) -> List[Episode]:
        """Return last n episodes."""
        return self.episodes[-n:]
    
    def get_episode_count(self) -> int:
        return len(self.episodes)
    
    def get_statistics(self) -> Dict[str, Any]:
        recall_rate = self._recall_hits / self._recall_count if self._recall_count > 0 else 0.0
        return {
            "total_episodes": len(self.episodes),
            "total_encodes": self._encode_count,
            "total_recalls": self._recall_count,
            "recall_hit_rate": round(recall_rate, 3),
            "capacity_used": f"{len(self.episodes)}/{self.max_episodes}",
        }
    
    def prune_weakest(self, keep_fraction: float = 0.8):
        """
        Keep only the top episodes by recency × arousal.
        Called during dormant mode consolidation.
        """
        if len(self.episodes) <= self.max_episodes * keep_fraction:
            return
        
        keep_count = int(self.max_episodes * keep_fraction)
        # Score by recency + arousal (salient episodes survive)
        now = time.time()
        scored = []
        for i, ep in enumerate(self.episodes):
            recency = 1.0 / (1.0 + (now - ep.timestamp) / 3600.0)  # hours
            score = recency * (1.0 + ep.arousal)
            scored.append((i, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        keep_indices = set(idx for idx, _ in scored[:keep_count])
        self.episodes = [ep for i, ep in enumerate(self.episodes) if i in keep_indices]
    
    def export(self) -> List[Dict[str, Any]]:
        """Export for persistence."""
        return [
            {
                "neuron_ids": ep.neuron_ids,
                "timestamp": ep.timestamp,
                "topic": ep.topic,
                "valence": ep.valence,
                "response_text": ep.response_text,
                "arousal": ep.arousal,
            }
            for ep in self.episodes
        ]
    
    def import_(self, data: List[Dict[str, Any]]):
        """Import from persistence."""
        self.episodes = [
            Episode(
                neuron_ids=d.get("neuron_ids", []),
                timestamp=d.get("timestamp", 0.0),
                topic=d.get("topic", ""),
                valence=d.get("valence", 0.0),
                response_text=d.get("response_text", ""),
                arousal=d.get("arousal", 0.0),
            )
            for d in data
        ]


def create_hippocampus_simple(max_episodes: int = 1000) -> HippocampusSimple:
    return HippocampusSimple(max_episodes)
