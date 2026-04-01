"""
codec/llm_codec.py — LLM Codec for Multiple Backends
===================================================
The ONLY place in the codebase where an LLM is called.
Supports: Local Ollama, OpenAI, Anthropic, or None (SNN-only)
"""

import json
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import requests

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LLM_CONFIG


@dataclass
class CodecResult:
    """Result of LLM generation."""
    text: str
    path: str  # "llm", "local", "cached"
    cost: float
    model: str
    backend: str


class LLMCodec:
    """
    The ONLY place in the codebase where an LLM is called.
    
    Supports multiple backends:
    - local_ollama: Local Ollama instance
    - openai: OpenAI API (GPT-4o, etc.)
    - anthropic: Anthropic API (Claude)
    - none: No LLM (SNN-only mode)
    
    Single responsibility: brain state → natural language.
    """
    
    def __init__(self):
        self.config = LLM_CONFIG
        self.gate = None  # Set externally
        self.phon_buffer = None  # Set externally
        self.cost_tracker = None  # Set externally
        
        # Response cache
        self._response_cache: Dict[str, str] = {}
        self._cache_max_size = 100
    
    def set_components(self, gate, phon_buffer, cost_tracker):
        """Set the gate, phonological buffer, and cost tracker."""
        self.gate = gate
        self.phon_buffer = phon_buffer
        self.cost_tracker = cost_tracker
    
    def articulate(
        self,
        brain_state: Dict[str, Any],
        force_local: bool = False,
        force_llm: bool = False,
    ) -> CodecResult:
        """
        Convert brain state to natural language.
        
        Parameters
        ----------
        brain_state : dict
            Current brain state
        force_local : bool
            Force local generation (no LLM)
        force_llm : bool
            Force LLM generation
            
        Returns
        -------
        CodecResult
            Generated text and metadata
        """
        # Check cache first
        cache_key = self._cache_key(brain_state)
        if cache_key in self._response_cache and not force_llm:
            return CodecResult(
                text=self._response_cache[cache_key],
                path="cached",
                cost=0.0,
                model="cache",
                backend="cache",
            )
        
        # Check gate decision
        should_call_llm = False
        if force_llm:
            should_call_llm = True
        elif not force_local and self.gate:
            gate_decision = self.gate.should_call_llm(brain_state)
            should_call_llm = gate_decision.should_call_llm
        elif force_local:
            should_call_llm = False
        
        # Generate response
        if should_call_llm:
            return self._llm_articulate(brain_state)
        else:
            return self._local_articulate(brain_state)
    
    def _cache_key(self, state: Dict[str, Any]) -> str:
        """Generate cache key from brain state."""
        key_parts = [
            str(state.get("active_concept_neuron", -1)),
            str(state.get("concept_layer_activity", 0)),
            str(state.get("confidence", 0)),
        ]
        return "|".join(key_parts)
    
    def _local_articulate(self, state: Dict[str, Any]) -> CodecResult:
        """Generate response using phonological buffer (local)."""
        if self.phon_buffer:
            text = self.phon_buffer.generate(state)
        else:
            text = "[No phonological buffer available]"
        
        # Cache the response
        cache_key = self._cache_key(state)
        if len(self._response_cache) < self._cache_max_size:
            self._response_cache[cache_key] = text
        
        return CodecResult(
            text=text,
            path="local",
            cost=0.0,
            model="phon_buffer",
            backend="local",
        )
    
    def _llm_articulate(self, state: Dict[str, Any]) -> CodecResult:
        """Generate response using configured LLM backend."""
        prompt = self._build_minimal_prompt(state)
        model = self.config.get_default_model()
        
        # Route to appropriate backend
        if self.config.backend == "local_ollama":
            return self._call_ollama(prompt, model, state)
        elif self.config.backend == "openai":
            return self._call_openai(prompt, model, state)
        elif self.config.backend == "anthropic":
            return self._call_anthropic(prompt, model, state)
        else:
            return CodecResult(
                text="[LLM disabled - SNN-only mode]",
                path="llm",
                cost=0.0,
                model="none",
                backend="none",
            )
    
    def _build_minimal_prompt(self, state: Dict[str, Any]) -> str:
        """
        Build the SMALLEST possible prompt.
        Contain: active concepts, confidence, uncertainty.
        NEVER include: raw user message, conversation history,
                       instructions to reason, instructions to add knowledge.
        """
        concept = state.get("active_concept_neuron", -1)
        confidence = state.get("confidence", 0.5)
        uncertainty = state.get("uncertainty", 0.5)
        memory = state.get("memory_snippet", "none")
        
        return f"""Brain state to articulate:
Active concept: #{concept}
Confidence: {confidence:.0%}
Uncertainty: {uncertainty:.0%}
Memory: {memory}

Articulate as natural language in 1-3 sentences. No added reasoning."""
    
    def _call_ollama(
        self,
        prompt: str,
        model: str,
        state: Dict[str, Any],
    ) -> CodecResult:
        """Call local Ollama instance."""
        url = f"{self.config.ollama_base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False,
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout,
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("response", "").strip()
                
                # Track cost (Ollama is free but we track tokens conceptually)
                tokens_in = len(prompt.split())
                tokens_out = len(text.split())
                
                if self.cost_tracker:
                    # Use 0 cost for local models
                    self.cost_tracker.track_call(tokens_in, tokens_out, model)
                
                # Cache the response
                cache_key = self._cache_key(state)
                if len(self._response_cache) < self._cache_max_size:
                    self._response_cache[cache_key] = text
                
                return CodecResult(
                    text=text,
                    path="llm",
                    cost=0.0,  # Local model
                    model=model,
                    backend="local_ollama",
                )
            else:
                return CodecResult(
                    text=f"[Ollama error: {response.status_code}]",
                    path="llm",
                    cost=0.0,
                    model=model,
                    backend="local_ollama",
                )
        except requests.exceptions.Timeout:
            return CodecResult(
                text="[Ollama timeout]",
                path="llm",
                cost=0.0,
                model=model,
                backend="local_ollama",
            )
        except Exception as e:
            return CodecResult(
                text=f"[Ollama error: {str(e)}]",
                path="llm",
                cost=0.0,
                model=model,
                backend="local_ollama",
            )
    
    def _call_openai(
        self,
        prompt: str,
        model: str,
        state: Dict[str, Any],
    ) -> CodecResult:
        """Call OpenAI API."""
        # This would need API key - placeholder
        return CodecResult(
            text="[OpenAI not configured - set OPENAI_API_KEY]",
            path="llm",
            cost=0.0,
            model=model,
            backend="openai",
        )
    
    def _call_anthropic(
        self,
        prompt: str,
        model: str,
        state: Dict[str, Any],
    ) -> CodecResult:
        """Call Anthropic API."""
        # This would need API key - placeholder
        return CodecResult(
            text="[Anthropic not configured - set ANTHROPIC_API_KEY]",
            path="llm",
            cost=0.0,
            model=model,
            backend="anthropic",
        )
    
    def clear_cache(self):
        """Clear response cache."""
        self._response_cache.clear()
    
    def get_cache_size(self) -> int:
        """Get current cache size."""
        return len(self._response_cache)


def create_llm_codec() -> LLMCodec:
    """Create a default LLM codec."""
    return LLMCodec()


if __name__ == "__main__":
    # Test the LLM Codec
    codec = create_llm_codec()
    
    # Test configuration
    print("Testing LLM Configuration:")
    print("-" * 40)
    print(f"Backend: {LLM_CONFIG.backend}")
    print(f"Default model: {LLM_CONFIG.get_default_model()}")
    print(f"Ollama URL: {LLM_CONFIG.ollama_base_url}")
    print(f"Available models: {LLM_CONFIG.get_all_models()}")
    
    # Test if Ollama is available
    if LLM_CONFIG.is_ollama_available():
        print(f"\nOllama is AVAILABLE at {LLM_CONFIG.ollama_base_url}")
        print(f"Available models: {LLM_CONFIG.list_ollama_models()}")
    else:
        print(f"\nOllama is NOT available at {LLM_CONFIG.ollama_base_url}")
    
    # Test articulation
    test_state = {
        "active_concept_neuron": 42,
        "concept_layer_activity": 0.5,
        "confidence": 0.75,
        "uncertainty": 0.2,
        "memory_snippet": "user asked about weather",
    }
    
    print("\n\nTesting articulation:")
    result = codec.articulate(test_state, force_local=True)
    print(f"Local result: {result.text}")
    print(f"Path: {result.path}")
