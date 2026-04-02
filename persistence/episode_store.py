"""
persistence/episode_store.py — Episode Persistence
===================================================
Save/load hippocampal episodes to disk.
Separate from BrainStore to keep concerns clean.
"""

import json
import os
from typing import List, Dict, Any


class EpisodeStore:
    """
    Persists episodic memories as JSON.
    
    Directory: brain_state/memory/
        episodes.json — list of episode dicts
    
    Save frequency: every 10,000 steps or on graceful shutdown.
    Max stored: last 1000 episodes.
    """
    
    def __init__(self, base_dir: str = "brain_state"):
        self.base_dir = base_dir
        self._ensure_directory()
    
    def _ensure_directory(self):
        os.makedirs(f"{self.base_dir}/memory", exist_ok=True)
    
    def save_episodes(self, episodes: List[Dict[str, Any]]) -> bool:
        """
        Save episodes to disk.
        
        Parameters
        ----------
        episodes : list[dict]
            Episode dicts from HippocampusSimple.export()
            
        Returns
        -------
        bool
            True if successful
        """
        try:
            self._ensure_directory()
            path = f"{self.base_dir}/memory/episodes.json"
            with open(path, "w") as f:
                json.dump(episodes[-1000:], f)
            return True
        except Exception as e:
            print(f"Error saving episodes: {e}")
            return False
    
    def load_episodes(self) -> List[Dict[str, Any]]:
        """
        Load episodes from disk.
        
        Returns
        -------
        list[dict]
            Episode dicts ready for HippocampusSimple.import_()
        """
        try:
            path = f"{self.base_dir}/memory/episodes.json"
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading episodes: {e}")
        return []
    
    def exists(self) -> bool:
        return os.path.exists(f"{self.base_dir}/memory/episodes.json")


def create_episode_store(base_dir: str = "brain_state") -> EpisodeStore:
    return EpisodeStore(base_dir)
