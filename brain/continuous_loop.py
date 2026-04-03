"""
brain/continuous_loop.py — Continuous Existence Loop
====================================================
Runs brain simulation 24/7 with different modes.
"""

import time
import threading
import numpy as np
import requests
from typing import Optional, Any


def _post_proactive(message: str):
    """Post a proactive message to the API queue (fire-and-forget)."""
    try:
        import os
        import requests
        port = int(os.getenv("API_PORT", "8000"))
        requests.post(
            f"http://127.0.0.1:{port}/api/proactive",
            json={"message": message},
            timeout=1.0,
        )
    except Exception:
        pass  # API may not be ready or loop may be running standalone


class ContinuousExistenceLoop:
    """
    Runs 24/7 in a daemon thread.
    Three modes:
      ACTIVE:  user is present. Full simulation speed.
      IDLE:    no user for >60s. Slow wandering. Memory consolidation.
      DORMANT: no user for >1h. Minimal ticking. Weight decay only.
    
    All three modes run. The brain never stops.
    """
    
    ACTIVE_STEPS_PER_TICK = 200
    IDLE_STEPS_PER_TICK = 20
    DORMANT_STEPS_PER_TICK = 2
    
    IDLE_THRESHOLD_S = 60
    DORMANT_THRESHOLD_S = 3600
    
    def __init__(self, brain: Optional[Any] = None):
        self.brain = brain
        self.last_input = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._mode = "DORMANT"
        
        # Configuration
        self.active_sleep = 0.05
        self.idle_sleep = 0.5
        self.dormant_sleep = 2.0
        
        # Statistics
        self.total_ticks = 0
        self.ticks_per_mode = {"ACTIVE": 0, "IDLE": 0, "DORMANT": 0}
        self.start_time = time.time()
        
        # Proactive message throttle (post ~every N idle/dormant ticks)
        self._proactive_tick = 0
    
    def notify_user_active(self):
        """Call when user sends a message."""
        self.last_input = time.time()
    
    def _current_mode(self) -> str:
        """Determine current mode based on time since last input."""
        idle = time.time() - self.last_input
        if idle < self.IDLE_THRESHOLD_S:
            return "ACTIVE"
        if idle < self.DORMANT_THRESHOLD_S:
            return "IDLE"
        return "DORMANT"
    
    def _loop(self):
        """Main loop running in background thread."""
        while self._running:
            mode = self._current_mode()
            self._mode = mode
            
            # Get steps for this mode
            steps = {
                "ACTIVE": self.ACTIVE_STEPS_PER_TICK,
                "IDLE": self.IDLE_STEPS_PER_TICK,
                "DORMANT": self.DORMANT_STEPS_PER_TICK,
            }[mode]
            
            try:
                if self.brain:
                    acquired = self.brain._lock.acquire(timeout=0.01)
                    if not acquired:
                        time.sleep(0.01)
                        continue
                    try:
                        for _ in range(steps):
                            self.brain.step()
                        if mode == "IDLE":
                            self._idle_behaviours()
                        elif mode == "DORMANT":
                            self._dormant_behaviours()
                        if hasattr(self.brain, 'self_model') and self.brain.self_model.total_steps % 10_000 == 0:
                            if hasattr(self.brain, 'persist'):
                                self.brain.persist()
                    finally:
                        self.brain._lock.release()
                    
                    self.total_ticks += 1
                    self.ticks_per_mode[mode] += 1

            except Exception as e:
                print(f"Error in continuous loop: {e}")
            
            # Sleep between ticks
            sleep_time = {
                "ACTIVE": self.active_sleep,
                "IDLE": self.idle_sleep,
                "DORMANT": self.dormant_sleep,
            }[mode]
            time.sleep(sleep_time)
    
    def _idle_behaviours(self):
        """
        During idle: spontaneous association wandering + memory replay.
        Brain randomly activates a recent concept and lets it
        spread through association cortex (free association).
        Biologically: default mode network activity + memory consolidation.
        """
        if not self.brain:
            return
        
        brain = self.brain
        
        # Try to activate a random recent concept from concept layer
        try:
            if hasattr(brain, 'concept') and hasattr(brain.concept, '_concept_id'):
                concept_id = brain.concept._concept_id
                if concept_id >= 0:
                    # Activate this concept in association region
                    if hasattr(brain, 'assoc') and hasattr(brain.assoc, 'population'):
                        target_idx = concept_id % brain.assoc.n
                        brain.assoc.population.inject_current(
                            np.array([target_idx]), 10.0
                        )
        except Exception as e:
            print(f"[ContinuousLoop] Idle behaviour error: {e}")
        
        # v0.2: Memory replay — re-encode 1-3 recent episodes during idle
        # Biologically: hippocampal replay during quiet wakefulness
        replayed = 0
        try:
            if hasattr(brain, 'hippocampus') and hasattr(brain, 'concept'):
                recent = brain.hippocampus.get_recent(3)
                for ep in recent:
                    if ep.neuron_ids:
                        # Re-inject concept neurons from episode
                        valid_ids = [n % brain.concept.n for n in ep.neuron_ids[:5]]
                        brain.concept.population.inject_current(
                            np.array(valid_ids, dtype=np.int32), 5.0
                        )
                        replayed += 1
        except Exception:
            pass
        
        # Recover energy
        if hasattr(brain, 'self_model'):
            brain.self_model.recover_energy(0.5)
        
        # Proactive messages (throttled: ~every 8 idle ticks)
        self._proactive_tick += 1
        if self._proactive_tick % 8 == 0:
            self._post_spontaneous_thought(mode="IDLE", replayed=replayed)
    
    def _dormant_behaviours(self):
        """
        During dormant: slow homeostatic decay + episode pruning.
        Weights that haven't been used recently decay slightly.
        Biologically: offline consolidation, synaptic downscaling.
        """
        if not self.brain:
            return
        
        brain = self.brain
        
        # Slow weight decay
        if hasattr(brain, 'all_synapses'):
            for syn in brain.all_synapses:
                syn.weights *= 0.9999
        
        # v0.2: Prune weakest episodes during dormant
        try:
            if hasattr(brain, 'hippocampus'):
                brain.hippocampus.prune_weakest(keep_fraction=0.8)
        except Exception:
            pass
        
        # Recover energy
        if hasattr(brain, 'self_model'):
            brain.self_model.recover_energy(0.5)
        
        # Proactive messages (throttled: ~every 20 dormant ticks)
        self._proactive_tick += 1
        if self._proactive_tick % 20 == 0:
            self._post_spontaneous_thought(mode="DORMANT")

    def _post_spontaneous_thought(self, mode: str, replayed: int = 0):
        brain = self.brain
        if not brain:
            return
        try:
            snapshot = brain.snapshot()
            vocab_size = brain.phon_buffer.get_vocabulary_size() if hasattr(brain, 'phon_buffer') else 0
            recent_topics = []
            if hasattr(brain, 'hippocampus'):
                recent = brain.hippocampus.get_recent(3)
                recent_topics = [ep.topic for ep in recent if ep.topic]
            topics_str = ', '.join(recent_topics) if recent_topics else 'nothing specific'
            idle_prompt = (
                f"You are BRAIN 2.0, currently {brain.self_model.brain_stage}. "
                f"Mode: {mode}. Vocabulary size: {vocab_size}. "
                f"Recent topics: {topics_str}. "
                f"If replayed memories exist, mention them. Be concise (<=15 words)."
            )
            from config import LLM_CONFIG
            if LLM_CONFIG.is_ollama_available():
                model = LLM_CONFIG.get_best_available_model()
                response = requests.post(
                    f"{LLM_CONFIG.ollama_base_url}/api/generate",
                    json={"model": model, "prompt": idle_prompt, "stream": False},
                    timeout=10
                )
                if response.status_code == 200:
                    thought = response.json().get("response", "").strip()
                    if thought:
                        _post_proactive(thought)
                        return
        except Exception:
            pass
        if replayed > 0:
            _post_proactive(f"Replayed {replayed} memory{'ies' if replayed != 1 else ''} while idle")
        elif hasattr(brain, 'self_model'):
            energy = getattr(brain.self_model, 'energy', 50)
            _post_proactive(f"Energy recovering at {energy:.0f}% in {mode.lower()} mode")
    
    def start(self):
        """Start the continuous loop in a background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[ContinuousLoop] Started in {self._mode} mode")
    
    def stop(self):
        """Stop the continuous loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("[ContinuousLoop] Stopped")
    
    def get_status(self) -> dict:
        """Get loop status."""
        return {
            "running": self._running,
            "mode": self._mode,
            "last_input_ago_s": round(time.time() - self.last_input, 1),
            "total_ticks": self.total_ticks,
            "ticks_per_mode": self.ticks_per_mode.copy(),
            "uptime_s": round(time.time() - self.start_time, 1),
        }
    
    def is_running(self) -> bool:
        """Check if loop is running."""
        return self._running


# Type hint for Any (to avoid circular imports)
from typing import Any


def create_continuous_loop(brain: Any) -> ContinuousExistenceLoop:
    """Create a default continuous loop."""
    return ContinuousExistenceLoop(brain)


if __name__ == "__main__":
    # Test the ContinuousExistenceLoop
    loop = ContinuousExistenceLoop()
    
    print("Testing loop modes:")
    print(f"  Mode now (no input): {loop._current_mode()}")
    
    loop.notify_user_active()
    print(f"  Mode after user active: {loop._current_mode()}")
    
    # Test status
    loop.total_ticks = 100
    loop.ticks_per_mode = {"ACTIVE": 50, "IDLE": 30, "DORMANT": 20}
    
    print(f"\nStatus: {loop.get_status()}")
