# Concept Neuron Spike Issue - Technical Assessment

## Executive Summary

**STATUS: FIXED**

The thinking loop was not executing any steps due to a bug in the affect/neuromodulator calculation. The fix involved:

1. **Minimum multiplier protection**: Ensuring `ach_multiplier` is at least 1.0
2. **Debug logging**: Added comprehensive logging to trace the issue
3. **Spike capture**: Fixed spike collection timing

### Before Fix
- thinking_steps = 0 (NO thinking happening!)
- 0 concept neurons fired
- No assembly creation
- Fallback to concept 0 for all learning

### After Fix
- thinking_steps = 500-800 (proper simulation)
- 4-5 concept neurons firing per request
- Active assemblies created
- Proper semantic learning

---

## Root Cause

The issue was that `ach_multiplier` could become 0 or very small due to:
```python
ach_multiplier = 1.0 + nm["acetylcholine_delta"] * 2.0
```

With neutral affect (arousal=0, valence=0), the acetylcholine delta was -0.5, making ach_multiplier = 0.0, resulting in 0 thinking steps!

### Solution Applied

```python
ach_multiplier = 1.0 + nm["acetylcholine_delta"] * 2.0
ach_multiplier = max(1.0, ach_multiplier)  # Ensure minimum 1.0
```

---

## Code Changes

### 1. brain/__init__.py - Thinking Loop

```python
# ── THINKING PHASE ────────────────────────────────────────────────────
# Process input through the SNN for N simulation steps.
# This is where the actual "thinking" happens - neurons fire,
# synapses strengthen via STDP, and concepts form.
concept_spikes_during_think = set()
peak_regions = {}

step_i = 0
first_spike_step = -1
while step_i < thinking_steps:
    batch_end = min(step_i + _STEP_BATCH, thinking_steps)
    with self._lock:
        for i in range(step_i, batch_end):
            if seed_concept_indices is not None:
                # FIX: Use constant high magnitude instead of decaying
                # The original decaying magnitude (20.0 → 0.2) prevented
                # neurons from accumulating enough potential to fire.
                # Constant 50.0 allows proper integration over time.
                magnitude = 50.0
                self.concept.population.inject_current(seed_concept_indices, magnitude)
            self.step(stdp_gain)
            # Collect spikes from concept layer
            if self.concept.last_spikes.size > 0:
                concept_spikes_during_think.update(self.concept.last_spikes.tolist())
                if first_spike_step < 0:
                    first_spike_step = i
    step_i = batch_end
    time.sleep(0)   # yield GIL between batches
```

### 2. codec/llm_gate.py - Confidence Threshold

```python
# Reduced min_confidence from 0.4 to 0.2 to allow more LLM calls
# The brain's confidence was stuck at 1.00 due to persistence, preventing
# the LLM from ever being called for natural language generation.
min_confidence: float = 0.2,  # was 0.4
```

---

## Debug Logging Output

Now shows detailed thinking process:
```
[THINK] Affect debug: arousal=0.25, valence=0.00, ach_delta=-0.500, ach_mult=1.00, base_steps=602
[THINK] Thinking params: steps=602, seed_count=5, words=5
[THINK] Thinking loop: 602 steps, 4 unique spikes, first spike at step 10
[THINK] === THINKING PROCESS ===
[THINK] Concept neurons fired: 4
[THINK] Active assembly: 20
[THINK] Concept activity: 4.0%
[THINK] === LLM GATE DECISION ===
[THINK] Confidence: 1.00 (threshold: 0.2)
[THINK] LLM Gate: should_call_llm=True, reason=...
```

---

## Files Modified

1. `brain/__init__.py` - Thinking loop with spike detection
2. `codec/llm_gate.py` - Reduced confidence threshold