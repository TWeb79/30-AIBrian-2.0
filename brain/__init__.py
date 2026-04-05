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
import hashlib
import json as _json
from typing import Optional
from dataclasses import dataclass, field

# Import v0.1 modules
from self.self_model import SelfModel, create_default_self_model
from emotion.salience import SalienceFilter, create_salience_filter, AffectiveState
from emotion.amygdala import AmygdalaRegion, create_amygdala
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
from cognition.attractor_chainer import AttractorChainer, create_attractor_chainer
from memory.hippocampus_simple import HippocampusSimple, create_hippocampus_simple

# Import v0.4 modules
from brain.oscillations.theta import SeptalThetaPacemaker, create_theta_pacemaker
from brain.oscillations.gamma import GammaOscillator, ThetaGammaCoupler, create_gamma_oscillator
from brain.modulation import NeuromodulatorSystem, create_neuromodulator_system

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
    scale=1.00 → BRAIN20 target (~1M neurons, needs Loihi/GPU)
    """
    factor: float = 0.01

    def n(self, full_size: int) -> int:
        return max(100, int(full_size * self.factor))


# ─── BRAIN20 Brain ──────────────────────────────────────────────────────────────

class BRAIN20Brain:
    """
    Full neuromorphic brain assembly.

    Usage
    -----
    brain = BRAIN20Brain(scale=0.01)
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
        self._snapshot_fresh_until: float = 0.0  # prevent background loop from overwriting fresh snapshots

        # ── Chat history ─────────────────────────────────────────────
        self.chat_history: list[dict] = []
        
        # ── Proactive messages via WebSocket ────────────────────────
        self._pending_proactive: list[str] = []
        
        # ── Auto-training flag (ISSUE-2) ───────────────────────
        self._auto_training = False

        # ── v0.1: Self Model and Identity ────────────────────────────────
        self.self_model = SelfModel.load()

        # ── v0.1: Emotion Detection ─────────────────────────────────────
        self.affect = SalienceFilter()

        # ── v0.1: Drive System ──────────────────────────────────────────
        self.drives = DriveSystem(self.self_model)

        # ── v0.1: Persistence ────────────────────────────────────────────
        from config import PERSIST_DIR
        _state_dir = os.getenv("BRAIN_STATE_DIR", PERSIST_DIR)
        self.store = BrainStore(base_dir=_state_dir)
        self.episode_store = EpisodeStore(base_dir=_state_dir)

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
        
        # ── v0.2: Attractor Chainer (for sequence learning) ─────────────────
        self.attractor_chainer = AttractorChainer()
        
        # ── v0.4: Theta Pacemaker (phase-gated STDP) ────────────────────────
        self.theta_pacemaker = SeptalThetaPacemaker()
        # ── v0.4: Gamma oscillator + theta-gamma coupler
        try:
            self.gamma_osc = create_gamma_oscillator(40.0)
            self.theta_gamma_coupler = ThetaGammaCoupler(preferred_phase=0.25, width=0.4)
        except Exception:
            self.gamma_osc = None
            self.theta_gamma_coupler = None
        # Optional: PING spiking gamma (disabled by default)
        self._use_ping_gamma = os.getenv("USE_PING_GAMMA", "false").lower() in ("1", "true", "yes")
        if self._use_ping_gamma:
            try:
                from brain.oscillations.gamma_ping import create_ping_gamma
                self.ping_gamma = create_ping_gamma(n_exc=max(100, int(self.concept.n * 0.02)), n_inh=max(20, int(self.concept.n * 0.005)))
            except Exception:
                self.ping_gamma = None
                self._use_ping_gamma = False
        else:
            self.ping_gamma = None

        # ISSUE-1: Neuromodulator system (emotions wired into learning)
        self.neuromod = create_neuromodulator_system(n_per_population=max(50, int(self.concept.n * 0.01)))

        # ── v0.2/v0.4: Hippocampus backend (selectable)
        # Default: use simple hippocampus for now, but allow switching to full implementation
        use_full_hipp = os.getenv("USE_FULL_HIPPOCAMPUS", "false").lower() in ("1", "true", "yes")
        use_spiking_hipp = os.getenv("USE_SPIKING_HIPPOCAMPUS", "false").lower() in ("1", "true", "yes")
        if use_full_hipp:
            try:
                from memory.hippocampus_full import create_hippocampus_full
                self.hippocampus = create_hippocampus_full(max_episodes=2000)
                self._hippocampus_backend = "full"
            except Exception:
                self.hippocampus = HippocampusSimple(max_episodes=1000)
                self._hippocampus_backend = "simple"
        elif use_spiking_hipp:
            try:
                from memory.hippocampus_spiking import create_hippocampus_spiking
                self.hippocampus = create_hippocampus_spiking(max_episodes=2000, dg_size=1024)
                self._hippocampus_backend = "spiking"
            except Exception:
                self.hippocampus = HippocampusSimple(max_episodes=1000)
                self._hippocampus_backend = "simple"
        else:
            self.hippocampus = HippocampusSimple(max_episodes=1000)
            self._hippocampus_backend = "simple"
        # ── v0.3: Amygdala (fast emotional tagging)
        self.amygdala = AmygdalaRegion(n=max(100, int(self.concept.n * 0.01)))
        self.episode_store = EpisodeStore(base_dir=_state_dir)

        # Last seen concept id / processing time for attractor transition recording
        # BUG-001 fix: do not use peak_regions activity_pct as an assembly id
        self._last_concept_id: int = -1
        self._last_process_time: float | None = None

        # ── v0.1: Continuous Existence Loop ─────────────────────────────
        self.continuous_loop = ContinuousExistenceLoop(self)

        # ── Load persisted state if available ────────────────────────────
        if self.store.exists():
            self.store.load_full(self)
            print(f"[BRAIN20Brain] Loaded persisted state - {self.self_model.total_turns} turns")

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
                # Load word_order if exists
                worder_path = f"{vocab_dir}/word_order.json"
                if os.path.exists(worder_path):
                    with open(worder_path) as f:
                        vocab_data["word_order"] = _json.load(f)
                else:
                    vocab_data["word_order"] = []
                self.phon_buffer.import_vocabulary(vocab_data)
                print(f"[BRAIN20Brain] Loaded vocabulary - {self.phon_buffer.get_vocabulary_size()} words")
        except Exception as e:
            print(f"[BRAIN20Brain] Vocabulary load skipped: {e}")
        
        # Load assemblies (FIX-007)
        asm_path = f"{self.store.BASE_DIR}/assemblies.json"
        try:
            if os.path.exists(asm_path):
                with open(asm_path) as f:
                    self.assembly_detector.import_(_json.load(f))
                print(f"[BRAIN20Brain] Loaded {self.assembly_detector.get_assembly_count()} assemblies")
        except Exception as e:
            print(f"[BRAIN20Brain] Assembly load skipped: {e}")
        
        # Load attractor chainer (FIX-018)
        chain_path = f"{self.store.BASE_DIR}/attractor_chainer.json"
        try:
            if os.path.exists(chain_path):
                with open(chain_path) as f:
                    self.attractor_chainer.import_(_json.load(f))
                print(f"[BRAIN20Brain] Loaded attractor chainer")
        except Exception as e:
            print(f"[BRAIN20Brain] Attractor chainer load skipped: {e}")
        
        # Load theta pacemaker (FIX-019)
        theta_path = f"{self.store.BASE_DIR}/theta_pacemaker.json"
        try:
            if os.path.exists(theta_path):
                with open(theta_path) as f:
                    self.theta_pacemaker.import_(_json.load(f))
                print(f"[BRAIN20Brain] Loaded theta pacemaker")
        except Exception as e:
            print(f"[BRAIN20Brain] Theta pacemaker load skipped: {e}")
        
        episodes_data = self.episode_store.load_episodes()
        if episodes_data:
            # EpisodeStore.save_episodes writes dicts compatible with HippocampusSimple.export();
            # HippocampusFull.import_ expects the same shape (list of dicts). Use import_ on whichever backend
            try:
                self.hippocampus.import_(episodes_data)
                print(f"[BRAIN20Brain] Loaded {len(episodes_data)} episodes into {self._hippocampus_backend} hippocampus backend")
            except Exception as e:
                print(f"[BRAIN20Brain] Hippocampus import skipped: {e}")

        # BUG-4: Auto-train vocabulary on first boot (background thread to not block API)
        _vocab_size = self.phon_buffer.get_vocabulary_size()
        if _vocab_size < 50:
            print(f"[BRAIN20Brain] Vocabulary empty ({_vocab_size} words) — auto-training in background")
            self._auto_training = True
            t = threading.Thread(target=self._auto_train_from_file, daemon=True)
            t.start()
        else:
            self._auto_training = False

        # ── Start continuous existence loop ────────────────────────────
        self.continuous_loop.start()
        print(f"[BRAIN20Brain] Continuous existence loop started")

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

        # FIX-016: Pause background loop competition during thinking phase
        was_running = self._running
        self._running = False

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
        # ISSUE-1: Use LIF neuromodulator biases instead of keyword-based affect biases
        if hasattr(self, 'neuromod') and self.neuromod is not None:
            nm = self.neuromod.get_biases()
        else:
            nm = affect_state.as_neuromodulator_biases()
        ne_gain = 1.0 + nm["norepinephrine_delta"]
        da_gain = 1.0 + nm["dopamine_delta"]
        ach_multiplier = 1.0 + nm["acetylcholine_delta"] * 2.0  # high ACh = more encoding steps
        drive_mods = self.drives.behavioural_modifiers()
        
        # Compute combined STDP gain from affect + drives (base gain from attention)
        base_gain = self._attention_gain
        stdp_gain = base_gain * ne_gain * da_gain * drive_mods["association_gain"]
        
        # ACTION-2: Wire ACh to thinking_steps (emotional learning rate)
        base_steps = self.affect.thinking_steps_for_salience(base_steps=400)
        # Ensure at least 1.0 multiplier so we get base_steps minimum
        ach_multiplier = max(1.0, ach_multiplier)
        thinking_steps = int(base_steps * ach_multiplier)
        print(f"[DEBUG] Affect: arousal={affect_state.arousal:.2f}, valence={affect_state.valence:.2f}, ach_multiplier={ach_multiplier:.2f}, base_steps={base_steps}, final_steps={thinking_steps}")

        # 2. Encode text locally (no LLM)
        self.char_encoder.encode(user_text, self.sensory)

        # 2a. Seed concept layer — inject every step for first N steps
        # Biologically: language input directly activates concept representations
        words_for_seeding = [w.lower().strip(".,!?;:'\"()-") for w in user_text.split() if len(w) > 1]
        seed_concept_indices = None
        if words_for_seeding:
            seed_concept_indices = np.array([
                int(hashlib.md5(w.encode()).hexdigest(), 16) % self.concept.n for w in words_for_seeding
            ], dtype=np.int32)

        # 3. Run SNN for N steps (the "thinking" phase)
        # Track ALL concept neuron spikes across the entire thinking window
        concept_spikes_during_think = set()
        # Track peak activity for snapshot
        peak_regions = {}
        print(f"[DEBUG] Starting thinking loop: {thinking_steps} steps, seed neurons: {len(seed_concept_indices) if seed_concept_indices is not None else 0}")
        with self._lock:
            for step_i in range(thinking_steps):
                if seed_concept_indices is not None:
                    # FIX-014: Decaying injection throughout entire thinking window
                    magnitude = 20.0 * max(0.2, 1.0 - step_i / thinking_steps)
                    self.concept.population.inject_current(seed_concept_indices, magnitude)
                self.step(stdp_gain)
                # Accumulate concept spikes
                if self.concept.last_spikes.size > 0:
                    concept_spikes_during_think.update(self.concept.last_spikes.tolist())
                # Debug: log first few steps
                if step_i < 5:
                    print(f"[DEBUG] Step {step_i}: concept_activity={self.concept.activity_pct:.2f}%, spikes={self.concept.last_spikes.size}")
                # Track peak activity per region
                for r in self.all_regions:
                    act = r.snapshot().get("activity_pct", 0)
                    if act > peak_regions.get(r.name, 0):
                        peak_regions[r.name] = act
        
        print(f"[DEBUG] Thinking complete: {len(concept_spikes_during_think)} unique neurons spiked, concept_activity={self.concept.activity_pct:.2f}%")
        
        # 3a. v0.2: Extract words and wire to active concept assembly
        words = [w.lower().strip(".,!?;:'\"()-") for w in user_text.split() if len(w) > 1]
        # Use all concept neurons that fired during thinking
        active_neurons = concept_spikes_during_think
        concept_id = self.assembly_detector.get_or_create_assembly(active_neurons)
        
        new_words = []
        if len(words) > 0:
            fallback_concept = 0 if concept_id < 0 else concept_id
            for word in words:
                is_new = self.phon_buffer.observe_pairing(word, fallback_concept)
                if is_new:
                    new_words.append(word)
        # Update vocabulary size in self model
        self.self_model.vocabulary_size = self.phon_buffer.get_vocabulary_size()

        # BUG-5: Persist vocabulary immediately on new learning (no throttle)
        if new_words:
            self.persist_vocabulary()
        
        # Report new words learned in response
        response_meta = {"new_words": new_words} if new_words else {}

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
            # Use amygdala score to bias recall ordering (higher score favours emotionally salient episodes)
            amyg_score = self.amygdala.get_score() if hasattr(self, 'amygdala') else 0.0
            # Pass amygdala score as a small boost to min_overlap so emotionally-charged contexts match more easily
            min_overlap = 0.15 - 0.05 * amyg_score
            # Hippocampus APIs expect a list of ints (hippocampus_simple uses Set[int] but
            # hippocampus_full expects List[int]). Ensure a list is passed for compatibility.
            # HippocampusSimple.recall expects a Set[int], while HippocampusFull.recall expects a List[int].
            # Convert to the appropriate type depending on backend.
            if getattr(self, '_hippocampus_backend', 'simple') == 'full':
                recalled = self.hippocampus.recall(list(active_neurons), top_k=1, min_overlap=min_overlap)
            else:
                recalled = self.hippocampus.recall(set(active_neurons), top_k=1, min_overlap=min_overlap)
            if recalled:
                ep = recalled[0]
                # ACTION-3: Richer memory context including valence and related words
                related = []
                if hasattr(self, 'assembly_detector') and hasattr(self, 'phon_buffer'):
                    active_assemblies = self.assembly_detector.get_active_assemblies(active_neurons)
                    if active_assemblies:
                        related = self.phon_buffer.assembly_to_words(active_assemblies[0], top_k=3)
                sentiment = "positive" if ep.valence > 0.1 else "negative" if ep.valence < -0.1 else "neutral"
                memory_snippet = (
                    f"Previously discussed '{ep.topic}' ({sentiment} memory"
                    + (f", related: {', '.join(related)}" if related else "")
                    + ")"
                )

        # 7a. Generate response (local or LLM)
        brain_state = {
            'message': user_text,
            'confidence': self.self_model.confidence,
            'prediction_confidence': snapshot.get('attention_gain', 1.0) / 4.0,
            'active_concept_neuron': snapshot.get('regions', {}).get('concept', {}).get('active_concept_neuron', -1),
            'concept_layer_activity': snapshot.get('regions', {}).get('concept', {}).get('activity_pct', 0),
            'expects_text': True,
            'memory_snippet': memory_snippet,
            'brain_stage': self.self_model.brain_stage,
            'total_turns': self.self_model.total_turns,
            'vocabulary_size': self.self_model.vocabulary_size,
            'drives': self.drives.state.__dict__,
            'affect': {'valence': affect_state.valence, 'arousal': affect_state.arousal},
            'chat_history': self.chat_history[-6:],
            # (AttractorChainer object is passed separately to phonological buffer to avoid serialization issues)
        }

        # Keep the chainer object separate from brain_state for serialization safety
        chainer_obj = self.attractor_chainer

        # Decide: LLM or local?
        gate_decision = self.llm_gate.should_call_llm(brain_state)

        if gate_decision.should_call_llm:
            result = self.codec.articulate(brain_state)
            response = result.text
            path = result.path
        else:
            # Use phonological buffer
            response = self.phon_buffer.generate(brain_state, chainer=chainer_obj)
            path = 'local'

        # 7b. v0.2: Record bypass and cache result
        self.bypass_monitor.record_turn(path)
        self.self_model.llm_bypass_rate = self.bypass_monitor.get_bypass_rate()
        if path == 'local':
            self.response_cache.store(user_text, response)

        # 8. Rebuild snapshot so API immediately reflects processing
        # Must be under lock to prevent background loop from overwriting
        with self._lock:
            self._last_snapshot = self._build_snapshot()
            # Inject peak activity into the snapshot so the UI shows what happened
            if peak_regions:
                for name, act in peak_regions.items():
                    if name in self._last_snapshot.get("regions", {}):
                        self._last_snapshot["regions"][name]["activity_pct"] = round(act, 2)
            self._snapshot_fresh_until = time.time() + 3.0  # keep fresh for 3 seconds
            fresh_snapshot = self._last_snapshot

        # 9. Save periodically (more frequently for vocabulary)
        if self.self_model.total_steps % 1000 == 0:
            self.persist()

        # FIX-016: Resume background loop
        self._running = was_running

        return {
            'response': response,
            'path': path,
            'brain_state': fresh_snapshot,
            'affect': affect_state,
            'drives': self.drives.state.__dict__,
            'self_model': self.self_model,
            'new_words': new_words,
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
        with open(f"{vocab_dir}/word_order.json", "w") as f:
            _json.dump(vocab_data.get("word_order", []), f)
        # Save assemblies (FIX-007)
        asm_path = f"{self.store.BASE_DIR}/assemblies.json"
        with open(asm_path, "w") as f:
            _json.dump(self.assembly_detector.export(), f)
        # Save attractor chainer (FIX-018)
        chain_path = f"{self.store.BASE_DIR}/attractor_chainer.json"
        with open(chain_path, "w") as f:
            _json.dump(self.attractor_chainer.export(), f)
        # Save theta pacemaker (FIX-019)
        theta_path = f"{self.store.BASE_DIR}/theta_pacemaker.json"
        with open(theta_path, "w") as f:
            _json.dump(self.theta_pacemaker.export(), f)
        # Save episodes
        self.episode_store.save_episodes(self.hippocampus.export())
        print(f"[BRAIN20Brain] Persisted state at step {self.self_model.total_steps}")

    def persist_vocabulary(self):
        """Lightweight persistence: save self-model + vocabulary only (no synapses)."""
        try:
            # Self-model is cheap and useful for tracking progress
            if hasattr(self, 'self_model') and self.self_model is not None:
                self.store.save_self_model(self.self_model)
            if hasattr(self, 'phon_buffer') and self.phon_buffer is not None:
                self.store.save_vocabulary_export(self.phon_buffer.export_vocabulary())
        except Exception as e:
            print(f"[BRAIN20Brain] persist_vocabulary failed: {e}")

    def _auto_train_from_file(self, batch_size: int = 200):
        """Bootstrap vocabulary from TrainingFile.md on first boot."""
        # ISSUE-5: Check TRAINING_FILE_PATH env var first
        env_path = os.getenv("TRAINING_FILE_PATH")
        candidates = [p for p in [
            env_path,
            "TrainingFile.md",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "TrainingFile.md"),
        ] if p]
        for path in candidates:
            path = os.path.abspath(path)
            if not os.path.exists(path):
                continue
            print(f"[BRAIN20Brain] Auto-training from {path}")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    chunk = []
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        chunk.append(line)
                        if len(chunk) >= batch_size:
                            self.process_input_v01(" ".join(chunk))
                            chunk = []
                    if chunk:
                        self.process_input_v01(" ".join(chunk))
                self.persist_vocabulary()
                print(f"[BRAIN20Brain] Auto-train complete — {self.phon_buffer.get_vocabulary_size()} words")
                self._auto_training = False
                return
            except Exception as e:
                print(f"[BRAIN20Brain] Auto-train error: {e}")
        self._auto_training = False

    def on_user_feedback(self, valence: float, message_id: int | None = None, response_text: str | None = None):
        """
        Called when user reacts positively (+1) or negatively (-1).
        Updates self-model personality and drive satisfaction.
        
        Args:
            valence: -1.0 to 1.0 sentiment score
            message_id: Optional index of the message being rated
            response_text: Optional preview of the response being rated
        """
        # Update sentiment tracking
        self.self_model.user_sentiment_avg = (
            0.95 * self.self_model.user_sentiment_avg + 0.05 * (valence * 0.5 + 0.5)
        )

        # Enhanced: Use feedback to adjust drives for motivation
        if valence > 0:
            # Positive feedback increases engagement drive
            self.drives.state.curiosity = min(1.0, self.drives.state.curiosity + 0.05)
            self.drives.state.competence = min(1.0, self.drives.state.competence + 0.03)
        else:
            # Negative feedback increases learning drive
            self.drives.state.competence = min(1.0, self.drives.state.competence + 0.08)

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

        # Store feedback for learning (keep last 10)
        if response_text:
            if not hasattr(self.self_model, 'recent_feedback'):
                self.self_model.recent_feedback = []
            self.self_model.recent_feedback.append({
                'valence': valence,
                'response_preview': response_text[:100] if response_text else None,
                'step': self.self_model.total_steps
            })
            # Keep only last 10
            if len(self.self_model.recent_feedback) > 10:
                self.self_model.recent_feedback = self.self_model.recent_feedback[-10:]

    # ─── Core simulation step ──────────────────────────────────────────────

    def step(self, stdp_gain: float = 1.0) -> dict:
        """Run one 0.1 ms simulation timestep. Returns mini-snapshot."""
        gain = self._attention_gain

        # 1. Brainstem homeostatic drive (already in i_ext; step it)
        bs_spikes = self.brainstem.step(np.zeros(self.brainstem.n, dtype=np.float32))
        # --- BUG-002: step the amygdala population so it produces a fast emotional score
        if hasattr(self, 'amygdala') and self.amygdala is not None:
            try:
                amyg_input = np.zeros(self.amygdala.n, dtype=np.float32)
                if getattr(self.sensory, 'last_spikes', None) is not None and self.sensory.last_spikes.size > 0:
                    n_spikes = min(self.amygdala.n, int(self.sensory.last_spikes.size))
                    amyg_input[:n_spikes] = 15.0
                # advance amygdala and update its internal score
                _ = self.amygdala.step(amyg_input)
            except Exception:
                # Fail-safe: do not break the main loop on amygdala errors
                pass

        # ISSUE-1: Step neuromodulator system with signals from brain state
        if hasattr(self, 'neuromod') and self.neuromod is not None:
            try:
                reward_signal = max(0, self._attention_gain - 1.0) / 4.0
                salience_signal = min(1.0, self.sensory.activity_pct / 50.0)
                self.neuromod.step(reward_signal=reward_signal, salience_signal=salience_signal)
            except Exception:
                pass

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

        # FIX-019: Phase-gated STDP - only apply during encoding window
        # Theta pacemaker: encoding window = phase 0-0.5, retrieval = 0.5-1.0
        theta_phase = self.theta_pacemaker.tick(0.1)  # 0.1ms per step
        # Advance gamma oscillator and compute coupling gain if available
        gamma_gain = 1.0
        try:
            if hasattr(self, 'gamma_osc') and self.gamma_osc is not None:
                self.gamma_osc.tick(0.1)
                if hasattr(self, 'theta_gamma_coupler') and self.theta_gamma_coupler is not None:
                    cg = self.theta_gamma_coupler.coupling_gain(theta_phase)
                    # Use gamma->inhibition coupling to slightly modulate STDP gains
                    gamma_gain = 1.0 + 0.5 * cg
        except Exception:
            pass
        # If PING gamma is enabled, step it and include its power in the gamma gain
        try:
            if getattr(self, '_use_ping_gamma', False) and getattr(self, 'ping_gamma', None) is not None:
                # Provide a small context-dependent external drive to PING (based on attention)
                ext = max(0.5, min(10.0, self._attention_gain * 2.0))
                self.ping_gamma.step(0.1, ext_drive=ext)
                ping_power = self.ping_gamma.get_power()
                # Blend ping power into gamma_gain (small influence)
                gamma_gain = gamma_gain * (1.0 + 0.5 * ping_power)
        except Exception:
            gamma_gain = 1.0
        # Split LTP/LTD gating: LTP only during encoding window; LTD may be active continuously
        apply_ltp = self.theta_pacemaker.is_encoding_window()
        apply_ltd = True
        
        # ISSUE-7: Scale LTP gain by dopamine (reward learning)
        da_multiplier = 1.0
        if hasattr(self, 'neuromod') and self.neuromod is not None:
            da_multiplier = self.neuromod.da.get_stdp_multiplier(1.0)  # 0.5x to 2x based on DA level
        
        # 10. STDP updates (event-driven, only on firing neurons)
        pop = {r.name: r.population for r in self.all_regions}

        if True:
            # STDP active during theta encoding phase, with DA-modulated LTP
            self.syn_s2f.update_stdp(
                self.sensory.last_spikes, f_spikes,
                pop["sensory"].trace, pop["feature"].trace,
                ltp_gain=stdp_gain * da_multiplier * gamma_gain, ltd_gain=1.0,
                apply_ltp=apply_ltp, apply_ltd=apply_ltd,
            )
            self.syn_f2a.update_stdp(
                f_spikes, a_spikes,
                pop["feature"].trace, pop["association"].trace,
                ltp_gain=stdp_gain * da_multiplier * gamma_gain, ltd_gain=1.0,
                apply_ltp=apply_ltp, apply_ltd=apply_ltd,
            )
            self.syn_a2p.update_stdp(
                a_spikes, p_spikes,
                pop["association"].trace, pop["predictive"].trace,
                ltp_gain=stdp_gain * da_multiplier * gamma_gain, ltd_gain=1.0,
                apply_ltp=apply_ltp, apply_ltd=apply_ltd,
            )
            self.syn_a2c.update_stdp(
                a_spikes, c_spikes,
                pop["association"].trace, pop["concept"].trace,
                ltp_gain=stdp_gain * da_multiplier * gamma_gain, ltd_gain=1.0,
                apply_ltp=apply_ltp, apply_ltd=apply_ltd,
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
                # Don't overwrite a fresh snapshot from process_input_v01
                if time.time() > self._snapshot_fresh_until:
                    self._last_snapshot = self._build_snapshot()
            elapsed = time.perf_counter() - t0
            self._step_rate = steps_per_tick / max(elapsed, 1e-6)
            # Tiny sleep to prevent 100% CPU
            time.sleep(0.01)

    # ─── Snapshot / telemetry ──────────────────────────────────────────────

    def _build_snapshot(self) -> dict:
        elapsed = max(time.time() - self.start_time, 1e-6)
        regions = {r.name: r.snapshot() for r in self.all_regions}
        # Include amygdala stats if available
        try:
            regions['amygdala'] = self.amygdala.snapshot()
        except Exception:
            pass

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
            "proactive_thought": self._pending_proactive.pop(0) if self._pending_proactive else None,
        }

    def snapshot(self) -> dict:
        with self._lock:
            if self._last_snapshot:
                return self._last_snapshot
            return self._build_snapshot()

    def _status(self) -> str:
        s = self.self_model.total_steps  # persisted across reboots
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
