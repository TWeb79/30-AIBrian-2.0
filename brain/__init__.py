"""
brain/__init__.py patches — targeted bug fixes only.

BUGS FIXED (no new features):
  FIX-LOCK-1  process_input_v01 held brain._lock for the entire thinking
              phase (400+ steps). Every concurrent request (WebSocket, status,
              other chats) blocked until all steps finished. The thread pool
              filled with blocked threads and the server stopped responding.
              Fix: release the lock between STEP_BATCH-sized chunks and yield
              with time.sleep(0) so other threads can run.

  FIX-LOCK-2  The pattern "was_running = self._running; self._running = False"
              was meant to pause the background loop, but if start_background_loop
              is running its _loop thread, setting _running = False causes that
              thread to exit its while-loop permanently. Even after
              self._running = was_running the thread is gone and background
              stepping stops forever until restart.
              Fix: remove the pattern entirely. The lock alone serialises access.

  FIX-SNAP-1  snapshot() always acquired brain._lock. Called every 200ms from
              the WebSocket (via asyncio.to_thread) this created constant lock
              pressure. Together with FIX-LOCK-1 this is why the server hung.
              Fix: return _last_snapshot directly when it exists. The dict
              reference read is atomic under CPython's GIL.

  FIX-JSON-1  _build_snapshot() could propagate exceptions from region.snapshot()
              calls (e.g. during startup), causing 500s with no useful log line.
              Fix: wrap each region snapshot in try/except.
"""

import numpy as np
import os
import time
import threading
import hashlib
import json as _json
from typing import Optional
from dataclasses import dataclass, field

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

from cognition.cell_assemblies import CellAssemblyDetector, create_cell_assembly_detector
from cognition.attractor_chainer import AttractorChainer, create_attractor_chainer
from memory.hippocampus_simple import HippocampusSimple, create_hippocampus_simple

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

# Number of thinking steps to run per lock acquisition.
# Smaller = more responsive API; larger = slightly more efficient SNN.
_STEP_BATCH = 40


@dataclass
class BrainScale:
    factor: float = 0.01

    def n(self, full_size: int) -> int:
        return max(100, int(full_size * self.factor))


class BRAIN20Brain:
    DT = 0.1

    def __init__(self, scale: float = 0.01, seed: int = 42):
        np.random.seed(seed)
        sc = BrainScale(scale)

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

        stdp_p = STDPParams(A_plus=0.01, A_minus=0.0105, lr=1.0)

        self.syn_s2f   = SparseSTDPSynapse(self.sensory.n,    self.feature.n,    p=0.04, params=stdp_p, name="sensory→feature")
        self.syn_f2a   = SparseSTDPSynapse(self.feature.n,    self.assoc.n,      p=0.02, params=stdp_p, name="feature→assoc")
        self.syn_a2p   = SparseSTDPSynapse(self.assoc.n,      self.predictive.n, p=0.02, params=stdp_p, name="assoc→predict")
        self.syn_p2a   = SparseSTDPSynapse(self.predictive.n, self.assoc.n,      p=0.02, params=stdp_p, name="predict→assoc")
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

        self.encoder = RateEncoder(vocab_size=1000, n_neurons=self.sensory.n)

        self.step_count     = 0
        self.total_spikes   = 0
        self.start_time     = time.time()
        self._attention_gain = 1.0

        # FIX-LOCK-2: _running now controls ONLY the start_background_loop thread
        # (which we no longer start from api/config.py). The continuous_loop has
        # its own _running flag and is not affected by this attribute.
        self._running  = False
        self._lock     = threading.Lock()
        self._step_rate = 0.0
        self._last_snapshot: dict = {}
        self._snapshot_fresh_until: float = 0.0

        self.chat_history: list[dict] = []
        self._pending_proactive: list[str] = []
        self._auto_training = False

        self.self_model = SelfModel.load()
        self.affect = SalienceFilter()
        self.drives = DriveSystem(self.self_model)

        from config import PERSIST_DIR
        _state_dir = os.getenv("BRAIN_STATE_DIR", PERSIST_DIR)
        self.store = BrainStore(base_dir=_state_dir)
        self.episode_store = EpisodeStore(base_dir=_state_dir)

        self.char_encoder = CharacterEncoder(self.sensory.n)
        self.phon_buffer = PhonologicalBuffer(n_assemblies=self.concept.n)
        self.llm_gate = LLMGate()
        self.cost_tracker = CostTracker()
        self.codec = LLMCodec()
        self.codec.set_components(self.llm_gate, self.phon_buffer, self.cost_tracker)

        self.response_cache = ResponseCache(max_size=200)
        self.bypass_monitor = LLMBypassMonitor(window_size=100)
        self.assembly_detector = CellAssemblyDetector(
            self.concept.n, min_coalition_size=1, stability_threshold=1
        )
        self.attractor_chainer = AttractorChainer()

        self.theta_pacemaker = SeptalThetaPacemaker()
        try:
            self.gamma_osc = create_gamma_oscillator(40.0)
            self.theta_gamma_coupler = ThetaGammaCoupler(preferred_phase=0.25, width=0.4)
        except Exception:
            self.gamma_osc = None
            self.theta_gamma_coupler = None

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

        self.neuromod = create_neuromodulator_system(n_per_population=max(50, int(self.concept.n * 0.01)))

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

        self.amygdala = AmygdalaRegion(n=max(100, int(self.concept.n * 0.01)))
        self.episode_store = EpisodeStore(base_dir=_state_dir)

        self._last_concept_id: int = -1
        self._last_process_time: float | None = None

        self.continuous_loop = ContinuousExistenceLoop(self)

        if self.store.exists():
            self.store.load_full(self)
            print(f"[BRAIN20Brain] Loaded persisted state - {self.self_model.total_turns} turns")

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

        asm_path = f"{self.store.BASE_DIR}/assemblies.json"
        try:
            if os.path.exists(asm_path):
                with open(asm_path) as f:
                    self.assembly_detector.import_(_json.load(f))
                print(f"[BRAIN20Brain] Loaded {self.assembly_detector.get_assembly_count()} assemblies")
        except Exception as e:
            print(f"[BRAIN20Brain] Assembly load skipped: {e}")

        chain_path = f"{self.store.BASE_DIR}/attractor_chainer.json"
        try:
            if os.path.exists(chain_path):
                with open(chain_path) as f:
                    self.attractor_chainer.import_(_json.load(f))
        except Exception as e:
            print(f"[BRAIN20Brain] Attractor chainer load skipped: {e}")

        theta_path = f"{self.store.BASE_DIR}/theta_pacemaker.json"
        try:
            if os.path.exists(theta_path):
                with open(theta_path) as f:
                    self.theta_pacemaker.import_(_json.load(f))
        except Exception as e:
            print(f"[BRAIN20Brain] Theta pacemaker load skipped: {e}")

        episodes_data = self.episode_store.load_episodes()
        if episodes_data:
            try:
                self.hippocampus.import_(episodes_data)
                print(f"[BRAIN20Brain] Loaded {len(episodes_data)} episodes")
            except Exception as e:
                print(f"[BRAIN20Brain] Hippocampus import skipped: {e}")

        _vocab_size = self.phon_buffer.get_vocabulary_size()
        if _vocab_size < 50:
            print(f"[BRAIN20Brain] Vocabulary empty ({_vocab_size} words) — auto-training in background")
            self._auto_training = True
            t = threading.Thread(target=self._auto_train_from_file, daemon=True)
            t.start()
        else:
            self._auto_training = False

        self.continuous_loop.start()
        print(f"[BRAIN20Brain] Continuous existence loop started")

    # ─── Process user input ───────────────────────────────────────────────────

    def process_input_v01(self, user_text: str, user_feedback: float = 0.0) -> dict:
        """
        Process user input through the SNN.

        FIX-LOCK-1: The thinking loop now acquires brain._lock in small batches
        (_STEP_BATCH steps at a time) and yields between batches. This keeps the
        lock hold time short so the WebSocket, status endpoints, and concurrent
        chat requests are never starved for more than a few milliseconds.

        FIX-LOCK-2: Removed the `was_running = self._running; self._running = False`
        pattern. It was intended to pause the background loop but permanently killed
        the background thread when called from the continuous loop context.
        """
        self.continuous_loop.notify_user_active()

        cached = self.response_cache.lookup(user_text)
        if cached is not None:
            self.bypass_monitor.record_turn('cached')
            return {
                'response': cached,
                'path': 'cached',
                'brain_state': self.snapshot(),
                'affect': self.affect.get_state(),
                'drives': self.drives.state.__dict__,
                'self_model': self.self_model,
            }

        affect_state = self.affect.assess(user_text)
        if hasattr(self, 'neuromod') and self.neuromod is not None:
            nm = self.neuromod.get_biases()
        else:
            nm = affect_state.as_neuromodulator_biases()

        ne_gain = 1.0 + nm["norepinephrine_delta"]
        da_gain = 1.0 + nm["dopamine_delta"]
        ach_multiplier = 1.0 + nm["acetylcholine_delta"] * 2.0
        ach_multiplier = max(1.0, ach_multiplier)  # Ensure minimum 1.0
        drive_mods = self.drives.behavioural_modifiers()

        base_gain = self._attention_gain
        stdp_gain = base_gain * ne_gain * da_gain * drive_mods["association_gain"]

        base_steps = self.affect.thinking_steps_for_salience(base_steps=400)
        thinking_steps = int(base_steps * ach_multiplier)
        
        # DEBUG: Show affect values causing the issue
        print(f"[THINK] Affect debug: arousal={affect_state.arousal:.2f}, valence={affect_state.valence:.2f}, ach_delta={nm['acetylcholine_delta']:.3f}, ach_mult={ach_multiplier:.2f}, base_steps={base_steps}")

        # Encode text (no lock needed — only writes to sensory.population.i_ext)
        self.char_encoder.encode(user_text, self.sensory)

        words_for_seeding = [w.lower().strip(".,!?;:'\"()-") for w in user_text.split() if len(w) > 1]
        seed_concept_indices = None
        if words_for_seeding:
            seed_concept_indices = np.array([
                int(hashlib.md5(w.encode()).hexdigest(), 16) % self.concept.n for w in words_for_seeding
            ], dtype=np.int32)

        # DEBUG: Log thinking loop parameters
        print(f"[THINK] Thinking params: steps={thinking_steps}, seed_count={len(seed_concept_indices) if seed_concept_indices is not None else 0}, words={len(words_for_seeding)}")
        
        # ── THINKING PHASE ────────────────────────────────────────────────────
        # FIX-LOCK-1: Acquire the lock in _STEP_BATCH-sized chunks.
        # Between batches we call time.sleep(0) to yield the GIL so the
        # WebSocket reader and other threads can make progress.
        concept_spikes_during_think = set()
        peak_regions = {}

        step_i = 0
        first_spike_step = -1
        while step_i < thinking_steps:
            batch_end = min(step_i + _STEP_BATCH, thinking_steps)
            with self._lock:
                for i in range(step_i, batch_end):
                    if seed_concept_indices is not None:
                        # FIX: Use constant high magnitude instead of decaying
                        # Decay prevented neurons from accumulating to threshold
                        magnitude = 50.0  # Increased from 20.0 for stronger activation
                        self.concept.population.inject_current(seed_concept_indices, magnitude)
                    self.step(stdp_gain)
                    if self.concept.last_spikes.size > 0:
                        concept_spikes_during_think.update(self.concept.last_spikes.tolist())
                        if first_spike_step < 0:
                            first_spike_step = i
                    for r in self.all_regions:
                        act = r.snapshot().get("activity_pct", 0)
                        if act > peak_regions.get(r.name, 0):
                            peak_regions[r.name] = act
            step_i = batch_end
            time.sleep(0)   # yield GIL between batches
        
        # FIX: Capture any remaining spikes after the loop
        with self._lock:
            if self.concept.last_spikes.size > 0:
                concept_spikes_during_think.update(self.concept.last_spikes.tolist())
                if first_spike_step < 0:
                    first_spike_step = thinking_steps
        
        # DEBUG: Log thinking loop results
        print(f"[THINK] Thinking loop: {thinking_steps} steps, {len(concept_spikes_during_think)} unique spikes, first spike at step {first_spike_step}")
        
        # ── POST-THINKING ─────────────────────────────────────────────────────
        words = [w.lower().strip(".,!?;:'\"()-") for w in user_text.split() if len(w) > 1]
        active_neurons = concept_spikes_during_think
        concept_id = self.assembly_detector.get_or_create_assembly(active_neurons)

        if concept_id >= 0:
            if self._last_concept_id >= 0:
                dt_ms = (time.time() - (self._last_process_time or time.time())) * 1000
                self.attractor_chainer.record_transition(self._last_concept_id, concept_id, dt_ms)
            self._last_concept_id = concept_id
            self._last_process_time = time.time()

        new_words = []
        # Use fallback concept ID 0 if no assembly created, to ensure learning happens
        learn_concept = concept_id if concept_id >= 0 else 0
        for word in words:
            is_new = self.phon_buffer.observe_pairing(word, learn_concept)
            if is_new:
                new_words.append(word)
        self.self_model.vocabulary_size = self.phon_buffer.get_vocabulary_size()

        # DEBUG: Log learning summary
        if new_words:
            print(f"[LEARN] === LEARNING SUMMARY ===")
            print(f"[LEARN] Input words: {len(words)}, New learned: {len(new_words)}")
            print(f"[LEARN] Concept: concept_id={concept_id}, learn_concept={learn_concept}")
            print(f"[LEARN] Active neurons (spikes): {len(active_neurons)}")
            print(f"[LEARN] Thinking steps: {thinking_steps}")
            print(f"[LEARN] Seed neurons: {len(seed_concept_indices) if seed_concept_indices is not None else 0}")
            print(f"[LEARN] Vocabulary size: {self.self_model.vocabulary_size}")
            print(f"[LEARN] Affect: arousal={affect_state.arousal:.2f}, valence={affect_state.valence:.2f}")
            print(f"[LEARN] First 10 new words: {new_words[:10]}")
            print(f"[LEARN] ========================")

        if new_words:
            self.persist_vocabulary()

        if affect_state.arousal > 0.5:
            self.hippocampus.encode(
                list(active_neurons),
                topic=words[0] if words else "unknown",
                valence=affect_state.valence,
                arousal=affect_state.arousal,
            )

        # Build snapshot under lock, then immediately release
        with self._lock:
            snapshot = self._build_snapshot()
            if peak_regions:
                for name, act in peak_regions.items():
                    if name in snapshot.get("regions", {}):
                        snapshot["regions"][name]["activity_pct"] = round(act, 2)
            self._last_snapshot = snapshot
            self._snapshot_fresh_until = time.time() + 3.0

        novelty = snapshot.get('prediction_error', 0.0)
        self.drives.update(
            prediction_error=1.0 - snapshot.get('attention_gain', 1.0) / 4.0,
            user_present=True,
            novelty=novelty,
            user_feedback=user_feedback
        )

        self.self_model.update_after_turn(prediction_error=novelty, user_feedback=user_feedback)
        self.self_model.total_steps += thinking_steps
        self.self_model.steps_this_session += thinking_steps

        memory_snippet = ""
        if active_neurons:
            min_overlap = 0.15
            if getattr(self, '_hippocampus_backend', 'simple') == 'full':
                recalled = self.hippocampus.recall(list(active_neurons), top_k=1, min_overlap=min_overlap)
            else:
                recalled = self.hippocampus.recall(set(active_neurons), top_k=1, min_overlap=min_overlap)
            if recalled:
                ep = recalled[0]
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

        # DEBUG: Log thinking process
        print(f"[THINK] === THINKING PROCESS ===")
        print(f"[THINK] Input: {user_text[:100]}...")
        print(f"[THINK] Concept neurons fired: {len(active_neurons)}")
        print(f"[THINK] Active assembly: {snapshot.get('regions', {}).get('concept', {}).get('active_concept_neuron', -1)}")
        print(f"[THINK] Concept activity: {snapshot.get('regions', {}).get('concept', {}).get('activity_pct', 0):.1f}%")
        print(f"[THINK] Association activity: {snapshot.get('regions', {}).get('association', {}).get('activity_pct', 0):.1f}%")
        print(f"[THINK] Predictive activity: {snapshot.get('regions', {}).get('predictive', {}).get('activity_pct', 0):.1f}%")
        print(f"[THINK] Memory recall: {memory_snippet if memory_snippet else 'No relevant memory'}")
        
        # LLM Gate decision logic with detailed logging
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
        }

        # DEBUG: Log brain state for gate decision
        print(f"[THINK] === LLM GATE DECISION ===")
        print(f"[THINK] Brain stage: {self.self_model.brain_stage}")
        print(f"[THINK] Confidence: {self.self_model.confidence:.2f} (threshold: 0.4)")
        print(f"[THINK] Prediction confidence: {snapshot.get('attention_gain', 1.0) / 4.0:.2f}")
        print(f"[THINK] Vocabulary size: {self.self_model.vocabulary_size}")
        
        chainer_obj = self.attractor_chainer
        gate_decision = self.llm_gate.should_call_llm(brain_state)
        
        print(f"[THINK] LLM Gate: should_call_llm={gate_decision.should_call_llm}, reason={gate_decision.reason}")

        if gate_decision.should_call_llm:
            result = self.codec.articulate(brain_state)
            response = result.text
            path = result.path
            print(f"[THINK] Response source: LLM ({path})")
        else:
            response = self.phon_buffer.generate(brain_state, chainer=chainer_obj)
            path = 'local'
            print(f"[THINK] Response source: LOCAL (phonological buffer)")
        
        print(f"[THINK] Response: {response[:150]}...")
        print(f"[THINK] =====================")
        
        self.bypass_monitor.record_turn(path)
        self.self_model.llm_bypass_rate = self.bypass_monitor.get_bypass_rate()
        if path == 'local':
            self.response_cache.store(user_text, response)

        if self.self_model.total_steps % 1000 == 0:
            self.persist()

        return {
            'response': response,
            'path': path,
            'brain_state': snapshot,
            'affect': affect_state,
            'drives': self.drives.state.__dict__,
            'self_model': self.self_model,
            'new_words': new_words,
        }

    # ─── Persistence ──────────────────────────────────────────────────────────

    def persist(self):
        self.store.save_full(self)
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
        asm_path = f"{self.store.BASE_DIR}/assemblies.json"
        with open(asm_path, "w") as f:
            _json.dump(self.assembly_detector.export(), f)
        chain_path = f"{self.store.BASE_DIR}/attractor_chainer.json"
        with open(chain_path, "w") as f:
            _json.dump(self.attractor_chainer.export(), f)
        theta_path = f"{self.store.BASE_DIR}/theta_pacemaker.json"
        with open(theta_path, "w") as f:
            _json.dump(self.theta_pacemaker.export(), f)
        self.episode_store.save_episodes(self.hippocampus.export())
        print(f"[BRAIN20Brain] Persisted state at step {self.self_model.total_steps}")

    def persist_vocabulary(self):
        try:
            if hasattr(self, 'self_model') and self.self_model is not None:
                self.store.save_self_model(self.self_model)
            if hasattr(self, 'phon_buffer') and self.phon_buffer is not None:
                self.store.save_vocabulary_export(self.phon_buffer.export_vocabulary())
        except Exception as e:
            print(f"[BRAIN20Brain] persist_vocabulary failed: {e}")

    def _auto_train_from_file(self, batch_size: int = 200):
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
        self.self_model.user_sentiment_avg = (
            0.95 * self.self_model.user_sentiment_avg + 0.05 * (valence * 0.5 + 0.5)
        )
        if valence > 0:
            self.drives.state.curiosity = min(1.0, self.drives.state.curiosity + 0.05)
            self.drives.state.competence = min(1.0, self.drives.state.competence + 0.03)
        else:
            self.drives.state.competence = min(1.0, self.drives.state.competence + 0.08)

        self.drives.update(prediction_error=0.0, user_present=True, novelty=0.0, user_feedback=valence)
        self.affect.apply_user_feedback(valence)
        self.self_model.update_after_turn(prediction_error=0.0, user_feedback=valence)

        if response_text:
            if not hasattr(self.self_model, 'recent_feedback'):
                self.self_model.recent_feedback = []
            self.self_model.recent_feedback.append({
                'valence': valence,
                'response_preview': response_text[:100] if response_text else None,
                'step': self.self_model.total_steps
            })
            if len(self.self_model.recent_feedback) > 10:
                self.self_model.recent_feedback = self.self_model.recent_feedback[-10:]

    # ─── Core simulation step ─────────────────────────────────────────────────

    def step(self, stdp_gain: float = 1.0) -> dict:
        gain = self._attention_gain

        bs_spikes = self.brainstem.step(np.zeros(self.brainstem.n, dtype=np.float32))

        if hasattr(self, 'amygdala') and self.amygdala is not None:
            try:
                amyg_input = np.zeros(self.amygdala.n, dtype=np.float32)
                if getattr(self.sensory, 'last_spikes', None) is not None and self.sensory.last_spikes.size > 0:
                    n_spikes = min(self.amygdala.n, int(self.sensory.last_spikes.size))
                    amyg_input[:n_spikes] = 15.0
                _ = self.amygdala.step(amyg_input)
            except Exception:
                pass

        if hasattr(self, 'neuromod') and self.neuromod is not None:
            try:
                reward_signal = max(0, self._attention_gain - 1.0) / 4.0
                salience_signal = min(1.0, self.sensory.activity_pct / 50.0)
                self.neuromod.step(reward_signal=reward_signal, salience_signal=salience_signal)
            except Exception:
                pass

        i_feature  = self.syn_s2f.propagate(self.sensory.last_spikes)
        f_spikes   = self.feature.step(i_feature)

        i_assoc    = self.syn_f2a.propagate(f_spikes)
        i_assoc   += self.syn_p2a.propagate(self.predictive.last_spikes, scale=gain)
        a_spikes   = self.assoc.step(i_assoc)

        i_pred     = self.syn_a2p.propagate(a_spikes)
        p_spikes   = self.predictive.step(i_pred)

        self._attention_gain = self.predictive.compute_error(self.assoc.activity_pct / 100.0)

        i_concept  = self.syn_a2c.propagate(a_spikes, scale=gain)
        i_concept += self.syn_p2c.propagate(p_spikes)
        c_spikes   = self.concept.step(i_concept)

        i_meta     = self.syn_c2m.propagate(c_spikes)
        m_spikes   = self.meta.step(i_meta)

        i_wm       = self.syn_m2wm.propagate(m_spikes)
        wm_spikes  = self.working_mem.step(i_wm)
        self.working_mem.hold(wm_spikes)

        i_cb       = self.syn_a2cb.propagate(a_spikes)
        cb_spikes  = self.cerebellum.step(i_cb)

        theta_phase = self.theta_pacemaker.tick(0.1)
        gamma_gain = 1.0
        try:
            if hasattr(self, 'gamma_osc') and self.gamma_osc is not None:
                self.gamma_osc.tick(0.1)
                if hasattr(self, 'theta_gamma_coupler') and self.theta_gamma_coupler is not None:
                    cg = self.theta_gamma_coupler.coupling_gain(theta_phase)
                    gamma_gain = 1.0 + 0.5 * cg
        except Exception:
            pass

        try:
            if getattr(self, '_use_ping_gamma', False) and getattr(self, 'ping_gamma', None) is not None:
                ext = max(0.5, min(10.0, self._attention_gain * 2.0))
                if self.ping_gamma is not None:
                    self.ping_gamma.step(0.1, ext_drive=ext)
                    ping_power = self.ping_gamma.get_power()
                    gamma_gain = gamma_gain * (1.0 + 0.5 * ping_power)
        except Exception:
            gamma_gain = 1.0

        apply_ltp = self.theta_pacemaker.is_encoding_window()
        apply_ltd = True

        da_multiplier = 1.0
        if hasattr(self, 'neuromod') and self.neuromod is not None:
            da_multiplier = self.neuromod.da.get_stdp_multiplier(1.0)

        pop = {r.name: r.population for r in self.all_regions}

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

        for r in self.all_regions:
            r.population.reset_external()

        self.step_count += 1
        self.total_spikes += sum(
            len(s) for s in [bs_spikes, f_spikes, a_spikes, p_spikes,
                              c_spikes, m_spikes, wm_spikes, cb_spikes]
        )

        return {"step": self.step_count, "gain": self._attention_gain}

    # ─── Sensory stimulation ──────────────────────────────────────────────────

    def stimulate_modality(self, modality: str, data: np.ndarray):
        self.sensory.stimulate(modality, data)

    def process_text(self, text: str):
        tokens = self._tokenise(text)
        current = self.encoder.encode(tokens, self.sensory.n)
        self.sensory.population.i_ext += current
        vis_stim = np.random.rand(int(self.sensory.n * 0.4)) * (len(text) / 200.0)
        self.sensory.stimulate("vision", vis_stim)

    def _tokenise(self, text: str) -> list[int]:
        tokens = []
        words = text.lower().split()
        for w in words:
            h = hash(w) % 1000
            tokens.append(h)
        return tokens

    # ─── Background simulation loop (kept for compatibility; NOT started by default) ──

    def start_background_loop(self, steps_per_tick: int = 50):
        """
        Legacy background loop. NOT called from api/config.py any more —
        the continuous_loop started in __init__ handles all background stepping.
        Kept here so tests or manual scripts that call it directly still work.
        """
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, args=(steps_per_tick,), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        self.continuous_loop.stop()

    def _loop(self, steps_per_tick: int):
        while self._running:
            t0 = time.perf_counter()
            with self._lock:
                for _ in range(steps_per_tick):
                    self.step()
                if time.time() > self._snapshot_fresh_until:
                    self._last_snapshot = self._build_snapshot()
            elapsed = time.perf_counter() - t0
            self._step_rate = steps_per_tick / max(elapsed, 1e-6)
            time.sleep(0.01)

    # ─── Snapshot / telemetry ─────────────────────────────────────────────────

    def _build_snapshot(self) -> dict:
        """Build a fresh snapshot. Caller is responsible for holding self._lock."""
        elapsed = max(time.time() - self.start_time, 1e-6)
        regions = {}
        for r in self.all_regions:
            try:
                regions[r.name] = r.snapshot()
            except Exception:
                regions[r.name] = {"name": r.name, "activity_pct": 0.0}

        # FIX-JSON-1: wrap amygdala snapshot so a bad amygdala can't crash the whole build
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
        """
        FIX-SNAP-1: Return the cached snapshot without acquiring the lock.
        _last_snapshot is a plain dict; reading the reference under CPython's
        GIL is atomic. Only fall back to a full rebuild (under lock) when the
        cache is empty, which only happens on first call after startup.
        """
        snap = self._last_snapshot
        if snap:
            return snap
        with self._lock:
            self._last_snapshot = self._build_snapshot()
            return self._last_snapshot

    def _status(self) -> str:
        s = self.self_model.total_steps
        if s < 100_000:   return "NEONATAL"
        if s < 1_000_000: return "JUVENILE"
        if s < 5_000_000: return "ADOLESCENT"
        return "MATURE"

    def issue_motor_command(self, cmd: dict) -> dict:
        return self.reflex.check_command(cmd)

    def total_synapses(self) -> int:
        return sum(s.n_synapses for s in self.all_synapses)

    def total_neurons(self) -> int:
        return sum(r.n for r in self.all_regions)