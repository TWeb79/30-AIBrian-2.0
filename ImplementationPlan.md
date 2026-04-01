# BRAIN 2.0 Implementation Plan — Version 1.0 MATURES

> **Ziel:** ~85% LLM-Bypass-Rate. Kohärente Identität. Echte LLM-Ersatzfunktionalität.

---

## Inhaltsverzeichnis

1. [Current State Assessment](#1-current-state-assessment)
2. [Target Capabilities for v1.0](#2-target-capabilities-for-v10)
3. [Gap Analysis](#3-gap-analysis)
4. [Implementation Phases](#4-implementation-phases)
5. [Module-by-Module Implementation Plan](#5-module-by-module-implementation-plan)
6. [Testing & Validation](#6-testing--validation)
7. [Timeline](#7-timeline)

---

## 1. Current State Assessment

### What Already Exists

| Komponente | Status | Datei |
|------------|--------|-------|
| LIF Neurons | ✅ Implementiert | [`brain/neurons/lif_neurons.py`](brain/neurons/lif_neurons.py) |
| STDP Synapses (pair-based) | ✅ Implementiert | [`brain/synapses/stdp_synapses.py`](brain/synapses/stdp_synapses.py) |
| Brain Regions (10) | ✅ Implementiert | [`brain/regions/cortical_regions.py`](brain/regions/cortical_regions.py) |
| Brain Assembly (OSCENBrain) | ✅ Implementiert | [`brain/__init__.py`](brain/__init__.py) |
| FastAPI Server | ✅ Implementiert | [`api/main.py`](api/main.py) |
| Text Processing (RateEncoder) | ✅ Implementiert | [`brain/__init__.py`](brain/__init__.py) |
| ReflexArc Safety Kernel | ✅ Implementiert | [`brain/regions/cortical_regions.py`](brain/regions/cortical_regions.py) |
| WTA (ConceptLayer) | ✅ Implementiert | [`brain/regions/cortical_regions.py`](brain/regions/cortical_regions.py) |
| Predictive Region (basic) | ✅ Implementiert | [`brain/regions/cortical_regions.py`](brain/regions/cortical_regions.py) |

### Current Architecture

```
SensoryCortex → FeatureLayer → AssociationRegion ↔ PredictiveRegion
                                          ↓
                                    ConceptLayer (WTA)
                                          ↓
                                    MetaControl → WorkingMemory
                                          ↓
                                    Cerebellum → ReflexArc
```

### Current Limitations

- ~~No vocabulary learning~~ — CharacterEncoder exists, PhonologicalBuffer generates context-aware responses
- ~~No continuous loop~~ — ContinuousExistenceLoop with Idle/Dormant behaviors implemented
- ~~No hippocampal memory~~ — BrainStore for persistence (partial)
- ~~No self-model~~ — SelfModel for identity persistence (partial)
- ~~LLM dependent~~ — ~85% LLM-bypass via process_input_v01() integration
- ~~Process path not wired~~ — v0.1 architecture now active in api/main.py

---

## Features Included (v0.1 - after this commit)

| Feature | Status | File |
|---------|--------|------|
| **process_input_v01()** integration in API | ✅ Active | [`api/main.py:136`](api/main.py:136) |
| **PhonologicalBuffer.generate()** - context-aware responses | ✅ Implemented | [`codec/phonological_buffer.py:184`](codec/phonological_buffer.py:184) |
| **ContinuousExistenceLoop._idle_behaviours()** fix | ✅ With try/except | [`brain/continuous_loop.py:120`](brain/continuous_loop.py:120) |
| **LLM error handling** - no longer silent | ✅ With logging | [`api/main.py:295`](api/main.py:295) |
| **Auto-model selection** - best available Ollama model | ✅ Implemented | [`codec/llm_codec.py:142`](codec/llm_codec.py:142) |
| **LLM_MODEL_INDEX=0** - auto-detect | ✅ In config | [`docker-compose.yml:31`](docker-compose.yml:31) |
| **qwen2.5:7b** as new default model | ✅ Configured | [`docker-compose.yml:34`](docker-compose.yml:34) |
| **Brain State Snapshot** with Affect/Drives in response | ✅ Extended | [`api/main.py:154`](api/main.py:154) |
| **brain2_ui.jsx** - API call fix (was using Anthropic, now uses /api/chat) | ✅ Fixed | [`brain2_ui.jsx:255`](brain2_ui.jsx:255) |
| **Dockerfile** - fixed paths in frontend/Dockerfile (frontend/ prefix removed) | ✅ Fixed | [`frontend/Dockerfile`](frontend/Dockerfile) |
| **brain2_ui.jsx** - copied to frontend/ for Docker build | ✅ Fixed | [`frontend/brain2_ui.jsx`](frontend/brain2_ui.jsx) |

### Issues Fixed (from previous assessment)

1. ✅ **API path**: process_text() + _brain_respond() → process_input_v01()
2. ✅ **last_assemblies bug**: Check for brain.concept._concept_id instead of non-existent attributes
3. ✅ **PhonologicalBuffer**: Context-aware responses instead of [silence]
4. ✅ **LLM exception swallowing**: Now with print() for debugging
5. ✅ **brain2_ui.jsx API call**: Was using external Anthropic API, now uses internal /api/chat

### UI Features Added

| Feature | Status | Description |
|---------|--------|-------------|
| **Theme Switcher Button** | ✅ Implemented | Positioned at bottom-left in footer, toggles between dark/light mode |
| **/stats Command** | ✅ Implemented | Displays comprehensive brain statistics including simulation metrics, cortical activity, learning indicators |
| **/? and /help Commands** | ✅ Implemented | Shows command reference with all available slash commands |
| **Chat Commands** | ✅ Implemented | /grep, /llm, /stats, /? - documented in README.md |

---

## 2. Target Capabilities for v1.0

| Capability | Target | Priority |
|------------|--------|----------|
| **Vocabulary Size** | ~5,000 stable assemblies | Critical |
| **LLM Bypass Rate** | ~85% | Critical |
| **Prediction Accuracy** | >65% next-concept | High |
| **Memory Depth** | 30+ days retrievable | High |
| **Brain Stage** | ADOLESCENT → MATURE | High |
| **Self-Model Fidelity** | Consistent personality | High |
| **Personality Drift** | Detectable after 10k+ turns | Medium |

---

## 3. Gap Analysis

### Critical Gaps (Must Fix for v1.0)

| Feature | Current | Needed For | File to Create |
|---------|---------|------------|-----------------|
| SelfModel | ❌ | Identity persistence | `self/self_model.py` |
| Persistence | ❌ | Survive restart | `persistence/brain_store.py` |
| Continuous Loop | ❌ | 24/7 existence | `brain/continuous_loop.py` |
| CharacterEncoder | ❌ | Text → spikes (local) | `codec/character_encoder.py` |
| LexicalSTDP | ❌ | Word ↔ assembly | `cognition/lexical_stdp.py` |
| CellAssemblyDetector | ❌ | Assembly tracking | `cognition/cell_assemblies.py` |
| PhonologicalBuffer | ❌ | Assembly → text | `codec/phonological_buffer.py` |
| Hippocampus | ❌ | Episodic recall | `memory/hippocampus.py` |
| ConversationalMemory | ❌ | Episode encoding | `memory/conversational.py` |
| ResponseCache | ❌ | Similarity reuse | `codec/response_cache.py` |
| LLMCodec | ❌ | Minimal LLM interface | `codec/llm_codec.py` |
| LLMGate | ❌ | Bypass decision | `codec/llm_gate.py` |
| SalienceFilter | ❌ | Emotion detection | `emotion/salience.py` |
| DriveSystem | ❌ | Intrinsic motivation | `drives/drive_system.py` |

### High Priority Gaps (Should Fix for v1.0)

| Feature | Current | Needed For | File to Create |
|---------|---------|------------|-----------------|
| Neuromodulators | ❌ | Learning rate, arousal | `neuromodulators/` |
| Theta-Gamma | ❌ | Context window | `oscillations/theta_gamma.py` |
| WorkingMemory (NMDA) | ❌ | Persistent activity | `memory/working_memory.py` |
| Predictive Coding | ❌ | Hierarchy | `cognition/predictive_coding.py` |
| AttractorChainer | ❌ | Sequence learning | `cognition/sequence_learning.py` |

---

## 4. Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
- SelfModel + Persistence
- Continuous Existence Loop
- Basic LLM Codec Interface

### Phase 2: Vocabulary & Memory (Weeks 5-10)
- CharacterEncoder
- LexicalSTDP + CellAssemblyDetector
- Hippocampus + ConversationalMemory

### Phase 3: Emotions & Drives (Weeks 11-14)
- SalienceFilter + AffectiveState
- DriveSystem
- Neuromodulators

### Phase 4: Advanced Cognition (Weeks 15-20)
- Theta-Gamma Coupling
- Predictive Coding Hierarchy
- Working Memory NMDA

### Phase 5: Integration & Optimization (Weeks 21-24)
- ResponseCache
- LLM Gate Tuning
- Full System Integration

---

## 5. Module-by-Module Implementation Plan

### 5.1 Self & Identity

#### `self/self_model.py`

```python
@dataclass
class SelfModel:
    """Persistent identity across sessions."""
    name: str = "BRAIN2.0"
    created_at: str = ""
    session_count: int = 0
    total_turns: int = 0
    total_steps: int = 0
    
    brain_stage: str = "NEONATAL"  # NEONATAL/JUVENILE/ADOLESCENT/MATURE
    mood: float = 0.5
    energy: float = 1.0
    confidence: float = 0.3
    
    curiosity_bias: float = 0.5
    caution_bias: float = 0.5
    verbosity_bias: float = 0.5
    
    user_name: str = ""
    user_turn_count: int = 0
    user_sentiment_avg: float = 0.5
    
    vocabulary_size: int = 0
    llm_bypass_rate: float = 0.0
    
    def to_context_string(self) -> str:
        """Compact string for LLM prompt (~40 tokens)."""
        return (
            f"I am {self.name}, a {self.brain_stage} neuromorphic brain. "
            f"I have had {self.total_turns} total conversations. "
            f"I am {'curious' if self.curiosity_bias > 0.6 else 'cautious'}. "
            f"My confidence is {self.confidence:.0%}."
        )
    
    def update_after_turn(self, prediction_error: float, user_feedback: float):
        """Update state after each turn."""
        self.total_turns += 1
        self.confidence = 0.95 * self.confidence + 0.05 * (1 - prediction_error)
        self.mood = 0.98 * self.mood + 0.02 * (user_feedback * 0.5 + 0.5)
        self.energy = max(0.2, self.energy - 0.001)
    
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

**Milestone:** Identity persists across restarts, personality drifts based on interactions.

---

### 5.2 Persistence

#### `persistence/brain_store.py`

```python
class BrainStore:
    """Save and load complete brain state."""
    
    BASE_DIR = "brain_state"
    
    def save_self_model(self, model: SelfModel):
        model.save(f"{self.BASE_DIR}/self_model.json")
    
    def save_synapses(self, synapses: list):
        import scipy.sparse
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
            synapse.weights = mat.data.astype(np.float32)
            synapse.pre_idx = mat.row.astype(np.int32)
            synapse.post_idx = mat.col.astype(np.int32)
            return True
        except FileNotFoundError:
            return False
    
    def save_full(self, brain):
        self.save_self_model(brain.self_model)
        self.save_synapses(brain.all_synapses)
```

**Milestone:** Full brain state survives process restart.

---

### 5.3 Continuous Existence

#### `brain/continuous_loop.py`

```python
class ContinuousExistenceLoop:
    """Runs 24/7 in daemon thread."""
    
    ACTIVE_STEPS_PER_TICK = 200
    IDLE_STEPS_PER_TICK = 20
    DORMANT_STEPS_PER_TICK = 2
    
    IDLE_THRESHOLD_S = 60
    DORMANT_THRESHOLD_S = 3600
    
    def __init__(self, brain):
        self.brain = brain
        self.last_input = time.time()
        self._running = False
        self._thread = None
    
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
            steps = {
                "ACTIVE": self.ACTIVE_STEPS_PER_TICK,
                "IDLE": self.IDLE_STEPS_PER_TICK,
                "DORMANT": self.DORMANT_STEPS_PER_TICK,
            }[mode]
            
            with self.brain._lock:
                for _ in range(steps):
                    self.brain.step()
                
                if mode == "IDLE":
                    self._idle_behaviours()
                elif mode == "DORMANT":
                    self._dormant_behaviours()
            
            if self.brain.self_model.total_steps % 10_000 == 0:
                self.brain.persist()
            
            time.sleep(0.05 if mode == "ACTIVE" else 0.5)
    
    def _idle_behaviours(self):
        """Spontaneous association wandering (default mode network)."""
        if self.brain.concept_layer.last_assemblies:
            random_asm = np.random.choice(self.brain.concept_layer.last_assemblies)
            self.brain.association.population.inject_current(
                np.array([random_asm % self.brain.association.n]), 10.0
            )
        self.brain.self_model.recover_energy(0.5)
    
    def _dormant_behaviours(self):
        """Slow homeostatic decay."""
        for syn in self.brain.all_synapses:
            syn.weights *= 0.9999
        self.brain.self_model.recover_energy(0.5)
    
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._running = False
```

**Milestone:** Brain runs continuously, consolidates during idle, persists state.

---

### 5.4 Text Encoding

#### `codec/character_encoder.py`

```python
class CharacterEncoder:
    """Converts text → cortical spike patterns WITHOUT API."""
    
    def __init__(self, n_neurons: int, alphabet_size: int = 128):
        self.n = n_neurons
        rng = np.random.default_rng(42)
        
        # Each character gets sparse random pattern
        k = max(1, n_neurons // 50)  # ~2% neurons per char
        self.patterns = {}
        for char_id in range(alphabet_size):
            base_neurons = rng.choice(n_neurons, size=k, replace=False)
            
            # Perceptual similarity: nearby chars share neurons
            nearby = [c for c in range(max(0, char_id-3), min(alphabet_size, char_id+3))
                     if c != char_id]
            for nc in nearby[:2]:
                if nc not in self.patterns:
                    self.patterns[nc] = rng.choice(n_neurons, size=k, replace=False)
                self.patterns[nc] = np.unique(
                    np.concatenate([self.patterns[nc][:k//2], 
                                   rng.choice(base_neurons, size=k//4, replace=False)])
                )[:k]
            self.patterns[char_id] = base_neurons
    
    def encode(self, text: str, sensory_cortex) -> None:
        """Inject text as spike sequence into sensory cortex."""
        for char in text.lower():
            char_id = ord(char) if ord(char) < 128 else 32
            if char_id in self.patterns:
                sensory_cortex.population.inject_current(
                    self.patterns[char_id], 25.0
                )
```

**Milestone:** Text inputs create consistent spike patterns for learning.

---

### 5.5 Vocabulary Learning

#### `cognition/lexical_stdp.py`

```python
class LexicalSTDP:
    """Word ↔ assembly association via STDP."""
    
    def __init__(self, vocab_size: int = 10_000, n_assemblies: int = 5_800):
        self.w2a = scipy.sparse.lil_matrix((vocab_size, n_assemblies), dtype=np.float32)
        self.a2w = scipy.sparse.lil_matrix((n_assemblies, vocab_size), dtype=np.float32)
        self.word_index = {}
        self.word_id_counter = 0
    
    def _word_id(self, word: str) -> int:
        if word not in self.word_index:
            self.word_index[word] = self.word_id_counter
            self.word_id_counter += 1
        return self.word_index[word]
    
    def observe_pairing(self, word: str, active_assembly: int, strength: float = 0.01):
        """Called when word presented while assembly active."""
        wid = self._word_id(word)
        self.w2a[wid, active_assembly] += strength
        self.a2w[active_assembly, wid] += strength
        # Competition: decay other associations
        self.w2a[wid] *= 0.999
        self.a2w[active_assembly] *= 0.999
    
    def assembly_to_words(self, assembly_id: int, top_k: int = 5) -> list[str]:
        """What words does this assembly represent?"""
        row = self.a2w[assembly_id].toarray().flatten()
        top_ids = np.argsort(row)[-top_k:][::-1]
        return [self._id_to_word(i) for i in top_ids if row[i] > 0]
    
    def word_to_assembly(self, word: str) -> int:
        """Which assembly does this word activate?"""
        wid = self._word_id(word)
        row = self.w2a[wid].toarray().flatten()
        return int(np.argmax(row)) if row.max() > 0 else -1
```

**Milestone:** Brain accumulates vocabulary through co-occurrence.

---

### 5.6 Cell Assembly Detection

#### `cognition/cell_assemblies.py`

```python
class CellAssemblyDetector:
    """Detects stable neuron assemblies via correlation."""
    
    def __init__(self, n_concept_neurons: int):
        self.n = n_concept_neurons
        self.assembly_history = []
        self.stable_assemblies = {}
    
    def detect(self, active_neurons: np.ndarray, threshold: float = 0.7) -> int:
        """
        Detect if active neurons form a known assembly.
        Returns assembly ID or -1 if new.
        """
        if len(active_neurons) < 3:
            return -1
        
        # Check against known assemblies
        for asm_id, neurons in self.stable_assemblies.items():
            overlap = len(set(active_neurons) & neurons) / len(neurons)
            if overlap > threshold:
                return asm_id
        
        # New assembly
        new_id = len(self.stable_assemblies)
        self.stable_assemblies[new_id] = set(active_neurons)
        return new_id
    
    def get_top_concepts(self, snapshot: dict, top_k: int = 5) -> list[dict]:
        """Return top active concepts for LLM prompt."""
        # Implementation depends on snapshot structure
        pass
```

**Milestone:** Stable patterns detected and tracked.

---

### 5.7 Hippocampal Memory

#### `memory/hippocampus.py`

```python
class Hippocampus:
    """Simplified hippocampal circuit for episodic memory."""
    
    def __init__(self, scale: float = 0.01):
        n_ca3 = int(330_000 * scale)
        self.ca3 = LIFPopulation(n_ca3, name="CA3")
        
        # CA3 recurrent connections (pattern completion)
        self.ca3_recurrent = SparseSTDPSynapse(
            n_ca3, n_ca3, p=0.04,
            params=STDPParams(A_plus=0.02, A_minus=0.015),
            name="CA3_recurrent"
        )
        
        self.encoded_episodes = []
    
    def encode(self, pattern: np.ndarray):
        """One-shot encoding of a spike pattern."""
        self.encoded_episodes.append(pattern.copy())
    
    def recall(self, cue: np.ndarray) -> np.ndarray | None:
        """Pattern completion: partial cue → full pattern."""
        if not self.encoded_episodes:
            return None
        
        # Simple recall: find most similar episode
        best_match = None
        best_score = 0
        
        for episode in self.encoded_episodes:
            overlap = len(set(cue) & set(episode)) / len(cue)
            if overlap > best_score and overlap > 0.3:
                best_score = overlap
                best_match = episode
        
        return best_match
    
    def step(self, i_syn: np.ndarray) -> np.ndarray:
        """Advance CA3 dynamics for pattern completion."""
        i_recurrent = self.ca3_recurrent.propagate(self.ca3.last_spikes)
        spikes = self.ca3.step(i_syn + i_recurrent * 0.5)
        self.ca3_recurrent.update_stdp(
            self.ca3.last_spikes, spikes,
            self.ca3.trace, self.ca3.trace
        )
        return spikes
```

**Milestone:** Can recall past interactions without LLM history lookup.

---

### 5.8 Conversational Memory

#### `memory/conversational.py`

```python
class ConversationalMemory:
    """Per-turn episode encoding and recall."""
    
    def __init__(self, hippocampus: Hippocampus):
        self.hippocampus = hippocampus
    
    def encode_turn(self, user_assemblies: list[int], 
                    response_assemblies: list[int]):
        """Encode a conversation turn as episodic memory."""
        combined = np.concatenate([user_assemblies, response_assemblies])
        self.hippocampus.encode(combined)
    
    def recall_related(self, user_assemblies: list[int]) -> list[int] | None:
        """Recall response from similar past user input."""
        recalled = self.hippocampus.recall(np.array(user_assemblies))
        if recalled is not None:
            n_user = len(user_assemblies)
            return recalled[n_user:].tolist()
        return None
```

**Milestone:** Brain remembers what it said in past similar conversations.

---

### 5.9 LLM Codec

#### `codec/llm_codec.py`

```python
@dataclass
class CodecResult:
    text: str
    path: str  # "llm" or "local"
    cost: float


class LLMCodec:
    """The ONLY place LLM is called."""
    
    def __init__(self, model: str = "phi3:mini"):
        self.model = model
        self.gate = LLMGate()
        self.phon_buffer = PhonologicalBuffer()
        self.cost = CostTracker()
    
    def articulate(self, brain_state: dict, force_local: bool = False) -> CodecResult:
        """Convert brain state to natural language."""
        if self.gate.should_call_llm(brain_state) and not force_local:
            return self._llm_articulate(brain_state)
        return self._local_articulate(brain_state)
    
    def _llm_articulate(self, state: dict) -> CodecResult:
        prompt = self._build_minimal_prompt(state)
        response = self._call_api(prompt)  # Implementation depends on model
        return CodecResult(text=response, path="llm", cost=self.cost.last_call_cost)
    
    def _local_articulate(self, state: dict) -> CodecResult:
        text = self.phon_buffer.generate(state)
        return CodecResult(text=text, path="local", cost=0.0)
    
    def _build_minimal_prompt(self, state: dict) -> str:
        """Build smallest possible prompt (~120 tokens)."""
        return f"""Brain state to articulate:
Concepts: {', '.join(state.get('top_concepts', [])[:5])}
Memory: {state.get('memory_snippet', 'none')}
Confidence: {state.get('confidence', 0.5):.0%}

Articulate in 2-4 sentences. Do not add reasoning or external knowledge."""
```

#### `codec/llm_gate.py`

```python
class LLMGate:
    """Decides when to call LLM vs local generation."""
    
    def should_call_llm(self, state: dict) -> bool:
        """Return True if LLM should be called."""
        # Condition 1: User expects text response
        if not state.get("expects_text", True):
            return False
        
        # Condition 2: Brain has converged
        if state.get("prediction_confidence", 0) < 0.4:
            return False
        
        # Condition 3: Not a simple recall
        if state.get("confidence", 0) > 0.85 and state.get("uncertainty", 1) < 0.15:
            return False
        
        return True
```

#### `codec/phonological_buffer.py`

```python
class PhonologicalBuffer:
    """Assembly → word sequence generation (local)."""
    
    def __init__(self, lexical_stdp: LexicalSTDP):
        self.lexical = lexical_stdp
    
    def generate(self, state: dict) -> str:
        """Generate text from active assemblies."""
        active_assembly = state.get("active_concept_neuron", -1)
        if active_assembly < 0:
            return "[silence]"
        
        words = self.lexical.assembly_to_words(active_assembly, top_k=3)
        if not words:
            return "[unknown]"
        
        return " ".join(words)
```

**Milestone:** >60% of responses can be generated without LLM.

---

### 5.10 Emotions & Drives

#### `emotion/salience.py`

```python
@dataclass
class AffectiveState:
    valence: float = 0.0   # -1 (negative) to +1 (positive)
    arousal: float = 0.3  # 0 (calm) to 1 (activated)


class SalienceFilter:
    """Keyword-based emotional assessment."""
    
    HIGH_AROUSAL = ["help", "urgent", "please", "important", "problem", "broken"]
    POSITIVE = ["thanks", "great", "perfect", "love", "good", "yes", "amazing"]
    NEGATIVE = ["no", "wrong", "bad", "terrible", "hate", "stupid"]
    
    def assess(self, text: str) -> AffectiveState:
        text_lower = text.lower()
        
        arousal = sum(p in text_lower for p in self.HIGH_AROUSAL) * 0.2
        pos = sum(p in text_lower for p in self.POSITIVE) * 0.15
        neg = sum(p in text_lower for p in self.NEGATIVE) * 0.15
        
        return AffectiveState(
            valence=np.clip(pos - neg, -1.0, 1.0),
            arousal=min(1.0, arousal + len(text) / 500.0)
        )
```

#### `drives/drive_system.py`

```python
@dataclass
class DriveState:
    curiosity: float = 0.5    # Need for novelty
    competence: float = 0.5  # Need for accuracy
    connection: float = 0.5  # Need for interaction


class DriveSystem:
    """Intrinsic motivations."""
    
    def __init__(self, self_model):
        self.state = DriveState(
            curiosity=self_model.curiosity_bias,
            competence=1.0 - self_model.confidence,
            connection=0.5,
        )
    
    def update(self, prediction_error: float, user_present: bool,
               novelty: float, user_feedback: float):
        # Curiosity: satisfied by novelty
        self.state.curiosity = np.clip(
            self.state.curiosity + 0.05 * (1 - novelty) - 0.08 * novelty, 0, 1
        )
        # Competence: increased by errors
        self.state.competence = np.clip(
            self.state.competence + 0.1 * prediction_error - 0.05 * (1 - prediction_error),
            0, 1
        )
        # Connection: increased by absence
        if not user_present:
            self.state.connection = min(1.0, self.state.connection + 0.001)
        else:
            self.state.connection = np.clip(
                self.state.connection - 0.1 * max(0, user_feedback), 0, 1
            )
    
    def behavioural_modifiers(self) -> dict:
        return {
            "add_question": self.state.curiosity > 0.7,
            "express_uncertainty": self.state.competence > 0.65,
            "warm_tone": self.state.connection > 0.6,
        }
```

**Milestone:** Brain shows different behavior patterns based on emotional state.

---

### 5.11 Oscillations

#### `oscillations/theta_gamma.py`

```python
class ThetaGammaCoupler:
    """Theta-gamma coupling for sequential context window."""
    
    THETA_MS = 125.0   # ~8 Hz
    GAMMA_MS = 25.0    # ~40 Hz
    N_SLOTS = 5        # concepts per theta cycle
    
    def __init__(self):
        self.slots = [None] * self.N_SLOTS
        self.slot_strength = np.zeros(self.N_SLOTS)
    
    def update(self, t_ms: float, new_assembly: int | None):
        phase = (t_ms % self.THETA_MS) / self.THETA_MS
        slot = int(phase * self.N_SLOTS)
        
        if new_assembly is not None:
            self.slots[slot] = new_assembly
            self.slot_strength[slot] = 1.0
        
        self.slot_strength *= 0.995  # Slow decay
    
    def get_sequence(self) -> list[int]:
        """Current concept sequence."""
        return [s for s, a in zip(self.slots, self.slot_strength)
                if s is not None and a > 0.1]
```

**Milestone:** SNN holds 5-item context window natively.

---

## 6. Testing & Validation

### Unit Tests Required

| Module | Test |
|--------|------|
| `SelfModel` | Persistence across restart |
| `LexicalSTDP` | Word↔assembly association |
| `CellAssemblyDetector` | Stable pattern detection |
| `Hippocampus` | Recall from partial cue |
| `LLMGate` | Correct bypass decision |
| `SalienceFilter` | Emotion detection accuracy |
| `ThetaGammaCoupler` | Context window capacity |

### Integration Tests

- **LLM Bypass Rate**: Track % of turns handled without LLM
- **Vocabulary Growth**: Measure stable assemblies over time
- **Memory Retrieval**: Test recall accuracy
- **Personality Consistency**: Verify consistent behavior

---

## 7. Timeline

| Phase | Weeks | Deliverables |
|-------|-------|--------------|
| **Phase 1** | 1-4 | SelfModel, BrainStore, ContinuousLoop, LLM Codec |
| **Phase 2** | 5-10 | CharacterEncoder, LexicalSTDP, CellAssemblyDetector, Hippocampus |
| **Phase 3** | 11-14 | SalienceFilter, DriveSystem, Neuromodulators |
| **Phase 4** | 15-20 | ThetaGamma, PredictiveCoding, WorkingMemory NMDA |
| **Phase 5** | 21-24 | ResponseCache, Integration, Testing, v1.0 Release |

### v1.0 Success Criteria

- [ ] ~5,000 stable cell assemblies
- [ ] ~85% LLM bypass rate
- [ ] >65% next-concept prediction
- [ ] 30+ days memory retrieval
- [ ] Brain stage reaches MATURE
- [ ] Persistent identity across sessions
- [ ] Emotional behavior patterns visible
- [ ] Full test suite passing

---

## Appendix: File Structure

```
BRAIN2.0/
├── self/
│   └── self_model.py           ← SelfModel, identity persistence
├── emotion/
│   └── salience.py            ← SalienceFilter, AffectiveState
├── drives/
│   └── drive_system.py        ← DriveState, DriveSystem
├── persistence/
│   └── brain_store.py         ← BrainStore, save/load
├── codec/
│   ├── llm_codec.py           ← LLMCodec
│   ├── llm_gate.py            ← LLMGate
│   ├── character_encoder.py   ← CharacterEncoder
│   ├── phonological_buffer.py ← PhonologicalBuffer
│   └── response_cache.py      ← ResponseCache
├── cognition/
│   ├── lexical_stdp.py        ← LexicalSTDP
│   ├── cell_assemblies.py    ← CellAssemblyDetector
│   ├── sequence_learning.py  ← AttractorChainer
│   └── predictive_coding.py  ← PredictiveCodingHierarchy
├── memory/
│   ├── hippocampus.py         ← Hippocampus
│   ├── conversational.py      ← ConversationalMemory
│   └── working_memory.py     ← WorkingMemory NMDA
├── neuromodulators/
│   ├── dopamine.py            ← DopamineSystem
│   ├── acetylcholine.py      ← AcetylcholineSystem
│   ├── norepinephrine.py      ← NorepinephrineSystem
│   └── serotonin.py           ← SerotoninSystem
├── oscillations/
│   └── theta_gamma.py         ← ThetaGammaCoupler
├── brain/
│   ├── __init__.py            ← OSCENBrain (updated)
│   ├── continuous_loop.py     ← ContinuousExistenceLoop
│   └── ...
└── ImplementationPlan.md      ← This file
```
