"""
brain/continuous_loop.py — Continuous Existence Loop
====================================================
Runs brain simulation 24/7 with different modes.
"""

import time
import threading
import numpy as np
from typing import Optional, Any


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
                # Run simulation steps
                if self.brain:
                    with self.brain._lock:
                        for _ in range(steps):
                            self.brain.step()
                        
                        # Mode-specific behaviors
                        if mode == "IDLE":
                            self._idle_behaviours()
                        elif mode == "DORMANT":
                            self._dormant_behaviours()
                        
                        # Periodic persistence
                        if hasattr(self.brain, 'self_model'):
                            if self.brain.self_model.total_steps % 10_000 == 0:
                                if hasattr(self.brain, 'persist'):
                                    self.brain.persist()
                
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
        During idle: spontaneous association wandering.
        Brain randomly activates a recent concept and lets it
        spread through association cortex (free association).
        Biologically: default mode network activity.
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
                        print(f"[ContinuousLoop] Idle: activated concept #{concept_id}")
        except Exception as e:
            print(f"[ContinuousLoop] Idle behaviour error: {e}")
        
        # Recover energy
        if hasattr(brain, 'self_model'):
            brain.self_model.recover_energy(0.5)
    
    def _dormant_behaviours(self):
        """
        During dormant: slow homeostatic decay.
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
        
        # Recover energy
        if hasattr(brain, 'self_model'):
            brain.self_model.recover_energy(0.5)
    
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
