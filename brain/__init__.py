"""
brain.py — Brain 2.0 Assembly V0.2
====================================
Wires all regions together with STDP synapses.
Implements the predictive feedback loop and step() logic.

v0.1 Features:
- SelfModel for persistent identity
- ContinuousExistenceLoop for 24/7 operation
- SalienceFilter for emotion detection
- DriveSystem for intrinsic motivation
- BrainStore for persistence

v0.2 Features:
- CellAssemblyDetector for concept tracking
- PhonologicalBuffer wiring (word↔assembly learning)
- HippocampusSimple for episodic memory
- ResponseCache for similarity-based reuse
- LLMBypassMonitor for learning metrics

Information flow:
  SensoryInput
    → SensoryCortex  [Poisson encode]
    → FeatureLayer   [STDP]
    → AssociationRegion  [STDP, bidirectional with Predictive]
    → ConceptLayer   [WTA + STDP]
    → MetaControl    [top-down modulation]
    → WorkingMemory  [recurrent buffer]

  PredictiveRegion ↔ AssociationRegion  (bidirectional feedback)
  PredictiveRegion   → attention_gain broadcast to all STDP synapses

  AssociationRegion → Cerebellum → motor output → ReflexArc
  Brainstem: constant low-level homeostatic drive
"""

import numpy as np
import os
import time
import threading
import json as _json
from typing import Optional
from dataclasses import dataclass, field

# Import v0.1 modules
from self.self_model import SelfModel, create_default_self_model
from emotion.salience import SalienceFilter, create_salience_filter, AffectiveState
from drives.drive_system import DriveSystem, create_drive_system
from persistence.brain_store import BrainStore, create_brain_store
from persistence.episode_store import EpisodeStore, create_episode_store
from codec.character_encoder import CharacterEncoder, create_character_encoder
from codec.llm_codec import LLMCodec, create_llm_codec
from codec.llm_gate import LLMGate, create_llm_gate
from codec.phonological_buffer import PhonologicalBuffer, create_phonological_buffer
from codec.cost_tracker import CostTracker, create_cost_tracker
from codec.response_cache import ResponseCache, create_response_cache
from codec.llm_bypass_monitor import LLMBypassMonitor, create_llm_bypass_monitor
from brain.continuous_loop import ContinuousExistenceLoop, create_continuous_loop

# Import v0.2 modules
from cognition.cell_assemblies import CellAssemblyDetector, create_cell_assembly_detector
from memory.hippocampus_simple import HippocampusSimple, create_hippocampus_simple

from brain.neurons import LIFParams, RateEncoder
from brain.synapses import SparseSTDPSynapse, STDPParams
from brain.regions import (
    SensoryCortex, FeatureLayer, AssociationRegion,
    PredictiveRegion, ConceptLayer, MetaControl,
    WorkingMemory, Cerebellum, Brainstem, ReflexArc,
)


# ─── Scale config (adjust for your hardware) ──────────────────────────────────

@dataclass
class BrainScale:
    """
    Scale factor 0.0–1.0 controls neuron counts.
    scale=0.01 → fast CPU demo (~50k total neurons)
    scale=0.10 → full demo (~500k neurons)
    scale=1.00 → OSCEN target (~1M neurons, needs Loihi/GPU)
    """
    factor: float = 0.01

    def n(self, full_size: int) -> int:
        return max(100, int(full_size * self.factor))


# ─── OSCEN Brain ──────────────────────────────────────────────────────────────

class OSCENBrain:
    """
    Full neuromorphic brain assembly.

    Usage
    -----
    brain = OSCENBrain(scale=0.01)
    brain.start_background_loop()

    # Stimulate with text
    brain.process_text("hello world")

    # Get snapshot
    state = brain.snapshot()
    """

    DT = 0.1    # ms timestep

    def __init__(self, scale: float = 0.01, seed: int = 42):
        np.random.seed(seed)
        sc = BrainScale(scale)

        # ── Instantiate regions ──────────────────────────────────────
        self.sensory    = SensoryCortex  (sc.n(40_000))
        self.feature    = FeatureLayer   (sc.n(80_000))
        self.assoc      = AssociationRegion(sc.n(500_000))
        self.predictive = PredictiveRegion (sc.n(100_000))
        self.concept    = ConceptLayer   (sc.n(5_800))
        self.meta       = MetaControl    (sc.n(60_000))
        self.working_mem= WorkingMemory  (sc.n(20_000))
        self.cerebellum = Cerebellum     (sc.n(15_000))
        self.brainstem  = Brainstem      (sc.n(8_000))
        self.reflex     = ReflexArc      (sc.n(30_000))

        self.all_regions = [
            self.sensory, self.feature, self.assoc, self.predictive,
            self.concept, self.meta, self.working_mem,
            self.cerebellum, self.brainstem, self.reflex,
        ]

        # ── Wire STDP synapses ──────────────────────────────────────
        stdp_p = STDPParams(A_plus=0.01, A_minus=0.0105, lr=1.0)

        self.syn_s2f   = SparseSTDPSynapse(self.sensory.n,    self.feature.n,    p=0.04, params=stdp_p, name="sensory→feature")
        self.syn_f2a   = SparseSTDPSynapse(self.feature.n,    self.assoc.n,      p=0.02, params=stdp_p, name="feature→assoc")
        self.syn_a2p   = SparseSTDPSynapse(self.assoc.n,      self.predictive.n, p=0.02, params=stdp_p, name="assoc→predict")
        self.syn_p2a   = SparseSTDPSynapse(self.predictive.n, self.assoc.n,      p=0.02, params=stdp_p, name="predict→assoc")   # feedback
        self.syn_a2c   = SparseSTDPSynapse(self.assoc.n,      self.concept.n,    p=0.05, params=stdp_p, name="assoc→concept")
        self.syn_p2c   = SparseSTDPSynapse(self.predictive.n, self.concept.n,    p=0.03, params=stdp_p, name="predict→concept")
        self.syn_c2m   = SparseSTDPSynapse(self.concept.n,    self.meta.n,       p=0.08, params=stdp_p, name="concept→meta")
        self.syn_m2wm  = SparseSTDPSynapse(self.meta.n,       self.working_mem.n,p=0.05, params=stdp_p, name="meta→wm")
        self.syn_a2cb  = SparseSTDPSynapse(self.assoc.n,      self.cerebellum.n, p=0.03, params=stdp_p, name="assoc→cerebellum")

        self.all_synapses = [
            self.syn_s2f, self.syn_f2a, self.syn_a2p, self.syn_p2a,
            self.syn_a2c, self.syn_p2c, self.syn_c2m, self.syn_m2wm,
            self.syn_a2cb,
        ]

        # ── Text encoder ─────────────────────────────────────────────
        self.encoder = RateEncoder(vocab_size=1000, n_neurons=self.sensory.n)

        # ── Runtime stats ────────────────────────────────────────────
        self.step_count     = 0
        self.total_spikes   = 0
        self.start_time     = time.time()
        self._attention_gain = 1.0

        # ── Background simulation thread ─────────────────────────────
        self._running  = False
        self._lock     = threading.Lock()
        self._step_rate = 0.0
        self._last_snapshot: dict = {}

        # ── Chat history ─────────────────────────────────────────────
        self.chat_history: list[dict] = []

        # ── v0.1: Self Model and Identity ────────────────────────────────
        self.self_model = SelfModel.load()

        # ── v0.1: Emotion Detection ─────────────────────────────────────
        self.affect = SalienceFilter()

        # ── v0.1: Drive System ──────────────────────────────────────────
        self.drives = DriveSystem(self.self_model)

        # ── v0.1: Persistence ────────────────────────────────────────────
        self.store = BrainStore()

        # ── v0.1: Character Encoder (local text→spikes) ────────────────
        self.char_encoder = CharacterEncoder(self.sensory.n)

        # ── v0.1: LLM Codec ─────────────────────────────────────────────
        self.phon_buffer = PhonologicalBuffer(n_assemblies=self.concept.n)
        self.llm_gate = LLMGate()
        self.cost_tracker = CostTracker()
        self.codec = LLMCodec()
        self.codec.set_components(self.llm_gate, self.phon_buffer, self.cost_tracker)

        # ── v0.2: Response Cache ──────────────────────────────────────────
        self.response_cache = ResponseCache(max_size=200)

        # ── v0.2: LLM Bypass Monitor ──────────────────────────────────────
        self.bypass_monitor = LLMBypassMonitor(window_size=100)

        # ── v0.2: Cell Assembly Detector ──────────────────────────────────
        self.assembly_detector = CellAssemblyDetector(
            self.concept.n, min_coalition_size=1, stability_threshold=1
        )

        # ── v0.2: Hippocampus (simplified) ────────────────────────────────
        self.hippocampus = HippocampusSimple(max_episodes=1000)
        self.episode_store = EpisodeStore()

        # ── v0.1: Continuous Existence Loop ─────────────────────────────
        self.continuous_loop = ContinuousExistenceLoop(self)

        # ── Load persisted state if available ────────────────────────────
        if self.store.exists():
            self.store.load_full(self)
            print(f"[OSCENBrain] Loaded persisted state - {self.self_model.total_turns} turns")

        # ── Load vocabulary and episodes ──────────────────────────────────
        try:
            vocab_dir = f"{self.store.BASE_DIR}/vocabulary"
            w2a_path = f"{vocab_dir}/word_to_assembly.json"
            a2w_path = f"{vocab_dir}/assembly_to_words.json"
            idw_path = f"{vocab_dir}/id_to_word.json"
            idx_path = f"{vocab_dir}/word_index.json"
            if os.path.exists(w2a_path) and os.path.exists(a2w_path):
                vocab_data = {}
                with open(w2a_path) as f:
                    vocab_data["w2a"] = _json.load(f)
                with open(a2w_path) as f:
                    vocab_data["a2w"] = _json.load(f)
                if os.path.exists(idw_path):
                    with open(idw_path) as f:
                        vocab_data["id_to_word"] = _json.load(f)
                else:
                    vocab_data["id_to_word"] = {}
                if os.path.exists(idx_path):
                    with open(idx_path) as f:
                        vocab_data["word_index"] = _json.load(f)
                else:
                    vocab_data["word_index"] = {}
                self.phon_buffer.import_vocabulary(vocab_data)
                print(f"[OSCENBrain] Loaded vocabulary - {self.phon_buffer.get_vocabulary_size()} words")
        except Exception as e:
            print(f"[OSCENBrain] Vocabulary load skipped: {e}")
        episodes_data = self.episode_store.load_episodes()
        if episodes_data:
            self.hippocampus.import_(episodes_data)
            print(f"[OSCENBrain] Loaded {len(episodes_data)} episodes")

    # ─── v0.1: Process user input ───────────────────────────────────────-

    def process_input_v01(self, user_text: str, user_feedback: float = 0.0) -> dict:
        """
        Process user input with v0.2 features.
        
        Returns dict with:
        - response: str (the generated response)
        - path: str ('llm', 'local', or 'cached')
        - brain_state: dict
        - affect: AffectiveState
        - drives: dict
        """
        # Notify continuous loop of user activity
        self.continuous_loop.notify_user_active()

        # 0. Response cache check — skip SNN entirely if similar input cached
        cached = self.response_cache.lookup(user_text)
        if cached is not None:
            self.bypass_monitor.record_turn('cached')
            snapshot = self.snapshot()
            return {
                'response': cached,
                'path': 'cached',
                'brain_state': snapshot,
                'affect': self.affect.get_state(),
                'drives': self.drives.state.__dict__,
                'self_model': self.self_model,
            }

        # 1. Assess emotional salience
        affect_state = self.affect.assess(user_text)
        thinking_steps = self.affect.thinking_steps_for_salience(base_steps=500)

        # 2. Encode text locally (no LLM)
        self.char_encoder.encode(user_text, self.sensory)

        # 2a. Seed concept layer — inject every step for first N steps
        # Biologically: language input directly activates concept representations
        words_for_seeding = [w.lower().strip(".,!?;:'\"()-") for w in user_text.split() if len(w) > 1]
        seed_concept_indices = None
        if words_for_seeding:
            seed_concept_indices = np.array([
                hash(w) % self.concept.n for w in words_for_seeding
            ], dtype=np.int32)

        # 3. Run SNN for N steps (the "thinking" phase)
        # Track ALL concept neuron spikes across the entire thinking window
        concept_spikes_during_think = set()
        seed_steps = min(30, thinking_steps)  # seed for first 30 steps
        with self._lock:
            for step_i in range(thinking_steps):
                if step_i < seed_steps and seed_concept_indices is not None:
                    self.concept.population.inject_current(seed_concept_indices, 20.0)
                self.step()
                # Accumulate concept spikes
                if self.concept.last_spikes.size > 0:
                    concept_spikes_during_think.update(self.concept.last_spikes.tolist())

        # 3a. v0.2: Extract words and wire to active concept assembly
        words = [w.lower().strip(".,!?;:'\"()-") for w in user_text.split() if len(w) > 1]
        # Use all concept neurons that fired during thinking
        active_neurons = concept_spikes_during_think
        concept_id = self.assembly_detector.get_or_create_assembly(active_neurons)
        if concept_id >= 0:
            for word in words:
                self.phon_buffer.observe_pairing(word, concept_id)
        # Update vocabulary size in self model
        self.self_model.vocabulary_size = self.phon_buffer.get_vocabulary_size()

        # 3b. v0.2: Encode episodic memory on high-salience events
        if affect_state.arousal > 0.5:
            self.hippocampus.encode(
                list(active_neurons),
                topic=words[0] if words else "unknown",
                valence=affect_state.valence,
                arousal=affect_state.arousal,
            )

        # 4. Get snapshot
        snapshot = self.snapshot()

        # 5. Update drives
        novelty = snapshot.get('prediction_error', 0.0)
        self.drives.update(
            prediction_error=1.0 - snapshot.get('attention_gain', 1.0) / 4.0,
            user_present=True,
            novelty=novelty,
            user_feedback=user_feedback
        )

        # 6. Update self model
        self.self_model.update_after_turn(
            prediction_error=novelty,
            user_feedback=user_feedback
        )
        self.self_model.total_steps += thinking_steps
        self.self_model.steps_this_session += thinking_steps

        # 7. v0.2: Memory recall — inject hippocampal memory snippet
        memory_snippet = ""
        if active_neurons:
            recalled = self.hippocampus.recall(active_neurons, top_k=1)
            if recalled:
                ep = recalled[0]
                memory_snippet = f"Previously discussed: {ep.topic}" if ep.topic else ""

        # 7a. Generate response (local or LLM)
        brain_state = {
            'confidence': self.self_model.confidence,
            'prediction_confidence': snapshot.get('attention_gain', 1.0) / 4.0,
            'active_concept_neuron': snapshot.get('regions', {}).get('concept', {}).get('active_concept_neuron', -1),
            'concept_layer_activity': snapshot.get('regions', {}).get('concept', {}).get('activity_pct', 0),
            'expects_text': True,
            'memory_snippet': memory_snippet,
        }

        # Decide: LLM or local?
        gate_decision = self.llm_gate.should_call_llm(brain_state)

        if gate_decision.should_call_llm:
            result = self.codec.articulate(brain_state)
            response = result.text
            path = result.path
        else:
            # Use phonological buffer
            response = self.phon_buffer.generate(brain_state)
            path = 'local'

        # 7b. v0.2: Record bypass and cache result
        self.bypass_monitor.record_turn(path)
        self.self_model.llm_bypass_rate = self.bypass_monitor.get_bypass_rate()
        if path in ('local', 'cached'):
            self.response_cache.store(user_text, response)

        # 8. Rebuild snapshot so API immediately reflects processing
        # Must be under lock to prevent background loop from overwriting
        with self._lock:
            self._last_snapshot = self._build_snapshot()
            fresh_snapshot = self._last_snapshot

        # 9. Save periodically
        if self.self_model.total_steps % 10000 == 0:
            self.persist()

        return {
            'response': response,
            'path': path,
            'brain_state': fresh_snapshot,
            'affect': affect_state,
            'drives': self.drives.state.__dict__,
            'self_model': self.self_model,
        }

    # ─── v0.1: Persistence ──────────────────────────────────────────────

    def persist(self):
        """Save brain state to disk."""
        self.store.save_full(self)
        # Save vocabulary (full export format for import_vocabulary compatibility)
        vocab_data = self.phon_buffer.export_vocabulary()
        vocab_dir = f"{self.store.BASE_DIR}/vocabulary"
        os.makedirs(vocab_dir, exist_ok=True)
        with open(f"{vocab_dir}/word_to_assembly.json", "w") as f:
            _json.dump(vocab_data.get("w2a", {}), f)
        with open(f"{vocab_dir}/assembly_to_words.json", "w") as f:
            _json.dump(vocab_data.get("a2w", {}), f)
        with open(f"{vocab_dir}/id_to_word.json", "w") as f:
            _json.dump(vocab_data.get("id_to_word", {}), f)
        with open(f"{vocab_dir}/word_index.json", "w") as f:
            _json.dump(vocab_data.get("word_index", {}), f)
        # Save episodes
        self.episode_store.save_episodes(self.hippocampus.export())
        print(f"[OSCENBrain] Persisted state at step {self.self_model.total_steps}")

    def on_user_feedback(self, valence: float):
        """
        Called when user reacts positively (+1) or negatively (-1).
        Updates self-model personality and drive satisfaction.
        """
        # Update sentiment tracking
        self.self_model.user_sentiment_avg = (
            0.95 * self.self_model.user_sentiment_avg + 0.05 * (valence * 0.5 + 0.5)
        )

        # Update drives
        self.drives.update(
            prediction_error=0.0,
            user_present=True,
            novelty=0.0,
            user_feedback=valence
        )

        # Apply reward to affect
        self.affect.apply_user_feedback(valence)

        # Update self model
        self.self_model.update_after_turn(prediction_error=0.0, user_feedback=valence)

    # ─── Core simulation step ──────────────────────────────────────────────

    def step(self) -> dict:
        """Run one 0.1 ms simulation timestep. Returns mini-snapshot."""
        gain = self._attention_gain

        # 1. Brainstem homeostatic drive (already in i_ext; step it)
        bs_spikes = self.brainstem.step(np.zeros(self.brainstem.n, dtype=np.float32))

        # 2. Sensory → Feature
        i_feature  = self.syn_s2f.propagate(self.sensory.last_spikes)
        f_spikes   = self.feature.step(i_feature)

        # 3. Feature → Association  (+  predictive feedback)
        i_assoc    = self.syn_f2a.propagate(f_spikes)
        i_assoc   += self.syn_p2a.propagate(self.predictive.last_spikes, scale=gain)
        a_spikes   = self.assoc.step(i_assoc)

        # 4. Association → Predictive
        i_pred     = self.syn_a2p.propagate(a_spikes)
        p_spikes   = self.predictive.step(i_pred)

        # 5. Compute prediction error → update attention gain
        self._attention_gain = self.predictive.compute_error(self.assoc.activity_pct / 100.0)

        # 6. Association + Predictive → Concept (WTA)
        i_concept  = self.syn_a2c.propagate(a_spikes, scale=gain)
        i_concept += self.syn_p2c.propagate(p_spikes)
        c_spikes   = self.concept.step(i_concept)

        # 7. Concept → MetaControl
        i_meta     = self.syn_c2m.propagate(c_spikes)
        m_spikes   = self.meta.step(i_meta)

        # 8. Meta → Working Memory
        i_wm       = self.syn_m2wm.propagate(m_spikes)
        wm_spikes  = self.working_mem.step(i_wm)
        self.working_mem.hold(wm_spikes)

        # 9. Association → Cerebellum
        i_cb       = self.syn_a2cb.propagate(a_spikes)
        cb_spikes  = self.cerebellum.step(i_cb)

        # 10. STDP updates (event-driven, only on firing neurons)
        pop = {r.name: r.population for r in self.all_regions}

        self.syn_s2f.update_stdp(
            self.sensory.last_spikes, f_spikes,
            pop["sensory"].trace, pop["feature"].trace,
            gain=gain,
        )
        self.syn_f2a.update_stdp(
            f_spikes, a_spikes,
            pop["feature"].trace, pop["association"].trace,
            gain=gain,
        )
        self.syn_a2p.update_stdp(
            a_spikes, p_spikes,
            pop["association"].trace, pop["predictive"].trace,
            gain=gain,
        )
        self.syn_a2c.update_stdp(
            a_spikes, c_spikes,
            pop["association"].trace, pop["concept"].trace,
            gain=gain,
        )

        # 11. Reset external currents
        for r in self.all_regions:
            r.population.reset_external()

        self.step_count += 1
        self.total_spikes += sum(
            len(s) for s in [bs_spikes, f_spikes, a_spikes, p_spikes,
                              c_spikes, m_spikes, wm_spikes, cb_spikes]
        )

        return {"step": self.step_count, "gain": self._attention_gain}

    # ─── Sensory stimulation ───────────────────────────────────────────────

    def stimulate_modality(self, modality: str, data: np.ndarray):
        """Inject sensory stimulus (called externally or from text pipeline)."""
        self.sensory.stimulate(modality, data)

    def process_text(self, text: str):
        """
        Encode text as spike current and inject into sensory cortex.
        Simple bag-of-words tokenisation → RateEncoder.
        """
        tokens = self._tokenise(text)
        current = self.encoder.encode(tokens, self.sensory.n)
        self.sensory.population.i_ext += current

        # Also create a "vision-like" activation pattern from text length
        vis_stim = np.random.rand(int(self.sensory.n * 0.4)) * (len(text) / 200.0)
        self.sensory.stimulate("vision", vis_stim)

    def _tokenise(self, text: str) -> list[int]:
        """Simple character n-gram tokeniser mapped to [0, 999]."""
        tokens = []
        words  = text.lower().split()
        for w in words:
            h = hash(w) % 1000
            tokens.append(h)
        return tokens

    # ─── Background simulation loop ───────────────────────────────────────

    def start_background_loop(self, steps_per_tick: int = 50):
        """Run simulation in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(
            target=self._loop, args=(steps_per_tick,), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self, steps_per_tick: int):
        while self._running:
            t0 = time.perf_counter()
            with self._lock:
                for _ in range(steps_per_tick):
                    self.step()
                self._last_snapshot = self._build_snapshot()
            elapsed = time.perf_counter() - t0
            self._step_rate = steps_per_tick / max(elapsed, 1e-6)
            # Tiny sleep to prevent 100% CPU
            time.sleep(0.01)

    # ─── Snapshot / telemetry ──────────────────────────────────────────────

    def _build_snapshot(self) -> dict:
        elapsed = max(time.time() - self.start_time, 1e-6)
        regions = {r.name: r.snapshot() for r in self.all_regions}

        return {
            "step":          self.step_count,
            "elapsed_s":     round(elapsed, 1),
            "step_rate":     round(self._step_rate, 2),
            "total_spikes":  self.total_spikes,
            "attention_gain": round(self._attention_gain, 3),
            "prediction_error": round(self.predictive.error, 4),
            "synapse_counts": {s.name: s.n_synapses for s in self.all_synapses},
            "mean_weights":  {s.name: round(s.mean_weight(), 4) for s in self.all_synapses},
            "regions":       regions,
            "status":        self._status(),
        }

    def snapshot(self) -> dict:
        with self._lock:
            if self._last_snapshot:
                return self._last_snapshot
            return self._build_snapshot()

    def _status(self) -> str:
        s = self.step_count
        if s < 100_000:   return "NEONATAL"
        if s < 1_000_000: return "JUVENILE"
        if s < 5_000_000: return "ADOLESCENT"
        return "MATURE"

    # ─── Motor output via safety kernel ───────────────────────────────────

    def issue_motor_command(self, cmd: dict) -> dict:
        return self.reflex.check_command(cmd)

    # ─── Synaptic statistics ──────────────────────────────────────────────

    def total_synapses(self) -> int:
        return sum(s.n_synapses for s in self.all_synapses)

    def total_neurons(self) -> int:
        return sum(r.n for r in self.all_regions)
