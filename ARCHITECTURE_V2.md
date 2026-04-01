# BRAIN2.0 v2 — SNN-Primary, LLM-Peripheral Architecture
## Revised Concept, Gap Analysis & Implementation Plan

**Version:** 2.0  
**Status:** Design Specification  
**Core Principle:** The SNN brain *is* the thinker. The LLM is a translator, nothing more.

---

## Table of Contents

1. [The Central Thesis](#1-the-central-thesis)
2. [The Brain Analogy for the LLM Role](#2-the-brain-analogy-for-the-llm-role)
3. [What the Brain Does vs. What the LLM Does — Full Responsibility Map](#3-responsibility-map)
4. [Revised Architecture: The Three-Layer Model](#4-revised-architecture)
5. [The LLM Interface: Minimal by Design](#5-the-llm-interface)
6. [Cost Model and LLM Call Budget](#6-cost-model)
7. [What the SNN Brain Must Implement to Minimise LLM Dependency](#7-snn-brain-capabilities)
8. [The Spike-to-Meaning Pipeline (No LLM Required)](#8-spike-to-meaning)
9. [Revised Implementation Plan (Sprint-by-Sprint)](#9-implementation-plan)
10. [Hardware Targets and Resource Budgets](#10-hardware-targets)
11. [File Architecture v2](#11-file-architecture)
12. [Decision Tree: When to Call the LLM](#12-decision-tree)

---

## 1. The Central Thesis

The previous architecture (v1) used an LLM to generate all responses, with the SNN providing only
decorative context. This is architecturally backwards. The correct model is:

```
┌────────────────────────────────────────────────────────────────┐
│                     THE BRAIN2.0 BRAIN                            │
│                                                                │
│  Thinking · Memory · Association · Prediction · Reasoning     │
│  Concept Formation · Sequence Learning · Attention            │
│  All implemented as SPIKE DYNAMICS                            │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           SNN COGNITIVE ENGINE                        │    │
│  │  (runs 100% locally, 0 API calls, continuous)        │    │
│  └──────────────────────────────────────────────────────┘    │
│                          │           ▲                         │
│               spike patterns    cell assembly state            │
│                          │           │                         │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           LANGUAGE CODEC LAYER                        │    │
│  │  Text IN  → spike encoding (local, no LLM)           │    │
│  │  Spikes OUT → text generation (LLM called ONLY here) │    │
│  └──────────────────────────────────────────────────────┘    │
│                          │           ▲                         │
│               natural language  natural language               │
└────────────────────────────────────────────────────────────────┘
                           │           │
                         USER        USER
```

The LLM is called **at most once per user turn**, and only to translate a completed brain
state into fluent natural language. Everything else — understanding, thinking, remembering,
predicting, reasoning — is the SNN's responsibility.

Target: **>90% of cognitive work done by the SNN. <10% by the LLM.**

---

## 2. The Brain Analogy for the LLM Role

In the biological brain, Broca's area (language production) and Wernicke's area (language
comprehension) are small, specialised regions that interface between internal cognition and
spoken/written language. They are NOT where thinking happens. The frontal cortex, association
areas, hippocampus and prefrontal cortex do the thinking. Broca's area just encodes the output.

The LLM in BRAIN2.0 plays exactly this role:
- It is Broca's area — the articulator.
- It receives the SNN's completed internal state as a structured "thought"
  (active cell assemblies, current context window, most-activated concepts)
- It converts that structured state into grammatical text.
- It is NOT asked to reason, remember, associate, or understand.

Similarly on input, Wernicke's area parses incoming speech. The LLM (or a local parser)
decodes incoming text into structured intent and feeds that as spike input to the SNN.
It does not decide what to do with it — the SNN does.

This is the neuroscience-grounded justification for the minimal-LLM architecture.

---

## 3. Responsibility Map

### Full Responsibility Table

| Cognitive Function | Biological Region | SNN Component | LLM Involved? |
|-------------------|-------------------|---------------|---------------|
| Hear/read input   | Auditory/Visual cortex | SensoryCortex (Poisson encode) | Input parser only (tiny, local) |
| Parse grammar     | Wernicke's area (BA22) | CharacterEncoder → assembly | Local parser (no API) |
| Understand intent | Angular gyrus | AssociationArea STDP | ❌ No |
| Recall from memory| Hippocampus CA3 | HippocampusRegion recall() | ❌ No |
| Form associations | Parietal assoc. cortex | AssociationArea + STDP | ❌ No |
| Predict next token/concept | Predictive cortex | PredictiveCodingHierarchy | ❌ No |
| Weigh options     | PFC + Basal Ganglia | BasalGanglia select_action() | ❌ No |
| Generate "thought"| Dorsolateral PFC  | ConceptLayer + AttractorChain | ❌ No |
| Attend to relevant| Thalamus + ACh    | ThalamusGating + NE system | ❌ No |
| Error-correct     | ACC + Cerebellum  | PredictionError broadcast | ❌ No |
| Produce words     | Broca's area BA44 | PhonologicalBuffer → LLM | ✅ ONE call |
| Articulate response | Motor speech    | LLM (text generation only) | ✅ |
| Check output safe | Spinal reflex arc | ReflexArcV2 | ❌ No |
| Learn from exchange | Cortical STDP   | All plastic synapses | ❌ No |

**Summary: LLM is called ONCE per user turn, for output articulation only.**

---

## 4. Revised Architecture: The Three-Layer Model

```
╔═══════════════════════════════════════════════════════════════╗
║  LAYER 0 — I/O BOUNDARY                                       ║
║  ─────────────────────────────────────────────────────────── ║
║  INPUT:  CharacterEncoder (local, no API)                     ║
║    Text → ASCII → spatial cortical spike pattern              ║
║    Runs entirely in Python, zero network calls                ║
║                                                               ║
║  OUTPUT: LanguageCodec (LLM API — ONE call per turn)          ║
║    Cell assembly state + context → prompt → text response     ║
║    Model: GPT-4o-mini / Phi-3-mini (local) / Mistral-7B       ║
║    Typical: 150 input tokens, 200 output tokens               ║
║    Cost: ~$0.00006 per turn (GPT-4o-mini) or $0 (local)       ╠═══════════════════════════════════════════════════════════════╣
║  LAYER 1 — COGNITIVE ENGINE (pure SNN, runs 24/7 locally)    ║
║  ─────────────────────────────────────────────────────────── ║
║                                                               ║
║  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    ║
║  │  SENSORY    │  │ ASSOCIATION  │  │   PREDICTIVE     │    ║
║  │  PATHWAY    │→ │     HUB      │↔ │   HIERARCHY      │    ║
║  │  Thalamus   │  │  500k (sc.)  │  │  4 levels        │    ║
║  │  SC+Feature │  │  STDP        │  │  FE minimise     │    ║
║  └─────────────┘  └──────┬───────┘  └──────────────────┘    ║
║                           │                    ▲              ║
║                    cell assemblies       prediction error      ║
║                           │                    │              ║
║  ┌────────────────────────▼───────────────────────────────┐  ║
║  │              CONCEPT LAYER (WTA 5.8k)                  │  ║
║  │  Stable attractors = words / concepts                  │  ║
║  │  Sequential chaining = sentence structure              │  ║
║  └────────────────────────┬───────────────────────────────┘  ║
║                            │                                   ║
║  ┌─────────────────────────▼──────────────────────────────┐  ║
║  │              MEMORY SYSTEM                              │  ║
║  │  Hippocampus: episodic recall + pattern completion     │  ║
║  │  Working Memory: thalamo-cortical buffer (NMDA)        │  ║
║  │  Semantic: distributed cortical attractors             │  ║
║  └─────────────────────────┬──────────────────────────────┘  ║
║                             │                                  ║
║  ┌──────────────────────────▼─────────────────────────────┐  ║
║  │              EXECUTIVE / MOTOR                          │  ║
║  │  PFC: goal maintenance, context                        │  ║
║  │  Basal Ganglia: action selection                       │  ║
║  │  Motor Cortex → ReflexArc (safety)                     │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║  LAYER 2 — NEUROMODULATORY GLOBAL STATE                       ║
║  ─────────────────────────────────────────────────────────── ║
║  Dopamine:      reward signal → STDP learning rate           ║
║  Acetylcholine: novelty → encoding vs. recall mode           ║
║  Norepinephrine: arousal → gain, WTA sharpness               ║
║  Serotonin:     temporal discount, patience                  ║
║  All four run as continuous background processes             ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 5. The LLM Interface: Minimal by Design

### 5.1 What the LLM Receives (Input Prompt)

The LLM never receives the full conversation history or raw user message.
It receives ONLY the structured brain state output — a condensed JSON snapshot:

```json
{
  "active_assemblies": [
    {"id": 47, "label": "query:weather", "activation": 0.91},
    {"id": 12, "label": "context:location=berlin", "activation": 0.78},
    {"id": 203, "label": "concept:forecast", "activation": 0.65}
  ],
  "working_memory": ["weather", "berlin", "tomorrow"],
  "sequence": [47, 12, 203],
  "prediction_confidence": 0.82,
  "neuromodulator_state": {
    "dopamine": 0.6,
    "acetylcholine": 0.7,
    "norepinephrine": 0.5,
    "serotonin": 0.5
  },
  "memory_retrieval": {
    "episode_recalled": "user asked about weather last week",
    "semantic_match": "weather = temperature + precipitation + forecast"
  },
  "brain_status": "JUVENILE",
  "uncertainty": 0.18
}
```

**System prompt for LLM (constant, ~80 tokens):**
```
You are a language articulator. Convert the brain state JSON below into
a natural, concise response. Do not add reasoning, opinions, or knowledge
not present in the brain state. Articulate only what the brain has concluded.
If uncertainty > 0.5, express appropriate hedging.
Max 150 words.
```

**Total per-turn LLM cost: ~80 (system) + 150 (brain state) + 200 (response) = ~430 tokens.**
At GPT-4o-mini: ~$0.000065 per turn.

### 5.2 LLM Call Conditions (Gate Logic)

The LLM is ONLY called when ALL of the following are true:

```python
class LLMGate:
    """
    Hard gate controlling when the LLM is invoked.
    Default: SNN generates response from phonological buffer (no LLM).
    LLM only called for fluent natural language output.
    """
    def should_call_llm(self, brain_state: dict, user_request: str) -> bool:
        # Condition 1: User expects natural language response
        if not self._expects_text_response(user_request):
            return False  # e.g. motor command, internal state query

        # Condition 2: Brain has reached stable concept activation
        if brain_state["prediction_confidence"] < 0.4:
            return False  # Brain hasn't converged — wait more steps

        # Condition 3: Not a simple lookup (SNN can answer directly)
        if self._is_direct_recall(brain_state):
            return False  # Working memory has exact answer

        # Condition 4: Rate limit — max 1 call per 3 seconds
        if self._rate_limited():
            return False

        return True

    def _is_direct_recall(self, state: dict) -> bool:
        """
        If working memory contains a complete response pattern
        AND confidence > 0.85, the phonological buffer can generate
        text directly without LLM. E.g. simple factual recall.
        """
        return (
            len(state["working_memory"]) > 0
            and state["prediction_confidence"] > 0.85
            and state["uncertainty"] < 0.15
        )
```

### 5.3 Fallback: SNN-Native Response Generation

When the LLM gate is closed, the brain generates responses using the phonological buffer:

```python
class PhonologicalBuffer:
    """
    Direct concept-assembly-to-text pathway.
    No LLM. Maps active cell assemblies → word sequences
    via learned association weights.
    
    Accuracy: initially poor (NEONATAL stage).
    Improves with STDP as concept-word mappings strengthen.
    Target: >60% of responses generated without LLM by MATURE stage.
    """
    def generate(self, assembly_sequence: list[int],
                 working_memory: list[str]) -> str:
        words = []
        for asm_id in assembly_sequence:
            best_word = self._assembly_to_word(asm_id)
            if best_word:
                words.append(best_word)
        # Simple template fill from working memory
        return self._fill_template(words, working_memory)

    def _assembly_to_word(self, assembly_id: int) -> str | None:
        """
        Lookup strongest word association for this assembly.
        Populated by STDP: every time a word co-occurs with
        an assembly activation, the mapping is strengthened.
        """
        if assembly_id in self.assembly_lexicon:
            return max(
                self.assembly_lexicon[assembly_id],
                key=lambda w: self.assembly_lexicon[assembly_id][w]
            )
        return None
```

### 5.4 LLM Model Selection Strategy

| Stage | LLM Option | Cost/turn | When to Use |
|-------|-----------|-----------|------------|
| Development | GPT-4o-mini | ~$0.00006 | Debugging output quality |
| Production (cloud) | GPT-4o-mini | ~$0.00006 | Final polish only |
| Production (local) | Phi-3-mini 3.8B (4-bit) | $0 | Privacy / offline |
| Production (offline) | Mistral-7B-Instruct Q4 | $0 | Full local operation |
| Fallback | PhonologicalBuffer | $0 | High confidence cases |

**Recommended target:** Phi-3-mini running via Ollama locally.
- RAM: ~2.5 GB at 4-bit quantisation
- Speed: ~15 tokens/sec on M1 Mac, ~8 tokens/sec on CPU-only
- Quality: sufficient for the articulation-only role

---

## 6. Cost Model

### Baseline Cost Comparison

| Architecture | Cost per 100 turns | RAM | Compute |
|-------------|-------------------|-----|---------|
| v1 (LLM-primary) | ~$0.15 (Claude/GPT-4o) | 2GB SNN + API | API-bound |
| v2 (SNN-primary, GPT-4o-mini) | ~$0.006 | 2GB SNN + 1GB model | SNN CPU |
| v2 (SNN-primary, Phi-3 local) | $0.00 | 2GB SNN + 2.5GB model | CPU only |
| v2 (SNN-primary, PhonologicalBuffer only) | $0.00 | 2GB SNN | CPU only |

**Cost reduction from v1 to v2: 96% at MATURE brain stage.**

### API Budget per Deployment Mode

```python
class CostTracker:
    BUDGET_DAILY   = 0.50   # USD — daily LLM API budget
    BUDGET_MONTHLY = 10.00  # USD — monthly hard limit

    # At GPT-4o-mini rates:
    # 430 tokens/call × $0.15/1M input + $0.60/1M output
    # ≈ $0.000065/call
    # Daily budget allows: ~7,692 LLM calls/day
    # If 50% handled by PhonologicalBuffer: ~15,384 total turns/day
    
    def track_call(self, tokens_in: int, tokens_out: int):
        cost = (tokens_in * 0.15 + tokens_out * 0.60) / 1_000_000
        self.daily_spend += cost
        if self.daily_spend > self.BUDGET_DAILY:
            self.force_local_mode()   # Switch to Phi-3 / phonological buffer
```

---

## 7. What the SNN Brain Must Implement to Minimise LLM Dependency

For the SNN to genuinely replace most of the LLM's cognitive load, it must implement
the following capabilities independently. These are ranked by impact on LLM reduction:

### Priority 1 — Stable Concept Representations (eliminates "understanding" LLM calls)

The SNN must form stable, reusable cell assemblies that reliably activate for consistent inputs.
Without this, the brain has no "vocabulary" and the LLM must supply all semantics.

```
Implementation: AssociationArea with STDP + BCM + WTA
Milestone: Same input → same top-3 active assemblies across 10 trials (cosine > 0.85)
Sprint: 7
```

### Priority 2 — Working Memory Context Window (eliminates "context" LLM calls)

The SNN must hold the last 4–6 concepts in an active buffer, ordered by time.
Without this, the LLM must re-read conversation history on every turn.

```
Implementation: NMDA-recurrent working memory + theta-gamma sequence coding
Milestone: 5-item sequence retained for >10 seconds of sim time
Sprint: 6
```

### Priority 3 — Memory Retrieval (eliminates "knowledge lookup" LLM calls)

The SNN must recall relevant past experiences via hippocampal pattern completion.
Without this, every question about prior exchanges requires an LLM.

```
Implementation: CA3 recurrent attractor + CA1 gating
Milestone: Partial cue (50% of pattern) → full recall (>65% Jaccard)
Sprint: 5
```

### Priority 4 — Prediction and Completion (eliminates "inference" LLM calls)

The SNN must predict the next likely concept in a sequence.
Without this, even simple completion tasks require an LLM.

```
Implementation: PredictiveCodingHierarchy + AttractorChainer
Milestone: Next-assembly prediction accuracy >55% on seen sequences
Sprint: 8
```

### Priority 5 — Semantic Association (eliminates "reasoning" LLM calls)

The SNN must activate related concepts when a concept is presented.
"dog" → activates "animal", "pet", "bark" etc. without an LLM.

```
Implementation: STDP-trained lateral connections in AssociationArea
Milestone: Semantic neighbourhood size >3 reliably for learned concepts
Sprint: 7
```

---

## 8. The Spike-to-Meaning Pipeline (No LLM Required)

The complete internal pathway from text input to response output, showing where
each step runs and confirming that the LLM is isolated to output articulation only.

```
USER TEXT INPUT
     │
     ▼
┌─────────────────────────────────────────────────┐
│  STEP 1: LOCAL TEXT PARSER  [no LLM]            │
│  CharacterEncoder.encode(text)                  │
│  • Tokenise by character n-grams                │
│  • Map tokens → cortical neuron indices         │
│  • Generate Poisson spike bursts                │
│  Duration: <1 ms compute                        │
└────────────────────────┬────────────────────────┘
                          │ spike indices
                          ▼
┌─────────────────────────────────────────────────┐
│  STEP 2: SENSORY PROCESSING  [SNN]              │
│  SensoryCortex → FeatureLayer (STDP)            │
│  • Low-level feature extraction                 │
│  • Character → phoneme → morpheme patterns      │
│  Duration: 50–200 ms simulated time             │
└────────────────────────┬────────────────────────┘
                          │ feature spike patterns
                          ▼
┌─────────────────────────────────────────────────┐
│  STEP 3: ASSOCIATION & PREDICTION  [SNN]        │
│  AssociationArea ↔ PredictiveHierarchy          │
│  • STDP binds features into concept patterns    │
│  • Prediction error drives attention gain       │
│  • Cell assemblies compete for activation (WTA) │
│  Duration: 100–500 ms simulated time            │
└────────────────────────┬────────────────────────┘
                          │ active assembly IDs
                          ▼
┌─────────────────────────────────────────────────┐
│  STEP 4: MEMORY RETRIEVAL  [SNN]                │
│  Hippocampus.recall(active_assemblies)          │
│  • Pattern completion via CA3 recurrent         │
│  • Retrieve relevant episodes and semantics     │
│  • Update working memory via theta-gamma        │
│  Duration: 100–300 ms simulated time            │
└────────────────────────┬────────────────────────┘
                          │ enriched context
                          ▼
┌─────────────────────────────────────────────────┐
│  STEP 5: EXECUTIVE PROCESSING  [SNN]            │
│  PrefrontalCortex + BasalGanglia                │
│  • Select response action from candidates       │
│  • Inhibit irrelevant concepts (NE-driven WTA)  │
│  • Build response sequence in working memory    │
│  Duration: 50–200 ms simulated time             │
└────────────────────────┬────────────────────────┘
                          │ concept sequence + confidence
                          ▼
┌─────────────────────────────────────────────────┐
│  STEP 6: LLM GATE CHECK  [local logic]          │
│  LLMGate.should_call_llm(brain_state)           │
│  → confidence > 0.85 AND simple recall?         │
│     → PhonologicalBuffer.generate()  [no LLM]  │
│  → confidence < 0.85 OR complex response?       │
│     → LLM articulation call  [ONE API call]     │
│  Duration: <1 ms decision                       │
└────────────────────────┬────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐      ┌──────────────────────────┐
│  PATH A: NO LLM     │      │  PATH B: LLM ARTICULATE  │
│  PhonologicalBuffer │      │  Input: brain state JSON │
│  Concept → words    │      │  Model: Phi-3-mini/GPT   │
│  Template fill      │      │  Role: ONLY articulate   │
│  Cost: $0           │      │  Cost: ~$0.00006         │
└────────────────────┬┘      └─────────────┬────────────┘
                     │                     │
                     └──────────┬──────────┘
                                │
                                ▼
                       TEXT RESPONSE → USER
                                │
                                ▼
┌─────────────────────────────────────────────────┐
│  STEP 7: ONLINE LEARNING  [SNN]                 │
│  • STDP update on all active synapses           │
│  • Dopamine: was response rewarded? (user +/-)  │
│  • ACh: update encoding based on novelty        │
│  • BCM: adjust modification thresholds          │
│  Duration: continuous background                │
└─────────────────────────────────────────────────┘
```

---

## 9. Revised Implementation Plan

### Architecture Decisions (Changed from v1)

| Decision | v1 | v2 | Reason |
|----------|----|----|--------|
| LLM role | Primary responder | Output codec only | Principle |
| LLM model | Claude Sonnet | Phi-3-mini local / GPT-4o-mini | Cost |
| SNN framework | NumPy custom | Brian2 (core) + NumPy (utils) | Correctness |
| Input encoding | RateEncoder + process_text() | CharacterEncoder (local, no API) | Self-sufficiency |
| Memory | Python list buffer | Hippocampal attractor network | Biological |
| Response gen | Always LLM | PhonologicalBuffer first, LLM fallback | Cost |
| Concept layer | WTA only | WTA + cell assembly tracker + lexicon | Language capability |

---

### Sprint 0 — Infrastructure & Codec Foundation (Week 1)

**Goal:** Get Brian2 running, implement the LLM interface layer first so it can be
validated independently of brain progress. Separate the codec from the brain cleanly.

```python
# codec/llm_codec.py
class LLMCodec:
    """
    The ONLY place in the codebase where an LLM is called.
    Single responsibility: brain state → natural language.
    All other modules are forbidden from calling any LLM.
    """
    def __init__(self, model: str = "phi3:mini"):
        self.model       = model
        self.gate        = LLMGate()
        self.phon_buffer = PhonologicalBuffer()
        self.cost        = CostTracker()
        self._is_local   = model.startswith("phi") or model.startswith("mistral")

    def articulate(self, brain_state: BrainSnapshot) -> CodecResult:
        """
        Convert brain state to natural language text.
        Returns CodecResult with: text, cost, path (llm|local)
        """
        if self.gate.should_call_llm(brain_state, force_local=self._is_local):
            return self._llm_articulate(brain_state)
        return self._local_articulate(brain_state)

    def _llm_articulate(self, state: BrainSnapshot) -> CodecResult:
        prompt = self._build_minimal_prompt(state)   # <150 tokens
        response = self._call_api(prompt)
        self.cost.track_call(len(prompt.split()), len(response.split()))
        return CodecResult(text=response, path="llm", cost=self.cost.last_call_cost)

    def _local_articulate(self, state: BrainSnapshot) -> CodecResult:
        text = self.phon_buffer.generate(
            state.assembly_sequence,
            state.working_memory_items
        )
        return CodecResult(text=text, path="local", cost=0.0)

    def _build_minimal_prompt(self, state: BrainSnapshot) -> str:
        """
        Build the SMALLEST possible prompt.
        Contain: active concepts, working memory, confidence, uncertainty.
        NEVER include: raw user message, conversation history,
                       instructions to reason, instructions to add knowledge.
        """
        return f"""Brain state to articulate:
Active concepts: {', '.join(state.top_concepts)}
Working memory: {state.working_memory_items}
Confidence: {state.confidence:.2f}
Uncertainty: {state.uncertainty:.2f}
Retrieved memory: {state.memory_snippet or 'none'}
Mood: dopamine={state.dopamine:.1f}, arousal={state.norepinephrine:.1f}

Articulate as natural language in 1-3 sentences. No added reasoning."""
```

**Deliverables:** `codec/__init__.py`, `codec/llm_codec.py`, `codec/phonological_buffer.py`,
`codec/llm_gate.py`, `codec/cost_tracker.py`

---

### Sprint 1 — E/I Balanced Neuron Populations (Week 2–3)

No change in goal from v1 design. Key addition: the CharacterEncoder (SNN-native text input).

```python
# codec/character_encoder.py
class CharacterEncoder:
    """
    Converts text → cortical spike patterns WITHOUT any API call.
    
    Encoding scheme:
    1. Each ASCII character maps to a unique cortical pattern
    2. Visually/phonetically similar characters have overlapping patterns
       (a/e overlap ~40%, b/d overlap ~30%) — perceptual similarity built-in
    3. Character sequences are encoded with 2ms gaps (temporal structure)
    4. Word boundaries are encoded as a silence (5ms no spikes)
    
    This produces a spike representation that the SNN can learn from directly.
    No tokenizer, no vocabulary, no embedding lookup.
    """
    def __init__(self, n_neurons: int, alphabet_size: int = 128):
        self.n = n_neurons
        rng = np.random.default_rng(42)

        # Each character gets a sparse random pattern of k neurons
        k = max(1, n_neurons // 50)  # ~2% of neurons per character
        self.patterns = {}
        for char_id in range(alphabet_size):
            base_neurons = rng.choice(n_neurons, size=k, replace=False)
            # Add perceptual similarity: characters close in ASCII share neurons
            nearby = [c for c in range(max(0, char_id-3), min(alphabet_size, char_id+3))
                      if c != char_id]
            for nc in nearby[:2]:
                shared = rng.choice(base_neurons, size=k//4, replace=False)
                if nc not in self.patterns:
                    self.patterns[nc] = rng.choice(n_neurons, size=k, replace=False)
                self.patterns[nc] = np.unique(
                    np.concatenate([self.patterns[nc][:k//2], shared])
                )[:k]
            self.patterns[char_id] = base_neurons

    def encode(self, text: str, sensory_cortex) -> None:
        """Inject text as spike sequence into sensory cortex."""
        for i, char in enumerate(text.lower()):
            char_id = ord(char) if ord(char) < 128 else 32
            if char_id in self.patterns:
                sensory_cortex.population.inject_current(
                    self.patterns[char_id], 25.0
                )
            # Simulate 2ms inter-character gap via refractory
```

**Deliverables:** `codec/character_encoder.py`, `neurons/ei_population.py`

---

### Sprint 2 — Synapse Diversity (Week 4–5)

Identical to v1 spec: AMPA + NMDA, short-term plasticity, triplet STDP, BCM, homeostatic.

Critical addition: **Lexical STDP** — the mechanism by which words become associated
with cell assemblies WITHOUT an LLM.

```python
# cognition/lexical_stdp.py
class LexicalSTDP:
    """
    Every time a word W is presented while cell assembly A is active:
    → Strengthen the W↔A connection (Hebbian pairing)
    
    After enough repetitions:
    → Assembly A "means" word W (and vice versa)
    → This is the SNN's vocabulary — built entirely from co-occurrence
    → No pre-trained embeddings, no LLM knowledge transfer
    
    This is how Wernicke's area works: sound patterns become
    associated with semantic representations through repeated experience.
    """
    def __init__(self, vocab_size: int = 10_000, n_assemblies: int = 5_800):
        # Sparse association matrix: word ↔ assembly
        self.w2a = scipy.sparse.lil_matrix((vocab_size, n_assemblies), dtype=np.float32)
        self.a2w = scipy.sparse.lil_matrix((n_assemblies, vocab_size), dtype=np.float32)
        self.word_index = {}   # word string → index

    def observe_pairing(self, word: str, active_assembly: int, strength: float = 0.01):
        """Called whenever a word is presented while an assembly is active."""
        wid = self._word_id(word)
        self.w2a[wid, active_assembly] += strength
        self.a2w[active_assembly, wid]  += strength
        # Weight decay on all other entries (competition)
        self.w2a[wid] *= 0.999
        self.a2w[active_assembly] *= 0.999

    def assembly_to_words(self, assembly_id: int, top_k: int = 5) -> list[str]:
        """What words does this assembly most strongly represent?"""
        row = self.a2w[assembly_id].toarray().flatten()
        top_ids = np.argsort(row)[-top_k:][::-1]
        return [self._id_to_word(i) for i in top_ids if row[i] > 0]

    def word_to_assembly(self, word: str) -> int:
        """Which assembly does this word most strongly activate?"""
        wid = self._word_id(word)
        if wid < 0:
            return -1
        row = self.w2a[wid].toarray().flatten()
        return int(np.argmax(row)) if row.max() > 0 else -1
```

---

### Sprint 3 — Neuromodulation (Week 6–7)

Identical to v1 spec. Critical addition: **Reward signal from user feedback.**

```python
# neuromodulators/reward_signal.py
class UserFeedbackReward:
    """
    Maps user feedback to dopamine signal.
    This closes the reinforcement learning loop without any LLM.
    
    Positive feedback (+1): dopamine burst → LTP on recently active synapses
    Negative feedback (-1): dopamine dip → LTD on recently active synapses
    Neutral (0): baseline dopamine
    
    The brain LEARNS from human interaction, not from pre-training.
    """
    def __init__(self, dopamine_system: DopamineSystem):
        self.da = dopamine_system

    def on_feedback(self, valence: float):   # valence in [-1, +1]
        δ = valence - self.da.prediction
        self.da.vta.inject_current(
            np.arange(self.da.vta.n),
            magnitude=δ * 20.0   # pA
        )
        self.da.td_error_history.append(δ)
```

---

### Sprint 4 — Cortical Columns & Laminar Structure (Week 8–9)

Identical to v1 spec. The laminar structure is critical for separating bottom-up
(sensory-driven) from top-down (prediction-driven) processing — the mechanism by
which the brain distinguishes what it "hears" from what it "expects".

---

### Sprint 5 — Hippocampal Memory (Week 10–11)

Identical to v1 spec. The hippocampus is the primary mechanism that allows the SNN
to answer questions about past interactions WITHOUT calling the LLM for history lookup.

**Key addition — Conversational Episode Encoding:**
```python
class ConversationalMemory:
    """
    After each turn, encode the (user_concept_pattern, brain_response_pattern)
    pair as a hippocampal episode.
    
    On next recall: partial cue (user concept) → full episode retrieval
    → brain knows what it said before → no conversation history in LLM prompt
    """
    def encode_turn(self, user_assemblies: list[int],
                    response_assemblies: list[int],
                    hippocampus: Hippocampus):
        combined = np.concatenate([user_assemblies, response_assemblies])
        hippocampus.encode(combined)

    def recall_response(self, user_assemblies: list[int],
                        hippocampus: Hippocampus) -> list[int] | None:
        recalled = hippocampus.recall(user_assemblies)
        if recalled is not None:
            # Strip user half, return response half
            n_user = len(user_assemblies)
            return recalled[n_user:].tolist()
        return None
```

---

### Sprint 6 — Oscillations & Sequence Encoding (Week 12–13)

**Critical for LLM reduction:** Theta-gamma coupling is what allows the SNN to
hold and process multi-concept "sentences" without relying on an LLM's context window.

The SNN's theta cycle (~125 ms, 5 gamma slots) IS the context window.
5 gamma slots × ~1 concept per slot = a 5-token context, built from neuroscience.

```python
# oscillations/context_window.py  
class SNNContextWindow:
    """
    The SNN's native context window, implemented via theta-gamma coupling.
    Replaces the LLM's token context window for most tasks.
    
    Capacity: ~5 concepts (gamma cycles per theta)
    Duration: ~125 ms per "thought cycle"
    Update: continuous — new concepts enter, old ones fade
    
    This is why you don't need a transformer for short-context tasks.
    """
    THETA_MS    = 125.0   # ms per cycle
    GAMMA_MS    =  25.0   # ms per slot
    N_SLOTS     =     5   # concepts per cycle

    def __init__(self):
        self.slots: list[int | None] = [None] * self.N_SLOTS
        self.slot_strength = np.zeros(self.N_SLOTS)
        self._theta_phase  = 0.0

    def update(self, t_ms: float, new_assembly: int | None):
        self._theta_phase = (t_ms % self.THETA_MS) / self.THETA_MS
        slot = int(self._theta_phase * self.N_SLOTS)
        if new_assembly is not None:
            self.slots[slot]         = new_assembly
            self.slot_strength[slot] = 1.0
        self.slot_strength *= 0.995   # slow decay

    def get_sequence(self) -> list[int]:
        """Returns current concept sequence in temporal order."""
        return [s for s, a in zip(self.slots, self.slot_strength)
                if s is not None and a > 0.1]
```

---

### Sprint 7 — Language Emergence (Week 14–16)

The most critical sprint for LLM cost reduction. When complete, the SNN can:
1. Form stable concept attractors for all frequently encountered words/ideas
2. Chain concepts into proto-sentences via sequential STDP
3. Retrieve the most associated words for any active assembly (LexicalSTDP)
4. Generate simple responses WITHOUT the LLM via PhonologicalBuffer

**Assembly Vocabulary Milestones:**
- After 1,000 turns: ~100 stable assemblies (basic vocabulary)
- After 10,000 turns: ~1,000 assemblies (functional vocabulary)
- After 100,000 turns: ~5,000 assemblies (near-full concept layer utilisation)

```python
# cognition/vocabulary_tracker.py
class VocabularyTracker:
    """
    Tracks the SNN brain's emergent vocabulary.
    A word is "learned" when its assembly activation is stable (cosine > 0.85)
    and its LexicalSTDP weight exceeds threshold.
    """
    def report(self) -> dict:
        return {
            "total_assemblies_formed": len(self.stable_assemblies),
            "vocabulary_size": len(self.lexicon),
            "top_10_words": self.top_words(10),
            "sequence_accuracy": self.measure_sequence_accuracy(),
            "llm_bypass_rate": self.phon_buffer_use_rate,
        }
```

---

### Sprint 8 — Full Predictive Coding (Week 17–18)

With full hierarchical predictive coding, the SNN can answer novel combinations
of familiar concepts by extrapolating from learned predictions — reducing the need
for LLM inference even on previously unseen questions.

---

### Sprint 9 — Integration, Tuning, and LLM Bypass Optimisation (Week 19–20)

**Goal:** Measure and maximise the percentage of turns handled without LLM calls.

```python
# monitoring/llm_bypass_monitor.py
class LLMBypassMonitor:
    """
    Tracks what percentage of turns are handled by the SNN alone.
    Target by brain stage:
      NEONATAL  (<100k steps): 10% bypass (brain has no vocabulary yet)
      JUVENILE  (<1M steps):   30% bypass
      ADOLESCENT(<5M steps):   60% bypass
      MATURE    (>5M steps):   85% bypass
    """
    def log_turn(self, path: str):   # path in {"llm", "local"}
        self.history.append(path)
        self.bypass_rate = self.history.count("local") / len(self.history)
```

**Tuning tasks:**
1. Optimise LLMGate thresholds for maximum bypass without quality loss
2. Profile most common LLM call types → implement SNN alternatives
3. Benchmark Phi-3-mini vs GPT-4o-mini quality for articulation-only role
4. Implement caching: if brain state is nearly identical to a past state, reuse response

```python
# codec/response_cache.py
class ResponseCache:
    """
    Cache LLM responses indexed by brain state similarity.
    If current brain state is >90% similar to a cached state,
    return the cached response without an LLM call.
    Uses cosine similarity of assembly activation vectors.
    """
    def lookup(self, brain_state: BrainSnapshot) -> str | None:
        vec = brain_state.to_vector()
        for cached_vec, cached_response in self.cache:
            if cosine_similarity(vec, cached_vec) > 0.90:
                return cached_response  # zero-cost response
        return None
```

---

### Sprint 10 — Full System Integration (Week 21–24)

**Complete BRAIN2.0BrainV2 with LLM codec integrated cleanly:**

```python
# brain.py
class BRAIN2.0BrainV2:
    def process_input(self, user_text: str) -> TurnResult:
        """
        Main entry point. Returns response without exposing internals.
        """
        # Step 1: Encode (local, no LLM)
        self.char_encoder.encode(user_text, self.sensory)

        # Step 2: Run SNN for N steps (the "thinking" phase)
        for _ in range(self.thinking_steps):   # ~500–2000 steps
            self.step()

        # Step 3: Snapshot brain state
        snapshot = self.snapshot_cognitive_state()

        # Step 4: Articulate (LLM only if needed)
        result = self.codec.articulate(snapshot)

        # Step 5: Learn from this turn (online STDP)
        self._post_turn_learning(snapshot, result)

        return TurnResult(
            response     = result.text,
            path         = result.path,        # "llm" or "local"
            cost         = result.cost,
            assemblies   = snapshot.top_concepts,
            confidence   = snapshot.confidence,
            brain_status = self._status(),
        )
```

---

## 10. Hardware Targets and Resource Budgets

### Target Machines

| Target | CPU | RAM | BRAIN2.0 Scale | LLM Option |
|--------|-----|-----|-------------|-----------|
| Raspberry Pi 5 | 4-core ARM | 8 GB | 0.005 (~4k neurons) | Phi-3-mini via Ollama (quantised) |
| Intel NUC / Mini PC | 8-core x86 | 16 GB | 0.02 (~17k neurons) | Phi-3-mini or GPT-4o-mini API |
| MacBook M1/M2 | 8-core ARM | 16 GB | 0.05 (~43k neurons) | Phi-3-mini local (fast) |
| Desktop PC | 16-core x86 | 32 GB | 0.10 (~85k neurons) | Local 7B model or API |
| Workstation | 32-core | 64 GB | 0.30 (~250k neurons) | Local 13B model |
| Loihi 2 target | Neuromorphic | — | 1.00 (~858k neurons) | Optional: tiny local model |

### Memory Budget at SCALE=0.02 (good baseline target)

```
SNN populations:      ~200 MB  (float32 voltage + traces for ~17k neurons)
Sparse synapses:      ~400 MB  (COO format, ~1.5M synapses × 3 arrays × 4 bytes)
Brian2 runtime:       ~100 MB
Hippocampus:         ~150 MB  (CA3 recurrent at 0.02 scale)
LexicalSTDP matrix:   ~50 MB   (sparse, 10k words × 5.8k assemblies)
Phi-3-mini (4-bit):  ~2.5 GB  (if running locally)
─────────────────────────────
TOTAL (with local LLM): ~3.5 GB RAM
TOTAL (API LLM):        ~1.0 GB RAM
```

### Compute Budget (SCALE=0.02, single CPU core)

```
Brian2 sim step (dt=0.1ms):     ~2–5 ms wall clock
Steps per second:                200–500 sim steps/sec
Simulated time per real second:  20–50 ms
Real-time ratio:                 1:20 to 1:50 (not real-time, deliberate)
To "think" for 100ms simulated:  ~2–5 seconds real time
LLM articulation call:           ~0.5–2 seconds
Total turn latency:              ~3–8 seconds (acceptable for chat)
```

**To approach real-time at SCALE=0.02:** Use Brian2's C++ standalone mode (10–100× speedup).
With standalone codegen: ~1–5 second total turn latency, including LLM.

---

## 11. File Architecture v2

```
BRAIN2.0/
├── README.md
├── requirements.txt          # brian2, numpy, scipy, fastapi, ollama, openai
├── config.py                 # SCALE, DT, LLM_MODEL, BUDGET_DAILY
│
├── codec/                    ← THE ONLY PLACE LLM IS CALLED
│   ├── __init__.py
│   ├── llm_codec.py          ← LLMCodec: single LLM call point
│   ├── llm_gate.py           ← LLMGate: when to call vs local
│   ├── phonological_buffer.py← PhonologicalBuffer: SNN-native text gen
│   ├── character_encoder.py  ← Text → spike (no API)
│   ├── response_cache.py     ← Similarity-based caching
│   └── cost_tracker.py       ← API spend tracking + budget enforcement
│
├── neurons/                  ← LIF models (all neuron types)
├── synapses/                 ← AMPA, NMDA, GABA, STDP, STP, BCM
├── regions/                  ← All brain regions (cortical, subcortical)
├── neuromodulators/          ← DA, ACh, NE, 5-HT + reward signal
├── memory/                   ← Hippocampus, working memory, consolidation
├── oscillations/             ← Gamma, theta, coupling, context window
├── cognition/
│   ├── cell_assemblies.py    ← Assembly detection + tracking
│   ├── sequence_learning.py  ← Attractor chaining
│   ├── lexical_stdp.py       ← Word ↔ assembly association (SNN vocab)
│   ├── predictive_coding.py  ← Hierarchical PC
│   ├── free_energy.py
│   ├── vocabulary_tracker.py ← LLM bypass metrics
│   └── conversational_memory.py← Per-turn episode encoding
│
├── monitoring/
│   ├── llm_bypass_monitor.py ← Track LLM call rate over time
│   ├── brain_monitor.py      ← Spike rates, weights, oscillations
│   └── cost_dashboard.py     ← Real-time API spend display
│
├── brain.py                  ← BRAIN2.0BrainV2 assembly + process_input()
├── api.py                    ← FastAPI (brain + codec, no LLM in routes)
└── tests/
    ├── test_codec.py         ← LLM gate, phonological buffer, encoder
    ├── test_llm_bypass.py    ← Verify bypass rate improves over time
    └── ...
```

---

## 12. Decision Tree: When to Call the LLM

```
User sends message
        │
        ▼
[SNN processes for N steps]
        │
        ▼
Confidence ≥ 0.85 AND uncertainty ≤ 0.15?
   YES → Check working memory
           │
           Active memory matches pattern exactly?
             YES → PhonologicalBuffer.generate() → RETURN [no LLM]
             NO  → Check response cache
                    │
                    Cached state with cosine > 0.90?
                      YES → Return cached response → RETURN [no LLM]
                      NO  → LLM call? Rate-limit OK?
   NO  ──────────────────────────────────────────────────────────┐
                                                                 │
        ┌───────────────────────────────────────────────────────┘
        ▼
Budget OK AND rate-limit OK AND user expects text?
   NO → PhonologicalBuffer.generate() (degraded quality, acceptable)
   YES → LLM.articulate(brain_state_json)  ← ONE API call, ~430 tokens
           │
           ▼
        Cache response for future reuse
           │
           ▼
        Return to user
           │
           ▼
    Post-turn: STDP update + dopamine reward signal + hippocampal encode
```

**Expected LLM call frequency at maturity:**
- NEONATAL (0–100k steps):   ~90% of turns (brain has no vocabulary)
- JUVENILE (100k–1M steps):  ~60% of turns
- ADOLESCENT (1M–5M steps):  ~35% of turns
- MATURE (>5M steps):        ~15% of turns (most responses from SNN directly)

---

## Appendix A: Why NOT to Use a Larger LLM

The temptation is to use a large LLM (Claude Sonnet, GPT-4o) for richer responses.
This should be resisted for three reasons:

1. **Architectural corruption:** A large LLM with its own memory, reasoning, and
   knowledge becomes the actual cognitive agent. The SNN becomes decorative.
   The LLM's responses will diverge from what the SNN "thought" — you now have
   two competing cognitive agents, not one brain with a voice.

2. **Cost drift:** A single GPT-4o call at 4,000 tokens costs ~$0.04.
   At 100 turns/day: $4/day = $1,460/year. GPT-4o-mini costs 20× less.
   Phi-3-mini local costs $0.

3. **Dependency:** Cloud LLM APIs introduce availability risk, privacy exposure,
   and latency. The SNN runs locally and always. The LLM codec should be
   a swappable, optional layer — not a dependency the brain cannot function without.

## Appendix B: The "Brain Stage" LLM Bypass Target

The brain becomes progressively MORE self-sufficient as it learns.
This is the correct framing: the LLM is training wheels, not the engine.

```
NEONATAL  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░│  10% bypass  → LLM carries 90% of output load
JUVENILE  │▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░│  30% bypass  → Brain learns basic vocabulary
ADOLESCENT│▓▓▓▓▓▓▓▓░░░░░░░░░░░░│  60% bypass  → Brain handles most simple turns
MATURE    │▓▓░░░░░░░░░░░░░░░░░░│  85% bypass  → LLM only for complex articulation

Legend: ▓ = SNN handles response, ░ = LLM handles response
```

The goal is that a MATURE brain, having had >5M simulation steps and thousands of
real interactions, sounds approximately coherent in 85%+ of exchanges without
ever calling an external API.

The remaining 15% — complex phrasing, novel constructions, ambiguous queries —
are handled by the LLM codec, keeping it firmly in the role of articulator, not thinker.

---

*Revision history: v2.0 — April 2026 — Complete rearchitecture to SNN-primary model*
*Based on: neuroscience literature, BrainTransformers (2024), NSLLM (2025), cost analysis*
