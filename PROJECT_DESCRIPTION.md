# BRAIN2.0: A Biologically Grounded Spiking Neural Network Brain
## Project Description, Gap Analysis & Implementation Plan

**Version:** 1.0  
**Status:** Pre-Implementation Specification  
**Classification:** Technical Architecture Document

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Part I — How the Real Human Brain Works](#2-part-i--how-the-real-human-brain-works)
   - 2.1 Scale and Physical Structure
   - 2.2 The Neuron: Biological Computation Unit
   - 2.3 Synaptic Transmission: Chemistry, Not Just Electricity
   - 2.4 Neuromodulatory Systems
   - 2.5 Cortical Architecture: Columns and Layers
   - 2.6 Memory Systems
   - 2.7 Oscillations and Neural Timing
   - 2.8 The Predictive Brain (Free Energy Principle)
   - 2.9 Glial Cells and Astrocytes
   - 2.10 Energy Metabolism and Homeostasis
3. [Part II — Gap Analysis: Current Implementation vs. Biological Reality](#3-part-ii--gap-analysis-current-implementation-vs-biological-reality)
4. [Part III — The Fundamental Question: Can SNN Be Its Own LLM?](#4-part-iii--the-fundamental-question-can-snn-be-its-own-llm)
5. [Part IV — Project Implementation Plan](#5-part-iv--project-implementation-plan)
   - Sprint 0: Foundation
   - Sprint 1: Biological Neuron Models
   - Sprint 2: Synapse Diversity
   - Sprint 3: Neuromodulation
   - Sprint 4: Cortical Architecture
   - Sprint 5: Memory Systems
   - Sprint 6: Oscillations
   - Sprint 7: Language & Concept Emergence
   - Sprint 8: Predictive Loop & Free Energy
   - Sprint 9: Safety & Motor Output
   - Sprint 10: Full System Integration
6. [Technical Reference Tables](#6-technical-reference-tables)
7. [File & Module Architecture](#7-file--module-architecture)
8. [Research Milestones & Evaluation Criteria](#8-research-milestones--evaluation-criteria)

---

## 1. Executive Summary

BRAIN2.0 aims to be a biologically grounded Spiking Neural Network (SNN) that operates as its own cognitive substrate — not as a wrapper around an LLM, but as a brain-like system capable of learning, concept formation, and proto-language from raw spike dynamics alone.

The current v1 implementation (NumPy-based, 10 regions, LIF neurons, basic STDP) establishes a valid architectural skeleton but operates at approximately **3–5% biological fidelity**. The gap is not primarily in neuron count or synapse density — it is in the depth of biological mechanisms modelled: neurotransmitter diversity, cortical laminar structure, oscillatory dynamics, neuromodulation, glial computation, and the temporal encoding of meaning via spike patterns rather than firing rates.

This document:
- Provides a rigorous account of how the biological brain actually works
- Precisely identifies each gap between the current implementation and biology
- Proposes a sprint-based implementation plan with concrete technical specifications
- Defines the architecture for a self-sufficient SNN-as-cognition system

The target is a system that produces **emergent language-like representations** from continuous spiking dynamics, without any transformer, attention mechanism, or external LLM call.

---

## 2. Part I — How the Real Human Brain Works

### 2.1 Scale and Physical Structure

The human brain contains approximately **86 billion neurons** and **100 trillion synapses** (1 × 10¹⁴). Neurons are not uniformly distributed: the cerebellum alone contains ~69 billion neurons, though these are mostly granule cells. The cerebral cortex — where higher cognition occurs — contains only ~16 billion neurons but receives a disproportionate fraction of the axonal projections.

Key structural facts relevant to any simulation:

| Region | Neuron Count | Key Function |
|--------|-------------|-------------|
| Cerebral cortex | ~16 billion | Cognition, perception, language |
| Cerebellum | ~69 billion | Motor timing, prediction |
| Basal ganglia | ~1.5 billion | Action selection, habit formation |
| Hippocampus | ~30 million | Episodic memory, spatial maps |
| Amygdala | ~12 million | Emotional appraisal, fear |
| Thalamus | ~14 million | Sensory relay, gating |
| Brainstem | ~10 million | Vital functions, arousal |
| Hypothalamus | ~2 million | Homeostasis, drives |

The average cortical neuron has **7,000 synaptic connections** (dendritic spines), but projection neurons in associative areas can have up to **200,000 synapses**. This is the biological substrate for the "universal approximator" claim of biological intelligence.

### 2.2 The Neuron: Biological Computation Unit

The biological neuron is far more complex than the Leaky Integrate-and-Fire (LIF) model captures.

**Real neuron computational properties:**

1. **Dendritic computation**: Dendrites are not passive summing wires. Each dendritic branch performs non-linear integration. A single pyramidal cell dendrite can fire its own local spike (a "dendritic spike") independent of the soma. This means a single neuron is already a multi-layer computation, not a point process.

2. **Multiple spike types**: Besides regular action potentials (1 ms), neurons produce:
   - Burst spikes (3–5 rapid spikes in 20 ms) — encode salience or novelty
   - Calcium spikes (100 ms) — in dendrites, trigger plasticity cascades
   - Graded potentials (no threshold, in some sensory neurons)

3. **Neuron types** — the brain contains at least **100 morphologically distinct neuron types**. The most important computational distinction:
   - **Excitatory (glutamatergic)**: ~80% of cortical neurons. Pyramidal cells. Long-range projection. Release glutamate (AMPA + NMDA receptors).
   - **Inhibitory (GABAergic)**: ~20% of cortical neurons. Local interneurons. Four major subtypes: PV (fast, precise), SST (distal dendrites, gain control), VIP (disinhibitory), SOM (feedback). Each serves a distinct computational role.

4. **AMPA vs NMDA dynamics**: The NMDA receptor is a coincidence detector — it only opens when the synapse is active AND the postsynaptic membrane is already depolarised. This makes it a key substrate for Hebbian learning and pattern completion. It has a 100–200 ms time window vs 5–10 ms for AMPA. The current implementation has no NMDA model at all.

5. **Axonal conduction delays**: Signals take 0.5–20 ms to traverse white matter connections between regions. This is not noise — it creates precise temporal windows that are critical for oscillatory synchrony and coincidence detection. Neglecting delays means the model cannot exhibit gamma oscillations (40 Hz), theta-gamma coupling, or any form of temporal binding.

### 2.3 Synaptic Transmission: Chemistry, Not Just Electricity

The current implementation models synapses as a single weight scalar. Real synapses are:

**Short-term dynamics:**
- **Short-term potentiation (STP)**: Rapid, transient strengthening due to residual calcium. Lasts 100–500 ms.
- **Short-term depression (STD)**: Vesicle depletion reduces transmission probability after bursts. Lasts 100 ms–several seconds. This is a fundamental mechanism for gain control and novelty detection — a synapse "habituates" to repeated stimuli.
- **Facilitation**: Some synapses (especially from thalamus) increase their release probability over repeated activations, acting as low-pass or high-pass filters.

**Long-term dynamics (plasticity):**
- **STDP**: As implemented, but the real rule is triplet-based (pre-post-pre or post-pre-post) for many synapse types, not just pair-based.
- **BCM rule (Bienenstock-Cooper-Munro)**: The threshold for LTP vs LTD is itself sliding — determined by the neuron's recent mean activity. This prevents runaway potentiation and explains orientation selectivity development.
- **Structural plasticity**: Synapses can appear (spinogenesis) and disappear (spine pruning) on timescales of hours to days. The total connectivity structure of the brain changes continuously throughout life.
- **Homeostatic scaling**: If a neuron is chronically under-active, it upscales ALL its synaptic weights (synaptic scaling). If chronically over-active, it downscales. This is a global normalization mechanism absent from the current code.

**Neurotransmitter release:**
- Release is probabilistic. A single action potential has a 10–90% probability of triggering neurotransmitter release (synapse-type dependent).
- Quantal release: transmitter is released in discrete packets (quanta) corresponding to individual synaptic vesicles.

### 2.4 Neuromodulatory Systems

This is the most critically absent subsystem in the current BRAIN2.0 implementation. The neuromodulatory systems are not just "gain" multipliers — they are the brain's global hyperparameter tuners that set the learning rate, exploration-exploitation balance, attention allocation, and metabolic state.

**Dopamine (DA) — Reward Prediction Error:**
- Source: Ventral Tegmental Area (VTA) + Substantia Nigra
- Computational role: Implements temporal difference (TD) learning. Dopamine neurons fire at reward, then shift their response to the earliest reliable predictor of reward as learning proceeds. The signal encodes: Δ = actual_reward − predicted_reward.
- Positive prediction error (unexpected reward): dopamine burst → strengthen active synapses (endocannabinoid-mediated retrograde signalling)
- Negative prediction error (expected reward omitted): dopamine dip → weaken recent synaptic activity
- Without dopamine modelling, the network has no reinforcement learning and cannot learn goal-directed behaviour.

**Acetylcholine (ACh) — Attention and Learning Rate:**
- Source: Basal forebrain (Nucleus Basalis of Meynert), brainstem (pedunculopontine nucleus)
- Computational role: Controls the trade-off between exploiting stored representations vs. learning new ones. High ACh = high learning rate, weaken attractor dynamics (new information overrides old). Low ACh = strong attractors, memory consolidation.
- In sensory cortex: ACh reduces lateral inhibition, sharpening receptive fields.
- In hippocampus: ACh gates the direction of information flow (encoding vs. recall modes).

**Norepinephrine (NE) — Arousal and Uncertainty:**
- Source: Locus Coeruleus (LC), only ~40,000 neurons but projects to the entire brain
- Computational role: Controls the exploration-exploitation trade-off. High NE = high "neural gain" (responses are more nonlinear, winner-take-all). Low NE = graded, exploratory responses.
- Models: NE implements the "gain" parameter of nonlinear input-output functions of neurons.
- Phasic NE bursts follow unexpected stimuli and errors — a novelty signal.

**Serotonin (5-HT) — Temporal Discounting and Risk:**
- Source: Dorsal Raphe Nucleus
- Computational role: Controls temporal discounting (how far into the future rewards are valued). Also modulates harm aversion and impulse control.
- Inverse relationship with dopamine in many circuits.

**Mapping to hyperparameters:**

| Neuromodulator | Computational Equivalent |
|---------------|-------------------------|
| Dopamine | Reward prediction error δ (TD learning) |
| Acetylcholine | Learning rate α |
| Norepinephrine | Neural gain / temperature τ of softmax |
| Serotonin | Discount factor γ |

The current implementation replaces all four of these with a single scalar `attention_gain` derived from prediction error. This is a fundamental simplification that prevents the network from exhibiting motivated behaviour, attention, or reinforcement-based learning.

### 2.5 Cortical Architecture: Columns and Layers

The cerebral cortex is not a flat sheet of uniformly connected neurons. It has a precise **6-layer laminar structure** that implements a canonical circuit repeated across all cortical areas.

**The 6 cortical layers:**

| Layer | Neurons | Connectivity | Function |
|-------|---------|-------------|---------|
| L1 | Mostly axons and dendrites | Receives top-down input | Feedback integration |
| L2/3 | Pyramidal + interneurons | Horizontal within area, projects to L5 | Pattern completion, association |
| L4 | Stellate + pyramidal | Receives thalamic (feedforward) input | Primary sensory processing |
| L5 | Large pyramidal (Betz cells) | Projects to subcortex, brainstem, spinal cord | Motor output, output to other areas |
| L6 | Pyramidal + stellate | Projects BACK to thalamus | Thalamo-cortical feedback loop |

**Cortical columns (hypercolumns):**
- A cortical column is ~500 µm in diameter, ~2 mm deep, contains ~10,000 neurons.
- Within a column, neurons are connected more densely than between columns.
- Adjacent columns represent similar features (orientation columns in V1, frequency columns in A1).
- The column is the computational unit of cortex.

**The canonical cortical microcircuit (simplified):**
```
Thalamus → L4 → L2/3 → L5 → output
                 ↑↓
L6 → thalamus (feedback gain control)
L2/3 ↔ L2/3 (lateral connections between columns, WTA via PV interneurons)
L1 ← prefrontal (top-down prediction, context)
```

The current BRAIN2.0 implementation has no laminar structure. All neurons within a region are treated as a flat, undifferentiated pool. This means there is no distinction between feedforward processing (L4→L2/3) and feedback (L1 top-down), no separation of output (L5) from associative processing (L2/3), and no thalamo-cortical loop.

### 2.6 Memory Systems

The brain has multiple distinct memory systems with different mechanisms:

**Working memory (prefrontal cortex):**
- Maintained by persistent firing of pyramidal neurons in sustained loops.
- Mechanism: NMDA-receptor-mediated recurrent excitation. Not a buffer — it's a dynamical attractor.
- Capacity: ~4 items (not 7 ± 2 — that's outdated).
- Timescale: seconds to minutes.

**Episodic memory (hippocampus → cortex):**
- The hippocampus (specifically CA3 + CA1) acts as a rapid one-shot associative memory.
- Pattern completion: CA3's recurrent connections can retrieve full patterns from partial cues (heteroassociative memory).
- Pattern separation: Dentate Gyrus "orthogonalises" similar inputs to prevent interference.
- Consolidation: During slow-wave sleep, the hippocampus "replays" recent experiences and trains the cortex via sharp-wave ripples. The cortex then stores compressed statistical regularities.

**Semantic memory (cortex):**
- Distributed across association cortex. No single location.
- Emerges from repeated co-activation patterns — Hebbian learning across many episodes.
- Represented as attractor states in recurrent networks.

**Procedural memory (basal ganglia + cerebellum):**
- Basal ganglia: Reinforcement-learned action sequences via dopamine-gated synaptic plasticity.
- Cerebellum: Error-signal-driven (climbing fibre from inferior olive provides teaching signal) fine-tuning of motor timing. Uses LTD at parallel fibre-Purkinje cell synapses.

The current implementation has a `WorkingMemory` region that is a simple spike buffer (a list). It has no hippocampal memory system, no sleep-based consolidation, and no basal ganglia.

### 2.7 Oscillations and Neural Timing

The brain is not a rate-code machine. It is a timing machine. Oscillations at distinct frequencies carry distinct computational functions:

| Frequency Band | Name | Function |
|---------------|------|---------|
| 0.5–4 Hz | Delta | Sleep consolidation, slow cortical oscillation |
| 4–8 Hz | Theta | Hippocampal sequence encoding, spatial navigation |
| 8–12 Hz | Alpha | Inhibitory gating ("idle rhythm"), top-down suppression |
| 12–30 Hz | Beta | Motor maintenance, top-down predictions |
| 30–80 Hz | Gamma | Local cortical processing, binding, attention |
| >80 Hz | High gamma | Highly localised, intense processing |

**Theta-gamma coupling** is particularly important: in the hippocampus, individual gamma cycles (~25 ms) are nested within theta cycles (~125 ms). Each gamma cycle encodes one item; a theta cycle encodes a sequence of items in order. This is the brain's mechanism for sequential representation of information — the biological analogue of a token sequence.

**Gamma oscillations and the binding problem:**
- Neurons in different brain areas that represent related features of the same object fire in synchrony at ~40 Hz (gamma).
- This "binding by synchrony" hypothesis (Wolf Singer, Francis Crick) proposes that temporal coherence across areas is how the brain integrates separate representations into unified percepts.

The current BRAIN2.0 implementation has zero oscillatory dynamics. Neurons fire according to their membrane voltage; there are no rhythmic inhibitory interneurons (fast-spiking PV cells driving gamma), no theta pacemaker (hippocampal septal input), and no alpha gating. This means the system cannot implement temporal binding and cannot perform sequential computation natively.

### 2.8 The Predictive Brain (Free Energy Principle)

The most influential modern framework for understanding cortical computation is **Predictive Processing** (Rao & Ballard, 1999) and Karl Friston's **Free Energy Principle** (2010).

**Core idea:** The brain does not process sensory input bottom-up. Instead, it continuously generates predictions top-down and only propagates **prediction errors** upward. The brain is fundamentally a hypothesis generator that tries to minimise the difference between its internal model of the world and the incoming sensory stream.

**Biological implementation:**
- Deep (L5/L6) pyramidal neurons send top-down "predictions" to lower areas via long-range feedback axons.
- Superficial (L2/3) pyramidal neurons encode "prediction errors" and send these upward.
- The precision of prediction errors (how much the brain trusts a mismatch) is controlled by ACh and NE — this is the mechanistic basis of attention.

**Implications for SNN design:**
1. Every feedforward connection should have a paired feedback connection carrying predictions.
2. The "signal" being propagated upward is the residual error, not the raw sensory data.
3. Learning occurs specifically at sites of persistent prediction error — this is a principled local learning rule compatible with STDP.
4. Consciousness may be the experience of the generative model's highest-level state — what the brain predicts the world to be.

The current implementation has a `PredictiveRegion` that computes a scalar prediction error and broadcasts an attention gain. This is a very crude approximation of the full hierarchical predictive coding framework.

### 2.9 Glial Cells and Astrocytes

Glia constitute roughly **half of all brain cells** and are increasingly understood as active computational participants, not mere support cells.

**Astrocytes:**
- Each astrocyte contacts ~100,000 synapses.
- Tripartite synapse: pre-neuron + post-neuron + astrocyte process all participate in transmission.
- Astrocytes release gliotransmitters (glutamate, ATP, D-serine) that modulate NMDA receptors.
- Astrocytic calcium waves propagate across networks on timescales of seconds — implementing a slow, diffuse modulation completely absent from any SNN model.
- Recent evidence suggests astrocytes implement something functionally analogous to attention (context-sensitive weighting of inputs via calcium signalling) — a mechanism analogous to transformer self-attention but implemented in biochemistry.

**Microglia:**
- Synaptic pruning during development and learning. Active synapses are protected; inactive ones are "eaten" by microglia. This is the biological mechanism underlying "use it or lose it."

None of these glial mechanisms are modelled in the current system.

### 2.10 Energy Metabolism and Homeostasis

The brain consumes ~20 watts (not 5 watts as BRAIN2.0 claims for its CPU simulation — 5W is the Loihi 2 chip's power consumption for a scaled neuromorphic version). This is ~20% of total body energy for 2% of body mass.

**Biological efficiency mechanisms:**
- Sparse coding: ~1–5% of neurons are active at any time. This is not an accident — it is actively maintained by inhibitory interneurons and homeostatic plasticity.
- Event-driven processing: Information is only transmitted when there is something to transmit.
- Spike-based communication eliminates the need for continuous clock-synchronised computation.

The current BRAIN2.0 simulation does approximate sparse coding via WTA in ConceptLayer and event-driven propagation. This is one of its most biologically accurate features.

---

## 3. Part II — Gap Analysis: Current Implementation vs. Biological Reality

### Summary Table

| Biological Feature | Current Status | Gap Severity | Sprint |
|-------------------|----------------|-------------|--------|
| LIF neuron model | ✅ Implemented (basic) | Medium — missing NMDA, bursting, dendritic computation | 1 |
| Neuron type diversity (E/I) | ❌ Absent — all neurons identical | Critical | 1 |
| AMPA + NMDA synaptic dynamics | ❌ Only generic weight scalar | Critical for learning | 2 |
| Short-term plasticity (STP/STD) | ❌ Absent | High | 2 |
| Triplet STDP | ❌ Only pair-based | Medium | 2 |
| BCM / homeostatic scaling | ❌ Absent | High | 2 |
| Dopamine (reward prediction error) | ❌ No dopamine system | Critical | 3 |
| Acetylcholine (learning rate control) | ❌ Absent (scalar gain only) | Critical | 3 |
| Norepinephrine (neural gain / arousal) | ❌ Absent | High | 3 |
| Serotonin (temporal discounting) | ❌ Absent | Medium | 3 |
| Cortical laminar structure (6 layers) | ❌ Flat neuron pools | High | 4 |
| Cortical columns / hypercolumns | ❌ Absent | High | 4 |
| Thalamo-cortical loops | ❌ Absent | High | 4 |
| Basal ganglia (action selection) | ❌ Absent | High | 4 |
| Hippocampal memory (episodic) | ❌ Simple spike buffer | Critical | 5 |
| Sleep-based memory consolidation | ❌ Absent | High | 5 |
| Pattern completion / separation | ❌ Absent | High | 5 |
| Gamma oscillations (40 Hz) | ❌ Absent | High | 6 |
| Theta oscillations (4–8 Hz) | ❌ Absent | High | 6 |
| Theta-gamma coupling (sequence encoding) | ❌ Absent | Critical for language | 6 |
| Alpha gating (top-down suppression) | ❌ Absent | Medium | 6 |
| Axonal conduction delays | ❌ All connections instantaneous | High | 6 |
| Dendritic computation | ❌ Point neuron model only | Medium | 1 |
| Full hierarchical predictive coding | ❌ Scalar error only | High | 8 |
| Free energy minimisation | ❌ Absent | High | 8 |
| Astrocyte / glial computation | ❌ Absent | Medium | 9 |
| Language as emergent spike patterns | ❌ No mechanism | Critical | 7 |
| Sparse population codes for concepts | ✅ WTA in ConceptLayer | Partial | — |
| Event-driven propagation | ✅ Implemented | Good | — |
| Predictive region with error signal | ✅ Scalar version implemented | Partial | 8 |
| Safety kernel (ReflexArc) | ✅ Implemented | Good | 9 |
| Brainstem homeostatic drive | ✅ Implemented (basic) | Good | — |
| Poisson sensory encoding | ✅ Implemented | Good | — |

**Overall Biological Fidelity Score: ~8–12%**

### Critical Gaps (in priority order)

**Gap 1 — No Excitatory/Inhibitory Balance (E/I Balance)**
This is the most fundamental missing feature. Real cortex is ~80% excitatory (glutamatergic) and ~20% inhibitory (GABAergic). The interplay between these two populations generates ALL oscillations, ALL gain control, ALL winner-take-all competition, and ALL sparse coding. Without a separate inhibitory interneuron population with its own properties (fast-spiking, low threshold, no STDP but connection-specific), the model cannot self-organise into biologically plausible activity patterns.

**Gap 2 — No Neuromodulatory Systems**
The four major neuromodulators (DA, ACh, NE, 5-HT) are the brain's global hyperparameters. Without them, the system has no reward-driven learning, no attention allocation, and no arousal/sleep cycling. Replacing them with a single scalar is like running a thermostat where temperature, humidity, pressure, and wind speed are all the same number.

**Gap 3 — No Oscillatory Dynamics**
All forms of temporal binding, sequence encoding, and working memory maintenance in the biological brain are implemented through oscillations. Without theta-gamma coupling in particular, there is no mechanism to encode sequential information (which is the foundation of language). SpikeGPT and BrainTransformers papers demonstrate that converting the recurrent dynamics of transformers to SNN form requires some equivalent of sequential temporal structure.

**Gap 4 — No Hippocampal Memory System**
The current `WorkingMemory` class is a Python list. A real hippocampal model (even simplified) requires CA3 recurrent connections with attractor dynamics, CA1 for output gating, dentate gyrus for pattern separation, and entorhinal cortex for compressed cortical representations.

**Gap 5 — No Language Emergence Mechanism**
The current system has no principled mechanism by which spike patterns become symbols. The path to emergent language requires: (1) stable attractor states in association cortex that represent concepts, (2) sequential access to these attractors via theta-gamma nesting, (3) Hebbian chaining of attractors (concept A activates concept B which activates concept C = a proto-sentence), (4) a motor output system for vocalisation-like sequence generation.

---

## 4. Part III — The Fundamental Question: Can SNN Be Its Own LLM?

### Current State of the Art (2024–2025)

Recent research has begun demonstrating that SNNs can replace transformers as language models:

- **SpikeGPT** (2023, UC Santa Cruz): First generative SNN language model. 260M parameters, achieves transformer-level perplexity on Enwik8 with 22× fewer synaptic operations. Uses spike-based RWKV architecture.
- **BrainTransformers** (2024, arXiv:2410.14687): Full SNN LLM with spike-based attention (SNNMatmul, SNNSoftmax).
- **SpikeLLM** (2024): Scales SNNs to LLM-scale via saliency-based spiking.
- **NSLLM** (National Science Review, 2025): Neuromorphic-SNN LLM framework as complete alternative to traditional LLMs.

**The key distinction** between these engineering approaches and BRAIN2.0's goal:

These papers take a **transformer architecture and replace the floating-point activations with binary spikes** — a quantisation approach. The underlying architecture remains transformer-shaped (attention matrices, softmax, residual connections, layer normalisation).

BRAIN2.0's goal is architecturally different: to build a system where **language-like behaviour emerges from biologically realistic spike dynamics**, not from a pre-designed language architecture. This is the harder problem. No one has succeeded at this yet at meaningful scale. It represents a genuine research frontier.

### The Theoretical Path from Spikes to Semantics

The theoretical framework for how meaning can emerge from spike patterns without a pre-programmed language model:

**Stage 1 — Stable Attractors = Concepts:**
Through STDP, frequently co-occurring spike patterns in the association cortex stabilise into attractor states. Each attractor is a sparse assembly of ~100–1000 neurons that fire together reliably when triggered by a subset of member neurons. This is a "cell assembly" (Hebb, 1949). Concept = cell assembly = attractor basin.

**Stage 2 — Sequential Attractor Chains = Proto-Language:**
Through temporal contiguity learning (spike sequences in time), attractors become chained: experiencing A before B repeatedly causes A's attractor to project excitation forward to B. This creates a "trajectory through attractor space" — the analogue of a sentence.

**Stage 3 — Theta-Gamma Nesting = Compositional Structure:**
Within each theta cycle (125 ms), 4–6 attractors can each be activated in successive gamma sub-cycles (25 ms). This provides a biological mechanism for "chunks" of information — the equivalent of a context window of ~4–6 items.

**Stage 4 — Predictive Completion = Grammar:**
If the sequence A→B→C is learned, presentation of A will cause prediction of B (via predictive region feedback). Prediction error occurs when C follows A directly. This "violation detection" is the neurological signature of grammatical rule knowledge.

**Stage 5 — Motor Output = Communication:**
A motor output pathway trained to generate vocalisation patterns from activated concept attractors would produce proto-speech — sounds reliably associated with internal attractor states.

This is the theoretical blueprint for an SNN that serves as its own language model. It is biologically inspired (it mirrors hypotheses in language neuroscience about Broca's area, sequence learning, and predictive coding of syntax), computationally principled, and at least partially achievable in the proposed implementation timeline.

---

## 5. Part IV — Project Implementation Plan

### Sprint 0 — Foundation & Infrastructure (Week 1–2)

**Goal:** Establish the development environment, benchmarking infrastructure, and basic simulation harness.

**Technical Tasks:**

1. **Install and configure Brian2** as the authoritative simulation engine.
   - Brian2 provides differential equation solvers, exact STDP implementations, and monitors
   - All LIF equations written in Brian2's equation syntax for correctness
   - NumPy used only for pre/post-processing, not for simulation core

2. **Profiling infrastructure:**
   - Per-region spike rate monitors (SpikeMonitor, PopulationRateMonitor)
   - Synaptic weight histogram tracking per synapse group
   - Simulation wall-clock time vs simulated time ratio
   - Memory usage per population and synapse group

3. **Scale parameter system:**
   ```python
   SCALE = 0.01  # 1% = ~8.5k neurons (fast dev iteration)
   SCALE = 0.10  # 10% = ~85k neurons (full feature test)
   SCALE = 1.00  # 100% = ~858k neurons (Loihi target)
   ```

4. **Unit test harness:**
   - Each region has an isolated test confirming: neurons fire at biologically plausible rates (1–100 Hz), STDP converges, inhibition correctly suppresses, no runaway excitation.

**Deliverables:** `environment.yml`, `tests/`, `simulation/core.py`, `simulation/monitor.py`

---

### Sprint 1 — Biological Neuron Models (Week 3–4)

**Goal:** Replace the single uniform LIF model with biologically accurate excitatory and inhibitory neuron populations.

**Technical Specification:**

**1A. Pyramidal Neuron (Excitatory, ~80% of region)**
```
dv/dt = (-(v - E_L) + R_m*(I_syn + I_ext)) / tau_m  : volt
dI_AMPA/dt = -I_AMPA / tau_AMPA  : amp
dI_NMDA/dt = -I_NMDA / tau_NMDA  : amp   # slow, coincidence detector
dI_GABA/dt = -I_GABA / tau_GABA  : amp

Parameters:
  tau_m    = 20 ms
  tau_AMPA = 5 ms
  tau_NMDA = 100 ms   ← key difference from LIF
  tau_GABA = 10 ms
  E_L      = -70 mV
  v_thresh = -55 mV
  v_reset  = -70 mV
  tau_ref  = 2 ms
  R_m      = 100 MΩ
```

**NMDA Voltage-Gating (Mg²⁺ block):**
```python
# NMDA only passes current when membrane is depolarised
NMDA_gate = 1 / (1 + exp(-0.062 * (v/mV)) * (Mg_conc / 3.57))
I_NMDA_eff = I_NMDA * NMDA_gate
```

**1B. Fast-Spiking Interneuron (PV, Inhibitory, ~15% of region)**
```
# Same LIF structure but:
tau_m    = 10 ms  (2x faster than pyramidal)
tau_ref  = 1 ms   (rapid re-firing)
v_thresh = -47 mV (lower threshold — fires more easily)
# Receives only AMPA (no NMDA — critical for fast inhibition)
# Releases GABA only
```

**1C. SST Interneuron (Somatostatin, inhibitory, ~5%)**
```
# Projects to distal dendrites of pyramidal cells
# Gain control for top-down vs bottom-up competition
tau_m    = 25 ms
# Activated by sustained excitation (vs PV by brief intense excitation)
```

**1D. VIP Interneuron (disinhibitory, rare)**
```
# Inhibits SST interneurons → releases pyramidal cells from SST inhibition
# Gateway for top-down facilitation
```

**Region class refactor:**
```python
class CorticalRegion(BrainRegion):
    def __init__(self, n_total, name):
        self.n_exc = int(n_total * 0.80)   # pyramidal
        self.n_pv  = int(n_total * 0.15)   # PV interneurons
        self.n_sst = int(n_total * 0.04)   # SST interneurons
        self.n_vip = int(n_total * 0.01)   # VIP interneurons

        self.exc = PyramidalPopulation(self.n_exc, name + "_exc")
        self.pv  = PVInterneuron(self.n_pv,  name + "_pv")
        self.sst = SSTInterneuron(self.n_sst, name + "_sst")
        self.vip = VIPInterneuron(self.n_vip, name + "_vip")
```

**Internal wiring within each cortical region:**
- Exc → PV  (AMPA, p=0.5, fast, strong) ← feedback inhibition
- PV  → Exc (GABA, p=0.5, fast) ← generates gamma
- Exc → SST (AMPA, p=0.3, slow, sustained) ← gain control
- SST → Exc:dendrite (GABA, p=0.4) ← distal inhibition
- VIP → SST (GABA, p=0.5) ← disinhibition gate
- Exc → Exc (AMPA+NMDA, p=0.1, recurrent) ← attractor dynamics

**Deliverables:** `neurons/pyramidal.py`, `neurons/interneurons.py`, `regions/cortical_region.py`

---

### Sprint 2 — Synapse Diversity (Week 5–6)

**Goal:** Implement realistic synaptic dynamics including STP/STD, triplet STDP, BCM rule, and homeostatic scaling.

**2A. Synaptic Model Hierarchy:**
```python
class SynapseType(Enum):
    AMPA   = "ampa"    # fast excitatory, 5ms tau
    NMDA   = "nmda"    # slow excitatory, 100ms tau, voltage-gated
    GABA_A = "gaba_a"  # fast inhibitory, 6ms tau
    GABA_B = "gaba_b"  # slow inhibitory, 150ms tau (metabotropic)
```

**2B. Short-Term Plasticity (Tsodyks-Markram model):**
```
# Synaptic resource equations
du/dt = -u / tau_rec   (resource recovery)
dx/dt = -u*x*delta_t  (depletion on each spike)
I_syn = A * u * x      (effective current)

Parameters for depressing synapses (e.g., cortical recurrent):
  A      = 1.0  (absolute synaptic strength)
  tau_rec = 200 ms  (recovery time)
  u_0    = 0.5  (baseline release probability)

Parameters for facilitating synapses (e.g., thalamo-cortical):
  tau_fac = 500 ms  (facilitation time constant)
  u_0    = 0.1  (initial low release probability)
```

**2C. Triplet STDP (Pfister & Gerstner, 2006):**
The pair-based STDP rule Δw = A+·exp(-Δt/τ+) − A-·exp(-Δt/τ-) is insufficient — it produces fixed-point weights at 0 or w_max. Triplet STDP adds:
```
# Pre-synaptic traces
dr1/dt = -r1 / tau_plus    (fast pre-trace)
dr2/dt = -r2 / tau_x       (slow pre-trace)

# Post-synaptic traces
do1/dt = -o1 / tau_minus   (fast post-trace)
do2/dt = -o2 / tau_y       (slow post-trace)

# LTP (at post-spike)
dw = o1 * (A2_plus + A3_plus * r2)

# LTD (at pre-spike)
dw = -r1 * (A2_minus + A3_minus * o2)

Parameters (visual cortex fit):
  tau_plus  = 16.8 ms
  tau_minus = 33.7 ms
  tau_x     = 101 ms
  tau_y     = 125 ms
  A2_plus   = 7.5e-10
  A3_plus   = 9.3e-3
  A2_minus  = 7.0e-3
  A3_minus  = 2.3e-4
```

**2D. BCM Sliding Threshold:**
```python
# Each neuron maintains a sliding modification threshold θ
dθ/dt = (v² - θ) / tau_BCM   (tau_BCM = 10 s)

# Plasticity rule
dw = η * phi(v, θ) * pre_rate
# where phi(v, θ) = v*(v - θ)   (changes sign at v = θ)
# If recent mean activity is high → θ rises → harder to potentiate
# If recent mean activity is low → θ drops → easier to potentiate
```

**2E. Homeostatic Synaptic Scaling:**
```python
class HomeostaticScaler:
    TARGET_RATE = 5.0  # Hz — target firing rate per neuron
    TAU_HOMEO = 100_000  # ms — very slow (hours equivalent)

    def update(self, population, dt):
        actual_rate = population.firing_rate * 1000  # Hz
        error = self.TARGET_RATE - actual_rate
        scale_factor = 1.0 + 1e-6 * error * dt
        population.synaptic_input_scale *= scale_factor
        population.synaptic_input_scale = np.clip(
            population.synaptic_input_scale, 0.5, 2.0
        )
```

**Deliverables:** `synapses/ampa.py`, `synapses/nmda.py`, `synapses/gaba.py`, `synapses/stdp_triplet.py`, `synapses/stp.py`, `synapses/homeostatic.py`

---

### Sprint 3 — Neuromodulatory Systems (Week 7–8)

**Goal:** Implement the four major neuromodulatory systems as distinct populations with their own dynamics, projecting globally to all cortical regions.

**3A. Dopamine System (VTA/SNc → Striatum, Prefrontal):**
```python
class DopamineSystem:
    """
    Implements temporal difference (TD) learning.
    VTA neurons fire when actual_reward > predicted_reward (δ > 0)
    VTA dip when expected_reward is omitted (δ < 0)
    """
    def __init__(self, n_vta=500):  # scaled; real VTA ~500k neurons
        self.vta = LIFPopulation(n_vta, LIFParams(tau_m=20.0, v_thresh=-50.0))
        self.prediction = 0.0
        self.gamma = 0.95  # discount factor

    def td_error(self, reward: float, next_value: float) -> float:
        δ = reward + self.gamma * next_value - self.prediction
        self.prediction = self.prediction + 0.1 * δ
        return δ

    def modulate_synapse(self, synapse: SparseSTDPSynapse, δ: float):
        """
        Dopamine modulates STDP learning rate.
        δ > 0: increase A_plus (LTP easier)
        δ < 0: increase A_minus (LTD easier)
        """
        if δ > 0:
            synapse.p.A_plus  *= (1 + 0.1 * δ)
        else:
            synapse.p.A_minus *= (1 + 0.1 * abs(δ))
```

**3B. Acetylcholine System (Basal Forebrain → all cortex):**
```python
class AcetylcholineSystem:
    """
    ACh = learning rate controller.
    High ACh: new learning dominates (hippocampal encoding mode)
    Low ACh:  old memories consolidate (cortical recall mode)
    """
    def __init__(self):
        self.ach_level = 0.5   # 0.0–1.0

    def modulate(self, synapse: SparseSTDPSynapse, novelty: float):
        # Novelty (prediction error) drives ACh release
        self.ach_level = 0.3 + 0.7 * novelty
        synapse.p.lr = self.ach_level

    def hippocampal_gate(self, encoding_mode: bool):
        # High ACh: strong feedforward, weak recurrent (encoding)
        # Low ACh: weak feedforward, strong recurrent (recall)
        self.ach_level = 0.8 if encoding_mode else 0.2
```

**3C. Norepinephrine System (Locus Coeruleus → whole brain):**
```python
class NorepinephrineSystem:
    """
    NE = gain (sharpness) of neural responses.
    High NE: winner-take-all, selective, vigilant
    Low NE: graded, exploratory
    """
    def __init__(self):
        self.ne_level = 0.5  # 0.0–1.0

    def set_gain(self, population: LIFPopulation):
        # NE shifts the sigmoid input-output curve
        # High NE = steeper sigmoid = more nonlinear
        gain = 0.5 + 2.0 * self.ne_level
        population.v_thresh_effective = (
            population.p.v_thresh * (1 - 0.3 * self.ne_level)
        )
```

**3D. Serotonin System (Dorsal Raphe → prefrontal, limbic):**
```python
class SerotoninSystem:
    """
    5-HT = temporal discounting and impulse control.
    High 5-HT: patient, long time horizon
    Low 5-HT: impulsive, short horizon
    """
    def __init__(self):
        self.serotonin_level = 0.5

    def discount_factor(self) -> float:
        return 0.7 + 0.3 * self.serotonin_level  # [0.7, 1.0]
```

**3E. Neuromodulator Interaction Matrix:**
```
           ACh    DA    NE    5-HT
Encoding:  HIGH   -     MED   -
Reward:    MED    HIGH  HIGH  -
Novelty:   HIGH   MED   HIGH  -
Sleep:     LOW    -     LOW   HIGH
Stress:    LOW    -     HIGH  LOW
```

**Deliverables:** `neuromodulators/dopamine.py`, `neuromodulators/acetylcholine.py`, `neuromodulators/norepinephrine.py`, `neuromodulators/serotonin.py`, `neuromodulators/system.py`

---

### Sprint 4 — Cortical Architecture (Week 9–10)

**Goal:** Implement 6-layer laminar structure, cortical columns, thalamo-cortical loops, and basal ganglia.

**4A. Laminar Cortical Column:**
```python
class CorticalColumn:
    """
    One hypercolumn: ~10,000 neurons (scaled), 6 layers.
    Internal wiring follows the canonical cortical microcircuit.
    """
    LAYER_FRACTIONS = {
        "L1": 0.02,   # axons/dendrites only — represented as input zone
        "L23": 0.30,  # associative, lateral connections
        "L4":  0.25,  # receives thalamic input
        "L5":  0.25,  # output layer (subcortex, other areas)
        "L6":  0.18,  # thalamo-cortical feedback
    }

    def __init__(self, n_total, column_id):
        self.layers = {}
        for name, frac in self.LAYER_FRACTIONS.items():
            n = max(10, int(n_total * frac))
            self.layers[name] = CorticalLayer(n, column_id, name)

        self._wire_canonical_circuit()

    def _wire_canonical_circuit(self):
        # Thalamus → L4 (direct feedforward)
        # L4 → L23 (within-column feedforward)
        # L23 → L5 (output preparation)
        # L5 → subcortex/other areas
        # L6 → thalamus (feedback control)
        # L23 ↔ L23 (lateral: columns exchange via association fibres)
        # PV interneurons in L23: E → PV → E (gamma generation)
        pass
```

**4B. Thalamo-Cortical Loop:**
```python
class ThalamusRegion(BrainRegion):
    """
    Relay and gating.
    - Specific thalamus (LGN, MGN): relay sensory to L4
    - Non-specific thalamus (Pulvinar, MD): broadcast attention to L1
    - Reticular nucleus (TRN): inhibitory wrapper, gating
    """
    def __init__(self, n=15_000):
        super().__init__("thalamus", n)
        self.trn = LIFPopulation(n // 4, LIFParams(), name="TRN")
        # TRN creates alpha rhythm via thalamo-reticular oscillation
```

**4C. Basal Ganglia (Action Selection):**
```python
class BasalGanglia:
    """
    Implements action selection via direct/indirect pathway.
    Direct path (Go):  D1 → SNr/GPi inhibition → release thalamus
    Indirect path (NoGo): D2 → GPe → STN → SNr/GPi → suppress thalamus
    Dopamine D1 activation promotes action, D2 inhibits.
    """
    def __init__(self, n_striatum=50_000, n_actions=100):
        self.striatum_d1 = LIFPopulation(n_striatum // 2)  # Go
        self.striatum_d2 = LIFPopulation(n_striatum // 2)  # NoGo
        self.n_actions   = n_actions

    def select_action(self, cortical_input, da_level) -> int:
        # Competition via lateral inhibition + dopamine gating
        # D1 activated by DA → go
        # D2 suppressed by DA → reduce NoGo
        pass
```

**Deliverables:** `regions/cortical_column.py`, `regions/thalamus.py`, `regions/basal_ganglia.py`, `regions/cortical_area.py`

---

### Sprint 5 — Hippocampal Memory System (Week 11–12)

**Goal:** Implement a biologically accurate hippocampal memory system with pattern separation (DG), associative completion (CA3), output gating (CA1), and cortical interfacing (EC).

**5A. Hippocampal Circuit:**
```python
class Hippocampus:
    """
    Full hippocampal circuit implementing episodic memory.

    Information flow (encoding):
      Cortex → EC_L2 → DG → CA3 → CA1 → EC_L5 → Cortex
                            ↑
              EC_L2 → CA3 (direct Schaffer collateral bypass)

    CA3 recurrent connections: pattern completion attractor
    DG→CA3 mossy fibres: detonator synapses (strong, force new patterns)
    """
    def __init__(self, scale=0.01):
        sc = int
        self.ec_l2  = LIFPopulation(sc(28_000 * scale), name="EC_L2")
        self.dg     = LIFPopulation(sc(1_200_000 * scale), name="DG")  # largest subfield
        self.ca3    = LIFPopulation(sc(330_000 * scale), name="CA3")
        self.ca1    = LIFPopulation(sc(430_000 * scale), name="CA1")
        self.ec_l5  = LIFPopulation(sc(28_000 * scale), name="EC_L5")

        # CA3 recurrent (pattern completion)
        self.ca3_recurrent = SparseSTDPSynapse(
            self.ca3.n, self.ca3.n, p=0.04,
            params=STDPParams(A_plus=0.02, A_minus=0.015),  # slightly LTP-biased
            name="CA3_recurrent"
        )

        # DG→CA3 mossy fibres (detonators — very strong, sparse, no STDP)
        self.mossy = SparseSynapse(
            self.dg.n, self.ca3.n, p=0.005, weight=5.0,
            name="mossy_fibres"
        )

    def encode(self, ec_pattern: np.ndarray):
        """One-shot encoding via high ACh state."""
        pass

    def recall(self, partial_cue: np.ndarray) -> np.ndarray:
        """Pattern completion via CA3 recurrent dynamics."""
        pass

    def replay(self) -> list[np.ndarray]:
        """
        Sharp-wave ripple replay during rest/sleep.
        Replays stored sequences in compressed form.
        Used for cortical consolidation.
        """
        pass
```

**5B. Sleep Consolidation Cycle:**
```python
class SleepCycle:
    """
    Implements slow-wave sleep (SWS) consolidation.
    During SWS: hippocampus replays → cortex receives and consolidates.
    Biologically: ~1.0–1.5 Hz slow oscillation, hippocampal SPW-Rs.
    """
    SLOW_WAVE_FREQ = 1.0    # Hz
    SPINDLE_FREQ   = 12.0   # Hz (sleep spindles — thalamo-cortical)
    RIPPLE_FREQ    = 100.0  # Hz (hippocampal sharp-wave ripples)

    def run_consolidation_epoch(
        self, hippocampus: Hippocampus,
        cortex: CorticalArea, duration_s: float = 60.0
    ):
        # Simulate SWS consolidation
        pass
```

**Deliverables:** `regions/hippocampus.py`, `memory/episodic.py`, `memory/consolidation.py`, `memory/pattern_separation.py`

---

### Sprint 6 — Oscillations and Temporal Coding (Week 13–14)

**Goal:** Implement oscillatory rhythms as emergent properties of E/I balance, and theta-gamma coupling as the basis for sequential information encoding.

**6A. Gamma Oscillation (Pyramidal-Interneuron Network Gamma — PING):**
```
Mechanism: Excitatory burst → PV interneurons fire → blanket inhibition → 
excitatory neurons recover → next gamma cycle begins.
Frequency determined by: inhibitory time constant (~10 ms → ~40 Hz).

Brian2 implementation:
  E-pop: AMPA → PV, receives external drive
  PV-pop: GABA_A (fast, tau=6ms) → E-pop
  Result: ~40 Hz oscillation emerges WITHOUT explicit oscillator.
```

**6B. Theta Oscillation:**
```python
class SeptalThetaPacemaker:
    """
    The medial septum provides theta input to hippocampus.
    Two populations: cholinergic (ACh) and GABAergic (GABA).
    Their mutual inhibition + rebound excitation generates ~7 Hz.
    """
    def __init__(self, target_freq_hz=7.0):
        self.period_ms = 1000.0 / target_freq_hz   # ~143 ms
        self.phase     = 0.0
        self.ach_level = 0.5

    def get_drive(self, t_ms: float) -> float:
        phase = (t_ms % self.period_ms) / self.period_ms
        return np.sin(2 * np.pi * phase) * self.ach_level
```

**6C. Theta-Gamma Coupling (Sequence Encoding):**
```python
class ThetaGammaCoupler:
    """
    Implements the Lisman-Idiart model of working memory.
    Each theta cycle (~125 ms) contains ~5 gamma sub-cycles (~25 ms each).
    Each gamma sub-cycle holds one 'item' in the sequence.
    """
    THETA_PERIOD_MS = 125.0   # 8 Hz
    GAMMA_PERIOD_MS = 25.0    # 40 Hz
    ITEMS_PER_THETA = 5       # gamma cycles per theta = capacity

    def assign_item_to_slot(self, item_id: int, slot: int):
        """
        Items are encoded by firing preferentially in one gamma slot.
        Slot order = sequential order in working memory.
        """
        phase_offset = slot * self.GAMMA_PERIOD_MS
        return phase_offset

    def decode_sequence(self, spike_trains: dict) -> list:
        """
        Read out item order from spike phases within theta.
        """
        pass
```

**6D. Axonal Conduction Delays:**
```python
# All inter-area synapses now have realistic delays
DELAYS = {
    ("sensory",    "feature"):       2.0,   # ms (adjacent cortex)
    ("feature",    "association"):   5.0,   # ms
    ("association","predictive"):    8.0,   # ms (longer-range)
    ("predictive", "association"):   8.0,   # ms (feedback)
    ("association","hippocampus"):  10.0,   # ms
    ("hippocampus","association"):  10.0,   # ms
    ("brainstem",  "thalamus"):      5.0,   # ms
    ("thalamus",   "sensory"):       3.0,   # ms
}
# In Brian2: syn.delay = "2*ms + rand()*1*ms"  (with jitter)
```

**Deliverables:** `oscillations/gamma.py`, `oscillations/theta.py`, `oscillations/coupling.py`, `regions/septum.py`

---

### Sprint 7 — Language and Concept Emergence (Week 15–17)

**Goal:** Build the pathway from stable spike attractors to proto-language. No transformer, no external LLM. All emergent.

**7A. Cell Assembly Detector:**
```python
class CellAssembly:
    """
    Detects and tracks stable attractor states in association cortex.
    A cell assembly = group of neurons that fire together reliably.
    Detected by: correlation of spike trains across time.
    """
    def __init__(self, population: LIFPopulation, threshold=0.7):
        self.population = population
        self.assemblies: list[set[int]] = []  # neuron index sets
        self.assembly_activations: dict[int, list[float]] = {}

    def detect_assemblies(self, spike_history: np.ndarray, window_ms=100.0):
        """
        Use Pearson correlation of spike trains to find correlated groups.
        Groups with mean pairwise correlation > threshold = assembly.
        """
        pass

    def get_active_assembly(self, current_spikes: np.ndarray) -> int:
        """Which assembly is currently activated? Returns assembly ID."""
        pass
```

**7B. Sequential Attractor Chaining:**
```python
class AttractorChainer:
    """
    Learns temporal sequences of cell assemblies via STDP.
    If assembly A is consistently followed by assembly B:
      → Forward synapses A→B strengthen (temporal order coding)
    Implements 'neural syntax': chains of concept activations.
    """
    def record_transition(self, from_assembly: int, to_assembly: int, dt_ms: float):
        """Record that from_assembly was followed by to_assembly after dt_ms."""
        pass

    def predict_next(self, current_assembly: int) -> list[tuple[int, float]]:
        """Return (assembly_id, probability) for next likely assemblies."""
        pass
```

**7C. Phonological Buffer (Speech-Motor Interface):**
```python
class PhonologicalBuffer:
    """
    Maps concept assembly activations to motor output sequences.
    Analogous to Broca's area (Brodmann area 44/45).
    Output: sequence of motor commands that could drive vocoder/TTS.
    Not trained — emerges from contiguity learning between
    concept assemblies and motor cortex co-activations.
    """
    def __init__(self, n_concepts: int, n_phonemes: int = 44):
        # Random initial mapping; learn via Hebbian pairing
        self.concept_to_phoneme = np.zeros((n_concepts, n_phonemes))

    def speak(self, assembly_sequence: list[int]) -> list[str]:
        """Convert assembly sequence to phoneme sequence."""
        pass
```

**7D. Text Input Encoding (No Tokenizer):**
```python
class CharacterEncoder:
    """
    Converts raw text to sensory spike patterns.
    Each character maps to a spatial pattern of sensory neuron activations.
    Similar letters (a/e, b/d) have overlapping patterns (perceptual similarity).
    """
    def encode_character(self, char: str, sensory_cortex: SensoryCortex):
        ascii_val = ord(char.lower())
        # Generate spatial pattern based on ASCII value
        # Adjacent characters → overlapping neuron populations
        pattern = self._ascii_to_cortical_pattern(ascii_val)
        sensory_cortex.stimulate("vision", pattern)
```

**Deliverables:** `cognition/cell_assemblies.py`, `cognition/sequence_learning.py`, `cognition/phonological_buffer.py`, `cognition/encoder.py`, `cognition/decoder.py`

---

### Sprint 8 — Full Predictive Coding (Week 18–19)

**Goal:** Replace the scalar prediction error with a full hierarchical predictive coding implementation.

**8A. Predictive Coding Layer:**
```python
class PredictiveCodingLayer:
    """
    Implements Rao-Ballard hierarchical predictive coding.
    Each cortical area maintains:
      - r: representation (current best estimate of input)
      - e: prediction error (actual - predicted)
    Feedforward: error signals (from L2/3 superficial pyramidals)
    Feedback: predictions (from L5/L6 deep pyramidals)
    Learning: STDP on error signal, gated by precision (ACh/NE)
    """
    def __init__(self, n_neurons, level, name):
        self.n = n_neurons
        self.level = level  # 1=primary sensory, ... N=highest
        self.representation = np.zeros(n_neurons, dtype=np.float32)
        self.prediction_in  = np.zeros(n_neurons, dtype=np.float32)
        self.error          = np.zeros(n_neurons, dtype=np.float32)
        self.precision      = 1.0   # controlled by NE level

    def compute_error(self, sensory_input: np.ndarray):
        self.error = sensory_input - self.prediction_in
        return self.error

    def generate_prediction(self) -> np.ndarray:
        """
        Generate prediction for the layer below.
        Implemented as top-down synapse propagation.
        """
        return self.prediction_down_synapse.propagate(
            np.where(self.representation > 0)[0]
        )

    def update_representation(self, error: np.ndarray, dt: float):
        """Gradient descent on free energy (variational inference)."""
        self.representation += dt * (
            self.precision * error
            - self.representation / self.tau_r
        )
```

**8B. Free Energy Minimisation:**
```python
class FreeEnergyMinimiser:
    """
    Implements Karl Friston's Free Energy Principle.
    Brain minimises F = complexity - accuracy
      = KL(posterior || prior) - log P(observations | model)
    In neural terms: minimise (prediction error)² weighted by precision.
    """
    def compute_free_energy(self, layers: list[PredictiveCodingLayer]) -> float:
        total_fe = 0.0
        for layer in layers:
            error_energy = 0.5 * layer.precision * np.sum(layer.error ** 2)
            complexity   = 0.5 * np.sum(layer.representation ** 2)  # L2 prior
            total_fe += error_energy + complexity
        return total_fe
```

**Deliverables:** `cognition/predictive_coding.py`, `cognition/free_energy.py`, `cognition/precision.py`

---

### Sprint 9 — Safety Kernel v2 + Motor System (Week 20)

**Goal:** Upgrade the ReflexArc with graded safety levels, integrate with basal ganglia for action selection, and add a proper motor cortex.

**9A. Motor Cortex:**
```python
class MotorCortex(CorticalRegion):
    """
    M1: Primary motor cortex. Layer 5 Betz cells project directly to spinal cord.
    Implements forward model: given desired state → compute motor commands.
    """
    def __init__(self, n=30_000, n_actuators=6):
        super().__init__(n, "motor_cortex")
        self.n_actuators = n_actuators
        # Somatotopic organisation: each actuator maps to a column
        self.actuator_columns = [
            CorticalColumn(n // n_actuators, f"motor_{i}")
            for i in range(n_actuators)
        ]
```

**9B. Enhanced Safety Kernel:**
```python
class ReflexArcV2:
    """
    Three-tier safety hierarchy:
    Tier 1 — HARD GATES (never bypassed):
      force > 10N, angle > 170°, vel > 2m/s
    Tier 2 — SOFT GATES (overridable by high-level command):
      force > 5N, angle > 120°, vel > 1m/s
    Tier 3 — ADVISORY (warnings only):
      force > 2N, angle > 90°

    Reflex arc neurons fire with intensity proportional to violation severity.
    Tier 1 violations cause instant motor inhibition via GABA burst.
    """
    HARD_FORCE  = 10.0
    SOFT_FORCE  =  5.0
    HARD_ANGLE  = 170.0
    SOFT_ANGLE  = 120.0
    HARD_VEL    =  2.0
    SOFT_VEL    =  1.0

    def check(self, cmd: dict, override_level: int = 0) -> dict:
        violations = self._classify_violations(cmd)
        tier1 = [v for v in violations if v["tier"] == 1]
        if tier1:
            return {"approved": False, "tier": 1,
                    "reason": "; ".join(v["msg"] for v in tier1),
                    "command": self._withdrawal()}
        # Tier 2 can be overridden by authorised high-level command
        tier2 = [v for v in violations if v["tier"] == 2]
        if tier2 and override_level < 2:
            return {"approved": False, "tier": 2, ...}
        return {"approved": True, "command": cmd}
```

---

### Sprint 10 — Full System Integration (Week 21–24)

**Goal:** Integrate all sprints, implement the background simulation loop at scale, REST/WebSocket API, and the React UI.

**10A. Unified Brain Assembly v2:**
```python
class BRAIN2.0BrainV2:
    def __init__(self, scale=0.01):
        # Sensory pathway
        self.thalamus   = ThalamusRegion(scale)
        self.sensory    = SensoryCortex(scale)   # laminar
        self.feature    = FeatureArea(scale)      # V2/A2 equivalent

        # Cortical hierarchy
        self.association = AssociationArea(scale) # laminar, columns
        self.predictive  = PredictiveCodingHierarchy(scale, levels=4)
        self.concept     = ConceptLayer(scale)    # WTA + assemblies
        self.meta        = PrefrontalCortex(scale) # L1 top-down

        # Memory
        self.hippocampus = Hippocampus(scale)
        self.working_mem = WorkingMemoryBuffer(scale)  # thalamo-cortical

        # Subcortical
        self.basal_ganglia = BasalGanglia(scale)
        self.cerebellum    = Cerebellum(scale)
        self.brainstem     = Brainstem(scale)
        self.septum        = SeptalThetaPacemaker()

        # Motor
        self.motor_cortex  = MotorCortex(scale)
        self.reflex        = ReflexArcV2()

        # Neuromodulators
        self.da  = DopamineSystem()
        self.ach = AcetylcholineSystem()
        self.ne  = NorepinephrineSystem()
        self.ht  = SerotoninSystem()

        # Cognition
        self.assemblies  = CellAssemblyDetector(self.association)
        self.seq_learner = AttractorChainer()
        self.free_energy = FreeEnergyMinimiser()
```

**10B. Simulation Loop (per timestep, dt=0.1ms):**
```
1.  Theta pacemaker → phase signal → hippocampus, cortex
2.  Sensory input → thalamus (Poisson encode)
3.  Thalamus → L4 (with conduction delays)
4.  L4 → L2/3 (intra-column feedforward)
5.  E → PV → E  (PING gamma generation within each area)
6.  Compute prediction errors (actual - predicted) in each PC layer
7.  Feedforward: error signals L2/3 → higher areas
8.  Feedback: predictions deep layers → lower L1
9.  Update neuromodulator levels (DA, ACh, NE, 5-HT)
10. Apply neuromodulator effects to synaptic parameters
11. STDP updates on all plastic synapses (event-driven)
12. BCM threshold update (very slow)
13. Homeostatic scaling update (very slow)
14. Hippocampus: encode current representation (if ACh high)
15. Basal ganglia: action selection
16. Motor cortex → ReflexArc → actuator
17. Cell assembly detection update
18. Sequence learning update
19. Compute free energy
20. Monitoring: log spikes, weights, modulator levels
```

---

## 6. Technical Reference Tables

### Neuron Parameters

| Type | tau_m (ms) | tau_ref (ms) | v_thresh (mV) | v_reset (mV) | Transmitter |
|------|-----------|-------------|--------------|-------------|------------|
| Pyramidal | 20 | 2 | -55 | -70 | Glutamate |
| PV interneuron | 10 | 1 | -47 | -60 | GABA |
| SST interneuron | 25 | 2 | -50 | -70 | GABA |
| VIP interneuron | 20 | 2 | -52 | -70 | GABA |
| CA3 pyramidal | 25 | 3 | -55 | -70 | Glutamate |
| Purkinje cell | 15 | 1.5 | -52 | -65 | GABA |
| Thalamic relay | 20 | 2 | -55 | -70 | Glutamate |

### Synapse Parameters

| Type | tau (ms) | Delay (ms) | E_rev (mV) | Plasticity |
|------|----------|-----------|-----------|-----------|
| AMPA | 5 | 0.5–2 | 0 | STDP |
| NMDA | 100 | 0.5–2 | 0 | STDP + voltage gate |
| GABA_A | 6 | 0.5–1 | -70 | None |
| GABA_B | 150 | 1–2 | -90 | None |
| Mossy fibre | 5 | 2–5 | 0 | None (detonator) |

### Connection Probabilities

| From | To | p | Weight | Plasticity |
|------|----|---|--------|-----------|
| Exc (L4) | Exc (L23) | 0.3 | 0.5 | STDP |
| Exc (L23) | Exc (L5) | 0.2 | 0.5 | STDP |
| Exc | PV (same) | 0.5 | 1.0 | Fixed |
| PV | Exc (same) | 0.5 | 2.0 | Fixed |
| Exc | SST | 0.3 | 0.5 | Fixed |
| SST | Exc (dist) | 0.4 | 1.5 | Fixed |
| VIP | SST | 0.5 | 1.5 | Fixed |
| L23→L23 (lateral) | — | 0.05 | 0.3 | STDP |
| CA3 recurrent | — | 0.04 | 0.8 | STDP |
| DG → CA3 (mossy) | — | 0.005 | 5.0 | None |

---

## 7. File & Module Architecture

```
BRAIN2.0/
├── README.md                        ← this document summary
├── requirements.txt
├── environment.yml                  ← Brian2 + NumPy + FastAPI conda env
├── config.py                        ← SCALE, DT, SEED, hardware flags
│
├── neurons/
│   ├── __init__.py
│   ├── lif.py                       ← Base LIF model (Brian2 NeuronGroup)
│   ├── pyramidal.py                 ← Pyramidal neuron (AMPA + NMDA)
│   ├── interneurons.py              ← PV, SST, VIP classes
│   └── encoders.py                  ← Poisson, Rate, Character encoders
│
├── synapses/
│   ├── __init__.py
│   ├── ampa.py                      ← AMPA synapse
│   ├── nmda.py                      ← NMDA with Mg2+ gating
│   ├── gaba.py                      ← GABA_A and GABA_B
│   ├── stdp_triplet.py              ← Pfister-Gerstner triplet STDP
│   ├── stp.py                       ← Short-term plasticity (Tsodyks-Markram)
│   ├── bcm.py                       ← BCM sliding threshold
│   └── homeostatic.py               ← Synaptic scaling
│
├── regions/
│   ├── __init__.py
│   ├── base.py                      ← BrainRegion abstract class
│   ├── cortical_layer.py            ← Single laminar layer
│   ├── cortical_column.py           ← 6-layer hypercolumn
│   ├── cortical_area.py             ← Area = many columns + inter-column synapses
│   ├── sensory_cortex.py            ← Multimodal sensory (columns by modality)
│   ├── association_area.py          ← 500k column assembly
│   ├── prefrontal.py                ← PFC: working memory + meta-control
│   ├── thalamus.py                  ← Relay + TRN
│   ├── basal_ganglia.py             ← Direct/indirect path + dopamine gating
│   ├── motor_cortex.py              ← M1: somatotopic columns
│   ├── cerebellum.py                ← Granule + Purkinje + error learning
│   ├── brainstem.py                 ← Homeostatic + arousal
│   └── reflex_arc.py                ← Safety kernel v2 (3-tier)
│
├── neuromodulators/
│   ├── __init__.py
│   ├── dopamine.py                  ← VTA/SNc + TD learning
│   ├── acetylcholine.py             ← BF + learning rate gating
│   ├── norepinephrine.py            ← LC + gain control
│   ├── serotonin.py                 ← DR + discount factor
│   └── system.py                   ← NM interaction manager
│
├── memory/
│   ├── __init__.py
│   ├── hippocampus.py               ← DG + CA3 + CA1 + EC
│   ├── working_memory.py            ← Thalamo-cortical buffer (NMDA)
│   ├── episodic.py                  ← Encoding / recall interface
│   └── consolidation.py             ← Sleep replay + cortical transfer
│
├── oscillations/
│   ├── __init__.py
│   ├── gamma.py                     ← PING gamma (emergent from E-I)
│   ├── theta.py                     ← Septal pacemaker
│   ├── coupling.py                  ← Theta-gamma sequence encoder
│   └── alpha.py                     ← Thalamic alpha gating
│
├── cognition/
│   ├── __init__.py
│   ├── cell_assemblies.py           ← Assembly detection + tracking
│   ├── sequence_learning.py         ← Attractor chain learning
│   ├── predictive_coding.py         ← Hierarchical PC layers
│   ├── free_energy.py               ← FE minimisation
│   ├── concept_layer.py             ← WTA + assembly readout
│   ├── phonological_buffer.py       ← Concept → motor sequence
│   └── language_decoder.py         ← Assembly sequence → text output
│
├── brain.py                         ← BRAIN2.0BrainV2: assembly + sim loop
├── api.py                           ← FastAPI + WebSocket
└── tests/
    ├── test_neurons.py
    ├── test_synapses.py
    ├── test_oscillations.py
    ├── test_memory.py
    └── test_full_brain.py
```

---

## 8. Research Milestones & Evaluation Criteria

### Milestone 1 (Sprint 1–2): E/I Balance & Realistic Neuron Models
- **Test:** A single cortical region (AssociationArea) spontaneously exhibits 20–80 Hz irregular spiking at 2–5% sparsity with no external drive.
- **Test:** STDP converges to bimodal weight distribution (not unimodal).
- **Metric:** Coefficient of variation (CV) of inter-spike intervals > 0.7 (irregular, like real cortex vs. <0.2 for regular clock-like oscillation).

### Milestone 2 (Sprint 3): Neuromodulation Working
- **Test:** High ACh → increased STDP learning rate measurable in weight convergence speed.
- **Test:** Dopamine reward signal causes selective potentiation of synapses active during reward window.
- **Test:** NE burst sharpens population response (increased sparsity, lower CV).

### Milestone 3 (Sprint 4–5): Memory Formation
- **Test:** Present pattern X 10 times → present partial X → CA3 completes to full X with >70% neuron overlap.
- **Test:** Present pattern X, wait, present Y, wait → replay during "rest" recovers both X and Y in order.
- **Metric:** Pattern overlap (Jaccard similarity) between recalled vs. original pattern > 0.6.

### Milestone 4 (Sprint 6): Oscillations Emerge
- **Test:** Power spectrum of association cortex shows a peak at 35–45 Hz (gamma) without explicit oscillator.
- **Test:** Hippocampal recording shows 6–8 Hz modulation of gamma amplitude (theta-gamma coupling).
- **Metric:** PAC (phase-amplitude coupling) measure > 0.1 between theta phase and gamma amplitude.

### Milestone 5 (Sprint 7): Proto-Language Emergence
- **Test:** Present text "cat" 100 times → detect stable cell assembly in association cortex.
- **Test:** Present "cat" + "sat" repeatedly → assembly for "cat" activates before assembly for "sat" (sequential chaining).
- **Test:** New partial input "c_t" → completion to full "cat" assembly via CA3.
- **Metric:** Assembly activation stability (cosine similarity of population vectors across trials) > 0.8.

### Milestone 6 (Sprint 10): Full Brain Coherence
- **Test:** System runs at SCALE=0.01 for 1 simulated hour (3.6M steps at dt=1ms) without runaway excitation or complete quiescence.
- **Test:** Free energy decreases over time as system learns to predict input statistics.
- **Test:** Novel input generates higher prediction error and higher NE response than familiar input.
- **Metric:** Resting-state mean firing rate per neuron: 1–10 Hz. Sparsity: 2–8% active at any time.

### Final Evaluation Criteria for "Brain-Like" Status

| Criterion | Required Level | How to Measure |
|-----------|---------------|----------------|
| E/I balance stability | No runaway for >1M steps | Max firing rate monitor |
| STDP convergence | Bimodal weight dist. | Weight histogram |
| Oscillation | Gamma peak 35–45 Hz | Welch power spectrum |
| Memory | Pattern completion >60% | Jaccard similarity |
| Prediction | FE decreases over 10k steps | Free energy time series |
| Concept stability | Cell assembly cosine >0.8 | Assembly tracker |
| Sequence learning | Transition prob >0.6 | Attractor chain accuracy |
| Language emergence | Top-1 next-assembly pred. >50% | Sequence completion test |

---

## Appendix: Why Not Just Use Brian2 From the Start?

The current NumPy implementation was a valid first step for architectural scaffolding. However, Brian2 is the correct engine for all Sprint 1+ work because:

1. Brian2 implements exact ODE solvers — no Euler integration errors that cause voltage drift.
2. Brian2's event-driven STDP is optimised and correct — pair, triplet, and voltage-based rules all supported.
3. Brian2 supports runtime-generated C++ code via Cython — 10–100× faster than NumPy loops.
4. Brian2's Network object handles all the step ordering, ensuring causal correctness.
5. For SCALE > 0.1, Brian2 with the CPP standalone device target is the only way to stay in real-time on a single CPU.

For SCALE = 1.0 (full BRAIN2.0 target: ~858k neurons), the target platforms are Intel Lava framework (Loihi 2 chip) or GPU-accelerated Brian2 (brian2cuda). These are direct drop-in replacements once the Brian2 equations are correctly written.

---

*Document generated: April 2026*  
*Based on: BRAIN2.0 v1 codebase analysis + neuroscience literature review (Nature Neuroscience 2024, NIH BRAIN NeuroAI Workshop 2024, SpikeGPT/BrainTransformers/NSLLM 2024–2025)*
