"""
cognition/attractor_chainer.py — Attractor Chain Module
========================================================
Records transitions between cell assemblies to enable sequential thinking.
This enables multi-word local generation without LLM by chaining 
assembly→word→next assembly→next word patterns.

Usage:
    chainer = AttractorChainer()
    chainer.record_transition(from_assembly_id, to_assembly_id, dt_ms=100)
    predictions = chainer.predict_next(current_assembly_id, top_k=3)
"""

from typing import Dict, List, Tuple, Optional


class AttractorChainer:
    """
    Tracks transitions between cell assemblies.
    
    When assembly A consistently precedes assembly B, a transition
    weight is strengthened. This forms an "attractor chain" - the
    brain's internal sequence model.
    
    Key methods:
    - record_transition(): Learn that A → B
    - predict_next(): Given current assembly, what assemblies follow?
    - get_sequence(): Generate a multi-step prediction
    """
    
    def __init__(
        self,
        decay_rate: float = 0.95,
        temporal_window_ms: float = 500.0,
        learning_rate: float = 0.10,
    ):
        """
        Parameters
        ----------
        decay_rate : float
            Transitions decay over time if not reinforced
        temporal_window_ms : float
            Only learn transitions within this time window
        learning_rate : float
            How quickly transition weights update
        """
        self.decay_rate = decay_rate
        self.temporal_window_ms = temporal_window_ms
        self.learning_rate = learning_rate
        
        # Transitions: from_id → {to_id: weight}
        self.transitions: Dict[int, Dict[int, float]] = {}
        
        # Last recorded assembly for timing
        self._last_assembly_id: Optional[int] = None
        self._last_timestamp_ms: float = 0.0
        
        # Statistics
        self._total_transitions: int = 0
    
    def record_transition(self, from_id: int, to_id: int, dt_ms: float) -> bool:
        """
        Record that assembly `from_id` was followed by `to_id`.
        
        Parameters
        ----------
        from_id : int
            Source assembly ID
        to_id : int
            Target assembly ID
        dt_ms : float
            Time elapsed since last transition (milliseconds)
            
        Returns
        -------
        bool
            True if transition was recorded
        """
        if from_id < 0 or to_id < 0:
            return False
        
        # Only learn within temporal window
        if dt_ms > self.temporal_window_ms:
            return False
        
        # Initialize if needed
        if from_id not in self.transitions:
            self.transitions[from_id] = {}
        
        # Update weight (increase)
        current = self.transitions[from_id].get(to_id, 0.0)
        self.transitions[from_id][to_id] = min(
            1.0, 
            current + self.learning_rate
        )
        
        self._total_transitions += 1
        return True
    
    def record_assembly(self, assembly_id: int, current_time_ms: float):
        """
        Record current assembly and optionally create transition from previous.
        
        Call this when a new assembly becomes active. It will:
        1. Record a transition from the previous assembly (if within window)
        2. Update state for next call
        
        Parameters
        ----------
        assembly_id : int
            The current active assembly
        current_time_ms : float
            Current timestamp in milliseconds
        """
        if self._last_assembly_id is not None and assembly_id >= 0:
            dt_ms = current_time_ms - self._last_timestamp_ms
            self.record_transition(self._last_assembly_id, assembly_id, dt_ms)
        
        self._last_assembly_id = assembly_id
        self._last_timestamp_ms = current_time_ms
    
    def predict_next(self, current_id: int, top_k: int = 3) -> List[Tuple[int, float]]:
        """
        Predict assemblies that follow the current one.
        
        Parameters
        ----------
        current_id : int
            Current assembly ID
        top_k : int
            Number of top predictions to return
            
        Returns
        -------
        list[tuple[int, float]]
            List of (assembly_id, probability) sorted by weight desc
        """
        if current_id < 0 or current_id not in self.transitions:
            return []
        
        t = self.transitions[current_id]
        sorted_items = sorted(t.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:top_k]
    
    def get_sequence(
        self, 
        start_id: int, 
        length: int = 3,
        temperature: float = 1.0
    ) -> List[int]:
        """
        Generate a sequence of assemblies starting from start_id.
        
        Parameters
        ----------
        start_id : int
            Starting assembly ID
        length : int
            Number of assemblies to predict
        temperature : float
            Sampling temperature (1.0 = deterministic, >0 = more random)
            
        Returns
        -------
        list[int]
            Sequence of assembly IDs
        """
        if start_id < 0:
            return []
        
        sequence = [start_id]
        current = start_id
        
        for _ in range(length - 1):
            preds = self.predict_next(current, top_k=5)
            if not preds:
                break
            
            if temperature == 1.0:
                # Deterministic: take top
                current = preds[0][0]
            else:
                # Stochastic: sample from distribution
                import random
                weights = [p[1] ** (1/temperature) for p in preds]
                total = sum(weights)
                probs = [w/total for w in weights]
                current = random.choices([p[0] for p in preds], weights=probs)[0]
            
            if current < 0:
                break
            sequence.append(current)
        
        return sequence
    
    def get_transition_count(self, from_id: int) -> int:
        """Get number of outgoing transitions from an assembly."""
        if from_id not in self.transitions:
            return 0
        return len(self.transitions[from_id])
    
    def get_total_transitions(self) -> int:
        """Get total number of recorded transitions."""
        return self._total_transitions
    
    def get_statistics(self) -> Dict:
        """Get statistics about the chainer."""
        all_targets = set()
        for t in self.transitions.values():
            all_targets.update(t.keys())
        
        return {
            "total_source_assemblies": len(self.transitions),
            "total_unique_targets": len(all_targets),
            "total_transitions": self._total_transitions,
        }
    
    def export(self) -> Dict:
        """Export for persistence."""
        return {
            "transitions": {str(k): v for k, v in self.transitions.items()},
            "decay_rate": self.decay_rate,
            "temporal_window_ms": self.temporal_window_ms,
            "learning_rate": self.learning_rate,
        }
    
    def import_(self, data: Dict):
        """Import from persistence."""
        if "transitions" in data:
            self.transitions = {int(k): v for k, v in data["transitions"].items()}
        if "decay_rate" in data:
            self.decay_rate = data["decay_rate"]
        if "temporal_window_ms" in data:
            self.temporal_window_ms = data["temporal_window_ms"]
        if "learning_rate" in data:
            self.learning_rate = data["learning_rate"]


def create_attractor_chainer() -> AttractorChainer:
    """Create a default attractor chainer."""
    return AttractorChainer()


if __name__ == "__main__":
    # Test the AttractorChainer
    chainer = create_attractor_chainer()
    
    # Simulate transitions
    print("Recording transitions...")
    chainer.record_transition(0, 1, dt_ms=100)
    chainer.record_transition(1, 2, dt_ms=80)
    chainer.record_transition(2, 3, dt_ms=120)
    chainer.record_transition(0, 2, dt_ms=150)
    chainer.record_transition(1, 3, dt_ms=90)
    
    print(f"\nStatistics: {chainer.get_statistics()}")
    
    print("\nPredictions from assembly 0:")
    preds = chainer.predict_next(0, top_k=3)
    for p in preds:
        print(f"  → Assembly {p[0]}: weight {p[1]:.2f}")
    
    print("\nPredictions from assembly 1:")
    preds = chainer.predict_next(1, top_k=3)
    for p in preds:
        print(f"  → Assembly {p[0]}: weight {p[1]:.2f}")
    
    print("\nGenerated sequence from 0:")
    seq = chainer.get_sequence(0, length=4)
    print(f"  {' → '.join(map(str, seq))}")