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
        
        # Use auto-detected best model if Ollama is available
        if self.config.backend == "local_ollama" and self.config.is_ollama_available():
            model = self.config.get_best_available_model()
        else:
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
        Build a context-aware prompt from brain state.
        Includes: user message, conversation history, drives, affect, memory.
        """
        message   = state.get("message", "")
        concept   = state.get("active_concept_neuron", -1)
        confidence = state.get("confidence", 0.5)
        memory    = state.get("memory_snippet", "")
        stage     = state.get("brain_stage", "NEONATAL")
        total_turns = state.get("total_turns", 0)
        vocab_size  = state.get("vocabulary_size", 0)
        drives    = state.get("drives", {})
        affect    = state.get("affect", {})
        history   = state.get("chat_history", [])

        # Drive-aware context instructions
        context_parts = []
        if memory and memory != "none" and memory != "":
            context_parts.append(f"Memory: {memory}")
        if drives.get("curiosity", 0) > 0.7:
            context_parts.append("Express curiosity, ask a follow-up question.")
        if drives.get("connection", 0) > 0.6:
            context_parts.append("Be warm and personal.")
        if affect.get("arousal", 0) > 0.6 and affect.get("valence", 0) < -0.2:
            context_parts.append("User seems stressed — be calm and supportive.")
        context_str = "\n".join(context_parts)

        # Conversation history
        history_str = ""
        if history:
            lines = []
            for h in history[-6:]:
                role = "User" if h.get("role") == "user" else "Brain"
                lines.append(f"{role}: {h.get('content', '')[:120]}")
            history_str = "Recent conversation:\n" + "\n".join(lines) + "\n\n"

        return f"""You are BRAIN 2.0, currently in {stage} stage.
You have had {total_turns} conversations. Your vocabulary has {vocab_size} words. Your confidence is {confidence:.0%}.
{context_str}
{history_str}
User said: {message}

Respond naturally in 2-4 sentences. Be genuine and conversational.
Do not mention being an AI. Respond as yourself."""
    
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
                # Log detailed error for debugging
                error_detail = response.text if response.text else "empty response"
                print(f"[Ollama] Error {response.status_code}: {error_detail}")
                print(f"[Ollama] URL: {url}")
                print(f"[Ollama] Model: {model}")
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
        # Use REST call so dependency on official client is optional
        api_key = self.config.openai_api_key
        if not api_key:
            return CodecResult(
                text="[OpenAI not configured - set OPENAI_API_KEY]",
                path="llm",
                cost=0.0,
                model=model,
                backend="openai",
            )

        url = f"{self.config.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        try:
            start = time.time()
            resp = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)
            elapsed = time.time() - start
            if resp.status_code != 200:
                return CodecResult(text=f"[OpenAI error: {resp.status_code}]", path="llm", cost=0.0, model=model, backend="openai")
            data = resp.json()
            # Extract text (chat completion)
            text = ""
            if "choices" in data and len(data["choices"]) > 0:
                ch = data["choices"][0]
                # Newer API uses message -> content
                msg = ch.get("message") or ch.get("delta") or {}
                if isinstance(msg, dict):
                    text = (msg.get("content") or "").strip()
                else:
                    text = str(ch.get("text", "")).strip()

            # Estimate cost from usage if available
            cost = 0.0
            usage = data.get("usage")
            if usage and self.cost_tracker:
                # Track token usage
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                self.cost_tracker.track_call(prompt_tokens, completion_tokens, model)
            return CodecResult(text=text, path="llm", cost=cost, model=model, backend="openai")
        except Exception as e:
            return CodecResult(text=f"[OpenAI error: {e}]", path="llm", cost=0.0, model=model, backend="openai")
    
    def _call_anthropic(
        self,
        prompt: str,
        model: str,
        state: Dict[str, Any],
    ) -> CodecResult:
        """Call Anthropic API."""
        api_key = self.config.anthropic_api_key
        if not api_key:
            return CodecResult(
                text="[Anthropic not configured - set ANTHROPIC_API_KEY]",
                path="llm",
                cost=0.0,
                model=model,
                backend="anthropic",
            )

        # Anthropic REST endpoint
        url = "https://api.anthropic.com/v1/complete"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
        }
        # Anthropic expects a prompt with assistant/human roles often; use a simple wrapper
        anthropic_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"
        payload = {
            "model": model,
            "prompt": anthropic_prompt,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)
            if resp.status_code != 200:
                return CodecResult(text=f"[Anthropic error: {resp.status_code}]", path="llm", cost=0.0, model=model, backend="anthropic")
            data = resp.json()
            text = data.get("completion", "").strip() if isinstance(data, dict) else ""
            # Track cost if possible (Anthropic may return token counts)
            if self.cost_tracker and isinstance(data, dict):
                # Anthropic may provide "completion_tokens" in some structures
                prompt_tokens = data.get("prompt_tokens", 0)
                completion_tokens = data.get("completion_tokens", 0)
                self.cost_tracker.track_call(prompt_tokens, completion_tokens, model)
            return CodecResult(text=text, path="llm", cost=0.0, model=model, backend="anthropic")
        except Exception as e:
            return CodecResult(text=f"[Anthropic error: {e}]", path="llm", cost=0.0, model=model, backend="anthropic")
    
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
