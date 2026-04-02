# BRAIN 2.0 — Complete Architecture

**Version:** 3.0 (Consolidated)  
**Principle:** Interface-first, brain-driven, LLM-Peripheral  
**Design Inversion:** Build the brain that users feel, then the brain that thinks, then the brain that understands.

---

## Table of Contents

1. [Core Thesis](#1-core-thesis)
2. [The Design Inversion](#2-the-design-inversion)
3. [Version Map](#3-version-map)
4. [The Three-Layer Model](#4-the-three-layer-model)
5. [Responsibility Map](#5-responsibility-map)
6. [The LLM Interface](#6-the-llm-interface)
7. [Cost Model](#7-cost-model)
8. [What the SNN Brain Must Implement](#8-what-the-snn-brain-must-implement)
9. [The Spike-to-Meaning Pipeline](#9-the-spike-to-meaning-pipeline)
10. [v0.1 Implementation Details](#10-v01-implementation-details)
11. [Versioned Roadmap](#11-versioned-roadmap)
12. [File Architecture](#12-file-architecture)
13. [API Contracts](#13-api-contracts)
14. [Decision Tree: When to Call the LLM](#14-decision-tree-when-to-call-the-llm)

---

## 1. Core Thesis

The previous architectures used an LLM to generate all responses, with the SNN providing only decorative context. This is architecturally backwards. The correct model is:

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

The LLM is called **at most once per user turn**, and only to translate a completed brain state into fluent natural language. Everything else — understanding, thinking, remembering, predicting, reasoning — is the SNN's responsibility.

Target: **>90% of cognitive work done by the SNN. <10% by the LLM.**

---

## 2. The Design Inversion

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

## 3. Version Map

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

## 4. The Three-Layer Model

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
║    Cost: ~$0.00006 per turn (GPT-4o-mini) or $0 (local)      ╠═══════════════════════════════════════════════════════════════╣
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
║  │              CONCEPT LAYER (WTA 5.8k)                 │  ║
║  │  Stable attractors = words / concepts                 │  ║
║  └────────────────────────┬───────────────────────────────┘  ║
║                            │                                   ║
║  ┌─────────────────────────▼──────────────────────────────┐  ║
║  │              MEMORY SYSTEM                             │  ║
║  │  Hippocampus: episodic recall + pattern completion      │  ║
║  │  Working Memory: thalamo-cortical buffer               │  ║
║  └─────────────────────────┬──────────────────────────────┘  ║
║                             │                                  ║
║  ┌──────────────────────────▼─────────────────────────────┐  ║
║  │              EXECUTIVE / MOTOR                         │  ║
║  │  PFC: goal maintenance, context                        │  ║
║  │  Basal Ganglia: action selection                       │  ║
║  │  Motor Cortex → ReflexArc (safety)                     ║
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

## 5. Responsibility Map

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

## 6. The LLM Interface

### 6.1 What the LLM Receives (Input Prompt)

The LLM never receives the full conversation history or raw user message.
It receives ONLY the structured brain state output:

```json
{
  "active_assemblies": [
    {"id": 47, "label": "query:weather", "activation": 0.91},
    {"id": 12, "label": "context:location=berlin", "activation": 0.78}
  ],
  "working_memory": ["weather", "berlin", "tomorrow"],
  "prediction_confidence": 0.82,
  "neuromodulator_state": {
    "dopamine": 0.6,
    "acetylcholine": 0.7,
    "norepinephrine": 0.5
  },
  "brain_status": "JUVENILE",
  "uncertainty": 0.18
}
```

**System prompt (constant, ~80 tokens):**
```
You are a language articulator. Convert the brain state JSON below into
a natural, concise response. Do not add reasoning, opinions, or knowledge
not present in the brain state. Articulate only what the brain has concluded.
If uncertainty > 0.5, express appropriate hedging.
Max 150 words.
```

### 6.2 LLM Call Conditions (Gate Logic)

The LLM is ONLY called when ALL of the following are true:

```python
class LLMGate:
    def should_call_llm(self, brain_state: dict, user_request: str) -> bool:
        # Condition 1: User expects natural language response
        if not self._expects_text_response(user_request):
            return False

        # Condition 2: Brain has reached stable concept activation
        if brain_state["prediction_confidence"] < 0.4:
            return False

        # Condition 3: Not a simple lookup (SNN can answer directly)
        if self._is_direct_recall(brain_state):
            return False

        # Condition 4: Rate limit — max 1 call per second
        if self._rate_limited():
            return False

        return True
```

### 6.3 Fallback: SNN-Native Response Generation

When the LLM gate is closed, the brain generates responses using the phonological buffer:

```python
class PhonologicalBuffer:
    """
    Direct concept-assembly-to-text pathway.
    No LLM. Maps active cell assemblies → word sequences
    via learned association weights.
    """
    def generate(self, assembly_sequence: list[int], working_memory: list[str]) -> str:
        words = []
        for asm_id in assembly_sequence:
            best_word = self._assembly_to_word(asm_id)
            if best_word:
                words.append(best_word)
        return self._fill_template(words, working_memory)
```

### 6.4 LLM Model Selection Strategy

| Stage | LLM Option | Cost/turn | When to Use |
|-------|-----------|-----------|------------|
| Development | GPT-4o-mini | ~$0.00006 | Debugging output quality |
| Production (cloud) | GPT-4o-mini | ~$0.00006 | Final polish only |
| Production (local) | Phi-3-mini 3.8B (4-bit) | $0 | Privacy / offline |
| Production (offline) | Mistral-7B-Instruct Q4 | $0 | Full local operation |
| Fallback | PhonologicalBuffer | $0 | High confidence cases |

---

## 7. Cost Model

| Architecture | Cost per 100 turns | RAM | Compute |
|-------------|-------------------|-----|---------|
| v1 (LLM-primary) | ~$0.15 (Claude/GPT-4o) | 2GB SNN + API | API-bound |
| v2 (SNN-primary, GPT-4o-mini) | ~$0.006 | 2GB SNN + 1GB model | SNN CPU |
| v2 (SNN-primary, Phi-3 local) | $0.00 | 2GB SNN + 2.5GB model | CPU only |

**Cost reduction from v1: 96% at MATURE brain stage.**

---

## 8. What the SNN Brain Must Implement

For the SNN to genuinely replace most of the LLM's cognitive load:

### Priority 1 — Stable Concept Representations
- Implementation: AssociationArea with STDP + BCM + WTA
- Milestone: Same input → same top-3 active assemblies across 10 trials

### Priority 2 — Working Memory Context Window
- Implementation: NMDA-recurrent working memory + theta-gamma sequence coding
- Milestone: 5-item sequence retained for >10 seconds of sim time

### Priority 3 — Memory Retrieval
- Implementation: CA3 recurrent attractor + CA1 gating
- Milestone: Partial cue (50% of pattern) → full recall

### Priority 4 — Prediction and Completion
- Implementation: PredictiveCodingHierarchy + AttractorChainer
- Milestone: Next-assembly prediction accuracy >55%

### Priority 5 — Semantic Association
- Implementation: STDP-trained lateral connections in AssociationArea
- Milestone: Semantic neighbourhood size >3 reliably

---

## 9. The Spike-to-Meaning Pipeline

```
USER TEXT INPUT
     │
     ▼
┌─────────────────────────────────────────────────┐
│  STEP 1: LOCAL TEXT PARSER  [no LLM]            │
│  CharacterEncoder.encode(text)                  │
└────────────────────────┬────────────────────────┘
                         │ spike indices
                         ▼
┌─────────────────────────────────────────────────┐
│  STEP 2: SENSORY PROCESSING  [SNN]              │
│  SensoryCortex → FeatureLayer                   │
└────────────────────────┬────────────────────────┘
                         │ feature spike patterns
                         ▼
┌─────────────────────────────────────────────────┐
│  STEP 3: ASSOCIATION & PREDICTION  [SNN]        │
│  AssociationArea ↔ PredictiveHierarchy          │
└────────────────────────┬────────────────────────┘
                         │ active assembly IDs
                         ▼
┌─────────────────────────────────────────────────┐
│  STEP 4: MEMORY RETRIEVAL  [SNN]                │
│  Hippocampus.recall(active_assemblies)          │
└────────────────────────┬────────────────────────┘
                         │ enriched context
                         ▼
┌─────────────────────────────────────────────────┐
│  STEP 5: LLM GATE CHECK  [local logic]         │
│  LLMGate.should_call_llm(brain_state)           │
│     → confidence > 0.85? → PhonologicalBuffer   │
│     → confidence < 0.85? → LLM articulation     │
└────────────────────────┬────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌─────────────────────┐      ┌──────────────────────────┐
│  PATH A: NO LLM     │      │  PATH B: LLM ARTICULATE  │
│  PhonologicalBuffer │      │  ONE API call, ~430 tokens
│  Cost: $0           │      │  Cost: ~$0.00006         │
└─────────────────────┘      └──────────────────────────┘
                                 │
                                 ▼
                        TEXT RESPONSE → USER
```

---

## 10. v0.1 Implementation Details

### 10.1 The Self-Model

A persistent data structure representing the brain's identity across sessions:

```python
@dataclass
class SelfModel:
    name:           str   = "BRAIN2.0"
    created_at:     str   = ""
    session_count:  int   = 0
    total_turns:    int   = 0
    total_steps:    int   = 0
    brain_stage:    str   = "NEONATAL"
    mood:           float = 0.5
    energy:         float = 1.0
    confidence:     float = 0.3
    curiosity_bias: float = 0.5
    caution_bias:   float = 0.5
    vocabulary_size: int   = 0
    llm_bypass_rate: float = 0.0
```

### 10.2 Continuous Existence Loop

The brain runs 24/7 in a background thread with three modes:

```python
class ContinuousExistenceLoop:
    ACTIVE_STEPS_PER_TICK  = 200   # fast, responsive
    IDLE_STEPS_PER_TICK    =  20   # slow, consolidating
    DORMANT_STEPS_PER_TICK =   2   # minimal, just alive

    IDLE_THRESHOLD_S       =  60
    DORMANT_THRESHOLD_S    = 3600
```

### 10.3 Emotional Salience Layer

```python
@dataclass
class AffectiveState:
    valence: float = 0.0    # -1 to +1
    arousal: float = 0.3    # 0 to 1
```

### 10.4 Intrinsic Drives

```python
@dataclass
class DriveState:
    curiosity:   float = 0.5   # Need for novel input
    competence:  float = 0.5   # Need to respond accurately
    connection:  float = 0.5   # Need for engaged interaction
```

---

## 11. Versioned Roadmap

### v0.1 — ALIVE (Build now)

| Module | Status |
|--------|--------|
| SelfModel | ✅ Build |
| ContinuousExistenceLoop | ✅ Build |
| SalienceFilter + AffectiveState | ✅ Build |
| DriveSystem | ✅ Build |
| BrainStore | ✅ Build |
| LLMCodec (v3) | ✅ Build |
| CharacterEncoder | ✅ Build |
| Core SNN (E/I, basic STDP) | ✅ Build |
| ReflexArcV2 | ✅ Build |
| REST API + WebSocket | ✅ Build |

### v0.2 — REMEMBERS

| Module | Description |
|--------|-------------|
| LexicalSTDP | Word ↔ assembly association |
| CellAssemblyDetector | Correlation-based stable pattern detection |
| VocabularyTracker | Reports learned concept count |
| Hippocampus (simplified) | CA3 recurrent attractor |
| PhonologicalBuffer (real) | Assembly → word sequence |
| ResponseCache | Cosine-similarity response reuse |

### v0.3 — FEELS

| Module | Description |
|--------|-------------|
| DopamineSystem | TD learning, reward prediction error |
| AcetylcholineSystem | Learning rate gating |
| NorepinephrineSystem | Neural gain / arousal |
| SerotoninSystem | Temporal discounting |
| AmygdalaRegion | Fast emotional tagging |

### v0.4 — REASONS

| Module | Description |
|--------|-------------|
| PredictiveCodingHierarchy | 4-level hierarchical PC |
| AttractorChainer | Sequential concept chaining |
| ThetaGammaCoupling | 5-slot context window |
| Full Hippocampus | DG + CA3 + CA1 + EC |

### v0.5 — LEARNS

| Module | Description |
|--------|-------------|
| Brian2 full migration | C++ codegen enabled |
| ThalamusRegion | Full thalamo-cortical loop |
| BasalGanglia | Action selection |
| STDP triplet rule | Replace pair-STDP |

### v1.0 — MATURES

| Capability | Target |
|-----------|--------|
| Vocabulary size | ~5,000 stable assemblies |
| LLM bypass rate | ~85% |
| Prediction accuracy | >65% next-concept |
| Brain stage | ADOLESCENT → MATURE |

---

## 12. File Architecture

```
BRAIN2.0/
├── config.py                     ← SCALE, DT, LLM_MODEL
│
├── self/
│   └── self_model.py             ← SelfModel (identity, personality)
│
├── emotion/
│   └── salience.py              ← SalienceFilter, AffectiveState
│
├── drives/
│   └── drive_system.py          ← DriveState, DriveSystem
│
├── persistence/
│   ├── brain_store.py           ← BrainStore (save/load)
│   └── episode_store.py         ← Episode index
│
├── codec/                       ← ONLY PLACE LLM IS CALLED
│   ├── llm_codec.py             ← LLMCodec
│   ├── llm_gate.py              ← When to call vs local
│   ├── character_encoder.py     ← Text → spikes
│   ├── phonological_buffer.py   ← Assembly → text
│   ├── response_cache.py        ← Similarity-based reuse
│   └── cost_tracker.py          ← API spend tracking
│
├── neurons/
│   ├── lif_neurons.py           ← LIF base
│   └── __init__.py
│
├── synapses/
│   ├── stdp_synapses.py         ← STDP, BCM
│   └── __init__.py
│
├── regions/
│   ├── cortical_regions.py      ← All brain regions
│   └── __init__.py
│
├── memory/
│   └── hippocampus_simple.py     ← CA3 attractor
│
├── cognition/
│   ├── cell_assemblies.py       ← Assembly detection
│   └── __init__.py
│
├── brain/
│   ├── continuous_loop.py       ← ContinuousExistenceLoop
│   └── __init__.py              ← BRAIN2.0BrainV3 assembly
│
├── api/
│   ├── main.py                  ← FastAPI + WebSocket
│   └── __init__.py
│
├── yt_transcriber.py            ← YouTube transcription
│
└── frontend/src/
    └── App.jsx                  ← React UI
```

---

## 13. API Contracts

```python
POST /chat
  Body:    { "message": str, "history": list, "brainState": dict }
  Returns: {
    "response": str,
    "path": "llm" | "local" | "cached",
    "brain_state": dict,
    "affect": { "valence": float, "arousal": float },
    "drives": dict,
    "stages": dict
  }

POST /feedback
  Body:    { "valence": float }   # -1.0 to +1.0
  Returns: { "acknowledged": true, "new_mood": float, "new_confidence": float }

GET  /status
  Returns: full brain snapshot + self_model + drive state + affect state

GET  /proactive
  Returns: { "messages": list }

POST /api/proactive
  Body:    { "message": str }
  Returns: { "queued": int }

WS   /ws/stream
  Emits every 200ms: { "regions": {...}, "self": {...} }
```

---

## 14. Decision Tree: When to Call the LLM

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
                  Cached state with cosine > 0.82?
                    YES → Return cached response
                    NO  → LLM call? Rate-limit OK?
   NO  ────────────────────────────────────────────┐
                                                      │
        ┌────────────────────────────────────────────┘
        ▼
Budget OK AND rate-limit OK AND user expects text?
   NO → PhonologicalBuffer.generate()
   YES → LLM.articulate(brain_state_json)

         │
         ▼
      Cache response for future reuse
         │
         ▼
      Return to user
         │
         ▼
Post-turn: STDP update + dopamine reward + hippocampal encode
```

**Expected LLM call frequency at maturity:**
- NEONATAL (0–100k steps):   ~90% of turns
- JUVENILE (100k–1M steps):  ~60% of turns
- ADOLESCENT (1M–5M steps):  ~35% of turns
- MATURE (>5M steps):        ~15% of turns

---

## Appendix A: Why NOT to Use a Larger LLM

1. **Architectural corruption:** A large LLM becomes the actual cognitive agent. The SNN becomes decorative.

2. **Cost drift:** A single GPT-4o call at 4,000 tokens costs ~$0.04. At 100 turns/day: $4/day = $1,460/year. GPT-4o-mini costs 20× less.

3. **Dependency:** Cloud LLM APIs introduce availability risk, privacy exposure, and latency. The SNN runs locally and always.

## Appendix B: The "Brain Stage" LLM Bypass Target

```
NEONATAL  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░│  10% bypass  → LLM carries 90%
JUVENILE  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  30% bypass
ADOLESCENT│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  60% bypass
MATURE   │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  85% bypass
```

---

*Document consolidated from ARCHITECTURE_V2.md and ARCHITECTURE_V3.md*
*Last updated: April 2026*
