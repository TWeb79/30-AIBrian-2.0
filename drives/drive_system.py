"""
drives/drive_system.py — Intrinsic Drive System
===============================================
Three minimal drives that generate the brain's own agenda.
Makes the brain have opinions and preferences, not just responses.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional
from self.self_model import SelfModel


@dataclass
class DriveState:
    """
    Three drives sufficient for v0.1 personality emergence.
    Each is a float 0–1 representing current need level.
    When a drive is high, the brain is motivated to satisfy it.
    """
    curiosity: float = 0.5     # Need for novel input / unexplored associations
    competence: float = 0.5    # Need to respond accurately / avoid errors
    connection: float = 0.5   # Need for engaged, reciprocal interaction
    
    def to_prompt_fragment(self) -> str:
        """~20 tokens for LLM prompt."""
        parts = []
        
        if self.curiosity > 0.7:
            parts.append("curious and seeking novelty")
        elif self.curiosity < 0.3:
            parts.append("content with current knowledge")
        
        if self.competence > 0.7:
            parts.append("uncertain and cautious")
        elif self.competence < 0.3:
            parts.append("confident in its knowledge")
        
        if self.connection > 0.7:
            parts.append("desiring interaction")
        elif self.connection < 0.3:
            parts.append("independent and self-sufficient")
        
        return ", ".join(parts) if parts else "balanced drives"


class DriveSystem:
    """
    Drives update based on experience and influence behaviour.
    They are not fixed personality traits — they evolve.
    
    Curiosity:
      Rises when inputs are repetitive (boredom) → seek novelty
      Falls when a novel concept is successfully processed
      High curiosity → more spontaneous associations, longer thinking
    
    Competence:
      Rises when prediction errors are high → need to understand better
      Falls when predictions are accurate
      High competence need → more conservative responses, more hedging
    
    Connection:
      Rises when user has been absent (loneliness equivalent)
      Falls when user engages positively
      High connection need → warmer responses, more questions back
    """
    
    def __init__(self, self_model: Optional[SelfModel] = None):
        self.self_model = self_model
        
        # Initialize from self_model if available
        if self_model:
            self.state = DriveState(
                curiosity=self_model.curiosity_bias,
                competence=1.0 - self_model.confidence,
                connection=0.5,
            )
        else:
            self.state = DriveState()
        
        self._history: list[DriveState] = []
    
    def update(self, prediction_error: float, user_present: bool,
               novelty: float, user_feedback: float):
        """
        Update drives based on experience.
        
        Parameters
        ----------
        prediction_error : float
            Prediction error from this turn (0 = perfect, 1 = total miss)
        user_present : bool
            Whether user is currently engaged
        novelty : float
            How novel the current input is (0 = familiar, 1 = entirely new)
        user_feedback : float
            User feedback valence (-1 to 1)
        """
        s = self.state
        
        # Curiosity: novelty satisfies, repetition increases need
        s.curiosity = np.clip(
            s.curiosity + 0.05 * (1 - novelty) - 0.08 * novelty,
            0, 1
        )
        
        # Competence: error increases need, accuracy reduces it
        s.competence = np.clip(
            s.competence + 0.1 * prediction_error - 0.05 * (1 - prediction_error),
            0, 1
        )
        
        # Connection: absence increases need, positive interaction reduces it
        if not user_present:
            s.connection = min(1.0, s.connection + 0.001)
        else:
            s.connection = np.clip(
                s.connection - 0.1 * max(0, user_feedback),
                0, 1
            )
        
        # Store in history
        self._history.append(DriveState(
            curiosity=s.curiosity,
            competence=s.competence,
            connection=s.connection
        ))
        
        # Keep history manageable
        if len(self._history) > 100:
            self._history = self._history[-100:]
        
        # Sync with self_model if available
        if self.self_model:
            self.self_model.curiosity_bias = (
                0.9 * self.self_model.curiosity_bias + 0.1 * s.curiosity
            )
            self.self_model.caution_bias = (
                0.9 * self.self_model.caution_bias + 0.1 * s.competence
            )
    
    def behavioural_modifiers(self) -> dict:
        """
        How drives currently modify brain behaviour.
        These are injected into the LLM prompt and into SNN gain.
        
        Returns
        -------
        dict
            Behavioral modifiers
        """
        s = self.state
        return {
            # High curiosity → ask a follow-up question, explore tangents
            "add_question": s.curiosity > 0.7,
            
            # High competence need → add hedging, express uncertainty
            "express_uncertainty": s.competence > 0.65,
            
            # High connection → warmer tone, acknowledge user specifically
            "warm_tone": s.connection > 0.6,
            
            # Low curiosity → brain is confident on this topic, be direct
            "be_direct": s.curiosity < 0.3,
            
            # SNN gain modifiers
            "association_gain": 1.0 + s.curiosity * 0.5,
            "predictive_gain": 1.0 + s.competence * 0.3,
            
            # Thinking time modifier
            "thinking_time_multiplier": 1.0 + s.curiosity * 0.5,
        }
    
    def to_prompt_fragment(self) -> str:
        """~20 tokens injected into articulation prompt."""
        mods = self.behavioural_modifiers()
        parts = []
        
        if mods["add_question"]:
            parts.append("ask one follow-up question")
        if mods["express_uncertainty"]:
            parts.append("express appropriate uncertainty")
        if mods["warm_tone"]:
            parts.append("be warm and personal")
        if mods["be_direct"]:
            parts.append("be direct and confident")
        
        return "Tone: " + ", ".join(parts) if parts else ""
    
    def get_curiosity(self) -> float:
        """Get current curiosity level."""
        return self.state.curiosity
    
    def get_competence(self) -> float:
        """Get current competence need."""
        return self.state.competence
    
    def get_connection(self) -> float:
        """Get current connection need."""
        return self.state.connection
    
    def get_state(self) -> DriveState:
        """Get full drive state."""
        return self.state
    
    def get_average_curiosity(self, n: int = 10) -> float:
        """Get average curiosity over last n updates."""
        if not self._history:
            return 0.5
        recent = self._history[-n:]
        return sum(s.curiosity for s in recent) / len(recent)
    
    def apply_reward(self, reward: float):
        """
        Apply a reward signal (from user feedback).
        
        Parameters
        ----------
        reward : float
            Reward value (-1 to 1)
        """
        if reward > 0:
            # Positive reward reduces drive needs
            self.state.competence = np.clip(
                self.state.competence - reward * 0.1,
                0, 1
            )
            self.state.connection = np.clip(
                self.state.connection - reward * 0.1,
                0, 1
            )
        else:
            # Negative reward increases connection need
            self.state.connection = np.clip(
                self.state.connection - reward * 0.1,
                0, 1
            )


def create_drive_system(self_model: Optional[SelfModel] = None) -> DriveSystem:
    """Create a default drive system."""
    return DriveSystem(self_model)


if __name__ == "__main__":
    # Test the DriveSystem
    from self.self_model import SelfModel
    
    model = SelfModel()
    system = DriveSystem(model)
    
    # Simulate some interactions
    interactions = [
        # (prediction_error, user_present, novelty, user_feedback)
        (0.8, True, 0.9, 0.0),   # New, surprising input
        (0.3, True, 0.2, 0.5),  # Familiar, positive feedback
        (0.6, True, 0.7, 0.0),  # Somewhat new
        (0.1, True, 0.1, 0.8),  # Very familiar, strong positive
        (0.5, False, 0.5, 0.0), # User left, idle
    ]
    
    for pe, present, nov, fb in interactions:
        system.update(pe, present, nov, fb)
        mods = system.behavioural_modifiers()
        print(f"After interaction (pe={pe}, present={present}, nov={nov}, fb={fb}):")
        print(f"  Curiosity: {system.state.curiosity:.2f}")
        print(f"  Competence: {system.state.competence:.2f}")
        print(f"  Connection: {system.state.connection:.2f}")
        print(f"  Add question: {mods['add_question']}")
        print(f"  Express uncertainty: {mods['express_uncertainty']}")
        print(f"  Warm tone: {mods['warm_tone']}")
        print()
