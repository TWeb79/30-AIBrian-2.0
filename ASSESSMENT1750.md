# BRAIN 2.0 — CHANGELIST
## Critical Fixes for Meaningful Responses & Autonomous Conversation

**Priority order:** P0 = brain is silent/broken | P1 = brain responds meaninglessly | P2 = brain can't initiate | P3 = quality improvements

---

## P0 — BRAIN NEVER CALLS LLM (total silence on real responses)

### FIX-001 — User message is never passed to the LLM prompt
**Status (Apr 2026):** ✅ Implemented. `brain/__init__.py:367-381` now injects `message`, `brain_stage`, `total_turns`, `chat_history`, drives, affect, etc. into `brain_state`, and `codec/llm_codec.py:_build_minimal_prompt()` consumes those keys.
**File:** `codec/llm_codec.py` → `_build_minimal_prompt()`  
**Symptom:** LLM receives only concept IDs and confidence numbers. It has no idea what the user said. Every response is hallucinated from metadata.  
**Root cause:** `brain_state` dict in `process_input_v01()` does not include `message`. The LLM prompt is: *"Active concept: #42, Confidence: 30%"* — nothing else.

**Fix — `brain/__init__.py`, `process_input_v01()`, step 7a:**
```python
# BEFORE:
brain_state = {
    'confidence': self.self_model.confidence,
    'prediction_confidence': snapshot.get('attention_gain', 1.0) / 4.0,
    'active_concept_neuron': ...,
    'concept_layer_activity': ...,
    'expects_text': True,
    'memory_snippet': memory_snippet,
}

# AFTER:
brain_state = {
    'message': user_text,                          # ← ADD THIS
    'confidence': self.self_model.confidence,
    'prediction_confidence': snapshot.get('attention_gain', 1.0) / 4.0,
    'active_concept_neuron': ...,
    'concept_layer_activity': ...,
    'expects_text': True,
    'memory_snippet': memory_snippet,
    'brain_stage': self.self_model.brain_stage,    # ← ADD THIS
    'vocabulary_size': self.self_model.vocabulary_size,
    'drives': self.drives.state.__dict__,
    'affect': {'valence': affect_state.valence, 'arousal': affect_state.arousal},
}
```

**Fix — `codec/llm_codec.py`, `_build_minimal_prompt()`:**
```python
def _build_minimal_prompt(self, state: Dict[str, Any]) -> str:
    message   = state.get("message", "")
    concept   = state.get("active_concept_neuron", -1)
    confidence = state.get("confidence", 0.5)
    memory    = state.get("memory_snippet", "none")
    stage     = state.get("brain_stage", "NEONATAL")
    drives    = state.get("drives", {})
    affect    = state.get("affect", {})

    context_parts = []
    if memory and memory != "none":
        context_parts.append(f"Memory: {memory}")
    if drives.get("curiosity", 0) > 0.7:
        context_parts.append("Express curiosity, ask follow-up question.")
    if drives.get("connection", 0) > 0.6:
        context_parts.append("Be warm and personal.")
    if affect.get("arousal", 0) > 0.6 and affect.get("valence", 0) < -0.2:
        context_parts.append("User seems stressed — be calm and supportive.")

    return f"""You are a {stage} neuromorphic brain called BRAIN 2.0.
You have had {state.get('total_turns', 0)} conversations.
Your confidence level is {confidence:.0%}.
{chr(10).join(context_parts)}

User said: {message}

Respond naturally in 2-4 sentences. Be genuine and conversational.
Do not mention being an AI. Respond as yourself."""
```

---

### FIX-002 — LLM gate rejects ALL calls in NEONATAL stage
**Status (Apr 2026):** ✅ Implemented. `codec/llm_gate.py:80-105` rate limits at 1 s and unconditionally green-lights NEONATAL/JUVENILE stages via `early_stage_always_llm`.
**File:** `codec/llm_gate.py`  
**Symptom:** Brain always falls back to phonological buffer which outputs "Processing your input. Association: 0%, Predictive: 0%."  
**Root cause:** `confidence` starts at 0.3. Gate `min_confidence=0.4`. Condition `prediction_confidence < self.min_confidence` is TRUE for the entire NEONATAL stage. The LLM is never called.  
**Secondary cause:** `rate_limit_seconds=3.0` — if two messages come within 3 seconds, second message goes local with no LLM.

**Fix — `codec/llm_gate.py`, `should_call_llm()`:**
```python
def should_call_llm(self, brain_state: Dict[str, Any], force_local: bool = False) -> GateDecision:
    self._total_decisions += 1
    
    if force_local:
        self._local_calls += 1
        return GateDecision(should_call_llm=False, reason="force_local=True")
    
    # P0 FIX: Always call LLM for NEONATAL and JUVENILE stages.
    # The brain has no vocabulary yet — local generation is useless.
    stage = brain_state.get("brain_stage", "NEONATAL")
    if stage in ("NEONATAL", "JUVENILE"):
        # Only rate-limit — don't apply confidence gate to early brain
        import time
        now = time.time()
        if now - self._last_call_time < self.rate_limit_seconds:
            self._local_calls += 1
            return GateDecision(should_call_llm=False, reason="rate_limited")
        self._llm_calls += 1
        self._last_call_time = now
        return GateDecision(should_call_llm=True, reason="early_stage_always_llm")
    
    # ... (existing logic for ADOLESCENT/MATURE)
```

**Also reduce rate limit:**
```python
def __init__(self, min_confidence=0.4, recall_confidence=0.85,
             max_uncertainty=0.15, rate_limit_seconds=1.0):  # ← was 3.0
```

---

### FIX-003 — `ContinuousExistenceLoop.start()` is never called
**Status (Apr 2026):** ✅ Implemented. `brain/__init__.py:247-250` starts the loop immediately after loading state.
**File:** `brain/__init__.py`  
**Symptom:** Brain never runs between sessions. IDLE/DORMANT modes never activate. Energy never recovers. Memory replay never happens.  
**Root cause:** `self.continuous_loop = ContinuousExistenceLoop(self)` is constructed but `.start()` is never called in `__init__`.

**Fix — `brain/__init__.py`, end of `__init__`:**
```python
# After loading persisted state:
self.continuous_loop.start()   # ← ADD THIS LINE
print(f"[OSCENBrain] Continuous existence loop started")
```

---

### FIX-004 — `_snapshot_fresh_until` defined twice
**Status (Apr 2026):** ✅ Implemented. Only a single declaration remains at `brain/__init__.py:165`.
**File:** `brain/__init__.py`, approximately line 172  
**Symptom:** Python SyntaxWarning, potential logic error.

**Fix:** Remove the duplicate line. Keep only one:
```python
self._snapshot_fresh_until: float = 0.0
```

---

## P1 — BRAIN RESPONDS BUT OUTPUT IS MEANINGLESS

### FIX-005 — Python `hash()` is non-deterministic across runs (concept seeds change every restart)
**Status (Apr 2026):** ✅ Implemented. `brain/__init__.py:288-297` uses `hashlib.md5(... ) % self.concept.n` for deterministic seeding.
**File:** `brain/__init__.py`, step 2a in `process_input_v01()`  
**Symptom:** Same word "hello" activates different concept neurons every time the process restarts (Python randomizes hash seeds by default). STDP learns associations that become invalid after restart. Vocabulary accumulates but means nothing after a restart.

**Fix:**
```python
import hashlib

# BEFORE:
seed_concept_indices = np.array([
    hash(w) % self.concept.n for w in words_for_seeding
], dtype=np.int32)

# AFTER — stable across restarts:
def _stable_hash(word: str, n: int) -> int:
    return int(hashlib.md5(word.encode()).hexdigest(), 16) % n

seed_concept_indices = np.array([
    _stable_hash(w, self.concept.n) for w in words_for_seeding
], dtype=np.int32)
```

Add `_stable_hash` as a method on `OSCENBrain` or as a module-level function.

---

### FIX-006 — PhonologicalBuffer fallback output is machine-readable noise, not language
**Status (Apr 2026):** ✅ Implemented. `codec/phonological_buffer.py:11-210` now defines `_NEONATAL_RESPONSES`/`_HIGH_ATTENTION` lists and returns conversational strings.
**File:** `codec/phonological_buffer.py`, `generate()`  
**Symptom:** When LLM is unavailable and vocabulary is empty, output is: *"Processing your input. Association: 0%, Predictive: 0%. My confidence is still developing."*

**Fix — give it a human-sounding fallback set keyed to brain state:**
```python
# Replace the "Generate contextually aware response" block with:
import random

_NEONATAL_RESPONSES = [
    "Still forming my first thoughts...",
    "I'm learning. Give me time.",
    "Something is activating but I can't quite articulate it yet.",
    "I'm here. My language is still developing.",
    "I sense your input. My vocabulary isn't there yet.",
]
_HIGH_ATTENTION = [
    "That caught my attention. My association cortex is firing strongly.",
    "Something about that input is novel to me.",
    "High novelty detected. I'm processing.",
]

if prediction_error > 0.1 or attention_gain > 2.5:
    return random.choice(_HIGH_ATTENTION)
return random.choice(_NEONATAL_RESPONSES)
```

This is a stopgap until LLM is properly routed. With FIX-001 and FIX-002 in place, the LLM should handle most turns and this fallback should rarely trigger.

---

### FIX-007 — `total_turns` and `brain_stage` not passed to codec
**Status (Apr 2026):** ✅ Implemented as part of FIX-001. See `brain_state` dict additions plus `chat_history` propagation.
**File:** `brain/__init__.py`, `process_input_v01()`, brain_state dict  
**Symptom:** `_build_minimal_prompt` references `state.get("total_turns", 0)` and `state.get("brain_stage")` but these keys are not in the dict.

**Fix:** Add to brain_state dict in step 7a (see FIX-001 — already included there):
```python
'total_turns': self.self_model.total_turns,
'brain_stage': self.self_model.brain_stage,
```

---

### FIX-008 — ResponseCache similarity threshold 0.6 causes false hits
**Status (Apr 2026):** ⚠️ Partially implemented. `codec/response_cache.py` now defaults to `similarity_threshold=0.82`, but `brain/__init__.py:396-400` still caches both `local` *and* `cached/llm` paths, so LLM outputs can be reused incorrectly.
**File:** `codec/response_cache.py`  
**Symptom:** "How are you?" and "What are you?" might score >0.6 cosine similarity on bag-of-words and return the same cached response, making the brain appear to ignore what you said.

**Fix:** Raise threshold, and disable cache for LLM path:
```python
class ResponseCache:
    def __init__(self, max_size: int = 200, similarity_threshold: float = 0.82):  # was 0.6
```

Also in `process_input_v01()`, only cache `local` path responses, never `llm` (since LLM responses already have their own internal cache):
```python
# BEFORE:
if path in ('local', 'cached'):
    self.response_cache.store(user_text, response)

# AFTER:
if path == 'local':   # don't cache LLM responses here — they are already unique
    self.response_cache.store(user_text, response)
```

---

## P2 — BRAIN CANNOT INITIATE CONVERSATION

### FIX-009 — Proactive messages are never displayed in the UI
**Status (Apr 2026):** ✅ Implemented (new React shell). `frontend/src/App.jsx` polls `/api/proactive` every ~1.2 s (see lines 438-514) and renders proactive thoughts with the `SPONTANEOUS THOUGHT` badge in both compact and full chat views.
**File:** `brain2_ui_unified.jsx` (and original `brain2_ui.jsx`)  
**Symptom:** The brain generates proactive messages via `_post_proactive()` and queues them at `GET /api/proactive`, but the UI never polls this endpoint. The brain's "thoughts between turns" are invisible.

**Fix — add polling loop to the React UI:**
```javascript
// Add inside the main component, after existing useEffect hooks:
useEffect(() => {
    const poll = setInterval(async () => {
        try {
            const res = await fetch('/api/proactive');
            if (res.ok) {
                const data = await res.json();
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        setMessages(prev => [...prev, {
                            role: 'brain',
                            content: msg,
                            isProactive: true,   // style differently
                        }]);
                    });
                }
            }
        } catch (_) {}
    }, 5000);  // poll every 5 seconds
    return () => clearInterval(poll);
}, []);
```

Style proactive messages with a dim/italic look (they're unsolicited thoughts, not responses):
```javascript
// In message render:
{m.isProactive && (
    <div style={{ fontSize: 7, color: theme.text.muted, letterSpacing: '0.15em', marginBottom: 2 }}>
        SPONTANEOUS THOUGHT
    </div>
)}
```

---

### FIX-010 — Proactive messages are trivial machine-state dumps, not thoughts
**Status (Apr 2026):** ❌ Not implemented. `brain/continuous_loop.py:_idle_behaviours()` still posts status strings like “Free association: concept #…”. No LLM call or richer language yet.
**File:** `brain/continuous_loop.py`, `_idle_behaviours()`  
**Symptom:** Brain posts *"Free association: concept #42"* and *"Replayed 1 episode from memory"* — not sentences, not thoughts.

**Fix — call the LLM to generate a real thought during idle:**
```python
def _idle_behaviours(self):
    # ... existing code ...

    # Generate a real spontaneous thought using LLM
    self._proactive_tick += 1
    if self._proactive_tick % 12 == 0:  # every ~6 seconds at idle speed
        try:
            brain = self.brain
            vocab_size = brain.phon_buffer.get_vocabulary_size() if hasattr(brain, 'phon_buffer') else 0
            recent_topics = []
            if hasattr(brain, 'hippocampus'):
                recent = brain.hippocampus.get_recent(3)
                recent_topics = [ep.topic for ep in recent if ep.topic]
            
            topics_str = ', '.join(recent_topics) if recent_topics else 'nothing specific'
            
            idle_prompt = (
                f"You are BRAIN 2.0, a {brain.self_model.brain_stage} neuromorphic brain. "
                f"You are idle and having a spontaneous thought. "
                f"Recent topics in memory: {topics_str}. "
                f"Vocabulary so far: {vocab_size} words. "
                f"Generate ONE short spontaneous thought (1 sentence, max 15 words). "
                f"Sound like a mind wandering, not a system status report."
            )
            
            from config import LLM_CONFIG
            import requests as _req
            if LLM_CONFIG.is_ollama_available():
                model = LLM_CONFIG.get_best_available_model()
                r = _req.post(
                    f"{LLM_CONFIG.ollama_base_url}/api/generate",
                    json={"model": model, "prompt": idle_prompt, "stream": False},
                    timeout=10
                )
                if r.status_code == 200:
                    thought = r.json().get("response", "").strip()
                    if thought:
                        _post_proactive(thought)
                        return
        except Exception as e:
            pass  # never block idle loop
        
        # Fallback: simple thought
        _post_proactive("Something is forming in my association cortex...")
```

---

### FIX-011 — No `/api/feedback` wiring in the UI
**Status (Apr 2026):** ❌ Not implemented. There is no `/api/feedback` endpoint in `api/main.py`, and the UI buttons shown here were not added—`frontend/src/App.jsx` lacks a `sendFeedback` helper or fetch to that route.
**File:** `brain2_ui_unified.jsx`  
**Symptom:** The API has `POST /api/feedback` but no UI element calls it. The brain never receives reward signals. Drives never update from user reaction. Personality never drifts.

**Fix — add thumbs up/down to each brain message:**
```javascript
const sendFeedback = async (valence) => {
    try {
        await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ valence }),
        });
    } catch (_) {}
};

// In message render for brain messages:
{m.role === 'brain' && !m.isProactive && (
    <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
        <button onClick={() => sendFeedback(1.0)} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 11, opacity: 0.4, padding: '2px 4px',
        }}>👍</button>
        <button onClick={() => sendFeedback(-1.0)} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 11, opacity: 0.4, padding: '2px 4px',
        }}>👎</button>
    </div>
)}
```

Add the API route to `api/main.py` (currently missing — `/api/feedback` is referenced in README but not in the actual routes):
```python
class FeedbackRequest(BaseModel):
    valence: float  # -1.0 to +1.0

@app.post("/api/feedback")
def feedback(req: FeedbackRequest):
    """User feedback signal → dopamine analogue."""
    brain.on_user_feedback(req.valence)
    brain.store.save_self_model(brain.self_model)
    return {
        "acknowledged": True,
        "new_mood": brain.self_model.mood,
        "new_confidence": brain.self_model.confidence,
    }
```

---

## P3 — QUALITY & INTELLIGENCE IMPROVEMENTS

### FIX-012 — LLM prompt gives no conversation history
**Status (Apr 2026):** ✅ Implemented. `brain_state['chat_history'] = self.chat_history[-6:]` and `_build_minimal_prompt()` renders the last exchanges before “User said…”.
**File:** `codec/llm_codec.py`, `_build_minimal_prompt()`  
**Symptom:** Each turn is stateless from the LLM's perspective. The brain "forgets" what was said 2 messages ago even though chat history is stored.

**Fix — add last 3 exchanges to prompt:**
```python
def _build_minimal_prompt(self, state: Dict[str, Any]) -> str:
    # ... base prompt as fixed in FIX-001 ...
    
    # Add recent history if available
    history = state.get("chat_history", [])[-6:]  # last 3 turns
    if history:
        history_lines = []
        for h in history:
            role = "User" if h["role"] == "user" else "Brain"
            history_lines.append(f"{role}: {h['content'][:100]}")
        history_str = "\n".join(history_lines)
        # Insert before "User said:"
        return f"""...(system context)...

Recent conversation:
{history_str}

User said: {message}
..."""
```

Also pass `chat_history` in `brain_state`:
```python
# brain/__init__.py, step 7a:
brain_state['chat_history'] = self.chat_history[-6:]
```

---

### FIX-013 — LLM timeout is too short for Ollama on slow hardware
**Status (Apr 2026):** ✅ Implemented. `config.py:74` sets `self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))`.
**File:** `config.py` (not uploaded — assumed to exist)  
**Symptom:** Ollama with qwen2.5:7b on CPU can take 20-60 seconds. Default timeout likely causes silent failure.

**Fix — increase Ollama timeout:**
```python
# In LLMConfig or wherever timeout is set:
self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))   # was likely 30 or 60
```

---

### FIX-014 — Concept layer gets no input during most of the 500-step thinking window
**Status (Apr 2026):** ✅ Implemented. `brain/__init__.py:302-308` injects seeds on *every* thinking step with decaying magnitude.
**File:** `brain/__init__.py`, `process_input_v01()`, step 2a  
**Symptom:** Seeds are injected for only `min(30, thinking_steps)` steps = 30 steps out of 500. After step 30, the concept layer goes quiet. STDP runs 470 more steps with no signal, slightly degrading the learned associations (LTD dominates with no pre-spikes).

**Fix — inject seeds throughout thinking window at decreasing strength:**
```python
# Replace:
seed_steps = min(30, thinking_steps)
# With:
seed_steps = thinking_steps  # seed throughout

# And inside the loop:
for step_i in range(thinking_steps):
    if seed_concept_indices is not None:
        # Decay magnitude over time: strong initial injection, fades to gentle reminder
        magnitude = 20.0 * max(0.2, 1.0 - step_i / thinking_steps)
        self.concept.population.inject_current(seed_concept_indices, magnitude)
    self.step()
```

---

### FIX-015 — `working_mem` region not in the `REGIONS` array in the UI
**Status (Apr 2026):** ✅ Implemented in the production UI. `frontend/src/App.jsx` defines `REGIONS` with `meta_control`, `working_memory`, `cerebellum`, `brainstem`, etc., ensuring the dashboard displays all 10 regions.
**File:** `brain2_ui_unified.jsx`  
**Symptom:** The UI shows 8 regions, the brain has 10. `meta_control` and `brainstem` are missing from the UI display. Their activity is invisible to the user.

**Fix:**
```javascript
const REGIONS = [
  { id: "sensory",      label: "SENSORY",    neurons: "40k"  },
  { id: "feature",      label: "FEATURE",    neurons: "80k"  },
  { id: "association",  label: "ASSOC",      neurons: "500k" },
  { id: "predictive",   label: "PREDICT",    neurons: "100k" },
  { id: "concept",      label: "CONCEPT",    neurons: "5.8k" },
  { id: "meta_control", label: "META",       neurons: "60k"  },
  { id: "working_memory", label: "WORKING",  neurons: "20k"  },
  { id: "cerebellum",   label: "CEREBELLUM", neurons: "15k"  },
  { id: "brainstem",    label: "BRAINSTEM",  neurons: "8k"   },
  { id: "reflex_arc",   label: "REFLEX",     neurons: "30k"  },
];
```

Also note: the brain uses `working_mem` as the attribute name but the region snapshot key is `working_memory` (from `BrainRegion.__init__`). Check consistency.

---

### FIX-016 — Background loop and `process_input_v01` both hold `_lock` — potential deadlock
**Status (Apr 2026):** ❌ Not implemented. `process_input_v01()` still runs the entire thinking loop under `self._lock` while `_loop()` grabs the same lock every tick, so contention remains.
**File:** `brain/__init__.py`  
**Symptom:** `process_input_v01` holds `self._lock` for 500+ steps while the background loop is also trying to acquire it. On slow hardware this can block the API for seconds and starve the background simulation.

**Fix — stop the background loop during active processing:**
```python
def process_input_v01(self, user_text, user_feedback=0.0):
    # Stop background loop competition during thinking phase
    was_running = self._running
    self._running = False   # pause background loop
    # ... run thinking steps without lock (single-threaded during processing) ...
    self._running = was_running   # resume
```

Alternatively, give the processing thread priority by having the background loop skip a tick if the lock is held:
```python
# In _loop():
acquired = self._lock.acquire(timeout=0.005)  # non-blocking with timeout
if not acquired:
    time.sleep(0.01)   # yield, try next tick
    continue
try:
    ...
finally:
    self._lock.release()
```

---

## SUMMARY — MINIMUM VIABLE FIX SET

To get the brain responding meaningfully today, apply only these in order:

| # | Fix | File | Impact |
|---|-----|------|--------|
| 001 | Pass user message to LLM prompt | `brain/__init__.py` + `codec/llm_codec.py` | 🔴 Critical |
| 002 | Bypass LLM gate for NEONATAL stage | `codec/llm_gate.py` | 🔴 Critical |
| 003 | Call `continuous_loop.start()` | `brain/__init__.py` | 🟠 High |
| 004 | Remove duplicate `_snapshot_fresh_until` | `brain/__init__.py` | 🟡 Medium |
| 005 | Stable hash for concept seeding | `brain/__init__.py` | 🟠 High |
| 009 | Poll `/api/proactive` in UI | `brain2_ui_unified.jsx` | 🟠 High |
| 011 | Add feedback endpoint + UI buttons | `api/main.py` + UI | 🟠 High |
| 012 | Add conversation history to LLM prompt | `codec/llm_codec.py` | 🟡 Medium |

FIX-001 + FIX-002 together = brain goes from silent to speaking.  
FIX-003 + FIX-009 + FIX-010 + FIX-011 together = brain starts conversations and learns from feedback.

---

## WHAT THE BRAIN SHOULD DO AFTER THESE FIXES

- **Turn 1:** User says anything → LLM called with actual message → real response
- **Turn 5:** Drive modifiers (curiosity/connection) begin shaping LLM tone
- **Turn 10:** Memory snippet from hippocampus appears in LLM context
- **Idle 60s:** Brain generates spontaneous thought, UI shows it
- **Turn 50:** Vocabulary has ~50 words, some turns bypass LLM from local assembly recall
- **Turn 500:** Stable personality visible; proactive thoughts reference conversation topics