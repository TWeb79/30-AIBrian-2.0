"""
codec/llm_bypass_monitor.py — LLM Bypass Rate Tracker
======================================================
Tracks the percentage of turns handled without calling the LLM.
The primary metric for v0.2 maturity: rising bypass rate = brain is learning.
"""

import time
from typing import Dict, Any, List


class LLMBypassMonitor:
    """
    Rolling window tracker for LLM bypass rate.
    
    Records each turn's path ('llm', 'local', 'cached') and computes
    the bypass rate over the last N turns.
    
    The bypass rate should rise over time as vocabulary grows,
    response cache fills, and the LLM gate's confidence threshold
    is met more often.
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._paths: List[str] = []
        self._total_turns = 0
        
        # Lifetime counters
        self._lifetime = {"llm": 0, "local": 0, "cached": 0}
    
    def record_turn(self, path: str):
        """
        Record a turn's generation path.
        
        Parameters
        ----------
        path : str
            One of 'llm', 'local', 'cached'
        """
        if path not in ("llm", "local", "cached"):
            path = "llm"  # default unknown to llm
        
        self._paths.append(path)
        self._total_turns += 1
        self._lifetime[path] = self._lifetime.get(path, 0) + 1
        
        # Keep only window
        if len(self._paths) > self.window_size:
            self._paths = self._paths[-self.window_size:]
    
    def get_bypass_rate(self) -> float:
        """
        % of last window_size turns that were 'local' or 'cached'.
        
        Returns
        -------
        float
            0.0 to 1.0
        """
        if not self._paths:
            return 0.0
        bypassed = sum(1 for p in self._paths if p in ("local", "cached"))
        return bypassed / len(self._paths)
    
    def get_llm_rate(self) -> float:
        """Inverse of bypass rate."""
        return 1.0 - self.get_bypass_rate()
    
    def get_path_distribution(self) -> Dict[str, int]:
        """Distribution in the current window."""
        dist = {"llm": 0, "local": 0, "cached": 0}
        for p in self._paths:
            dist[p] = dist.get(p, 0) + 1
        return dist
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_turns": self._total_turns,
            "window_size": len(self._paths),
            "bypass_rate": round(self.get_bypass_rate(), 3),
            "llm_rate": round(self.get_llm_rate(), 3),
            "path_distribution": self.get_path_distribution(),
            "lifetime": dict(self._lifetime),
        }
    
    def export(self) -> Dict[str, Any]:
        """Export for persistence."""
        return {
            "paths": self._paths[-self.window_size:],
            "total_turns": self._total_turns,
            "lifetime": dict(self._lifetime),
        }
    
    def import_(self, data: Dict[str, Any]):
        """Import from persistence."""
        if "paths" in data:
            self._paths = data["paths"]
        if "total_turns" in data:
            self._total_turns = data["total_turns"]
        if "lifetime" in data:
            self._lifetime = data["lifetime"]


def create_llm_bypass_monitor(window_size: int = 100) -> LLMBypassMonitor:
    return LLMBypassMonitor(window_size)
