"""
emotion/salience.py — Emotional Salience Layer
=============================================
Valence/arousal system that asymmetrically weights inputs.
Makes the brain respond differently to emotionally significant inputs.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class AffectiveState:
    """
    The brain's current emotional colouration.
    Two dimensions (Russell circumplex model):
      valence:  -1 (negative) to +1 (positive)
      arousal:   0 (calm)     to  1 (activated)
    
    Updated continuously by inputs and internal events.
    Influences: attention allocation, learning rate, response tone.
    """
    valence: float = 0.0    # neutral
    arousal: float = 0.3    # lightly awake
    
    def as_neuromodulator_biases(self) -> dict:
        """
        Maps affect to neuromodulator perturbations.
        
        High arousal + negative valence → norepinephrine spike (stress/alertness)
        High arousal + positive valence → dopamine boost (reward/excitement)
        Low arousal  + negative valence → serotonin dip (low mood)
        Low arousal  + positive valence → acetylcholine rise (calm curiosity)
        """
        return {
            "norepinephrine_delta": self.arousal * max(0, -self.valence) * 0.5,
            "dopamine_delta": self.arousal * max(0, self.valence) * 0.5,
            "serotonin_delta": (1 - self.arousal) * self.valence * 0.3,
            "acetylcholine_delta": (1 - self.arousal) * max(0, self.valence) * 0.3,
        }
    
    def to_prompt_fragment(self) -> str:
        """~15 tokens for LLM prompt."""
        v = self.valence
        a = self.arousal
        
        if a > 0.7:
            if v > 0.3:
                return "excited and positive"
            elif v < -0.3:
                return "stressed and alert"
            else:
                return "highly aroused"
        elif a < 0.3:
            if v > 0.3:
                return "calm and content"
            elif v < -0.3:
                return "sad or withdrawn"
            else:
                return "neutral and calm"
        else:
            if v > 0:
                return "moderately positive"
            elif v < 0:
                return "concerned"
            else:
                return "balanced"


class SalienceFilter:
    """
    Intercepts all inputs and assigns emotional weight before
    they enter the SNN. High-salience inputs get more simulation
    steps, more STDP gain, and are more likely to reach hippocampus.
    
    Salience detection (v0.1 — pattern-based, no ML):
      Keywords indicating distress, urgency, novelty, or intimacy
      trigger elevated arousal. Reward/praise triggers positive valence.
      This is crude but immediately effective.
    """
    
    HIGH_AROUSAL_PATTERNS = [
        "help", "urgent", "please", "important", "problem",
        "broken", "stuck", "confused", "hurt", "error", "wrong",
        "! !", "???", "!!!!", " urgent ", " asap ", " emergency ",
    ]
    
    POSITIVE_VALENCE_PATTERNS = [
        "thanks", "great", "perfect", "love", "excellent",
        "good", "yes", "correct", "amazing", "brilliant", "awesome",
        "wonderful", "fantastic", "happy", "nice", "appreciate",
    ]
    
    NEGATIVE_VALENCE_PATTERNS = [
        "no", "wrong", "bad", "terrible", "hate", "stupid",
        "useless", "broken", "fail", "never", "disappointing",
        "frustrated", "annoying", "annoyed", "upset", "sad",
    ]
    
    def __init__(self, decay_rate: float = 0.95):
        self.state = AffectiveState()
        self._decay_rate = decay_rate
        self._history: list[AffectiveState] = []
    
    def assess(self, text: str) -> AffectiveState:
        """
        Compute affect state for this input.
        Updates internal state and returns it.
        
        Parameters
        ----------
        text : str
            Input text to analyze
            
        Returns
        -------
        AffectiveState
            The computed emotional state
        """
        text_lower = text.lower()
        
        # Keyword salience
        arousal_score = sum(
            p in text_lower for p in self.HIGH_AROUSAL_PATTERNS
        ) * 0.2
        
        pos_score = sum(
            p in text_lower for p in self.POSITIVE_VALENCE_PATTERNS
        ) * 0.15
        
        neg_score = sum(
            p in text_lower for p in self.NEGATIVE_VALENCE_PATTERNS
        ) * 0.15
        
        # Length heuristic — longer inputs imply more importance
        length_arousal = min(len(text) / 500.0, 0.3)
        
        # Question mark — arousal (uncertainty/seeking)
        question_arousal = 0.1 if "?" in text else 0.0
        
        # Exclamation — arousal (emphasis)
        exclamation_arousal = min(text.count("!") * 0.05, 0.2)
        
        # All caps words — arousal (emphasis)
        all_caps = sum(1 for w in text.split() if w.isupper() and len(w) > 1) * 0.1
        caps_arousal = min(all_caps, 0.3)
        
        target_arousal = min(
            1.0, 
            arousal_score + length_arousal + question_arousal + 
            exclamation_arousal + caps_arousal
        )
        target_valence = np.clip(pos_score - neg_score, -1.0, 1.0)
        
        # Smooth update (don't snap instantly)
        self.state.arousal = 0.7 * self.state.arousal + 0.3 * target_arousal
        self.state.valence = 0.7 * self.state.valence + 0.3 * target_valence
        
        # Clip to valid ranges
        self.state.arousal = np.clip(self.state.arousal, 0.0, 1.0)
        self.state.valence = np.clip(self.state.valence, -1.0, 1.0)
        
        # Store in history
        self._history.append(AffectiveState(
            valence=self.state.valence,
            arousal=self.state.arousal
        ))
        
        # Keep history manageable
        if len(self._history) > 100:
            self._history = self._history[-100:]
        
        return self.state
    
    def thinking_steps_for_salience(self, base_steps: int = 500) -> int:
        """
        High-salience inputs deserve more simulation time.
        A distressed user gets 3× the normal processing depth.
        
        Parameters
        ----------
        base_steps : int
            Base number of simulation steps
            
        Returns
        -------
        int
            Adjusted number of steps
        """
        multiplier = 1.0 + self.state.arousal * 2.0
        return int(base_steps * multiplier)
    
    def decay(self):
        """Called after each turn — affect returns toward baseline."""
        self.state.arousal *= self._decay_rate
        self.state.valence *= self._decay_rate * 0.5  # Valence decays slower
        
        # Drift toward neutral
        self.state.arousal = np.clip(self.state.arousal, 0.0, 1.0)
        self.state.valence = np.clip(self.state.valence, -1.0, 1.0)
    
    def apply_user_feedback(self, valence: float):
        """
        Update affect based on user feedback.
        
        Parameters
        ----------
        valence : float
            User feedback (-1 to 1)
        """
        if valence > 0:
            self.state.valence = 0.7 * self.state.valence + 0.3 * min(valence, 1.0)
        else:
            self.state.valence = 0.7 * self.state.valence + 0.3 * max(valence, -1.0)
        
        self.state.arousal = np.clip(self.state.arousal, 0.0, 1.0)
        self.state.valence = np.clip(self.state.valence, -1.0, 1.0)
    
    def get_state(self) -> AffectiveState:
        """Get current affective state."""
        return self.state
    
    def get_average_arousal(self, n: int = 10) -> float:
        """Get average arousal over last n inputs."""
        if not self._history:
            return 0.3
        recent = self._history[-n:]
        return sum(s.arousal for s in recent) / len(recent)
    
    def get_average_valence(self, n: int = 10) -> float:
        """Get average valence over last n inputs."""
        if not self._history:
            return 0.0
        recent = self._history[-n:]
        return sum(s.valence for s in recent) / len(recent)


def create_salience_filter() -> SalienceFilter:
    """Create a default salience filter."""
    return SalienceFilter()


if __name__ == "__main__":
    # Test the SalienceFilter
    filter = create_salience_filter()
    
    test_inputs = [
        "Hello, how are you?",
        "This is terrible and I hate it!",
        "Thanks, that's perfect!",
        "Please help me, it's urgent and important!",
        "Just wanted to say thanks for your help.",
    ]
    
    for text in test_inputs:
        state = filter.assess(text)
        steps = filter.thinking_steps_for_salience(500)
        print(f"Input: {text}")
        print(f"  Valence: {state.valence:+.2f}, Arousal: {state.arousal:.2f}")
        print(f"  Thinking steps: {steps}")
        print(f"  Prompt fragment: {state.to_prompt_fragment()}")
        print()
