# BRAIN 2.0 — Biologically Grounded Neuromorphic SNN Brain

> **Pure NumPy spiking neural network modelled after biological brain principles.**  
> No backpropagation. No dense matrix multiplication. Event-driven STDP learning.  
> The SNN brain *is* the thinker. The LLM is a translator — nothing more.

---

## The Core Vision

BRAIN 2.0 aims to be a biologically grounded Spiking Neural Network (SNN) that operates as its own cognitive substrate — not as a wrapper around an LLM, but as a brain-like system capable of learning, concept formation, and proto-language from raw spike dynamics alone.

The **fundamental question** the project explores: *Can an SNN be its own LLM?*

## Current Release

- **Stage:** `v1.0 — MATURES`
- **Status:** All critical bugs fixed. Brain is production-ready.
- **Last audited:** 2026-04-03 (see [`ASSESSMENT1750.md`](ASSESSMENT1750.md))

This release builds on v0.2 (REMEMBERS) with:
- Vocabulary learning that persists across restarts
- Proactive thoughts reaching the UI
- Feedback buttons that update brain drives
- Fixed vocabulary save/load corruption
- Correct system prompt grammar

This is architecturally different from approaches like SpikeGPT or BrainTransformers, which take a transformer architecture and replace floating-point activations with binary spikes (a quantisation approach). BRAIN 2.0's goal is to build a system where **language-like behaviour emerges from biologically realistic spike dynamics**, not from a pre-designed language architecture.

---

## Version Roadmap

```
v0.1  ALIVE          ← Brain exists, persists, has a self
v0.2  REMEMBERS      ← Brain accumulates vocabulary and episodes
v0.3  FEELS          ← Brain has salience, drives, emotional colouring
v0.4  REASONS        ← Brain predicts, chains concepts, bypasses LLM
v0.5  LEARNS         ← Brain improves measurably from interaction
v1.0  MATURES        ← 85% LLM bypass. Coherent identity. Real replacement. ✅
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

── v1.0: Production Features ───────────────────────
ConceptLayer → AssemblyDetector → PhonologicalBuffer
                 (coalition tracking)    (word↔assembly)
ConceptLayer → Hippocampus → EpisodeStore
                 (encode/recall)         (disk persistence)
ResponseCache (BoW similarity) → skip SNN on hit
LLMGate → bypass decision based on confidence
```

### Three-Layer Model

| Layer | Description |
|-------|-------------|
| **Layer 0 — I/O Boundary** | Input: CharacterEncoder (local). Output: LLMCodec (LLM — ONE call per turn) |
| **Layer 1 — Cognitive Engine** | Pure SNN, runs 24/7 locally. Sensory → Association → Predictive → Concept → Memory → Executive |
| **Layer 2 — Neuromodulatory** | AffectiveState (valence/arousal), DriveSystem (curiosity/competence/connection) |

---

## Key Features

### 🧠 Biologically Inspired

- **LIF Neurons** with Poisson encoding for sensory input
- **STDP Learning** — Spike-Timing-Dependent Plasticity (Hebbian learning without global error signal)
- **Winner-Take-All** competition in ConceptLayer for sparse coding
- **Predictive Coding** hierarchy with error signals driving attention gain
- **Safety Kernel** (ReflexArc) — hard gate blocking dangerous motor commands
- **Stable Hash** for concept seeding (survives restarts)

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
- Spontaneous association wandering (default mode network)
- Proactive thought generation via LLM

### 💾 Persistence

Everything the brain learns survives process restart:
- Weights, self-model, vocabulary, episodes, drive history
- Complete brain state saved/loaded from disk
- **Docker:** `brain_state/` bind-mounted to host — survives container restart
- **Graceful shutdown:** `brain.persist()` called automatically on `docker stop`
- **Configurable:** set `BRAIN_STATE_DIR` env var for custom paths

### 💬 User Feedback

- Thumbs up/down buttons on each brain response
- Tooltips explaining what each button does
- Feedback updates brain drives (curiosity, competence)
- Sentiment tracked in self-model

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
# Install dependencies
pip install -r requirements.txt

# Start API
uvicorn api:app --host 0.0.0.0 --port 8000

# Access UI
# Navigate to http://localhost:8000 (if using Docker) or run frontend separately

# Direct chat API
curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "hello world"}'
```

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
| [`codec/phonological_buffer.py`](codec/phonological_buffer.py) | Word↔assembly association, vocabulary learning |
| [`codec/llm_codec.py`](codec/llm_codec.py) | LLM articulation with self-model context |
| [`codec/llm_gate.py`](codec/llm_gate.py) | Decision logic for LLM vs local generation |
| [`codec/response_cache.py`](codec/response_cache.py) | BoW similarity cache (threshold 0.82), excludes LLM responses |
| [`self/self_model.py`](self/self_model.py) | SelfModel: identity, personality, stage tracking |
| [`drives/drive_system.py`](drives/drive_system.py) | Curiosity, competence, connection drives |
| [`emotion/salience.py`](emotion/salience.py) | AffectiveState: valence/arousal |
| [`persistence/brain_store.py`](persistence/brain_store.py) | Full brain state save/load |
| [`persistence/episode_store.py`](persistence/episode_store.py) | Episode disk persistence |
| [`memory/hippocampus_simple.py`](memory/hippocampus_simple.py) | Episodic memory encode/recall |
| [`api/main.py`](api/main.py) | FastAPI REST + WebSocket server |
| [`frontend/src/App.jsx`](frontend/src/App.jsx) | React UI with chat, brain state, feedback buttons |
| [`yt_transcriber.py`](yt_transcriber.py) | YouTube transcription (bundled ffmpeg) |
| [`ASSESSMENT1750.md`](ASSESSMENT1750.md) | Implementation status checklist |

---

## The Path to Emergent Language

The theoretical framework for how meaning emerges from spike patterns:

1. **Stable Attractors = Concepts** — Through STDP, frequently co-occurring spike patterns stabilize into attractor states (cell assemblies)
2. **Sequential Attractor Chains = Proto-Language** — Temporal contiguity creates trajectories through attractor space
3. **Theta-Gamma Nesting = Compositional Structure** — Gamma cycles (~25 ms) nested within theta cycles (~125 ms) encode sequential information
4. **Predictive Completion = Grammar** — Prediction error detection is the neurological signature of grammatical rule knowledge
5. **Motor Output = Communication** — Motor pathway trained to generate vocalisation patterns from activated concept attractors

---

## Project Status

- **Current Stage:** v1.0 — MATURES (production ready)
- **Completed:** v0.1 ALIVE → v0.2 REMEMBERS → v1.0 MATURES
- **All 19 Bugs Fixed:**
  - FIX-001 through FIX-016 (original assessment)
  - BUG-A through E (additional fixes)
- **Biological Fidelity:** Growing with interaction
- **Modules:** 22+ implemented
- **API:** 17 endpoints, 6 chat commands

---

## Requirements

- Python 3.10+
- NumPy (pure NumPy implementation)
- FastAPI (for REST API)

### Dependencies

We split dependencies to keep the main app image small:

- `requirements.txt` — core runtime (API, frontend)
- `requirements.ml.txt` — optional transcriber deps (youtube-transcript-api, yt-dlp)
- `requirements.prod.txt` — production dependencies (same as requirements.txt)

---

## 🐳 Docker Deployment

BRAIN 2.0 can be run entirely in Docker with both the Python API and React frontend.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (2.0+)
- [Ollama](https://ollama.ai/) running on host (for LLM integration)

### Quick Start

```bash
# 1. Clone and navigate to project
cd brain2

# 2. Copy environment template
cp .env.example .env

# 3. Start all services
docker-compose up --build
```

This starts:
- **Brain API** (Python): http://localhost:8030
- **Brain UI** (React): http://localhost:8031

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `brain-api` | 8030 | Python FastAPI backend |
| `brain-frontend` | 8031 | React UI (Nginx) |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BRAIN_SCALE` | 0.01 | Brain scale (0.01 = ~8.5k neurons) |
| `BRAIN_STATE_DIR` | brain_state | Brain state directory path |
| `LLM_BACKEND` | local_ollama | LLM backend (local_ollama, openai, anthropic, none) |
| `API_PORT` | 8000 | API port (inside container) |
| `OLLAMA_BASE_URL` | http://host.docker.internal:11434 | Ollama API URL |
| `OLLAMA_MODELS` | llama3.2:latest,phi3:mini | Available models |
| `DAILY_BUDGET` | 0.50 | Daily LLM budget (USD) |

### Ollama Setup

For LLM integration, install and run Ollama on your host:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull a model (in another terminal)
ollama pull llama3.2:latest
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/brain/status` | GET | Get current brain state (includes vocabulary, memory, bypass stats) |
| `/api/chat` | POST | Send message to brain |
| `/api/stimulate` | POST | Inject sensory stimulus |
| `/api/reflex/check` | POST | Check motor command safety |
| `/api/motor` | POST | Issue motor command |
| `/api/ws/stream` | WS | WebSocket for real-time brain state |
| `/api/vocabulary` | GET | Learned words, assembly coverage, generation stats |
| `/api/memory` | GET | Episode count, recent episodes, recall stats |
| `/api/bypass` | GET | LLM bypass rate, path distribution (llm/local/cached) |
| `/api/assemblies` | GET | Cell assembly detection stats |
| `/api/feedback` | POST | User feedback (thumbs up/down), updates drives and self-model |
| `/api/proactive` | GET/POST | Get/queue proactive brain messages |
| `/api/grep` | POST | Web crawler results |
| `/api/wiki` | GET | Wikipedia lookup |
| `/api/yt` | POST | YouTube transcription with bundled ffmpeg |
| `/api/llm/chat` | POST | Direct LLM prompt (bypasses SNN) |
| `/api/llm/status` | GET | Ollama connection status |
| `/api/synapses/{name}/weights` | GET | Synapse weight distribution |
| `/api/persist` | POST | Force immediate persistence |
| `/api/drive` | GET | Get current drive state |

---

## Chat Commands

| Command | Description |
|---------|-------------|
| `/stats` | Displays comprehensive brain statistics |
| `/vocabulary` | Shows learned vocabulary and assembly statistics |
| `/grep <n> <url>` | Crawls web pages and extracts content |
| `/llm <prompt>` | Sends direct query to LLM (Ollama) |
| `/yt <n> <url>` | Transcribes YouTube videos |
| `/?` or `/help` | Shows command reference |
| Any other text | Sends message to brain for processing |

---

## UI Features

- **Theme Switcher**: Toggle between dark and light mode (header, right side)
- **Neural Canvas**: Real-time visualization of neural activity
- **Region Monitor**: Activity levels across all 10 brain regions
- **Feedback Buttons**: Thumbs up/down with tooltips on each brain response
- **Architecture Tab**: Visual documentation of brain architecture
- **Debug Tab**: View API requests and responses

---

## License

MIT