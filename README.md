# BRAIN 2.0 — Biologically Grounded Neuromorphic SNN Brain

> **Pure NumPy spiking neural network modelled after biological brain principles.**  
> No backpropagation. No dense matrix multiplication. Event-driven STDP learning.  
> The SNN brain *is* the thinker. The LLM is a translator — nothing more.

---

## The Core Vision

BRAIN 2.0 aims to be a biologically grounded Spiking Neural Network (SNN) that operates as its own cognitive substrate — not as a wrapper around an LLM, but as a brain-like system capable of learning, concept formation, and proto-language from raw spike dynamics alone.

The **fundamental question** the project explores: *Can an SNN be its own LLM?*

## Current Release

- **Stage:** `v0.3 — FEELS` (COMPLETE)
- **Status:** All features from ASSESSMENT1750.md implemented. Emotional modulation wired into STDP. Model selector in header. API status indicator. Debug tab with LLM communication logging.
- **Last updated:** 2026-04-04

This release builds on v0.1 (ALIVE) with persistent vocabulary, episodic memory, bypass monitoring, and a deployed React UI + FastAPI stack.

This is architecturally different from approaches like SpikeGPT or BrainTransformers, which take a transformer architecture and replace floating-point activations with binary spikes (a quantisation approach). BRAIN 2.0's goal is to build a system where **language-like behaviour emerges from biologically realistic spike dynamics**, not from a pre-designed language architecture.

---

## Version Roadmap

```
v0.1  ALIVE          ← Brain exists, persists, has a self ✅
v0.2  REMEMBERS      ← Brain accumulates vocabulary and episodes ✅
v0.3  FEELS          ← Brain has salience, drives, emotional colouring ✅ COMPLETE
v0.4  REASONS        ← Brain predicts, chains concepts, bypasses LLM ✅ IN PROGRESS
v0.5  LEARNS         ← Brain improves measurably from interaction
v1.0  MATURES        ← 85% LLM bypass. Coherent identity. Real replacement.
v2.0  EMBODIES       ← Physical grounding. Long-term goal.
```

---

## Architecture

```
SensoryCortex (multimodal: vision / audio / touch)
    │  STDP
    ▼
FeatureLayer (edge/texture/phoneme detection)
    │  STDP
    ▼
AssociationRegion ◄──── PredictiveRegion (feedback + error signal)
    │  STDP              │
    ▼                    ▼
ConceptLayer (WTA)    attention_gain broadcast to all synapses
    │  STDP
    ▼                    ▼
MetaControl → WorkingMemory
    │
    ▼
Cerebellum → motor output → ReflexArc (safety kernel) → actuator

─── v0.2: Vocabulary & Memory Layer ────────────────────────
ConceptLayer → CellAssemblyDetector → PhonologicalBuffer
                (coalition tracking)    (word↔assembly + attractor chains)
ConceptLayer → HippocampusSimple → EpisodeStore
                (encode/recall)         (disk persistence)
ResponseCache (BoW similarity) → skip SNN on hit
LLMBypassMonitor (rolling window) → track bypass rate

─── v0.3: Emotional Modulation ────────────────────────────
AffectiveState → neuromodulator biases → STDP gain
DriveSystem → behavioural modifiers → association/predictive gain
AmygdalaRegion → fast emotional tagging
NeuromodulatorSystem (DA/ACh/NE/5-HT) → full populations
```

### Three-Layer Model

| Layer | Description |
|-------|-------------|
| **Layer 0 — I/O Boundary** | Input: CharacterEncoder (local). Output: LanguageCodec (LLM — ONE call per turn) |
| **Layer 1 — Cognitive Engine** | Pure SNN, runs 24/7 locally. Sensory → Association → Predictive → Concept → Memory → Executive |
| **Layer 2 — Neuromodulatory** | Dopamine, Acetylcholine, Norepinephrine, Serotonin as full LIF populations |

---

## Key Features

### 🧠 Biologically Inspired

- **LIF Neurons** with Poisson encoding for sensory input
- **STDP Learning** — Spike-Timing-Dependent Plasticity (Hebbian learning without global error signal)
- **Winner-Take-All** competition in ConceptLayer for sparse coding
- **Predictive Coding** hierarchy with error signals driving attention gain
- **Safety Kernel** (ReflexArc) — hard gate blocking dangerous motor commands

### SNN-First Design

- **SNN processes all input locally** — LLM called only when gate permits
- **Three bypass layers:** response cache, phonological buffer, LLM gate
- **Bypass rate tracked** via `/api/bypass` — rises as vocabulary grows
- Text input → spike encoding (local, no LLM)
- Cell assembly → word association learning (local, no LLM)
- LLM called at most once per turn, only when local generation insufficient

### 🔄 Continuous Existence

The brain runs in a background thread at all times — not just when a user sends a message. During idle it performs:
- Low-level housekeeping (weight decay, energy recovery)
- Slow memory consolidation
- Self-initiated thoughts (every 60 idle ticks)
- Proactive messages via WebSocket

### 📊 UI Features

- **Theme Switcher**: Toggle between dark and light mode
- **API Status Indicator**: Shows API response time or error (e.g., `API 45ms` or `API ERR502`)
- **LLM Model Selector**: Click LLM status to select model from dropdown
- **Real-time Neural Visualization**: Watch neural activity in the canvas
- **Region Activity Monitor**: Track activity levels across all 10 brain regions
- **Debug Log**: View API requests/responses and LLM communication

---

## What's New (April 2026)

### Core Fixes (from ASSESSMENT1750.md)
- ✅ `_status()` uses `total_steps` (persists across reboots)
- ✅ BrainStore constructed with `base_dir` from env var
- ✅ LLM gate respects vocabulary size (>50 words = local generation)
- ✅ Auto-train vocabulary on first boot from TrainingFile.md
- ✅ Removed vocabulary persist throttle (immediate save on new words)

### UI Enhancements
- ✅ Sentence templates in PhonologicalBuffer for readable local responses
- ✅ ACh wired to thinking_steps (emotional learning rate)
- ✅ Richer memory context in LLM prompt (valence + related words)
- ✅ EIBalancedRegion crash fix (handles zero-length input)
- ✅ Competitive decay cap for YouTube ingestion
- ✅ STDP LTP/LTD event counters for telemetry
- ✅ Rich `/api/brain/health` endpoint

### Proactive Behavior
- ✅ Proactive messages via WebSocket (`proactive_thought` in snapshot)
- ✅ Self-initiated conversation during idle (`_trigger_self_thought`)
- ✅ Better proactive prompt (interesting, not generic)

### Architecture Evolution
- ✅ Full neuromodulator populations (`brain/modulation/__init__.py`)
- ✅ PredictiveHierarchy observability (per-level errors in snapshot)
- ✅ AttractorChainer transition tests

---

## 💾 Persistence

Everything the brain learns survives process restart:
- Weights, self-model, vocabulary, episodes, drive history
- Complete brain state saved/loaded from disk
- **Docker:** `brain_state/` bind-mounted to host — survives container restart
- **Graceful shutdown:** `brain.persist()` called automatically on `docker stop`
- **Configurable:** set `BRAIN_STATE_DIR` env var for custom paths
- **Model preference:** saved to `brain_state/llm_preference.json`

---

## Scale

| Scale | Neurons | Synapses | RAM | Platform |
|-------|---------|----------|-----|----------|
| 0.01 | ~8.5k | ~800k | ~200MB | Any CPU |
| 0.05 | ~42k | ~4M | ~1GB | Modern CPU |
| 0.10 | ~85k | ~8M | ~2GB | Multi-core |
| 1.00 | ~858k | ~80M | ~20GB | Loihi 2 / GPU |

Set scale via: `BRAIN_SCALE=0.05 uvicorn api:app ...`

---

## Quickstart

```bash
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8030
```

Open http://localhost:8031 or use the API:
```bash
curl -X POST http://localhost:8030/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "hello world"}'
```

---

## Testing

23 tests implemented for early error diagnosis:

```bash
python -m pytest tests/ -v
```

| Test File | Coverage |
|-----------|----------|
| test_lif_neurons.py | LIF neuron behavior, refractory, traces |
| test_stdp.py | STDP weight bounds, LTP/LTD, event counters |
| test_response_cache.py | Cache hit/miss, eviction, stats |
| test_vocabulary_persistence.py | Export/import roundtrip |
| test_attractor_chainer.py | Transition learning, chaining |
| test_llm_config.py | Model selection, persistence |

---

## Learning Rule (STDP)

```
If  t_pre < t_post  →  Δw = +A_plus  · exp(-Δt / τ_plus)   [LTP]
If  t_pre > t_post  →  Δw = −A_minus · exp(-Δt / τ_minus)  [LTD]
```

Weights bounded in [w_min, w_max]. No global error signal.
High prediction error scales the learning rate (attention gain).

---

## Safety Kernel

Motor commands are intercepted by `ReflexArc.check_command()`:
- **force > 10 N** → BLOCKED + withdrawal reflex
- **angle > 170°** → BLOCKED + withdrawal reflex
- **velocity > 2 m/s** → BLOCKED + withdrawal reflex

This is a hard gate — no neural pathway can bypass it.

---

## Key Files

| File | Description |
|------|-------------|
| [`brain/__init__.py`](brain/__init__.py) | Full brain assembly, simulation loop, process_input pipeline |
| [`brain/neurons/lif_neurons.py`](brain/neurons/lif_neurons.py) | LIF neuron model, Poisson encoder, rate encoder |
| [`brain/synapses/stdp_synapses.py`](brain/synapses/stdp_synapses.py) | STDP synapse, lateral inhibition |
| [`brain/regions/cortical_regions.py`](brain/regions/cortical_regions.py) | All brain regions (Sensory, Assoc, Predictive, Concept, etc.) |
| [`brain/continuous_loop.py`](brain/continuous_loop.py) | 24/7 daemon: ACTIVE/IDLE/DORMANT, proactive thoughts |
| [`brain/modulation/__init__.py`](brain/modulation/__init__.py) | Neuromodulator populations (DA/ACh/NE/5-HT) |
| [`cognition/cell_assemblies.py`](cognition/cell_assemblies.py) | Cell assembly detection and tracking |
| [`cognition/attractor_chainer.py`](cognition/attractor_chainer.py) | Sequential concept chaining |
| [`codec/phonological_buffer.py`](codec/phonological_buffer.py) | Word↔assembly association, sentence templates |
| [`codec/llm_gate.py`](codec/llm_gate.py) | Decision logic for LLM vs local generation |
| [`codec/response_cache.py`](codec/response_cache.py) | BoW similarity cache |
| [`api/routes/debug.py`](api/routes/debug.py) | LLM communication logging |
| [`frontend/src/components/Header.jsx`](frontend/src/components/Header.jsx) | UI with model selector, API indicator |
| [`frontend/src/components/DebugTab.jsx`](frontend/src/components/DebugTab.jsx) | API + LLM communication logs |
| [`ASSESSMENT1750.md`](ASSESSMENT1750.md) | Implementation checklist |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/brain/health` | GET | Rich brain health (stage, steps, vocab, bypass rate) |
| `/api/brain/status` | GET | Get current brain state |
| `/api/chat` | POST | Send message to brain |
| `/api/llm/status` | GET | Ollama connection status, available models |
| `/api/llm/set_model` | POST | Set active LLM model |
| `/api/debug/llm_logs` | GET | LLM communication logs |
| `/api/vocabulary` | GET | Learned words, assembly stats |
| `/api/memory` | GET | Episode count, recent episodes |
| `/api/bypass` | GET | LLM bypass rate |
| `/api/feedback` | POST | User feedback (thumbs up/down) |
| `/api/proactive` | GET/POST | Proactive brain messages |
| `/api/yt` | POST | YouTube transcription |
| `/api/reflex/check` | POST | Check motor command safety |

---

## Project Status

- **Current Stage:** v0.3 — FEELS (COMPLETE)
- **Completed:** v0.1 ALIVE + v0.2 + v0.3 all features
- **Tests:** 23 passing
- **Biological Fidelity:** ~20%
- **Modules:** 25+ implemented
- **API:** 20+ endpoints
- **Next:** v0.4 REASONS (predictive coding, full reasoning)

---

## Requirements

- Python 3.10+
- NumPy (pure NumPy implementation)
- FastAPI (for REST API)

---

## 🐳 Docker Deployment

```bash
cp .env.example .env
docker-compose up --build
```

This starts:
- **Brain API** (Python): http://localhost:8030
- **Brain UI** (React): http://localhost:8031

---

## License

MIT
