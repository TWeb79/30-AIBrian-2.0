"""
codec/llm_gate.py — LLM Call Decision Gate
==========================================
Decides when to call the LLM vs. using local generation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class GateDecision:
    """Result of a gate decision."""
    should_call_llm: bool
    reason: str
    confidence: float = 0.0
    uncertainty: float = 1.0


class LLMGate:
    """
    Hard gate controlling when the LLM is invoked.
    
    Default: SNN generates response from phonological buffer (no LLM).
    LLM only called for fluent natural language output.
    """
    
    def __init__(
        self,
        min_confidence: float = 0.4,
        recall_confidence: float = 0.85,
        max_uncertainty: float = 0.15,
        rate_limit_seconds: float = 3.0,
    ):
        self.min_confidence = min_confidence
        self.recall_confidence = recall_confidence
        self.max_uncertainty = max_uncertainty
        self.rate_limit_seconds = rate_limit_seconds
        
        self._last_call_time: float = 0.0
        self._total_decisions = 0
        self._llm_calls = 0
        self._local_calls = 0
    
    def should_call_llm(
        self,
        brain_state: Dict[str, Any],
        force_local: bool = False,
    ) -> GateDecision:
        """
        Decide whether to call the LLM.
        
        Parameters
        ----------
        brain_state : dict
            Current brain state with keys like:
            - confidence: float (0-1)
            - uncertainty: float (0-1)
            - expects_text: bool
            - prediction_confidence: float
            - is_recall: bool
        force_local : bool
            Force local generation (ignore gate)
            
        Returns
        -------
        GateDecision
            The decision result
        """
        self._total_decisions += 1
        
        if force_local:
            self._local_calls += 1
            return GateDecision(
                should_call_llm=False,
                reason="force_local=True",
            )
        
        # Condition 1: Rate limit check
        import time
        now = time.time()
        if now - self._last_call_time < self.rate_limit_seconds:
            # Too soon after last call - use local
            self._local_calls += 1
            return GateDecision(
                should_call_llm=False,
                reason="rate_limited",
            )
        
        # Condition 2: User expects text response
        expects_text = brain_state.get("expects_text", True)
        if not expects_text:
            self._local_calls += 1
            return GateDecision(
                should_call_llm=False,
                reason="not_text_response",
            )
        
        # Condition 3: Brain has reached stable concept activation
        confidence = brain_state.get("confidence", 0.0)
        prediction_confidence = brain_state.get("prediction_confidence", confidence)
        
        if prediction_confidence < self.min_confidence:
            self._local_calls += 1
            return GateDecision(
                should_call_llm=False,
                reason="low_confidence",
                confidence=prediction_confidence,
            )
        
        # Condition 4: Simple recall (direct memory lookup)
        is_recall = brain_state.get("is_recall", False)
        uncertainty = brain_state.get("uncertainty", 1.0)
        
        if is_recall and confidence > self.recall_confidence and uncertainty < self.max_uncertainty:
            self._local_calls += 1
            return GateDecision(
                should_call_llm=False,
                reason="direct_recall",
                confidence=confidence,
                uncertainty=uncertainty,
            )
        
        # All conditions passed - call LLM
        self._llm_calls += 1
        self._last_call_time = now
        
        return GateDecision(
            should_call_llm=True,
            reason="all_conditions_met",
            confidence=prediction_confidence,
            uncertainty=uncertainty,
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics."""
        total = self._total_decisions
        if total == 0:
            return {
                "total_decisions": 0,
                "llm_calls": 0,
                "local_calls": 0,
                "llm_call_rate": 0.0,
            }
        
        return {
            "total_decisions": total,
            "llm_calls": self._llm_calls,
            "local_calls": self._local_calls,
            "llm_call_rate": self._llm_calls / total,
        }
    
    def reset_statistics(self):
        """Reset statistics."""
        self._total_decisions = 0
        self._llm_calls = 0
        self._local_calls = 0
    
    def force_llm_next_call(self):
        """Force the next call to use LLM (reset rate limit)."""
        self._last_call_time = 0
    
    def is_rate_limited(self) -> bool:
        """Check if currently rate limited."""
        import time
        now = time.time()
        return (now - self._last_call_time) < self.rate_limit_seconds


def create_llm_gate() -> LLMGate:
    """Create a default LLM gate."""
    return LLMGate()


if __name__ == "__main__":
    # Test the LLMGate
    gate = create_llm_gate()
    
    test_states = [
        {"confidence": 0.3, "prediction_confidence": 0.3, "expects_text": True},
        {"confidence": 0.5, "prediction_confidence": 0.5, "expects_text": True},
        {"confidence": 0.9, "prediction_confidence": 0.9, "is_recall": True, "uncertainty": 0.1},
        {"confidence": 0.6, "prediction_confidence": 0.6, "expects_text": True},
        {"confidence": 0.7, "prediction_confidence": 0.7, "expects_text": False},
    ]
    
    for state in test_states:
        decision = gate.should_call_llm(state)
        print(f"State: {state}")
        print(f"  Decision: {decision.should_call_llm} - {decision.reason}")
        print()
    
    print(f"Stats: {gate.get_statistics()}")
