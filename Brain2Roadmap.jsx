import { useState } from "react";

const VERSIONS = [
  {
    id: "v0.1", label: "ALIVE", color: "#00ffc8", weeks: "Now",
    theme: "The brain exists, persists, and feels like someone is home.",
    essential: true,
    modules: [
      { name: "SelfModel", file: "self/self_model.py", desc: "Persistent identity — name, stage, personality drift, mood, confidence. Lives on disk. Never resets.", essential: true },
      { name: "ContinuousExistenceLoop", file: "brain/continuous_loop.py", desc: "24/7 daemon thread. ACTIVE → IDLE → DORMANT modes. Brain runs between sessions.", essential: true },
      { name: "SalienceFilter + AffectiveState", file: "emotion/salience.py", desc: "Valence/arousal. Distressed inputs get 3× thinking steps. Flat processing ends here.", essential: true },
      { name: "DriveSystem", file: "drives/drive_system.py", desc: "Curiosity, competence, connection. Brain has opinions. Asks questions when curious. Hedges when uncertain.", essential: true },
      { name: "BrainStore", file: "persistence/brain_store.py", desc: "Weights, self-model, vocabulary all survive restart. Brain stage progression is real.", essential: true },
      { name: "LLMCodec v3", file: "codec/llm_codec.py", desc: "Self-model + drive + affect injected into every prompt. LLM articulates who the brain is.", essential: true },
      { name: "CharacterEncoder", file: "codec/character_encoder.py", desc: "Text → spike patterns locally. No API. Similar characters share neurons.", essential: true },
      { name: "Core SNN (E/I, STDP)", file: "neurons/lif.py + synapses/stdp_pair.py", desc: "LIF neurons, sparse pair-STDP, 8 regions. The ticking engine.", essential: true },
      { name: "ReflexArcV2", file: "regions/reflex_arc.py", desc: "3-tier motor safety gate. Force / angle / velocity hard limits.", essential: true },
      { name: "API + UI v0.1", file: "api.py + ui/", desc: "/chat, /feedback, /status, /ws/stream. Chat UI with affect display and drive gauges.", essential: true },
    ]
  },
  {
    id: "v0.2", label: "REMEMBERS", color: "#00cfff", weeks: "4–6w after v0.1",
    theme: "Brain accumulates vocabulary. Recalls past exchanges. First LLM bypass.",
    essential: false,
    modules: [
      { name: "LexicalSTDP", file: "cognition/lexical_stdp.py", desc: "Word ↔ assembly Hebbian pairing wired into sim loop. Brain grows its own vocabulary." },
      { name: "CellAssemblyDetector", file: "cognition/cell_assemblies.py", desc: "Correlation-based stable pattern detection. Foundation of all concept-level capability." },
      { name: "Hippocampus (simplified)", file: "memory/hippocampus_simple.py", desc: "CA3 recurrent attractor only. Pattern completion from partial cues." },
      { name: "ConversationalMemory", file: "memory/conversational_memory.py", desc: "Per-turn episode encoding + recall. Brain remembers specific past exchanges." },
      { name: "PhonologicalBuffer (real)", file: "codec/phonological_buffer.py", desc: "Assembly → word sequence. First turns handled without LLM." },
      { name: "ResponseCache", file: "codec/response_cache.py", desc: "Cosine-similarity reuse. Identical questions → zero-cost response." },
      { name: "VocabularyTracker", file: "cognition/vocabulary_tracker.py", desc: "Reports learned concept count, top words, LLM bypass rate." },
      { name: "Brian2 migration (partial)", file: "neurons/ (Brian2)", desc: "STDP and LIF migrate to Brian2 equations. Correctness improves. 10× faster." },
    ],
    milestone: "~100 stable assemblies after 1,000 turns. ~20% LLM bypass."
  },
  {
    id: "v0.3", label: "FEELS", color: "#ffb300", weeks: "6–10w after v0.2",
    theme: "Genuine internal states colour all processing. Personality becomes visible.",
    essential: false,
    modules: [
      { name: "DopamineSystem", file: "neuromodulators/dopamine.py", desc: "TD learning. Reward prediction error. User feedback → synaptic strengthening." },
      { name: "AcetylcholineSystem", file: "neuromodulators/acetylcholine.py", desc: "Learning rate control. Novelty → encoding mode. Familiarity → recall mode." },
      { name: "NorepinephrineSystem", file: "neuromodulators/norepinephrine.py", desc: "Neural gain / arousal. High NE = sharper WTA. Low NE = exploratory." },
      { name: "SerotoninSystem", file: "neuromodulators/serotonin.py", desc: "Temporal discounting. Patience. Impulse control." },
      { name: "AmygdalaRegion", file: "emotion/amygdala.py", desc: "Fast emotional tagging before cortical processing. Some inputs matter more." },
      { name: "SleepCycle", file: "memory/consolidation.py", desc: "Dormant-mode memory consolidation. Hippocampus replays → cortex learns." },
      { name: "Mood persistence", file: "self/self_model.py (update)", desc: "Affect state persists across sessions. Brain can be in a good or bad mood for days." },
    ],
    milestone: "Personality biases measurably consistent after 5,000 turns. ~40% LLM bypass."
  },
  {
    id: "v0.4", label: "REASONS", color: "#b36bff", weeks: "8–12w after v0.3",
    theme: "Brain predicts, chains concepts. Handles most turns independently.",
    essential: false,
    modules: [
      { name: "PredictiveCodingHierarchy", file: "cognition/predictive_coding.py", desc: "4-level hierarchical PC. Free energy minimisation. Top-down predictions." },
      { name: "AttractorChainer", file: "cognition/sequence_learning.py", desc: "Sequential concept chaining. Proto-syntax. A→B→C learned from co-occurrence." },
      { name: "ThetaGammaCoupling", file: "oscillations/coupling.py", desc: "5-slot SNN context window. Sequence encoding without transformer." },
      { name: "Full Hippocampus", file: "memory/hippocampus_full.py", desc: "DG + CA3 + CA1 + EC. Pattern separation. Episodic memory at full depth." },
      { name: "WorkingMemory (NMDA)", file: "regions/working_memory.py", desc: "Thalamo-cortical persistent activity. Holds concepts across seconds." },
      { name: "CorticalColumn", file: "regions/cortical_column.py", desc: "6-layer laminar structure. Separates feedforward from top-down." },
      { name: "AMPA + NMDA + GABA", file: "synapses/ampa.py + nmda.py + gaba.py", desc: "Full synapse type diversity. NMDA coincidence detection. GABA inhibition." },
    ],
    milestone: "Next-concept prediction >50%. 5-item context window. ~60% LLM bypass."
  },
  {
    id: "v0.5", label: "LEARNS", color: "#fd79a8", weeks: "Ongoing after v0.4",
    theme: "Measurable improvement from interaction. Stage progression verifiable.",
    essential: false,
    modules: [
      { name: "Brian2 full migration", file: "all sim code", desc: "C++ codegen. 10–100× faster. SCALE=0.1 feasible on standard CPU." },
      { name: "GammaOscillation (emergent)", file: "oscillations/gamma.py", desc: "PING gamma from E/I balance. 40Hz emerges without explicit oscillator." },
      { name: "STDP triplet rule", file: "synapses/stdp_triplet.py", desc: "Replace pair-STDP. Bimodal weight distribution. More realistic plasticity." },
      { name: "BCM sliding threshold", file: "synapses/bcm.py", desc: "Per-neuron modification threshold. Prevents runaway. Enables specialisation." },
      { name: "ThalamusRegion", file: "regions/thalamus.py", desc: "Full thalamo-cortical loop. Alpha gating. Attentional selection." },
      { name: "BasalGanglia", file: "regions/basal_ganglia.py", desc: "Action selection. Habit formation. Dopamine-gated direct/indirect pathways." },
      { name: "SleepConsolidation", file: "memory/consolidation.py (full)", desc: "Full SWS replay. Cortical weight transfer. Effective long-term memory." },
    ],
    milestone: "JUVENILE stage at 1M steps. ~75% LLM bypass. Measurable vocabulary growth."
  },
  {
    id: "v1.0", label: "MATURES", color: "#ff9f43", weeks: "~6 months from v0.1",
    theme: "Coherent identity. Genuine LLM replacement for regular use.",
    essential: false,
    modules: [
      { name: "~5,000 stable assemblies", file: "emergent", desc: "Full functional vocabulary through accumulated STDP learning." },
      { name: "85% LLM bypass", file: "codec/llm_gate.py", desc: "Most turns handled by PhonologicalBuffer + AttractorChainer." },
      { name: "30-day episodic recall", file: "memory/", desc: "Retrievable episodes from weeks ago." },
      { name: "Consistent personality", file: "self/", desc: "Character measurably stable across 100+ sessions." },
      { name: "MATURE brain stage", file: "self/stage_tracker.py", desc: "All stage milestones reached. Brain behaves like a known entity." },
    ],
    milestone: "Full LLM replacement for everyday conversational use."
  },
  {
    id: "v2.0", label: "EMBODIES", color: "#a8e6cf", weeks: "Post v1.0 — research",
    theme: "Physical grounding. Concepts backed by simulated experience.",
    essential: false,
    modules: [
      { name: "Physics simulation interface", file: "embodiment/physics.py", desc: "PyBullet/MuJoCo environment. Body state as sensory input." },
      { name: "Proprioceptive encoder", file: "embodiment/proprioception.py", desc: "Body state → spike trains. 'Heavy' learned from lifting." },
      { name: "Grounded concept formation", file: "cognition/grounding.py", desc: "Concepts backed by physical experience, not text co-occurrence." },
      { name: "Full sensorimotor cycle", file: "embodiment/", desc: "Complete perception → action → consequence loop." },
    ],
    milestone: "Research milestone. Concepts have real-world grounding."
  },
];

const MISSING_ADDRESSED = [
  { label: "Self-model", v: "v0.1", color: "#00ffc8", note: "First — without it there's no subject" },
  { label: "Continuous existence", v: "v0.1", color: "#00ffc8", note: "First — brain must run between sessions" },
  { label: "Emotion (salience)", v: "v0.1", color: "#00ffc8", note: "First — flat processing is the obvious tell" },
  { label: "Intrinsic drives", v: "v0.1", color: "#00ffc8", note: "First — without drives there's no perspective" },
  { label: "Embodiment", v: "v2.0", color: "#a8e6cf", note: "Last — text interface works without it" },
];

export default function BRAIN20Roadmap() {
  const [selected, setSelected] = useState("v0.1");
  const [expandedModule, setExpandedModule] = useState(null);

  const ver = VERSIONS.find(v => v.id === selected);

  return (
    <div style={{
      fontFamily: "'JetBrains Mono', monospace",
      background: "#030912",
      color: "#c0d8f0",
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
    }}>
      {/* Header */}
      <div style={{
        padding: "16px 24px 12px",
        borderBottom: "1px solid #00ffc815",
        background: "linear-gradient(90deg, #030912, #061428, #030912)",
      }}>
        <div style={{ fontSize: 20, fontWeight: 800, color: "#00ffc8", letterSpacing: "0.12em" }}>BRAIN2.0 v3</div>
        <div style={{ fontSize: 8, letterSpacing: "0.3em", color: "#2a6070", marginTop: 2 }}>
          VERSIONED ROADMAP — INTERFACE-FIRST, BRAIN-DRIVEN, LLM-PERIPHERAL
        </div>
      </div>

      {/* Missing → addressed banner */}
      <div style={{
        padding: "10px 24px",
        borderBottom: "1px solid #ffffff08",
        display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center",
      }}>
        <span style={{ fontSize: 7, color: "#2a6070", letterSpacing: "0.2em", marginRight: 4 }}>5 MISSING CONCEPTS →</span>
        {MISSING_ADDRESSED.map(m => (
          <div key={m.label} style={{
            padding: "3px 10px",
            border: `1px solid ${m.color}40`,
            borderRadius: 20, fontSize: 8,
            background: `${m.color}10`,
            display: "flex", gap: 6, alignItems: "center",
          }}>
            <span style={{ color: m.color, fontWeight: 700 }}>{m.label}</span>
            <span style={{ color: m.color, opacity: 0.5, fontSize: 7 }}>→ {m.v}</span>
          </div>
        ))}
      </div>

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* Version timeline sidebar */}
        <div style={{
          width: 200, flexShrink: 0,
          borderRight: "1px solid #00ffc810",
          display: "flex", flexDirection: "column",
          padding: "16px 0",
          overflowY: "auto",
        }}>
          {VERSIONS.map((v, i) => {
            const active = selected === v.id;
            return (
              <button key={v.id} onClick={() => { setSelected(v.id); setExpandedModule(null); }}
                style={{
                  background: active ? `${v.color}12` : "none",
                  border: "none",
                  borderLeft: `3px solid ${active ? v.color : "transparent"}`,
                  padding: "12px 16px",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s",
                  position: "relative",
                }}>
                {/* Connector line */}
                {i < VERSIONS.length - 1 && (
                  <div style={{
                    position: "absolute", left: 16, bottom: -1,
                    width: 1, height: 2,
                    background: `${v.color}30`,
                  }} />
                )}
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: "50%",
                    background: v.essential ? v.color : "none",
                    border: `1px solid ${v.color}`,
                    boxShadow: v.essential ? `0 0 8px ${v.color}` : "none",
                  }} />
                  <span style={{ fontSize: 10, fontWeight: 700, color: active ? v.color : "#4a7a8a" }}>
                    {v.id}
                  </span>
                  {v.essential && (
                    <span style={{ fontSize: 6, color: v.color, letterSpacing: "0.15em", opacity: 0.8 }}>NOW</span>
                  )}
                </div>
                <div style={{ fontSize: 11, fontWeight: 700, color: active ? v.color : "#6a9ab0", marginLeft: 16 }}>
                  {v.label}
                </div>
                <div style={{ fontSize: 7, color: "#2a5060", marginLeft: 16, marginTop: 2 }}>{v.weeks}</div>
              </button>
            );
          })}
        </div>

        {/* Main content */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px" }}>
          {ver && (
            <>
              {/* Version header */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 6 }}>
                  <span style={{ fontSize: 22, fontWeight: 800, color: ver.color }}>{ver.id}</span>
                  <span style={{ fontSize: 16, fontWeight: 700, color: ver.color, opacity: 0.7 }}>— {ver.label}</span>
                  {ver.essential && (
                    <span style={{
                      padding: "2px 10px", borderRadius: 20, fontSize: 7,
                      background: `${ver.color}20`, border: `1px solid ${ver.color}40`,
                      color: ver.color, letterSpacing: "0.2em",
                    }}>BUILD NOW — NON-NEGOTIABLE</span>
                  )}
                </div>
                <div style={{ fontSize: 12, color: "#6a9ab0", lineHeight: 1.6, maxWidth: 600 }}>
                  {ver.theme}
                </div>
                {ver.milestone && (
                  <div style={{
                    marginTop: 10, padding: "6px 12px",
                    background: `${ver.color}08`, border: `1px solid ${ver.color}25`,
                    borderRadius: 8, fontSize: 9, color: ver.color, letterSpacing: "0.08em",
                  }}>
                    MILESTONE: {ver.milestone}
                  </div>
                )}
              </div>

              {/* Module grid */}
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {ver.modules.map((mod, i) => {
                  const isExpanded = expandedModule === i;
                  return (
                    <div key={i}
                      onClick={() => setExpandedModule(isExpanded ? null : i)}
                      style={{
                        background: isExpanded ? `${ver.color}0c` : "#040e1e",
                        border: `1px solid ${isExpanded ? ver.color + "40" : "#ffffff08"}`,
                        borderRadius: 10, padding: "10px 14px",
                        cursor: "pointer", transition: "all 0.15s",
                      }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <div style={{
                            width: 6, height: 6, borderRadius: "50%",
                            background: mod.essential ? ver.color : "none",
                            border: `1px solid ${ver.color}`,
                            flexShrink: 0,
                          }} />
                          <span style={{ fontSize: 11, fontWeight: 700, color: isExpanded ? ver.color : "#8ab4cc" }}>
                            {mod.name}
                          </span>
                        </div>
                        <span style={{ fontSize: 8, color: "#2a5060", fontFamily: "monospace" }}>
                          {mod.file}
                        </span>
                      </div>
                      {isExpanded && (
                        <div style={{
                          marginTop: 10, paddingTop: 10,
                          borderTop: `1px solid ${ver.color}20`,
                          fontSize: 11, color: "#6a9ab0", lineHeight: 1.65,
                        }}>
                          {mod.desc}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* What's NOT in this version */}
              {ver.essential && (
                <div style={{
                  marginTop: 20, padding: "14px 16px",
                  background: "#0a0614", border: "1px solid #ff4d6d20",
                  borderRadius: 10,
                }}>
                  <div style={{ fontSize: 8, color: "#ff4d6d70", letterSpacing: "0.2em", marginBottom: 8 }}>
                    EXPLICITLY DEFERRED FROM v0.1
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {["LexicalSTDP training loop", "CellAssemblyDetector", "Hippocampal memory",
                      "Neuromodulators (DA/ACh/NE/5-HT)", "Oscillations", "PhonologicalBuffer (real)",
                      "Brian2 migration", "Cortical columns", "Full predictive coding"].map(item => (
                      <span key={item} style={{
                        padding: "3px 8px", fontSize: 8,
                        background: "#ff4d6d08", border: "1px solid #ff4d6d20",
                        borderRadius: 4, color: "#ff4d6d60",
                      }}>{item}</span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Right panel: feel difference table */}
        <div style={{
          width: 260, flexShrink: 0,
          borderLeft: "1px solid #00ffc810",
          padding: "16px 14px",
          overflowY: "auto",
        }}>
          <div style={{ fontSize: 7, letterSpacing: "0.2em", color: "#2a6070", marginBottom: 12 }}>
            v0.1 vs TYPICAL LLM
          </div>
          {[
            { dim: "Identity",    llm: "Resets each session", BRAIN20: "Persistent self-model", good: true },
            { dim: "Personality", llm: "Injected by prompt",  BRAIN20: "Emerges from reward history", good: true },
            { dim: "Memory",      llm: "Context window only", BRAIN20: "Persists indefinitely", good: true },
            { dim: "Emotion",     llm: "Simulated in text",   BRAIN20: "Drives processing depth", good: true },
            { dim: "Drives",      llm: "None",                BRAIN20: "Curiosity / competence / connection", good: true },
            { dim: "Continuous",  llm: "Request-response",    BRAIN20: "Runs between sessions", good: true },
            { dim: "Reasoning",   llm: "Excellent",           BRAIN20: "Poor until v0.4", good: false },
            { dim: "Articulation",llm: "Excellent",           BRAIN20: "LLM-assisted until v0.4", good: false },
            { dim: "Cost",        llm: "Per-token always",    BRAIN20: "Declines as brain matures", good: true },
          ].map(row => (
            <div key={row.dim} style={{
              marginBottom: 8, padding: "7px 10px",
              background: row.good ? "#001a12" : "#0a0608",
              border: `1px solid ${row.good ? "#00ffc815" : "#ff4d6d15"}`,
              borderRadius: 7,
            }}>
              <div style={{ fontSize: 8, fontWeight: 700, color: "#6a9ab0", marginBottom: 4, letterSpacing: "0.08em" }}>
                {row.dim}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                <div style={{ fontSize: 8, color: "#ff4d6d80" }}>LLM: {row.llm}</div>
                <div style={{ fontSize: 8, color: row.good ? "#00ffc880" : "#ff9f4380" }}>
                  v0.1: {row.BRAIN20}
                </div>
              </div>
            </div>
          ))}

          <div style={{ marginTop: 16, fontSize: 7, color: "#2a5060", lineHeight: 1.7 }}>
            The first three rows — identity, personality, memory — are what users feel
            most immediately. v0.1 delivers all three without a single feature from v0.2 onwards.
          </div>
        </div>
      </div>

      <style>{`
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: #030912; }
        ::-webkit-scrollbar-thumb { background: #00ffc820; border-radius: 2px; }
      `}</style>
    </div>
  );
}
