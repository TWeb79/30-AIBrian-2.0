# BRAIN 2.0 — Assessment 0049
**Date:** April 2026  
**Scope:** Full codebase audit — post-v0.2 + API refactor  
**Baseline:** statusanalysis.md (2026-04-02) + ASSESSMENT1750.md

---

## Δ Changes Since statusanalysis.md

| Area | Change | Impact |
|------|--------|--------|
| API | Monolithic `api/main.py` → split into `api/routes/` (9 files) + `api/config.py` + `api/models.py` + `api/helpers.py` | +maintainability, -latency from import chains |
| API | All 19+5 bugs from ASSESSMENT1750 confirmed fixed | Stable baseline |
| Brain loop | `brain/continuous_loop.py` now calls `continuous_loop.start()` internally, confirmed | Fixed FIX-003 |
| Phonological buffer | `observe_pairing()` returns `is_new` bool correctly | Fixed FIX-006/B |
| Persistence | Vocabulary export uses correct `w2a` key | Fixed FIX-C |
| Response cache | Threshold 0.82, LLM responses excluded from cache | Fixed FIX-008 |
| Proactive | LLM generates real thoughts via Ollama | Fixed FIX-010 |

**Net: v0.2 REMEMBERS is complete. Brain is in production state. Biological fidelity: ~14%.**

---

## Current Subsystem Scores (revised)

| Subsystem | Prior | Current | Notes |
|-----------|-------|---------|-------|
| Neural Substrate | 25% | 25% | Unchanged — no new neuron types |
| Brain Regions | 35% | 36% | Minor: continuous loop improvements |
| Memory | 35% | 38% | EpisodeStore working, prune_weakest confirmed |
| Emotional/Drives | 65% | 65% | Biases computed, still not wired to SNN |
| Language/Codec | 72% | 74% | API refactor improves testability |
| Oscillations | 0% | 0% | Still entirely absent |
| API/Frontend | 92% | 95% | Route split, helpers extracted |
| Persistence | 90% | 90% | Stable |

**Weighted total: ~52%** of defined scope. Full roadmap: ~28%.

---

## Top 10 Next Changes

Priority ordered by: (1) blocking downstream v0.3/v0.4 features, (2) correctness of existing wiring, (3) leverage — changes that enable multiple future features.

---

### #1 — Wire neuromodulator biases into STDP gain [CRITICAL — blocks v0.3]

`AffectiveState.as_neuromodulator_biases()` computes four floats. Nothing consumes them.  
`DriveSystem.behavioural_modifiers()` returns `association_gain` and `predictive_gain`. Neither reaches a synapse.

**Status:** ✅ FIXED - Implemented in `brain/__init__.py`:
- After `affect.assess()`, now extracts neuromodulator biases and drive modifiers
- Computes `stdp_gain = gain * ne_gain * da_gain * drive_mods["association_gain"]`
- `step()` now accepts `stdp_gain` parameter and applies it to all STDP updates
- The SNN learning is now emotionally modulated

**Files:** `brain/__init__.py` (process_input_v01, step), `brain/synapses/stdp_synapses.py` (STDPParams.lr already exists).  
**Effort:** ~2h. **Unlocks:** v0.3 FEELS milestone.

---

### #2 — Add E/I neuron type separation [HIGH — biological fidelity +8%]

All 10 regions use identical LIF params. ConceptLayer has one `InhibitorySynapse` for WTA but AssociationRegion, FeatureLayer, and PredictiveRegion have no inhibitory population.

**Fix:** Add `n_inh = int(n * 0.2)` inhibitory sub-population per region with:
- `tau_m=10ms` (PV-like fast spiking)
- `v_thresh=-47mV`
- No STDP on inhibitory synapses
- Fixed GABA-A connections: `Exc → PV (p=0.5, weight=1.0)`, `PV → Exc (p=0.5, weight=2.0, negative)`

Minimal change: add `InhibitorySynapse` within `AssociationRegion.__init__()` and apply `lateral_inhibit()` inside its `step()`. Extend to FeatureLayer and PredictiveRegion.

**Files:** `brain/regions/cortical_regions.py`.  
**Effort:** ~3h. **Unlocks:** emergent gamma oscillations (Sprint 6), realistic sparse coding.

---

### #3 — Implement real AttractorChainer in `cognition/` [HIGH — blocks v0.4 LLM bypass]

`CellAssemblyDetector` detects stable coalitions. Nothing learns *transitions* between them. The attractor chain is the prerequisite for `PhonologicalBuffer` generating multi-word sequences without LLM.

**Status:** ✅ FIXED - Implemented in `cognition/attractor_chainer.py`:
- Created `AttractorChainer` class with transition learning and prediction
- Wired into `brain/__init__.py` - records transitions between concept assemblies
- Integrated with `PhonologicalBuffer.generate()` - uses chainer for multi-word sequences
- Added persistence for attractor chainer state

**Files:** `cognition/attractor_chainer.py` (new), `brain/__init__.py`, `codec/phonological_buffer.py`.  
**Effort:** ~3h. **Unlocks:** multi-word local generation, rising LLM bypass rate.

---

### #4 — Build `tests/` suite [HIGH — zero coverage is a liability]

`tests/__init__.py` is a whitespace file. Every module has a `if __name__ == "__main__":` block but no pytest harness.

**Priority test targets:**

| Test | File | What to Assert |
|------|------|---------------|
| `test_lif_neurons.py` | `brain/neurons/lif_neurons.py` | Neuron fires at expected rate given constant current |
| `test_stdp.py` | `brain/synapses/stdp_synapses.py` | LTP when pre→post, LTD when post→pre |
| `test_reflex_arc.py` | `brain/regions/cortical_regions.py` | Force>10N returns approved=False |
| `test_phonological_buffer.py` | `codec/phonological_buffer.py` | `observe_pairing` + `generate` returns word |
| `test_response_cache.py` | `codec/response_cache.py` | Similar inputs hit cache above threshold |
| `test_brain_roundtrip.py` | `brain/__init__.py` | `process_input_v01("hello")` returns non-empty response |

**Files:** `tests/` directory (6 new files).  
**Effort:** ~4h. **Unlocks:** safe iteration, regression detection.

---

### #5 — Implement `AmygdalaRegion` in `emotion/` [MEDIUM — v0.3 emotional tagging]

SalienceFilter does text keyword scanning (slow path). The amygdala's role is fast emotional tagging of episodic memories and priority boosting for high-valence inputs. Currently `hippocampus.encode()` is called for `arousal > 0.5` but valence is stored, never used for retrieval prioritisation.

**Fix:**  
1. Create `emotion/amygdala.py` — a small LIF population (~2k neurons at scale=0.01) with direct input from SensoryCortex and direct output modulating hippocampal encoding threshold.  
2. Modify `hippocampus.recall()` to sort by `abs(valence)` as secondary key after Jaccard similarity.  
3. Add `amygdala_score` to proactive thought generation so idle thoughts prefer emotionally tagged episodes.

**Files:** `emotion/amygdala.py` (new), `memory/hippocampus_simple.py`, `brain/__init__.py`.  
**Effort:** ~3h.

---

### #6 — Fix rate-limit bypass regression in LLMGate [CORRECTNESS BUG]

`LLMGate.should_call_llm()` has a 1-second rate limit. In NEONATAL/JUVENILE stages it correctly always calls LLM — but it does NOT reset `_last_call_time` after the early-exit path. Result: the first call in a fast test loop hits the 1s rate limit on the *second* call, falls through to the stage check, and calls LLM anyway — but `_last_call_time` was never set, so the rate limit counter is wrong from that point.

**Fix in `codec/llm_gate.py`:**

```python
if stage in ("NEONATAL", "JUVENILE"):
    self._llm_calls += 1
    self._last_call_time = now   # ← this line is missing
    return GateDecision(should_call_llm=True, reason="early_stage_always_llm")
```

**Status:** ✅ FIXED - The fix is already present in the code (line 95). `self._last_call_time = now` is correctly set when in early stages.

**Files:** `codec/llm_gate.py` line ~75.  
**Effort:** 5 min. **Severity:** low impact in prod (Ollama timeout prevents hammering), high impact in test.

---

### #7 — Persist and restore `CellAssemblyDetector` state [CORRECTNESS]

`OSCENBrain.persist()` saves vocabulary and episodes but **does not save** `assembly_detector` state. After restart, all detected assemblies are lost — vocabulary is restored but the assembly→word links are broken because assembly IDs are regenerated from scratch.

**Status:** ✅ FIXED - Added assembly persistence in `brain/__init__.py`:
- `persist()` now saves `assembly_detector.export()` to `data/assemblies.json`
- `__init__()` loads assemblies from file and calls `assembly_detector.import_()`

**Files:** `brain/__init__.py`.  
**Effort:** 30 min. **Impact:** vocabulary survives restart cleanly.

---

### #8 — Upgrade PredictiveRegion to 3-level hierarchy [MEDIUM — v0.4 reasoning]

`PredictiveRegion.compute_error()` uses a scalar EMA of `assoc.activity_pct`. This produces a single `attention_gain` float — not a prediction of what will fire next.

**Minimal hierarchical upgrade (no Brian2 required):**

```python
class PredictiveHierarchy:
    def __init__(self, n, levels=3):
        self.levels = [LIFPopulation(n // (2**i)) for i in range(levels)]
        self.errors = [0.0] * levels
        self.predictions = [np.zeros(n // (2**i)) for i in range(levels)]

    def compute_errors(self, bottom_up: np.ndarray) -> float:
        # Each level predicts level below; error propagates up
        total_error = 0.0
        signal = bottom_up
        for i, lvl in enumerate(self.levels):
            pred = self.predictions[i][:len(signal)]
            err = np.mean(np.abs(signal[:len(pred)] - pred))
            self.errors[i] = err
            total_error += err * (0.5 ** i)  # higher levels weighted less
            self.predictions[i][:len(signal)] = (
                0.9 * self.predictions[i][:len(signal)] + 0.1 * signal[:len(pred)]
            )
            signal = self.levels[i].step(np.zeros(len(self.levels[i].v)))
        return 1.0 + 4.0 * min(total_error, 1.0)
```

**Files:** `brain/regions/cortical_regions.py`.  
**Effort:** ~4h. **Unlocks:** richer prediction error signal, more varied STDP gain.

---

### #9 — Add `SeptalThetaPacemaker` stub + phase-gated STDP [MEDIUM — Sprint 6 prerequisite]

Theta/gamma is 0% implemented. A minimal theta pacemaker (no Brian2 needed) would enable phase-gated STDP — STDP only fires during specific theta phase windows, which is the mechanism for sequence-order encoding.

**Minimal implementation:**

```python
# brain/oscillations/theta.py
class SeptalThetaPacemaker:
    THETA_PERIOD_MS = 125.0  # 8 Hz
    def __init__(self):
        self.phase = 0.0
    def tick(self, dt_ms: float) -> float:
        self.phase = (self.phase + dt_ms / self.THETA_PERIOD_MS) % 1.0
        return np.sin(2 * np.pi * self.phase)
    def is_encoding_window(self) -> bool:
        return 0.0 < self.phase < 0.5  # first half-cycle = encoding
```

Wire into `step()`: only call `update_stdp()` when `theta.is_encoding_window()` is True. This immediately gives temporally structured learning at zero additional biological complexity.

**Files:** `brain/oscillations/theta.py` (new), `brain/__init__.py`.  
**Effort:** ~2h. **Unlocks:** Sprint 6, theta-gamma coupling, sequence encoding.

---

### #10 — OpenAI/Anthropic backend completion in LLMCodec [LOW-MEDIUM — cloud fallback]

`_call_openai()` and `_call_anthropic()` both return `"[backend not configured]"` placeholder strings. This means the system has no cloud LLM fallback when Ollama is unavailable.

**Fix `_call_openai()`:**

```python
def _call_openai(self, prompt, model, state):
    import openai
    client = openai.OpenAI(api_key=self.config.openai_api_key,
                           base_url=self.config.openai_base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=self.config.max_tokens,
        temperature=self.config.temperature,
    )
    text = resp.choices[0].message.content.strip()
    cost = self._estimate_openai_cost(resp.usage, model)
    if self.cost_tracker:
        self.cost_tracker.track_call(resp.usage.prompt_tokens,
                                     resp.usage.completion_tokens, model)
    return CodecResult(text=text, path="llm", cost=cost, model=model, backend="openai")
```

Same pattern for Anthropic using `anthropic.Anthropic()`. Add `openai` and `anthropic` to `requirements.txt` as optional extras.

**Files:** `codec/llm_codec.py`, `requirements.txt`.  
**Effort:** ~2h.

---

## Sprint Mapping

| # | Change | v-target | Days |
|---|--------|----------|------|
| 1 | Wire neuromodulator biases to STDP | v0.3 | 0.5 |
| 2 | E/I neuron separation | v0.3 | 1 |
| 3 | AttractorChainer | v0.4 | 1 |
| 4 | Test suite (6 files) | infra | 1 |
| 5 | AmygdalaRegion | v0.3 | 1 |
| 6 | LLMGate rate-limit fix | hotfix | 0.1 |
| 7 | Persist CellAssemblyDetector | hotfix | 0.1 |
| 8 | 3-level PredictiveHierarchy | v0.4 | 1 |
| 9 | SeptalThetaPacemaker + phase-gated STDP | v0.4 | 0.5 |
| 10 | OpenAI/Anthropic backends | v1.0 | 0.5 |

**Recommended order:** 7 → 6 → 1 → 3 → 9 → 2 → 4 → 5 → 8 → 10

Start with the two hotfixes (7, 6) since they're trivial and fix silent data corruption. Then wire drives→STDP (1) to unlock measurable emotional behavior. Then AttractorChainer (3) + ThetaPacemaker (9) together since they both touch the step() loop and will drive LLM bypass rate upward. E/I balance (2) after theta since oscillations emerge from E/I dynamics.

---

## Estimated State After All 10

| Metric | Current | After top 10 |
|--------|---------|--------------|
| v0.3 FEELS completion | ~50% | ~85% |
| v0.4 REASONS completion | 5% | ~35% |
| Biological fidelity | ~14% | ~22% |
| LLM bypass rate (target at v1.0: 85%) | ~10% | ~25% |
| Test coverage | 0% | ~40% |
| Weighted subsystem score | ~52% | ~62% |