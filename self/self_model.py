"""
self_model.py — Self Model and Identity
========================================
Persistent identity, personality drift, and brain stage tracking.
"""

import json
import os
import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SelfModel:
    """
    The brain's model of itself. Persisted to disk after every turn.
    Read at startup. Never reset.
    
    This is not metadata — it is an active part of cognition.
    The brain consults self_model when deciding how to respond,
    what to pay attention to, and how confident to be.
    """
    
    # Identity
    name: str = "BRAIN2.0"
    created_at: str = ""
    session_count: int = 0
    total_turns: int = 0
    total_steps: int = 0
    
    # Current state
    brain_stage: str = "NEONATAL"  # NEONATAL/JUVENILE/ADOLESCENT/MATURE
    mood: float = 0.5              # 0=low, 1=high — persists between sessions
    energy: float = 1.0            # degrades with use, recovers during idle
    confidence: float = 0.3         # grows with successful predictions
    
    # Personality (emerges from reward history, never hardcoded)
    curiosity_bias: float = 0.5     # shaped by novelty reward over time
    caution_bias: float = 0.5      # shaped by error punishment over time
    verbosity_bias: float = 0.5    # shaped by user feedback length
    
    # Relationship with this user
    user_name: str = ""
    user_turn_count: int = 0
    user_sentiment_avg: float = 0.5  # rolling average of user feedback valence
    shared_topics: list = field(default_factory=list)  # learned over time
    
    # What the brain knows about its own capabilities
    vocabulary_size: int = 0        # number of stable cell assemblies
    llm_bypass_rate: float = 0.0    # last 100 turns % handled without LLM
    strongest_domain: str = ""      # topic area with most stable assemblies
    
    # Runtime (not persisted — recalculated at startup)
    uptime_s: float = 0.0
    steps_this_session: int = 0
    
    def to_context_string(self) -> str:
        """
        Compact string injected into every LLM prompt.
        Tells the LLM who it is articulating for.
        ~40 tokens.
        """
        personality = "curious" if self.curiosity_bias > 0.6 else "cautious"
        return (
            f"I am {self.name}, a {self.brain_stage} neuromorphic brain. "
            f"I have had {self.total_turns} total conversations. "
            f"I am {personality}. "
            f"My confidence is {self.confidence:.0%}. "
            f"My vocabulary has {self.vocabulary_size} learned concepts."
        )
    
    def update_after_turn(self, prediction_error: float, user_feedback: float):
        """
        Update state after each turn.
        
        Parameters
        ----------
        prediction_error : float
            Prediction error from this turn (0 = perfect prediction, 1 = total miss)
        user_feedback : float
            User feedback valence (-1 = negative, 0 = neutral, +1 = positive)
        """
        self.total_turns += 1
        self.user_turn_count += 1
        
        # Confidence grows when predictions are accurate
        self.confidence = 0.95 * self.confidence + 0.05 * (1 - prediction_error)
        
        # Mood drifts toward user sentiment
        self.mood = 0.98 * self.mood + 0.02 * (user_feedback * 0.5 + 0.5)
        
        # Energy depletes slightly per turn
        self.energy = max(0.2, self.energy - 0.001)
        
        # Update brain stage based on experience
        self._update_stage()
    
    def _update_stage(self):
        """Update brain stage based on total steps and confidence."""
        if self.total_steps > 5_000_000 and self.confidence > 0.85:
            self.brain_stage = "MATURE"
        elif self.total_steps > 1_000_000 and self.confidence > 0.65:
            self.brain_stage = "ADOLESCENT"
        elif self.total_steps > 100_000 and self.confidence > 0.45:
            self.brain_stage = "JUVENILE"
        else:
            self.brain_stage = "NEONATAL"
    
    def recover_energy(self, idle_seconds: float):
        """Called during background idle loop."""
        self.energy = min(1.0, self.energy + idle_seconds * 0.0001)
    
    def add_shared_topic(self, topic: str):
        """Add a topic to the shared topics list."""
        if topic not in self.shared_topics:
            self.shared_topics.append(topic)
            # Keep only last 50 topics
            if len(self.shared_topics) > 50:
                self.shared_topics = self.shared_topics[-50:]
    
    def save(self, path: str = "brain_state/self_model.json"):
        """Save self model to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=2)
    
    @classmethod
    def load(cls, path: str = "brain_state/self_model.json") -> "SelfModel":
        """Load self model from disk."""
        try:
            with open(path) as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items()
                         if k in cls.__dataclass_fields__})
        except FileNotFoundError:
            m = cls()
            m.created_at = datetime.datetime.utcnow().isoformat()
            m.save(path)
            return m
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.__dict__
    
    @classmethod
    def from_dict(cls, data: dict) -> "SelfModel":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items()
                     if k in cls.__dataclass_fields__})


def create_default_self_model() -> SelfModel:
    """Create a new default self model."""
    model = SelfModel()
    model.created_at = datetime.datetime.utcnow().isoformat()
    return model


if __name__ == "__main__":
    # Test the SelfModel
    model = create_default_self_model()
    print(f"Created: {model.name}")
    print(f"Stage: {model.brain_stage}")
    print(f"Context: {model.to_context_string()}")
    
    # Test saving and loading
    model.total_turns = 10
    model.confidence = 0.5
    model.save("test_self_model.json")
    
    loaded = SelfModel.load("test_self_model.json")
    print(f"Loaded: {loaded.total_turns} turns, confidence: {loaded.confidence}")
    
    # Cleanup
    if os.path.exists("test_self_model.json"):
        os.remove("test_self_model.json")
