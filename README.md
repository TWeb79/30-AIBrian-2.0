# BRAIN 2.0 — Biologically Grounded Neuromorphic SNN Brain

> **Pure NumPy spiking neural network modelled after biological brain principles.**  
> No backpropagation. No dense matrix multiplication. Event-driven STDP learning.  
> The SNN brain *is* the thinker. The LLM is a translator — nothing more.

---

## The Core Vision

BRAIN 2.0 aims to be a biologically grounded Spiking Neural Network (SNN) that operates as its own cognitive substrate — not as a wrapper around an LLM, but as a brain-like system capable of learning, concept formation, and proto-language from raw spike dynamics alone.

The **fundamental question** the project explores: *Can an SNN be its own LLM?*

## Current Release

- **Stage:** `v0.2 — REMEMBERS`
- **Status:** Core vocabulary + episodic memory modules built; LLM bypass layers (cache, phonological buffer, gate) active; feedback loop closed.
- **Last audited:** 2026-04-02 (see [`ASSESSMENT1750.md`](ASSESSMENT1750.md) for implementation checklist)

This release builds on v0.1 (ALIVE) with persistent vocabulary, episodic memory, bypass monitoring, and a deployed React UI + FastAPI stack.

This is architecturally different from approaches like SpikeGPT or BrainTransformers, which take a transformer architecture and replace floating-point activations with binary spikes (a quantisation approach). BRAIN 2.0's goal is to build a system where **language-like behaviour emerges from biologically realistic spike dynamics**, not from a pre-designed language architecture.

---

## Version Roadmap

```
v0.1  ALIVE          ← Brain exists, persists, has a self
v0.2  REMEMBERS      ← Brain accumulates vocabulary and episodes
v0.3  FEELS          ← Brain has salience, drives, emotional colouring
v0.4  REASONS        ← Brain predicts, chains concepts, bypasses LLM
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

── v0.2: Vocabulary & Memory Layer ────────────────────────
ConceptLayer → CellAssemblyDetector → PhonologicalBuffer
                (coalition tracking)    (word↔assembly)
ConceptLayer → HippocampusSimple → EpisodeStore
                (encode/recall)         (disk persistence)
ResponseCache (BoW similarity) → skip SNN on hit
LLMBypassMonitor (rolling window) → track bypass rate
```

### Three-Layer Model

| Layer | Description |
|-------|-------------|
| **Layer 0 — I/O Boundary** | Input: CharacterEncoder (local). Output: LanguageCodec (LLM — ONE call per turn) |
| **Layer 1 — Cognitive Engine** | Pure SNN, runs 24/7 locally. Sensory → Association → Predictive → Concept → Memory → Executive |
| **Layer 2 — Neuromodulatory** | Dopamine, Acetylcholine, Norepinephrine, Serotonin as global state |

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
- Spontaneous association wandering (default mode network)

### 💾 Persistence

Everything the brain learns survives process restart:
- Weights, self-model, vocabulary, episodes, drive history
- Complete brain state saved/loaded from disk
- **Docker:** `brain_state/` bind-mounted to host — survives container restart
- **Graceful shutdown:** `brain.persist()` called automatically on `docker stop`
- **Configurable:** set `BRAIN_STATE_DIR` env var for custom paths

### 🧠 Neuromodulatory Systems (Planned v0.3)

Four global modulators — not yet implemented, planned for v0.3:
| Modulator | Function |
|-----------|----------|
| Dopamine | Reward prediction error → STDP learning rate |
| Acetylcholine | Novelty → encoding vs. recall mode |
| Norepinephrine | Arousal → gain, WTA sharpness |
| Serotonin | Temporal discount, patience |

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
cd oscen/
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000
```

Open the React UI or standalone brain2_ui.jsx:
```bash
# React UI (standard)
curl http://localhost:8000/status

# Standalone brain2_ui.jsx
# Build frontend and access via http://localhost:8031/index-brain2.html

# Direct chat API
curl -X POST http://localhost:8000/chat \
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
| [`brain/continuous_loop.py`](brain/continuous_loop.py) | 24/7 daemon: ACTIVE/IDLE/DORMANT, proactive LLM thoughts |
| [`cognition/cell_assemblies.py`](cognition/cell_assemblies.py) | Cell assembly detection and tracking |
| [`memory/hippocampus_simple.py`](memory/hippocampus_simple.py) | Episodic memory encode/recall |
| [`codec/response_cache.py`](codec/response_cache.py) | BoW similarity cache (threshold 0.82), excludes LLM responses |
| [`codec/llm_bypass_monitor.py`](codec/llm_bypass_monitor.py) | Rolling-window bypass rate tracker |
| [`codec/phonological_buffer.py`](codec/phonological_buffer.py) | Word↔assembly association |
| [`codec/llm_codec.py`](codec/llm_codec.py) | LLM articulation with self-model context |
| [`codec/llm_gate.py`](codec/llm_gate.py) | Decision logic for LLM vs local generation |
| [`self/self_model.py`](self/self_model.py) | SelfModel: identity, personality, stage tracking |
| [`drives/drive_system.py`](drives/drive_system.py) | Curiosity, competence, connection drives |
| [`emotion/salience.py`](emotion/salience.py) | AffectiveState: valence/arousal |
| [`persistence/episode_store.py`](persistence/episode_store.py) | Episode disk persistence |
| [`persistence/brain_store.py`](persistence/brain_store.py) | Full brain state save/load |
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

- **Current Stage:** v0.2 — REMEMBERS (core modules built)
- **Completed:** v0.1 ALIVE + v0.2 core (vocabulary, memory, response cache, bypass monitor, feedback loop)
- **Implemented Fixes (Apr 2026):**
  - FIX-008: ResponseCache threshold 0.82, LLM responses never cached
  - FIX-010: Proactive messages use LLM for real thoughts
  - FIX-011: `/api/feedback` endpoint + UI feedback buttons
  - FIX-016: Lock contention fixed (background loop pauses during processing)
- **Biological Fidelity:** ~14%
- **Modules:** 22 implemented
- **API:** 17 endpoints, 6 chat commands
- **Next Stage:** v0.3 — FEELS (neuromodulators, amygdala)
- **Research Frontier:** No system has yet succeeded at this goal at meaningful scale

---

## Requirements

-- Python 3.10+
-- NumPy (pure NumPy implementation)
-- FastAPI (for REST API)

Dependencies split
------------------
We split heavy / optional dependencies to keep the main app image small.

- requirements.txt — core runtime (API, frontend). Installed in production image.
- requirements.prod.txt — same as requirements.txt (kept for compatibility with Dockerfile).
- requirements.ml.txt — optional transcriber deps (caption-first): youtube-transcript-api, yt-dlp. Use this when you want YouTube caption fetching.

If you need Whisper or other heavy ML packages, install them separately (not included by default): e.g. openai-whisper, faster-whisper, torch.

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
| `OLLAMA_BASE_URL` | http://host.docker.internal:11434 | Ollama API URL |
| `OLLAMA_MODELS` | llama3.2:latest,phi3:mini | Available models |
| `DAILY_BUDGET` | 0.50 | Daily LLM budget (USD) |

### Manual Build Commands

```bash
# Build and run API only
docker build -t brain2:api --target development .
docker run -p 8030:8000 -e OLLAMA_BASE_URL=http://host.docker.internal:11434 brain2:api

# Build frontend
cd frontend
docker build -t brain2:frontend .
docker run -p 8031:80 brain2:frontend
```

### Development

```bash
# Run with live reload
docker-compose up --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

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
| `/api/grep` | GET | Web crawler results |
| `/api/wiki` | GET | Wikipedia lookup |
| `/api/yt` | POST | YouTube transcription with bundled ffmpeg |
| `/api/llm/chat` | POST | Direct LLM prompt (bypasses SNN) |
| `/api/llm/status` | GET | Ollama connection status |
| `/api/synapses/{name}/weights` | GET | Synapse weight distribution |

---

## Chat Commands

The BRAIN 2.0 UI supports several slash commands for interacting with the brain:

| Command | Description |
|---------|-------------|
| `/stats` | Displays comprehensive brain statistics including:
  - Simulation metrics (step, rate, gain, prediction error)
  - Cortical activity breakdown per region
  - Learning indicators (STDP, concepts, memory)
  - Processing efficiency metrics
  - Conversation history

| `/vocabulary` | Shows learned vocabulary and assembly statistics.
  - Words learned by the SNN (comma-separated)
  - Assembly count and activation stats
  - Generation success rate

| `/grep <n> <url>` | Crawls web pages and extracts content.
  - `<n>`: Number of pages to crawl (1-10)
  - `<url>`: Starting URL for crawl
  - Example: `/grep 3 https://example.com`

| `/llm <prompt>` | Sends direct query to LLM (Ollama).
  - `<prompt>`: Your question or command
  - Example: `/llm What is neural plasticity?`

| `/yt <n> <url>` | Transcribes YouTube videos and teaches the brain.
  - `<n>`: Number of videos to process (1-10)
  - `<url>`: YouTube video URL
  - Supports playlists and video chains
  - Example: `/yt 3 https://youtube.com/watch?v=VIDEO_ID`

| `/?` or `/help` | Shows this command reference.

| Any other text | Sends message to brain for processing using the neural network architecture.

---

## UI Features

- **Theme Switcher**: Toggle between dark and light mode (button at bottom-left of footer)
- **Real-time Neural Visualization**: Watch neural activity in the canvas
- **Region Activity Monitor**: Track activity levels across all 10 brain regions
- **Debug Log**: View API requests and responses

---

## License

MIT
