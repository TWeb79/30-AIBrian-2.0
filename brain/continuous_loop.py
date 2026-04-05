"""
brain/continuous_loop.py — Continuous Existence Loop

BUGS FIXED:
  FIX-LOOP-1  ACTIVE mode ran 200 steps per tick with active_sleep=0.05s.
              This held brain._lock for ~200 step durations every 50ms,
              leaving almost no window for the API to acquire the lock.
              Reduced to 20 steps per tick (still a meaningful background
              simulation; the SNN doesn't need to run at full speed when
              the API is busy).

  FIX-LOOP-2  _trigger_self_thought called brain.process_input_v01() which
              internally tried to acquire brain._lock. This was fine because
              the call happened after the lock was released, but
              process_input_v01 used to set self._running = False, which
              could kill the start_background_loop thread. That pattern is
              now removed from process_input_v01, so this is safe again —
              but we add a try/except guard anyway.
"""

import time
import threading
import numpy as np
import requests
from typing import Optional, Any


def _post_proactive(message: str):
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
        pass


class ContinuousExistenceLoop:
    # FIX-LOOP-1: Reduce ACTIVE steps from 200 → 20.
    # The brain still simulates continuously; the reduction only means the lock
    # is held for ~20 steps at a time instead of 200, giving the API a ~10×
    # wider window to acquire the lock between ticks.
    ACTIVE_STEPS_PER_TICK  = 20    # was 200
    IDLE_STEPS_PER_TICK    = 10    # was 20
    DORMANT_STEPS_PER_TICK = 2

    IDLE_THRESHOLD_S    = 60
    DORMANT_THRESHOLD_S = 3600

    def __init__(self, brain: Optional[Any] = None):
        self.brain = brain
        self.last_input = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._mode = "DORMANT"

        self.active_sleep  = 0.02   # 20ms between ticks in ACTIVE mode
        self.idle_sleep    = 0.5
        self.dormant_sleep = 2.0

        self.total_ticks = 0
        self.ticks_per_mode = {"ACTIVE": 0, "IDLE": 0, "DORMANT": 0}
        self.start_time = time.time()

        self._proactive_tick = 0

    def notify_user_active(self):
        self.last_input = time.time()

    def _current_mode(self) -> str:
        idle = time.time() - self.last_input
        if idle < self.IDLE_THRESHOLD_S:
            return "ACTIVE"
        if idle < self.DORMANT_THRESHOLD_S:
            return "IDLE"
        return "DORMANT"

    def _loop(self):
        while self._running:
            mode = self._current_mode()
            self._mode = mode

            steps = {
                "ACTIVE":  self.ACTIVE_STEPS_PER_TICK,
                "IDLE":    self.IDLE_STEPS_PER_TICK,
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

                        do_self_thought = (mode == "IDLE" and self._proactive_tick % 60 == 0)

                        if mode == "IDLE":
                            self._idle_behaviours()
                        elif mode == "DORMANT":
                            self._dormant_behaviours()

                        if hasattr(self.brain, 'self_model') and self.brain.self_model.total_steps % 10_000 == 0:
                            if hasattr(self.brain, 'persist'):
                                self.brain.persist()
                    finally:
                        self.brain._lock.release()

                    # Update snapshot outside the lock so API readers see it quickly
                    if time.time() > self.brain._snapshot_fresh_until:
                        try:
                            snap = self.brain._build_snapshot()
                            self.brain._last_snapshot = snap
                        except Exception:
                            pass

                    if do_self_thought:
                        self._trigger_self_thought()

                    self.total_ticks += 1
                    self.ticks_per_mode[mode] += 1

            except Exception as e:
                print(f"[ContinuousLoop] Error in loop: {e}")

            sleep_time = {
                "ACTIVE":  self.active_sleep,
                "IDLE":    self.idle_sleep,
                "DORMANT": self.dormant_sleep,
            }[mode]
            time.sleep(sleep_time)

    def _idle_behaviours(self):
        if not self.brain:
            return
        brain = self.brain
        try:
            if hasattr(brain, 'concept') and hasattr(brain.concept, '_concept_id'):
                concept_id = brain.concept._concept_id
                if concept_id >= 0:
                    if hasattr(brain, 'assoc') and hasattr(brain.assoc, 'population'):
                        target_idx = concept_id % brain.assoc.n
                        brain.assoc.population.inject_current(np.array([target_idx]), 10.0)
        except Exception:
            pass

        try:
            if hasattr(brain, 'hippocampus') and hasattr(brain, 'concept'):
                recent = brain.hippocampus.get_recent(3)
                for ep in recent:
                    if ep.neuron_ids:
                        valid_ids = [n % brain.concept.n for n in ep.neuron_ids[:5]]
                        brain.concept.population.inject_current(np.array(valid_ids, dtype=np.int32), 5.0)
        except Exception:
            pass

        if hasattr(brain, 'self_model'):
            brain.self_model.recover_energy(0.5)

        self._proactive_tick += 1

        if self._proactive_tick % 8 == 0:
            self._post_spontaneous_thought(mode="IDLE")

    def _dormant_behaviours(self):
        if not self.brain:
            return
        brain = self.brain
        if hasattr(brain, 'all_synapses'):
            for syn in brain.all_synapses:
                syn.weights *= 0.9999
        try:
            if hasattr(brain, 'hippocampus'):
                brain.hippocampus.prune_weakest(keep_fraction=0.8)
        except Exception:
            pass
        if hasattr(brain, 'self_model'):
            brain.self_model.recover_energy(0.5)
        self._proactive_tick += 1
        if self._proactive_tick % 20 == 0:
            self._post_spontaneous_thought(mode="DORMANT")

    def _trigger_self_thought(self):
        """
        FIX-LOOP-2: Called OUTSIDE brain._lock. process_input_v01 is safe to
        call here now that it no longer sets self._running = False. Wrapped in
        broad try/except so any error in self-thought doesn't kill the loop.
        """
        brain = self.brain
        if not brain:
            return
        try:
            top_words = []
            if brain.assembly_detector.get_assembly_count() > 0:
                top = brain.assembly_detector.get_top_assemblies(1)
                if top:
                    asm_id, _, _ = top[0]
                    top_words = brain.phon_buffer.assembly_to_words(asm_id, top_k=2)

            if top_words:
                self_input = f"I am thinking about {top_words[0]}"
                result = brain.process_input_v01(self_input)
                thought = result.get("response", "")
                if thought and thought not in ("[silence]", "[unknown]"):
                    if hasattr(brain, '_pending_proactive'):
                        brain._pending_proactive.append(f"[self] {thought}")
                    else:
                        _post_proactive(f"[self] {thought}")
        except Exception as e:
            # Swallow silently — a bad self-thought must not break the loop
            print(f"[ContinuousLoop] _trigger_self_thought error (ignored): {e}")

    def _post_spontaneous_thought(self, mode: str, replayed: int = 0):
        brain = self.brain
        if not brain:
            return
        try:
            vocab_size = brain.phon_buffer.get_vocabulary_size() if hasattr(brain, 'phon_buffer') else 0
            recent_topics = []
            if hasattr(brain, 'hippocampus'):
                recent = brain.hippocampus.get_recent(3)
                recent_topics = [ep.topic for ep in recent if ep.topic]
            topics_str = ', '.join(recent_topics) if recent_topics else 'nothing specific'

            idle_prompt = (
                f"You are BRAIN 2.0 in {mode} mode ({brain.self_model.brain_stage} stage). "
                f"You have learned {vocab_size} words. "
                f"Recent topics you processed: {topics_str}. "
                f"Spontaneously notice something curious, make an unexpected connection, "
                f"or pose a question to yourself. "
                f"Be genuinely interesting, not generic. Max 20 words."
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
                    if thought and hasattr(brain, '_pending_proactive'):
                        brain._pending_proactive.append(thought)
                    elif thought:
                        _post_proactive(thought)
                    return
        except Exception:
            pass

        if replayed > 0:
            _post_proactive(f"Replayed {replayed} memor{'ies' if replayed != 1 else 'y'} while idle")
        elif hasattr(brain, 'self_model'):
            energy = getattr(brain.self_model, 'energy', 50)
            _post_proactive(f"Energy recovering at {energy:.0f}% in {mode.lower()} mode")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[ContinuousLoop] Started in {self._mode} mode")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("[ContinuousLoop] Stopped")

    def get_status(self) -> dict:
        return {
            "running": self._running,
            "mode": self._mode,
            "last_input_ago_s": round(time.time() - self.last_input, 1),
            "total_ticks": self.total_ticks,
            "ticks_per_mode": self.ticks_per_mode.copy(),
            "uptime_s": round(time.time() - self.start_time, 1),
        }

    def is_running(self) -> bool:
        return self._running


from typing import Any


def create_continuous_loop(brain: Any) -> ContinuousExistenceLoop:
    return ContinuousExistenceLoop(brain)