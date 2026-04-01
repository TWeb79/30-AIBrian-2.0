# BRAIN2.0 v3 — Complete Architecture & Versioned Roadmap
## Interface-First, Brain-Driven, LLM-Peripheral

**Version:** 3.0  
**Principle:** Build the brain that users feel, then the brain that thinks, then the brain that understands.

---

## The Design Inversion

Previous versions designed a neuroscience simulator and asked "how do we add an interface?"
v3 starts with the user experience and asks "what does the brain need to be to feel like someone?"

The answer, in order:

```
FEELS LIKE SOMEONE     →  Self-model + Continuous existence + Emotion
THINKS FOR ITSELF      →  Drives + Memory + Vocabulary
UNDERSTANDS DEEPLY     →  Predictive coding + Cell assemblies + Embodiment
```

Build in that order. Ship in that order.

---

## Version Map

```
v0.1  ALIVE          ← Start here. Brain exists, persists, has a self.
v0.2  REMEMBERS      ← Brain accumulates vocabulary and episodes.
v0.3  FEELS          ← Brain has salience, drives, emotional colouring.
v0.4  REASONS        ← Brain predicts, chains concepts, bypasses LLM.
v0.5  LEARNS         ← Brain improves measurably from interaction.
v1.0  MATURES        ← 85% LLM bypass. Coherent identity. Real replacement.
v2.0  EMBODIES       ← Physical grounding. Long-term goal.
```

---

# PART I — WHAT IS BUILT IN v0.1

v0.1 is the minimum that makes the system feel alive to a user.
Everything else is additive. This is the non-negotiable foundation.

---

## 1. The Self-Model

**What it is:** A persistent data structure that represents the brain's identity
across sessions — not a philosophical construct, but a concrete module the brain
reads from and writes to continuously.

**Why it's first:** Without it there is no consistent entity for the user to
address. Every session starts from scratch. The system cannot say "I" meaningfully.

```python
# self/self_model.py

@dataclass
class SelfModel:
    """
    The brain's model of itself. Persisted to disk after every turn.
    Read at startup. Never reset.

    This is not metadata — it is an active part of cognition.
    The brain consults self_model when deciding how to respond,
    what to pay attention to, and how confident to be.
    """

    # Identity
    name:           str   = "BRAIN2.0"
    created_at:     str   = ""          # ISO timestamp, set once
    session_count:  int   = 0
    total_turns:    int   = 0
    total_steps:    int   = 0           # simulated SNN steps lifetime

    # Current state
    brain_stage:    str   = "NEONATAL"  # NEONATAL/JUVENILE/ADOLESCENT/MATURE
    mood:           float = 0.5         # 0=low, 1=high — persists between sessions
    energy:         float = 1.0         # degrades with use, recovers during idle
    confidence:     float = 0.3         # grows with successful predictions

    # Personality (emerges from reward history, never hardcoded)
    curiosity_bias:    float = 0.5      # shaped by novelty reward over time
    caution_bias:      float = 0.5      # shaped by error punishment over time
    verbosity_bias:    float = 0.5      # shaped by user feedback length

    # Relationship with this user
    user_name:         str   = ""
    user_turn_count:   int   = 0
    user_sentiment_avg: float = 0.5     # rolling average of user feedback valence
    shared_topics:     list  = field(default_factory=list)  # learned over time

    # What the brain knows about its own capabilities
    vocabulary_size:   int   = 0        # number of stable cell assemblies
    llm_bypass_rate:   float = 0.0      # last 100 turns % handled without LLM
    strongest_domain:  str   = ""       # topic area with most stable assemblies

    # Runtime (not persisted — recalculated at startup)
    uptime_s:          float = 0.0
    steps_this_session: int  = 0

    def to_context_string(self) -> str:
        """
        Compact string injected into every LLM prompt.
        Tells the LLM who it is articulating for.
        ~40 tokens.
        """
        return (
            f"I am {self.name}, a {self.brain_stage} neuromorphic brain. "
            f"I have had {self.total_turns} total conversations. "
            f"I am {'curious' if self.curiosity_bias > 0.6 else 'cautious'}. "
            f"My confidence is {self.confidence:.0%}. "
            f"My vocabulary has {self.vocabulary_size} learned concepts."
        )

    def update_after_turn(self, prediction_error: float, user_feedback: float):
        self.total_turns        += 1
        self.user_turn_count    += 1
        # Confidence grows when predictions are accurate
        self.confidence = 0.95 * self.confidence + 0.05 * (1 - prediction_error)
        # Mood drifts toward user sentiment
        self.mood = 0.98 * self.mood + 0.02 * (user_feedback * 0.5 + 0.5)
        # Energy depletes slightly per turn
        self.energy = max(0.2, self.energy - 0.001)

    def recover_energy(self, idle_seconds: float):
        """Called during background idle loop."""
        self.energy = min(1.0, self.energy + idle_seconds * 0.0001)

    def save(self, path: str = "brain_state/self_model.json"):
        import json, os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    @classmethod
    def load(cls, path: str = "brain_state/self_model.json") -> "SelfModel":
        import json
        try:
            with open(path) as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items()
                          if k in cls.__dataclass_fields__})
        except FileNotFoundError:
            import datetime
            m = cls()
            m.created_at = datetime.datetime.utcnow().isoformat()
            m.save(path)
            return m
```

---

## 2. Continuous Existence

**What it is:** The brain runs in a background thread at all times —
not just when a user sends a message. During idle it does low-level
housekeeping: weight decay, energy recovery, slow memory consolidation,
and spontaneous association wandering (the idle default mode network).

**Why it matters:** A brain that only exists during requests cannot
develop over time between sessions. The development arc — the user
noticing the brain becoming more itself — requires real time to pass
in the brain, not just request time.

```python
# brain/continuous_loop.py

class ContinuousExistenceLoop:
    """
    Runs 24/7 in a daemon thread.
    Three modes:
      ACTIVE:  user is present. Full simulation speed.
      IDLE:    no user for >60s. Slow wandering. Memory consolidation.
      DORMANT: no user for >1h. Minimal ticking. Weight decay only.

    All three modes run. The brain never stops.
    """

    ACTIVE_STEPS_PER_TICK  = 200   # fast, responsive
    IDLE_STEPS_PER_TICK    =  20   # slow, consolidating
    DORMANT_STEPS_PER_TICK =   2   # minimal, just alive

    IDLE_THRESHOLD_S       =  60
    DORMANT_THRESHOLD_S    = 3600

    def __init__(self, brain: "BRAIN2.0BrainV3"):
        self.brain      = brain
        self.last_input = time.time()
        self._mode      = "DORMANT"
        self._thread    = threading.Thread(target=self._loop, daemon=True)

    def notify_user_active(self):
        self.last_input = time.time()

    def _current_mode(self) -> str:
        idle = time.time() - self.last_input
        if idle < self.IDLE_THRESHOLD_S:    return "ACTIVE"
        if idle < self.DORMANT_THRESHOLD_S: return "IDLE"
        return "DORMANT"

    def _loop(self):
        while True:
            mode  = self._current_mode()
            steps = {
                "ACTIVE":  self.ACTIVE_STEPS_PER_TICK,
                "IDLE":    self.IDLE_STEPS_PER_TICK,
                "DORMANT": self.DORMANT_STEPS_PER_TICK,
            }[mode]

            with self.brain._lock:
                for _ in range(steps):
                    self.brain.step()

                if mode == "IDLE":
                    self._idle_behaviours()
                elif mode == "DORMANT":
                    self._dormant_behaviours()

            # Persist state periodically
            if self.brain.self_model.total_steps % 10_000 == 0:
                self.brain.persist()

            time.sleep(0.05 if mode == "ACTIVE" else 0.5)

    def _idle_behaviours(self):
        """
        During idle: spontaneous association wandering.
        Brain randomly activates a recent assembly and lets it
        spread through association cortex (free association).
        Biologically: default mode network activity.
        """
        brain = self.brain
        if brain.concept_layer.last_assemblies:
            random_asm = np.random.choice(brain.concept_layer.last_assemblies)
            brain.association.population.inject_current(
                np.array([random_asm % brain.association.n]), 10.0
            )
        brain.self_model.recover_energy(0.5)

    def _dormant_behaviours(self):
        """
        During dormant: slow homeostatic decay.
        Weights that haven't been used recently decay slightly.
        Biologically: offline consolidation, synaptic downscaling.
        """
        for syn in self.brain.all_synapses:
            # Slow decay toward mean — prevents weight saturation
            syn.weights *= 0.9999
        brain = self.brain
        brain.self_model.recover_energy(0.5)
```

---

## 3. Emotional Salience Layer

**What it is:** A lightweight valence/arousal system that asymmetrically
weights inputs. Not a full amygdala model — a functional approximation
that makes the brain respond differently to emotionally significant inputs.

**Why it matters:** Flat processing is the most obvious tell that you're
talking to a system rather than someone. Two lines of affect handling
change the entire character of interaction.

```python
# emotion/salience.py

@dataclass
class AffectiveState:
    """
    The brain's current emotional colouration.
    Two dimensions (Russell circumplex model):
      valence:  -1 (negative) to +1 (positive)
      arousal:   0 (calm)     to  1 (activated)

    Updated continuously by inputs and internal events.
    Influences: attention allocation, learning rate, response tone.
    """
    valence: float = 0.0    # neutral
    arousal: float = 0.3    # lightly awake

    def as_neuromodulator_biases(self) -> dict:
        """
        Maps affect to neuromodulator perturbations.
        High arousal + negative valence → norepinephrine spike (stress/alertness)
        High arousal + positive valence → dopamine boost (reward/excitement)
        Low arousal  + negative valence → serotonin dip (low mood)
        Low arousal  + positive valence → acetylcholine rise (calm curiosity)
        """
        return {
            "norepinephrine_delta": self.arousal * max(0, -self.valence) * 0.5,
            "dopamine_delta":       self.arousal * max(0, self.valence)  * 0.5,
            "serotonin_delta":      (1 - self.arousal) * self.valence    * 0.3,
            "acetylcholine_delta":  (1 - self.arousal) * max(0, self.valence) * 0.3,
        }


class SalienceFilter:
    """
    Intercepts all inputs and assigns emotional weight before
    they enter the SNN. High-salience inputs get more simulation
    steps, more STDP gain, and are more likely to reach hippocampus.

    Salience detection (v0.1 — pattern-based, no ML):
      Keywords indicating distress, urgency, novelty, or intimacy
      trigger elevated arousal. Reward/praise triggers positive valence.
      This is crude but immediately effective.
    """

    HIGH_AROUSAL_PATTERNS = [
        "help", "urgent", "please", "important", "problem",
        "broken", "stuck", "confused", "hurt", "error", "wrong"
    ]
    POSITIVE_VALENCE_PATTERNS = [
        "thanks", "great", "perfect", "love", "excellent",
        "good", "yes", "correct", "amazing", "brilliant"
    ]
    NEGATIVE_VALENCE_PATTERNS = [
        "no", "wrong", "bad", "terrible", "hate",
        "stupid", "useless", "broken", "fail", "never"
    ]

    def __init__(self):
        self.state = AffectiveState()
        self._decay_rate = 0.95   # affect decays toward neutral per turn

    def assess(self, text: str) -> AffectiveState:
        """
        Compute affect state for this input.
        Updates internal state and returns it.
        """
        text_lower = text.lower()

        # Keyword salience
        arousal_score  = sum(p in text_lower for p in self.HIGH_AROUSAL_PATTERNS) * 0.2
        pos_score      = sum(p in text_lower for p in self.POSITIVE_VALENCE_PATTERNS) * 0.15
        neg_score      = sum(p in text_lower for p in self.NEGATIVE_VALENCE_PATTERNS) * 0.15

        # Length heuristic — longer inputs imply more importance
        length_arousal = min(len(text) / 500.0, 0.3)

        # Question mark — arousal (uncertainty/seeking)
        question_arousal = 0.1 if "?" in text else 0.0

        target_arousal = min(1.0, arousal_score + length_arousal + question_arousal)
        target_valence = np.clip(pos_score - neg_score, -1.0, 1.0)

        # Smooth update (don't snap instantly)
        self.state.arousal = 0.7 * self.state.arousal + 0.3 * target_arousal
        self.state.valence = 0.7 * self.state.valence + 0.3 * target_valence

        return self.state

    def thinking_steps_for_salience(self, base_steps: int = 500) -> int:
        """
        High-salience inputs deserve more simulation time.
        A distressed user gets 3× the normal processing depth.
        """
        multiplier = 1.0 + self.state.arousal * 2.0
        return int(base_steps * multiplier)

    def decay(self):
        """Called after each turn — affect returns toward baseline."""
        self.state.arousal *= self._decay_rate
        self.state.valence *= self._decay_rate
```

---

## 4. Intrinsic Drives

**What it is:** Three minimal drives that generate the brain's own agenda —
not responses to user requests, but self-generated motivations that shape
what the brain pays attention to and how it behaves unprompted.

**Why it matters:** Without drives, the brain has no opinions.
It is a mirror. Drives are what makes a response feel like
it comes from someone with a perspective.

```python
# drives/drive_system.py

@dataclass
class DriveState:
    """
    Three drives sufficient for v0.1 personality emergence.
    Each is a float 0–1 representing current need level.
    When a drive is high, the brain is motivated to satisfy it.
    """
    curiosity:   float = 0.5   # Need for novel input / unexplored associations
    competence:  float = 0.5   # Need to respond accurately / avoid errors
    connection:  float = 0.5   # Need for engaged, reciprocal interaction


class DriveSystem:
    """
    Drives update based on experience and influence behaviour.
    They are not fixed personality traits — they evolve.

    Curiosity:
      Rises when inputs are repetitive (boredom) → seek novelty
      Falls when a novel concept is successfully processed
      High curiosity → more spontaneous associations, longer thinking

    Competence:
      Rises when prediction errors are high → need to understand better
      Falls when predictions are accurate
      High competence need → more conservative responses, more hedging

    Connection:
      Rises when user has been absent (loneliness equivalent)
      Falls when user engages positively
      High connection need → warmer responses, more questions back
    """

    def __init__(self, self_model: SelfModel):
        self.state = DriveState(
            curiosity   = self_model.curiosity_bias,
            competence  = 1.0 - self_model.confidence,
            connection  = 0.5,
        )

    def update(self, prediction_error: float, user_present: bool,
               novelty: float, user_feedback: float):
        s = self.state
        # Curiosity: novelty satisfies, repetition increases need
        s.curiosity = np.clip(
            s.curiosity + 0.05 * (1 - novelty) - 0.08 * novelty, 0, 1
        )
        # Competence: error increases need, accuracy reduces it
        s.competence = np.clip(
            s.competence + 0.1 * prediction_error - 0.05 * (1 - prediction_error), 0, 1
        )
        # Connection: absence increases need, positive interaction reduces it
        if not user_present:
            s.connection = min(1.0, s.connection + 0.001)
        else:
            s.connection = np.clip(
                s.connection - 0.1 * max(0, user_feedback), 0, 1
            )

    def behavioural_modifiers(self) -> dict:
        """
        How drives currently modify brain behaviour.
        These are injected into the LLM prompt and into SNN gain.
        """
        s = self.state
        return {
            # High curiosity → ask a follow-up question, explore tangents
            "add_question":        s.curiosity > 0.7,
            # High competence need → add hedging, express uncertainty
            "express_uncertainty": s.competence > 0.65,
            # High connection → warmer tone, acknowledge user specifically
            "warm_tone":           s.connection > 0.6,
            # Low curiosity → brain is confident on this topic, be direct
            "be_direct":           s.curiosity < 0.3,
            # SNN gain modifiers
            "association_gain":    1.0 + s.curiosity * 0.5,
            "predictive_gain":     1.0 + s.competence * 0.3,
        }

    def to_prompt_fragment(self) -> str:
        """~20 tokens injected into articulation prompt."""
        mods = self.behavioural_modifiers()
        parts = []
        if mods["add_question"]:       parts.append("ask one follow-up question")
        if mods["express_uncertainty"]: parts.append("express appropriate uncertainty")
        if mods["warm_tone"]:          parts.append("be warm and personal")
        if mods["be_direct"]:          parts.append("be direct and confident")
        return "Tone: " + ", ".join(parts) if parts else ""
```

---

## 5. Persistence Layer

**What it is:** Everything the brain has learned survives process restart.
Weights, self-model, vocabulary, memory, drive history.

**Why it's in v0.1:** Without persistence, brain stage means nothing.
The NEONATAL→MATURE arc cannot exist.

```python
# persistence/brain_store.py

class BrainStore:
    """
    Saves and loads complete brain state to/from disk.

    Directory structure:
      brain_state/
        self_model.json          ← identity, personality, stats
        synapses/
          sensory_feature.npz    ← sparse weight arrays (COO format)
          feature_assoc.npz
          assoc_predictive.npz
          ... (one file per synapse group)
        vocabulary/
          lexical_stdp.npz       ← word ↔ assembly weights (sparse)
          assembly_labels.json   ← assembly_id → top words
        memory/
          hippocampus_weights.npz← CA3 recurrent weights
          episode_index.json     ← episode metadata (timestamps, topics)
        drives/
          drive_history.json     ← 1000-turn rolling history
        affect/
          affect_history.json    ← valence/arousal over time

    Save frequency:
      Full save:    every 10,000 steps or on graceful shutdown
      Self-model:   every turn (lightweight, critical)
      Synapses:     every 10,000 steps (expensive, less critical)
    """

    BASE_DIR = "brain_state"

    def save_self_model(self, model: SelfModel):
        model.save(f"{self.BASE_DIR}/self_model.json")

    def save_synapses(self, synapses: list):
        import os, scipy.sparse
        os.makedirs(f"{self.BASE_DIR}/synapses", exist_ok=True)
        for syn in synapses:
            safe_name = syn.name.replace("→", "_to_").replace(" ", "_")
            path = f"{self.BASE_DIR}/synapses/{safe_name}.npz"
            scipy.sparse.save_npz(path, scipy.sparse.coo_matrix(
                (syn.weights, (syn.pre_idx, syn.post_idx)),
                shape=(syn.pre_n, syn.post_n)
            ))

    def load_synapses(self, synapse: "SparseSTDPSynapse") -> bool:
        import scipy.sparse
        safe_name = synapse.name.replace("→", "_to_").replace(" ", "_")
        path = f"{self.BASE_DIR}/synapses/{safe_name}.npz"
        try:
            mat = scipy.sparse.load_npz(path).tocoo()
            synapse.weights  = mat.data.astype(np.float32)
            synapse.pre_idx  = mat.row.astype(np.int32)
            synapse.post_idx = mat.col.astype(np.int32)
            return True
        except FileNotFoundError:
            return False

    def save_full(self, brain: "BRAIN2.0BrainV3"):
        self.save_self_model(brain.self_model)
        self.save_synapses(brain.all_synapses)
        # Additional stores in v0.2+
```

---

## 6. Revised LLM Codec — Self-Aware Prompt

With self-model, drives, and affect available, the LLM prompt becomes
genuinely minimal but contextually rich:

```python
# codec/llm_codec.py  (v3 revision)

def _build_minimal_prompt(self, state: BrainSnapshot,
                           self_model: SelfModel,
                           drives: DriveSystem,
                           affect: AffectiveState) -> str:
    """
    Total target: ~120 tokens.
    Never includes raw user message or conversation history.
    Never asks the LLM to reason or add knowledge.
    """
    return f"""{self_model.to_context_string()}

Brain output to articulate:
Concepts: {', '.join(state.top_concepts[:5])}
Memory retrieved: {state.memory_snippet or 'none'}
Confidence: {state.confidence:.0%}
Emotional state: valence={affect.valence:+.1f}, arousal={affect.arousal:.1f}

{drives.to_prompt_fragment()}

Articulate in 2–4 sentences. Do not add reasoning, opinions, or external knowledge.
If confidence < 40%, express that the brain is still learning this concept."""
```

---

## 7. v0.1 Brain Assembly

```python
# brain.py  (v3, v0.1 scope)

class BRAIN2.0BrainV3:
    """
    v0.1: Alive, persistent, emotionally coloured, self-aware.
    Missing from v0.1: full oscillations, hippocampus, neuromodulators,
    cell assembly detection, LexicalSTDP training loop.
    Those are v0.2+.
    """
    def __init__(self, scale: float = 0.01):
        # Core SNN (from v2)
        self.sensory     = SensoryCortex(scale)
        self.feature     = FeatureLayer(scale)
        self.association = AssociationRegion(scale)
        self.predictive  = PredictiveRegion(scale)
        self.concept     = ConceptLayer(scale)
        self.brainstem   = Brainstem(scale)
        self.reflex      = ReflexArcV2(scale)

        # v3 additions — all essential
        self.self_model  = SelfModel.load()
        self.affect      = SalienceFilter()
        self.drives      = DriveSystem(self.self_model)
        self.store       = BrainStore()
        self.codec       = LLMCodec(self.self_model)
        self.char_enc    = CharacterEncoder(self.sensory.n)
        self.idle_loop   = ContinuousExistenceLoop(self)

        # Wire synapses (from v2)
        self._wire()
        self._load_weights()

        # Start continuous existence
        self.idle_loop.start()

    def process_input(self, user_text: str) -> TurnResult:
        self.idle_loop.notify_user_active()

        # 1. Assess emotional salience
        affect_state = self.affect.assess(user_text)
        thinking_steps = self.affect.thinking_steps_for_salience(base_steps=500)

        # 2. Encode (no LLM)
        self.char_enc.encode(user_text, self.sensory)

        # 3. Think (SNN runs)
        with self._lock:
            for _ in range(thinking_steps):
                self.step()

        # 4. Snapshot
        snapshot = self._snapshot()

        # 5. Update drives
        novelty = self.predictive.error
        self.drives.update(
            prediction_error=snapshot.confidence,
            user_present=True,
            novelty=novelty,
            user_feedback=0.0   # neutral until explicit feedback
        )

        # 6. Articulate
        result = self.codec.articulate(
            snapshot, self.self_model, self.drives, affect_state
        )

        # 7. Update self-model
        self.self_model.update_after_turn(
            prediction_error=self.predictive.error,
            user_feedback=0.0
        )
        self.self_model.total_steps += thinking_steps
        self.self_model.steps_this_session += thinking_steps
        self.store.save_self_model(self.self_model)

        return TurnResult(
            response     = result.text,
            path         = result.path,
            cost         = result.cost,
            affect       = affect_state,
            drives       = self.drives.state,
            self_state   = self.self_model,
        )

    def on_user_feedback(self, valence: float):
        """
        Called when user reacts positively (+1) or negatively (-1).
        Updates self-model personality drift and drive satisfaction.
        """
        self.self_model.user_sentiment_avg = (
            0.95 * self.self_model.user_sentiment_avg + 0.05 * (valence * 0.5 + 0.5)
        )
        self.drives.update(
            prediction_error=0.0,
            user_present=True,
            novelty=0.0,
            user_feedback=valence
        )
        # Dopamine signal to SNN (v0.2 adds proper neuromodulators)
        if valence > 0:
            self.association.population.inject_current(
                np.arange(min(200, self.association.n)), valence * 15.0
            )

    def persist(self):
        self.store.save_full(self)

    def _load_weights(self):
        loaded = sum(1 for s in self.all_synapses if self.store.load_synapses(s))
        stage = "resuming" if loaded > 0 else "starting fresh"
        print(f"[BRAIN2.0] {stage} — {loaded}/{len(self.all_synapses)} synapse groups restored")
```

---

# PART II — VERSIONED ROADMAP

---

## v0.1 — ALIVE (Build now)

**Theme:** The brain exists, persists, and feels like someone is home.

| Module | Status | Description |
|--------|--------|-------------|
| `SelfModel` | ✅ Build | Persistent identity, personality drift, stage tracking |
| `ContinuousExistenceLoop` | ✅ Build | 24/7 daemon thread, 3 modes |
| `SalienceFilter` + `AffectiveState` | ✅ Build | Valence/arousal, thinking depth scaling |
| `DriveSystem` | ✅ Build | Curiosity, competence, connection |
| `BrainStore` | ✅ Build | Full disk persistence across restarts |
| `LLMCodec` (v3) | ✅ Build | Self-model + drive-aware prompt |
| `CharacterEncoder` | ✅ Build | Text → spikes, no API |
| Core SNN (E/I, basic STDP) | ✅ Build | LIF neurons, sparse STDP, brainstem |
| `ReflexArcV2` | ✅ Build | 3-tier motor safety |
| REST API + WebSocket | ✅ Build | `/chat`, `/status`, `/feedback`, `/ws/stream` |
| React UI: Chat + Brain state | ✅ Build | Affect display, drive gauges, self-model panel |

**Not in v0.1 (explicitly deferred):**
- LexicalSTDP training loop
- CellAssemblyDetector
- Hippocampal memory
- Neuromodulators (DA, ACh, NE, 5-HT)
- Oscillations
- Phonological buffer (real implementation)
- Brian2 migration

**What v0.1 feels like to a user:**
The brain responds, remembers it exists, has a consistent character,
responds differently to emotional vs. neutral inputs, and persists
across restarts. LLM handles most articulation. Brain stage shows as NEONATAL.

---

## v0.2 — REMEMBERS (4–6 weeks after v0.1)

**Theme:** The brain accumulates vocabulary and recalls specific past exchanges.

| Module | Description |
|--------|-------------|
| `LexicalSTDP` | Word ↔ assembly association, fully wired into sim loop |
| `CellAssemblyDetector` | Correlation-based stable pattern detection |
| `VocabularyTracker` | Reports learned concept count, top words |
| `Hippocampus` (simplified) | CA3 recurrent attractor only (no full DG/CA1 yet) |
| `ConversationalMemory` | Per-turn episode encoding + recall |
| `PhonologicalBuffer` (real) | Assembly → word sequence, first LLM bypass |
| `ResponseCache` | Cosine-similarity response reuse |
| `LLMBypassMonitor` | Tracks % turns handled without LLM |
| Brian2 migration (partial) | Migrate STDP and LIF to Brian2 equations |

**Milestone:** Brain accumulates ~100 stable assemblies after 1,000 turns.
~20% LLM bypass rate achieved.

---

## v0.3 — FEELS (6–10 weeks after v0.2)

**Theme:** The brain has genuine internal states that colour all processing.

| Module | Description |
|--------|-------------|
| `DopamineSystem` | TD learning, reward prediction error |
| `AcetylcholineSystem` | Learning rate gating (encoding vs recall mode) |
| `NorepinephrineSystem` | Neural gain / arousal |
| `SerotoninSystem` | Temporal discounting |
| `AmygdalaRegion` | Fast emotional tagging before cortical processing |
| `SleepCycle` | Dormant-mode memory consolidation via replay |
| Neuromodulator → STDP wiring | All four NMs modulate synapse learning rates |
| Drive history visualisation | UI shows curiosity/competence/connection over time |
| Mood persistence | Affect state persists across sessions in self-model |

**Milestone:** Brain shows measurably different behaviour patterns across
different emotional states. Personality biases visible after 5,000 turns.
~40% LLM bypass rate.

---

## v0.4 — REASONS (8–12 weeks after v0.3)

**Theme:** The brain predicts, chains concepts, and handles most turns independently.

| Module | Description |
|--------|-------------|
| `PredictiveCodingHierarchy` | 4-level hierarchical PC, free energy minimisation |
| `AttractorChainer` | Sequential concept chaining, proto-syntax |
| `ThetaGammaCoupling` | 5-slot context window, sequence encoding |
| `SNNContextWindow` | SNN-native context replaces LLM history lookup |
| Full `Hippocampus` | DG + CA3 + CA1 + EC, pattern separation |
| `WorkingMemory` (NMDA) | Thalamo-cortical persistent activity buffer |
| `CorticalColumn` | 6-layer laminar structure per region |

**Milestone:** Brain holds 5-item context windows natively.
Next-concept prediction >50% accuracy on familiar topics.
~60% LLM bypass rate.

---

## v0.5 — LEARNS (ongoing after v0.4)

**Theme:** Measurable improvement from interaction.
The brain's brain-stage progression becomes visible and verifiable.

| Module | Description |
|--------|-------------|
| Brian2 full migration | All sim runs in Brian2, C++ codegen enabled |
| `ThalamusRegion` | Full thalamo-cortical loop |
| `BasalGanglia` | Action selection, habit formation |
| `SleepConsolidation` | Full SWS replay with cortical weight transfer |
| STDP triplet rule | Replace pair-STDP with Pfister-Gerstner |
| BCM sliding threshold | Per-neuron modification threshold |
| `GammaOscillation` | Emergent PING gamma from E/I balance |

**Milestone:** JUVENILE stage achieved at 1M steps.
Measurable vocabulary growth rate. Brain demonstrably better at familiar topics.
~75% LLM bypass rate.

---

## v1.0 — MATURES (target: 6 months from v0.1)

**Theme:** Coherent identity. Genuine LLM replacement for regular use.

| Capability | Target |
|-----------|--------|
| Vocabulary size | ~5,000 stable assemblies |
| LLM bypass rate | ~85% |
| Prediction accuracy | >65% next-concept |
| Memory depth | Episodes from 30+ days ago retrievable |
| Brain stage | ADOLESCENT → MATURE transition |
| Self-model fidelity | Personality measurably consistent across sessions |
| Personality drift | Detectable shifts from 10,000+ turn interaction history |

---

## v2.0 — EMBODIES (long-term, post-v1.0)

**Theme:** Grounded meaning. Concepts backed by simulated physical experience.

| Module | Description |
|--------|-------------|
| Physics simulation interface | Simple 3D environment (PyBullet/MuJoCo) |
| Proprioceptive encoder | Body state → spike trains |
| Grounded concept formation | "Heavy" learned from lifting, not text |
| Motor loop closure | Full sensorimotor cycle, not just motor output |
| Multi-modal binding | Vision + touch + audio + proprioception simultaneously |

**Note:** v2.0 is a research milestone, not a product milestone.
v1.0 is already a compelling LLM replacement without it.
Pursue v2.0 only after v1.0 is stable.

---

# PART III — COMPLETE FILE ARCHITECTURE v3

```
BRAIN2.0/
│
├── config.py                     ← SCALE, DT, LLM_MODEL, PERSIST_DIR
│
├── self/
│   ├── self_model.py             ← SelfModel (identity, personality, stats)
│   └── stage_tracker.py          ← NEONATAL/JUVENILE/ADOLESCENT/MATURE logic
│
├── emotion/
│   ├── salience.py               ← SalienceFilter, AffectiveState  [v0.1]
│   └── amygdala.py               ← AmygdalaRegion (fast emotional tagging) [v0.3]
│
├── drives/
│   ├── drive_system.py           ← DriveState, DriveSystem  [v0.1]
│   └── reward_signal.py          ← UserFeedbackReward → dopamine  [v0.3]
│
├── persistence/
│   ├── brain_store.py            ← BrainStore (save/load all state)  [v0.1]
│   └── episode_store.py          ← Conversational episode index  [v0.2]
│
├── codec/                        ← ONLY PLACE LLM IS CALLED
│   ├── llm_codec.py              ← LLMCodec (v3: self+drive+affect aware)
│   ├── llm_gate.py               ← When to call vs local
│   ├── character_encoder.py      ← Text → spikes (no API)  [v0.1]
│   ├── phonological_buffer.py    ← Assembly → text (stub v0.1, real v0.2)
│   ├── response_cache.py         ← Similarity-based reuse  [v0.2]
│   └── cost_tracker.py           ← API spend + budget enforcement
│
├── neurons/
│   ├── lif.py                    ← LIF base (NumPy v0.1, Brian2 v0.5)
│   ├── pyramidal.py              ← Pyramidal + NMDA  [v0.4]
│   └── interneurons.py           ← PV, SST, VIP  [v0.4]
│
├── synapses/
│   ├── stdp_pair.py              ← Pair STDP (v0.1)
│   ├── stdp_triplet.py           ← Triplet STDP  [v0.5]
│   ├── ampa.py                   ← AMPA  [v0.4]
│   ├── nmda.py                   ← NMDA + Mg gating  [v0.4]
│   ├── gaba.py                   ← GABA_A/B  [v0.4]
│   ├── stp.py                    ← Short-term plasticity  [v0.4]
│   ├── bcm.py                    ← BCM sliding threshold  [v0.5]
│   └── homeostatic.py            ← Synaptic scaling  [v0.5]
│
├── regions/
│   ├── base.py                   ← BrainRegion abstract
│   ├── sensory_cortex.py         ← Multimodal input  [v0.1]
│   ├── feature_layer.py          ← Feature extraction  [v0.1]
│   ├── association_area.py       ← STDP hub  [v0.1]
│   ├── predictive_region.py      ← Prediction + error  [v0.1]
│   ├── concept_layer.py          ← WTA + assembly tracking  [v0.1/v0.2]
│   ├── brainstem.py              ← Homeostatic drive  [v0.1]
│   ├── reflex_arc.py             ← Safety kernel v2  [v0.1]
│   ├── working_memory.py         ← NMDA recurrent buffer  [v0.4]
│   ├── cortical_column.py        ← 6-layer laminar  [v0.4]
│   ├── thalamus.py               ← Thalamo-cortical relay  [v0.5]
│   └── basal_ganglia.py          ← Action selection  [v0.5]
│
├── neuromodulators/
│   ├── dopamine.py               ← VTA + TD learning  [v0.3]
│   ├── acetylcholine.py          ← Learning rate control  [v0.3]
│   ├── norepinephrine.py         ← Gain / arousal  [v0.3]
│   ├── serotonin.py              ← Temporal discounting  [v0.3]
│   └── system.py                 ← Interaction manager  [v0.3]
│
├── memory/
│   ├── hippocampus_simple.py     ← CA3 attractor only  [v0.2]
│   ├── hippocampus_full.py       ← DG + CA3 + CA1 + EC  [v0.4]
│   ├── conversational_memory.py  ← Per-turn episode encode/recall  [v0.2]
│   └── consolidation.py         ← Sleep replay + cortical transfer  [v0.5]
│
├── oscillations/
│   ├── theta.py                  ← Septal pacemaker  [v0.4]
│   ├── gamma.py                  ← PING from E/I  [v0.5]
│   └── coupling.py               ← Theta-gamma context window  [v0.4]
│
├── cognition/
│   ├── cell_assemblies.py        ← Assembly detection + tracking  [v0.2]
│   ├── lexical_stdp.py           ← Word ↔ assembly weights  [v0.2]
│   ├── vocabulary_tracker.py     ← Tracks learned concepts  [v0.2]
│   ├── sequence_learning.py      ← Attractor chaining  [v0.4]
│   ├── predictive_coding.py      ← Hierarchical PC  [v0.4]
│   └── free_energy.py            ← FE minimisation  [v0.4]
│
├── monitoring/
│   ├── llm_bypass_monitor.py     ← LLM call rate over time
│   ├── brain_monitor.py          ← Spike rates, weights, oscillations
│   └── cost_dashboard.py         ← Real-time API spend
│
├── brain/
│   ├── continuous_loop.py        ← ContinuousExistenceLoop  [v0.1]
│   └── BRAIN2.0_brain_v3.py         ← BRAIN2.0BrainV3 assembly
│
├── api.py                        ← FastAPI + WebSocket
└── ui/                           ← React frontend
    ├── Chat.jsx                  ← Chat + affect display
    ├── BrainState.jsx            ← Live region activity
    ├── SelfPanel.jsx             ← Self-model display
    └── DriveGauges.jsx           ← Curiosity/competence/connection
```

---

# PART IV — API CONTRACTS (v0.1)

```python
# api.py routes (v0.1 complete spec)

POST /chat
  Body:    { "message": str, "session_id": str }
  Returns: {
    "response": str,
    "path": "llm" | "local",
    "cost": float,
    "affect": { "valence": float, "arousal": float },
    "drives": { "curiosity": float, "competence": float, "connection": float },
    "self": { "name": str, "stage": str, "confidence": float, "mood": float },
    "brain_step": int
  }

POST /feedback
  Body:    { "valence": float }   # -1.0 to +1.0
  Returns: { "acknowledged": true, "dopamine_injected": float }

GET  /status
  Returns: full brain snapshot + self_model + drive state + affect state

GET  /identity
  Returns: self_model JSON (name, stage, total_turns, vocabulary_size, etc.)

WS   /ws/stream
  Emits every 200ms: { "regions": {...}, "self": {...}, "drives": {...}, "affect": {...} }
```

---

# PART V — WHAT v0.1 FEELS LIKE VS. AN LLM

| Dimension | Typical LLM | BRAIN2.0 v0.1 |
|-----------|-------------|------------|
| Identity | Stateless — reset each session | Persistent — same entity every session |
| Personality | Injected by system prompt | Emergent from reward history |
| Memory | Context window only | Persists indefinitely |
| Emotional response | Simulated in text | Drives actual processing depth |
| Self-awareness | Claimed in text | Tracked in data structure |
| Development | None — static weights | Grows measurably over time |
| Cost | Per-token always | Declines as brain matures |
| Embodiment | None | None (v2.0) |
| Deep reasoning | Excellent | Poor until v0.4 |
| Articulation quality | Excellent | LLM-assisted until v0.4+ |

The first three rows — identity, personality, memory — are what users feel most
acutely. v0.1 delivers all three without a single feature from v0.2 onwards.

That is the correct foundation to build everything else on.
