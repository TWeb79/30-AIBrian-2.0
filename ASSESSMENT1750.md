# ASSESSMENT1750 — Pending Actions (detailed)

This document now contains only the items that remain pending along with available details and suggested implementation steps. Implemented items have been removed.

TASK CHECKLIST

- [x] Implement high-priority fixes (BUG-002, BUG-003, thinking_steps)
- [x] Add /api/train_vocabulary and CLI tool + basic tests
- [x] Implement STDP LTP/LTD split
- [x] Add amygdala snapshot to telemetry
- [ ] Implement remaining items (PredictiveHierarchy observability, attractor_chainer tests, frontend CI)

PENDING ITEMS

1) PredictiveHierarchy observability (LOW-MEDIUM)

 - Symptom: PredictiveHierarchy creates level populations that are not included in all_regions; therefore not visible in snapshots and not reset for external currents.
 - Location: brain/regions/cortical_regions.py
 - Suggested fix:
   - Add hooks to export level statistics in snapshots (prediction error per level), and optionally append the hierarchy populations to brain.all_regions or provide explicit snapshot keys.

2) Tests: AttractorChainer transition correctness & sequence generation (HIGH)

 - Files: tests/test_attractor_chainer.py, tests/test_sequence_generation.py
 - Tests to add:
   - record transitions between known assembly ids and assert predict_next returns expected top_k
   - end-to-end: create several recorded transitions and assert phonological buffer.generate() returns multi-word sequences using chained predictions


LOWER-PRIORITY / RESEARCH ITEMS (brief)

- Represent neuromodulators (NE/DA/ACh) as LIF populations and wire to stdp gains — design and integration work (neuromodulators/)
- Gamma oscillation detection and automatic param sweep to elicit gamma via E/I adjustments (brain/regions) — research + automation
- Expand hippocampus to recurrent attractor model (DG/CA3/CA1) for better episodic recall
- Offline training pipeline to ingest external corpora and schedule runs (tools/)

Notes and next steps:

- All implemented items were removed from this file; this document focuses only on pending work and includes implementation hints/specific code snippets where available.
- Suggested immediate order: PredictiveHierarchy observability → attractor/sequence tests → frontend/CI.







