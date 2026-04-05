# Concept Neuron Spike Issue - Technical Assessment

## Executive Summary

During the "thinking loop" phase of the brain's processing pipeline, **zero concept neurons fire** despite:
- Proper seed neuron calculation and injection (150-160 neurons per request)
- Sufficient thinking steps (700-800 per request)
- Activity percentage showing 0% during simulation, then jumping to 10-20% at completion

This is a critical architectural issue because concept neurons are the bridge between sensory input and semantic memory formation. Without spikes, assembly creation fails, and the brain falls back to a hardcoded concept_id=0 for all word learning.

---

## Problem Analysis

### 1. The Symptom

**Observed Behavior:**
- Step 0-4: `concept_activity=0.00%, spikes=0`
- At completion: `concept_activity=10-20%, spikes=40-50`

This creates a paradox: activity appears at the end, but spikes are never captured during the loop.

### 2. The Seed Injection Mechanism

Current implementation in `brain/__init__.py`:

```python
magnitude = 20.0 * max(0.2, 1.0 - step_i / thinking_steps)
self.concept.population.inject_current(seed_concept_indices, magnitude)
```

**Problems:**
1. **Aggressive Decay**: Magnitude starts at 20.0 and decays to 0.2 over ~800 steps. The input is essentially gone by step 160.
2. **Single-Pulse Injection**: Each step injects a pulse, but LIF neurons need **sustained current** to integrate and fire. A decaying signal may never reach threshold.
3. **Bypassing Layer Hierarchy**: Direct injection into concept layer skips the natural signal propagation through sensory→feature→association→concept, which may be necessary for proper activation.

### 3. The Spike Collection Issue

```python
concept_spikes_during_think = set()
for step_i in range(thinking_steps):
    self.step(stdp_gain)
    if self.concept.last_spikes.size > 0:
        concept_spikes_during_think.update(self.concept.last_spikes.tolist())
```

**Potential Issues:**
- `last_spikes` may be getting **overwritten** each step instead of accumulating
- The `step()` method may need to **return** spikes rather than storing them in `last_spikes`
- Activity percentage might be calculated differently than spike counting

### 4. Layer Parameters

The concept layer uses Leaky Integrate-and-Fire (LIF) neurons. Check these parameters:
- **Threshold**: Is it too high relative to the injected current?
- **Membrane Time Constant (tau)**: Too high means slow integration
- **Reset Potential**: After spike, does it reset too far causing hyperpolarization?

---

## Architecture Context

### The Complete Processing Pipeline

```
1. Text Input
   ↓
2. Char Encoder → Sensory Layer
   ↓
3. Seed Calculation (md5 hash of words → concept indices)
   ↓
4. Thinking Loop (700-800 iterations):
   - Inject current into concept neurons
   - Run SNN step (sensory→feature→assoc→concept→predictive→meta→wm)
   - Collect concept spikes
   ↓
5. Assembly Detection (get_or_create_assembly)
   ↓
6. Word Learning (phon_buffer.observe_pairing with concept_id)
   ↓
7. Response Generation (local or LLM)
```

The problem occurs at step 4-5: even though step 4 runs, the spike collection is empty.

---

## Evidence from Logs

```
[DEBUG] Affect: arousal=0.50, valence=0.28, ach_multiplier=1.00, base_steps=798, final_steps=798
[DEBUG] Starting thinking loop: 798 steps, seed neurons: 159
[DEBUG] Step 0: concept_activity=0.00%, spikes=0
[DEBUG] Step 1: concept_activity=0.00%, spikes=0
[DEBUG] Step 2: concept_activity=0.00%, spikes=0
[DEBUG] Step 3: concept_activity=0.00%, spikes=0
[DEBUG] Step 4: concept_activity=0.00%, spikes=0
[DEBUG] Thinking complete: 46 unique neurons spiked, concept_activity=20.00%
```

Key observation: At "Thinking complete" we suddenly see spikes and activity. This suggests:
- Either spikes are being calculated **after** the loop
- Or the **last step** of the loop is the one that produces the activity

---

## Current Workaround

The code already has a fallback:

```python
learn_concept = concept_id if concept_id >= 0 else 0
for word in words:
    is_new = self.phon_buffer.observe_pairing(word, learn_concept)
```

This works because `observe_pairing()` only checks if the word exists in `self.word_index`. It doesn't validate that the concept assembly is real or meaningful.

**Downside**: All words from a chunk get associated with the **same** concept ID (0), instead of creating differentiated assemblies for different semantic contexts.

---

## Recommended Fixes (Priority Order)

### Priority 1: Fix Spike Collection
Verify that `concept_spikes_during_think` is actually capturing spikes during the loop. Add debug at each step to see if spikes appear at any point.

### Priority 2: Remove Decay
```python
# Before
magnitude = 20.0 * max(0.2, 1.0 - step_i / thinking_steps)

# After
magnitude = 20.0  # Constant injection
```

### Priority 3: Increase Magnitude
If constant magnitude doesn't work, try higher values:
```python
magnitude = 50.0  # or 100.0
```

### Priority 4: Add More Steps
Increase thinking steps significantly to give neurons more time to integrate.

### Priority 5: Check LIF Parameters
Review concept neuron parameters in the neural population configuration.

---

## Impact Assessment

| Issue | Severity | Impact |
|-------|----------|--------|
| No concept spikes | **High** | Assembly creation fails |
| Fallback to concept 0 | **Medium** | All words learned with same semantic context |
| Words not differentiated | **Medium** | Reduced semantic precision in recall |

---

## Files to Review

1. `brain/__init__.py` - Lines 440-470 (thinking loop)
2. `cognition/cell_assemblies.py` - Assembly detection logic
3. `brain/regions/concept.py` - LIF neuron parameters
4. `synapses/` - Synaptic weights from association to concept