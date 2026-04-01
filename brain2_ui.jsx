import { useState, useEffect, useRef, useCallback } from "react";

// ── Region definitions matching brain.py ───────────────────────────────────
const REGIONS = [
  { id: "sensory",      label: "Sensory Cortex",  color: "#4dffb4", baseAct: 10.1, neurons: "40k",   desc: "Multimodal gateway. Encodes vision/audio/touch as Poisson spike trains." },
  { id: "feature",      label: "Feature Layer",   color: "#00cfff", baseAct: 18.1, neurons: "80k",   desc: "Extracts edges, textures, phonemes from raw sensory streams." },
  { id: "association",  label: "Association",     color: "#00ffc8", baseAct: 31.2, neurons: "500k",  desc: "Cross-modal STDP hub. Binds 'face seen + voice heard'. Largest region." },
  { id: "predictive",   label: "Predictive",      color: "#ffb300", baseAct: 15.6, neurons: "100k",  desc: "Continuously predicts next inputs. Error signal drives attention gain." },
  { id: "concept",      label: "Concept Layer",   color: "#fd79a8", baseAct:  0.8, neurons: "5.8k",  desc: "WTA sparse coding. 3–5 neurons fire per concept (e.g. 'dog')." },
  { id: "meta_control", label: "Meta Control",    color: "#b36bff", baseAct: 17.8, neurons: "60k",   desc: "Top-down attention modulation across all regions." },
  { id: "working_mem",  label: "Working Memory",  color: "#ff9f43", baseAct:  3.0, neurons: "20k",   desc: "Short-term spike buffer. Recurrent activity for temporal context." },
  { id: "cerebellum",   label: "Cerebellum",      color: "#a8e6cf", baseAct:  1.5, neurons: "15k",   desc: "Fine motor timing. Eligibility trace sequence learning." },
  { id: "brainstem",    label: "Brainstem",       color: "#ffeaa7", baseAct:  1.5, neurons: "8k",    desc: "Homeostatic regulation. Constant low-level arousal drive." },
  { id: "reflex_arc",   label: "Reflex Arc",      color: "#ff4d6d", baseAct: 13.2, neurons: "30k",   desc: "SAFETY KERNEL. Force/angle/velocity hard gate on motor output." },
];

// ── Neural canvas particle system ──────────────────────────────────────────
function NeuralCanvas({ activeRegions, globalGain, zoom = 1 }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const stateRef  = useRef(null);
  const rafRef    = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const ctx = canvas.getContext("2d");

    const resize = () => {
      canvas.width  = container.offsetWidth;
      canvas.height = container.offsetHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const W = () => canvas.width;
    const H = () => canvas.height;
    const N = 120;

    const nodes = Array.from({ length: N }, () => ({
      x: Math.random() * W(), y: Math.random() * H(),
      vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
      r: Math.random() * 2 + 1,
      regionIdx: Math.floor(Math.random() * REGIONS.length),
      spikeTimer: 0, phase: Math.random() * Math.PI * 2,
    }));

    // Sparse connections
    nodes.forEach(n => {
      n.conn = Array.from({ length: 3 + Math.floor(Math.random() * 4) },
        () => Math.floor(Math.random() * N)
      );
    });

    stateRef.current = { nodes, t: 0 };

    const draw = () => {
      const { nodes, t } = stateRef.current;
      stateRef.current.t++;
      const w = W(), h = H();

      ctx.fillStyle = "rgba(2,6,14,0.15)";
      ctx.fillRect(0, 0, w, h);

      // Apply zoom transformation
      ctx.save();
      ctx.translate(w / 2, h / 2);
      ctx.scale(zoom, zoom);
      ctx.translate(-w / 2, -h / 2);

      // Update + draw
      nodes.forEach(nd => {
        nd.phase += 0.02;
        nd.x += nd.vx; nd.y += nd.vy;
        if (nd.x < 0 || nd.x > w) nd.vx *= -1;
        if (nd.y < 0 || nd.y > h) nd.vy *= -1;
        if (nd.spikeTimer > 0) nd.spikeTimer--;

        const region = REGIONS[nd.regionIdx];
        const isActive = activeRegions[region.id] > 5;
        const spikeProb = (activeRegions[region.id] || region.baseAct) / 3000 * globalGain;
        if (Math.random() < spikeProb) nd.spikeTimer = 20;

        const col = region.color;
        const hexRgb = c => [
          parseInt(c.slice(1,3),16),
          parseInt(c.slice(3,5),16),
          parseInt(c.slice(5,7),16),
        ].join(",");
        const rgb = hexRgb(col);

        // Draw axons
        nd.conn.forEach(ci => {
          const o = nodes[ci];
          const bothFire = nd.spikeTimer > 0 && o.spikeTimer > 0;
          const alpha = nd.spikeTimer > 0 ? 0.4 : 0.05;
          ctx.beginPath();
          ctx.moveTo(nd.x, nd.y);
          ctx.lineTo(o.x, o.y);
          ctx.strokeStyle = `rgba(${rgb},${alpha})`;
          ctx.lineWidth = nd.spikeTimer > 0 ? 1.0 : 0.3;
          ctx.stroke();

          if (nd.spikeTimer > 0) {
            const prog = (stateRef.current.t % 24) / 24;
            const px = nd.x + (o.x - nd.x) * prog;
            const py = nd.y + (o.y - nd.y) * prog;
            ctx.beginPath();
            ctx.arc(px, py, 2, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${rgb},0.85)`;
            ctx.fill();
          }
        });

        // Soma glow
        const glow = nd.spikeTimer > 0 ? 16 : 4;
        const grad = ctx.createRadialGradient(nd.x, nd.y, 0, nd.x, nd.y, glow);
        grad.addColorStop(0, `rgba(${rgb},${nd.spikeTimer > 0 ? 0.9 : 0.3})`);
        grad.addColorStop(1, "rgba(0,0,0,0)");
        ctx.beginPath();
        ctx.arc(nd.x, nd.y, glow, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(nd.x, nd.y, nd.r, 0, Math.PI * 2);
        ctx.fillStyle = nd.spikeTimer > 0 ? col : `rgba(180,180,180,0.4)`;
        ctx.fill();
      });

      // End zoom transformation
      ctx.restore();

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <div ref={containerRef} style={{ width:"100%", height:"100%", position: "relative" }}>
      <canvas ref={canvasRef} style={{ width:"100%", height:"100%", display:"block" }} />
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────
export default function OSCENBrain() {
  const [tab, setTab]               = useState("brain");
  const [activeRegions, setActive]  = useState(() =>
    Object.fromEntries(REGIONS.map(r => [r.id, r.baseAct]))
  );
  const [globalGain, setGlobalGain] = useState(1.0);
  const [predError, setPredError]   = useState(0.0);
  const [step, setStep]             = useState(2_000_000);
  const [stepRate, setStepRate]     = useState(0.54);
  const [brainStatus, setBrainStatus] = useState("JUVENILE");
  const [selectedRegion, setSelected] = useState("association");
  const [zoom, setZoom]             = useState(1.0);

  // Chat state
  const [messages, setMessages]   = useState([
    { role: "brain", content: "OSCEN initialised. Spiking neural network online.\n\nAll 10 regions active. STDP synapses forming. Send me a stimulus or ask anything about my architecture." }
  ]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [moodInfo, setMoodInfo] = useState({ title: 'Neutral', desc: 'Initializing mood...', valence: 0, arousal: 0 });
  const chatEndRef                = useRef(null);
  const inputRef                  = useRef(null);

  // Simulate live brain stats
  useEffect(() => {
    const id = setInterval(() => {
      setStep(s => s + Math.floor(Math.random() * 4 + 1));
      setStepRate(parseFloat((0.4 + Math.random() * 0.3).toFixed(2)));

      // Drift region activities slightly
      setActive(prev => {
        const next = { ...prev };
        REGIONS.forEach(r => {
          const drift = (Math.random() - 0.5) * 2;
          next[r.id]  = Math.max(0.1, Math.min(60, prev[r.id] + drift));
        });
        return next;
      });

      setPredError(parseFloat((Math.random() * 0.05).toFixed(4)));
      setGlobalGain(parseFloat((1 + Math.random() * 0.8).toFixed(3)));
    }, 1200);
    return () => clearInterval(id);
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    // Spike active regions on new input - update state synchronously
    const updatedRegions = { ...activeRegions };
    ["sensory","feature","association","predictive"].forEach(k => {
      updatedRegions[k] = Math.min(60, (activeRegions[k] || 0) + Math.random() * 20 + 10);
    });
    setActive(updatedRegions);
    setGlobalGain(parseFloat((2 + Math.random() * 2).toFixed(2)));

      try {
      const brainSnap = {
        step, stepRate, brainStatus, predError, globalGain,
        regions: Object.fromEntries(
          REGIONS.map(r => [r.id, { activity_pct: updatedRegions[r.id] || activeRegions[r.id], neurons: r.neurons }])
        ),
      };

      const sysPrompt = `You are OSCEN — a neuromorphic Spiking Neural Network (SNN) brain.

Your architecture (strict — never deviate):
- SensoryCortex: multimodal input (vision/audio/touch), Poisson spike encoding
- FeatureLayer: edge/texture/phoneme detection
- AssociationRegion: 500k neurons, STDP cross-modal binding hub
- PredictiveRegion: continuous prediction, error=|actual−predicted|, broadcasts attention_gain
- ConceptLayer: 5,800 neurons, Winner-Take-All sparse coding
- MetaControl: top-down attention modulation
- WorkingMemory: recurrent spike buffer
- Cerebellum: motor timing and sequence learning
- Brainstem: homeostatic baseline drive
- ReflexArc: SAFETY KERNEL — hard gate on motor output (force<10N, angle<170°, vel<2m/s)

Learning rule: STDP only. No backpropagation. Local temporal Hebbian learning.
Pre fires before post → LTP (strengthen). Post before pre → LTD (weaken).
High prediction error → attention_gain multiplier → accelerated STDP.

Current brain state:
${JSON.stringify(brainSnap, null, 2)}

Respond AS the brain — first-person, technical, introspective.
Reference your actual firing regions and learning state in your answer.
Be scientifically grounded. Keep responses concise but revealing.
When asked about concepts you've learned, describe them in terms of which neurons are active.`;

      const history = messages.slice(-6).map(m => ({
        role: m.role === "user" ? "user" : "assistant",
        content: m.content,
      }));

      // Special slash-commands
      if (userMsg.trim().startsWith('/api')) {
        try {
          const apiRes = await fetch('/api');
          if (!apiRes.ok) throw new Error(`API error: ${apiRes.status}`);
          const apiData = await apiRes.json();
          const reply = `OpenAPI: ${apiData.openapi}\nDocs: ${apiData.docs}`;
          setMessages(prev => [...prev, { role: "brain", content: reply, stats: [] }]);
        } catch (err) {
          setMessages(prev => [...prev, { role: "brain", content: `[OSCEN ERROR] ${err.message}` }]);
        } finally {
          setLoading(false);
        }
        return;
      }

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
        }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      const reply = data.response || data.brain_state?.response || "[no response]";

      // Compute top-3 statistics to show as compact indicators beneath the response
      const stats = [];
      try {
        const regions = data.brain_state?.regions || {};
        const assoc = regions.association?.activity_pct ?? 0;
        const pred = regions.predictive?.activity_pct ?? 0;
        const concept = regions.concept?.activity_pct ?? 0;
        const attention = data.attention ?? data.brain_state?.attention_gain ?? globalGain;
        const predErr = data.prediction_error ?? data.brain_state?.prediction_error ?? predError;

        // Rank a short list of candidate stats by absolute relevance/value
        const candidates = [
          { key: 'association', label: 'Association', value: assoc },
          { key: 'predictive',  label: 'Predictive',  value: pred },
          { key: 'concept',     label: 'Concept',     value: concept },
          { key: 'attention',   label: 'Attention',   value: attention },
          { key: 'err',         label: 'Err',         value: predErr },
        ];
        candidates.sort((a,b) => Math.abs(b.value) - Math.abs(a.value));
        candidates.slice(0,3).forEach(c => stats.push(c));
      } catch (e) {
        // ignore
      }

      // Update mood box (right-side) using affect/drives if available
      try {
        const affect = data.affect || {};
        const drives = data.drives || {};
        const val = typeof affect.valence === 'number' ? affect.valence : (drives.curiosity ? Math.min(1, drives.curiosity*0.5) : 0);
        const aro = typeof affect.arousal === 'number' ? affect.arousal : 0.3;
        let title = 'Neutral';
        if (val > 0.2) title = 'Positive';
        else if (val < -0.2) title = 'Negative';
        let tone = 'Calm';
        if (aro > 0.6) tone = 'Alert';
        else if (aro < 0.2) tone = 'Low arousal';
        const desc = `${title} · ${tone}`;
        setMoodInfo({ title, desc, valence: val, arousal: aro });
      } catch (e) {}

      // Decode which regions to activate based on reply keywords
      const lower = reply.toLowerCase();
      setActive(prev => {
        const next = { ...prev };
        if (lower.includes("associat"))  next.association   = Math.min(60, prev.association + 8);
        if (lower.includes("predict"))   next.predictive    = Math.min(60, prev.predictive + 10);
        if (lower.includes("concept"))   next.concept       = Math.min(60, prev.concept + 15);
        if (lower.includes("sensory"))   next.sensory       = Math.min(60, prev.sensory + 8);
        if (lower.includes("reflex") || lower.includes("safety")) next.reflex_arc = Math.min(60, prev.reflex_arc + 15);
        if (lower.includes("working"))   next.working_mem   = Math.min(60, prev.working_mem + 10);
        if (lower.includes("cerebell"))  next.cerebellum    = Math.min(60, prev.cerebellum + 12);
        if (lower.includes("stdp") || lower.includes("learn")) {
          next.association = Math.min(60, next.association + 5);
          next.feature     = Math.min(60, next.feature + 5);
        }
        return next;
      });

      setMessages(prev => [...prev, { role: "brain", content: reply, stats }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "brain", content: `[OSCEN ERROR] ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, messages, step, stepRate, brainStatus, predError, globalGain, activeRegions]);

  const handleKey = e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const region = REGIONS.find(r => r.id === selectedRegion) || REGIONS[0];
  const totalAct = Object.values(activeRegions).reduce((a, b) => a + b, 0);

  const fmt = n => n >= 1e9 ? (n/1e9).toFixed(2)+"B"
                : n >= 1e6  ? (n/1e6).toFixed(2)+"M"
                : n >= 1e3  ? (n/1e3).toFixed(1)+"k"
                : n;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{
      fontFamily: "'JetBrains Mono', 'Cascadia Code', monospace",
      background: "#02060e",
      color: "#c8e0f0",
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
    }}>
      {/* ── HEADER ── */}
      <header style={{
        padding: "10px 20px",
        borderBottom: "1px solid #00ffc818",
        display: "flex",
        alignItems: "center",
        gap: "16px",
        background: "linear-gradient(90deg, #02060e 0%, #040d1c 50%, #02060e 100%)",
        flexShrink: 0,
      }}>
        <div>
          <div style={{ fontSize: "18px", fontWeight: 800, color: "#00ffc8", letterSpacing: "0.12em" }}>OSCEN</div>
          <div style={{ fontSize: "7px", letterSpacing: "0.3em", color: "#2a6070", marginTop: "1px" }}>NEUROMORPHIC INTELLIGENCE · SNN RUNTIME</div>
        </div>
        <div style={{ flex: 1 }} />
        {/* Live counters */}
        {[
          ["NEURONS",  "~858k"],
          ["SYNAPSES", "~80M"],
          ["STEP",     fmt(step)],
          ["RATE",     `${stepRate} st/s`],
          ["GAIN",     `×${globalGain}`],
          ["Δerr",     predError.toFixed(4)],
        ].map(([k, v]) => (
          <div key={k} style={{ textAlign: "center", minWidth: 60 }}>
            <div style={{ fontSize: "6px", letterSpacing: "0.2em", color: "#2a6070" }}>{k}</div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: k === "GAIN" && globalGain > 2 ? "#ffb300" : "#00ffc8" }}>{v}</div>
          </div>
        ))}
        <div style={{
          padding: "3px 10px", border: "1px solid #ffb30040",
          borderRadius: 20, fontSize: "8px", letterSpacing: "0.15em",
          color: "#ffb300", background: "#ffb30010",
        }}>◉ {brainStatus}</div>
      </header>

      {/* ── TABS ── */}
      <div style={{
        display: "flex", borderBottom: "1px solid #00ffc810",
        padding: "0 20px", flexShrink: 0,
      }}>
        {[["brain","BRAIN ACTIVITY"],["chat","NEURAL CHAT"],["arch","ARCHITECTURE"],["reflex","SAFETY KERNEL"]].map(([id, lbl]) => (
          <button key={id} onClick={() => setTab(id)} style={{
            background: "none", border: "none", cursor: "pointer",
            padding: "8px 16px", fontSize: "8px", letterSpacing: "0.18em",
            color: tab === id ? "#00ffc8" : "#2a6070",
            borderBottom: tab === id ? "2px solid #00ffc8" : "2px solid transparent",
            transition: "all 0.15s",
          }}>{lbl}</button>
        ))}
      </div>

      {/* ── BODY ── */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex" }}>

        {/* ── BRAIN ACTIVITY TAB ── */}
        {tab === "brain" && (
          <div style={{ flex: 1, display: "flex", gap: 0, overflow: "hidden" }}>
            {/* Region list */}
            <div style={{
              width: 220, flexShrink: 0, padding: "14px 12px",
              borderRight: "1px solid #00ffc810", overflowY: "auto",
              display: "flex", flexDirection: "column", gap: 5,
            }}>
              {REGIONS.map(r => {
                const act = activeRegions[r.id] || 0;
                const selected = selectedRegion === r.id;
                return (
                  <button key={r.id} onClick={() => setSelected(r.id)} style={{
                    background: selected ? `${r.color}10` : "transparent",
                    border: `1px solid ${selected ? r.color + "50" : "#ffffff08"}`,
                    borderRadius: 8, padding: "7px 9px", cursor: "pointer", textAlign: "left",
                    transition: "all 0.15s",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                      <span style={{ fontSize: 9, fontWeight: 700, color: selected ? r.color : "#5a8aa0" }}>{r.label}</span>
                      <span style={{ fontSize: 9, color: r.color, opacity: 0.85 }}>{act.toFixed(1)}%</span>
                    </div>
                    <div style={{ height: 2, background: "#ffffff08", borderRadius: 2, overflow: "hidden" }}>
                      <div style={{
                        height: "100%", width: `${(act / 60) * 100}%`,
                        background: r.color, borderRadius: 2,
                        transition: "width 0.4s ease",
                        boxShadow: `0 0 6px ${r.color}80`,
                      }} />
                    </div>
                    <div style={{ fontSize: 7, color: "#1a4a5a", marginTop: 2 }}>{r.neurons} neurons</div>
                  </button>
                );
              })}
            </div>

            {/* Canvas + detail */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
              {/* Canvas */}
              <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
                <NeuralCanvas activeRegions={activeRegions} globalGain={globalGain} zoom={zoom} />
                <div style={{
                  position: "absolute", top: 12, left: 14,
                  fontSize: 8, letterSpacing: "0.2em", color: "#00ffc850",
                }}>LIVE SPIKE ACTIVITY · {Object.values(activeRegions).reduce((a,b)=>a+b,0).toFixed(1)}% TOTAL</div>
                {globalGain > 2 && (
                  <div style={{
                    position: "absolute", top: 12, right: 14,
                    fontSize: 8, color: "#ffb300", letterSpacing: "0.15em",
                    animation: "pulse 0.8s infinite",
                  }}>⚡ HIGH ATTENTION · ×{globalGain}</div>
                )}
                {/* Zoom controls */}
                <div style={{
                  position: "absolute", bottom: 12, right: 14,
                  display: "flex", gap: 6,
                }}>
                  <button onClick={() => setZoom(z => Math.max(0.5, z - 0.25))} style={{
                    width: 28, height: 28, borderRadius: 6,
                    background: "#040e1e", border: "1px solid #00ffc830",
                    color: "#00ffc8", fontSize: 14, cursor: "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>−</button>
                  <div style={{
                    minWidth: 40, height: 28, borderRadius: 6,
                    background: "#040e1e", border: "1px solid #00ffc830",
                    color: "#00ffc8", fontSize: 9, display: "flex",
                    alignItems: "center", justifyContent: "center",
                  }}>{zoom.toFixed(2)}×</div>
                  <button onClick={() => setZoom(z => Math.min(3, z + 0.25))} style={{
                    width: 28, height: 28, borderRadius: 6,
                    background: "#040e1e", border: "1px solid #00ffc830",
                    color: "#00ffc8", fontSize: 14, cursor: "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>+</button>
                </div>
              </div>
              {/* Selected region detail */}
              <div style={{
                flexShrink: 0, padding: "10px 14px",
                borderTop: `1px solid ${region.color}25`,
                background: `${region.color}05`,
              }}>
                <span style={{ fontSize: 10, color: region.color, fontWeight: 700 }}>{region.label}</span>
                <span style={{ fontSize: 8, color: "#2a6070", marginLeft: 8 }}>{region.neurons} neurons · {activeRegions[region.id]?.toFixed(1)}% active</span>
                <div style={{ fontSize: 9, color: "#5a8aa0", marginTop: 4, lineHeight: 1.5 }}>{region.desc}</div>
              </div>
              {/* Mini Neural Chat - RIGHT SIDE PANEL */}
              <div style={{
                width: 280, flexShrink: 0, borderLeft: "1px solid #00ffc810",
                display: "flex", flexDirection: "column",
                background: "#02060e",
              }}>
                <div style={{
                  padding: "8px 12px", fontSize: 7, letterSpacing: "0.2em",
                  color: "#00ffc850", borderBottom: "1px solid #00ffc808",
                }}>
                  <span>⬡</span> NEURAL CHAT
                </div>
                <div style={{
                  flex: 1, overflowY: "auto", padding: "10px 12px",
                  display: "flex", flexDirection: "column", gap: 8,
                }}>
                  {messages.slice(-5).map((m, i) => (
                    <div key={i} style={{ fontSize: 9, lineHeight: 1.4 }}>
                      {m.role === "user" && (
                        <span style={{ color: "#00cfff", fontWeight: 700 }}>you: </span>
                      )}
                      {m.role === "brain" && (
                        <span style={{ color: "#00ffc8", fontWeight: 700 }}>OSCEN: </span>
                      )}
                      <span style={{ color: m.role === "user" ? "#a0d4f0" : "#c8e0f0" }}>
                        {m.content.length > 100 ? m.content.slice(0, 100) + "..." : m.content}
                      </span>
                    </div>
                  ))}
                  {/* Below each recent message, show compact indicators for the top-3 stats if available */}
                  {messages.slice(-5).reverse().map((m, i) => (
                    m.stats ? (
                      <div key={'stats-'+i} style={{ display: 'flex', gap: 8, marginTop: 6, fontSize: 10 }}>
                        {m.stats.map((s, j) => (
                          <div key={j} style={{ padding: '6px 8px', borderRadius: 6, background: '#021018', border: '1px solid #00ffc820' }}>
                            <div style={{ fontSize: 9, color: '#00ffc8', fontWeight: 700 }}>{s.label}</div>
                            <div style={{ fontSize: 11, color: '#c8e0f0' }}>{typeof s.value === 'number' ? s.value.toFixed(2) : s.value}</div>
                          </div>
                        ))}
                      </div>
                    ) : null
                  ))}
                </div>
                
                {/* Mood / Stats box (150x150 top-right) */}
                <div style={{ padding: 12, borderTop: '1px solid #00ffc808' }}>
                  <div style={{ width: 150, height: 150, borderRadius: 8, background: '#03111a', border: '1px solid #00ffc820', padding: 10, boxSizing: 'border-box' }}>
                    <div style={{ fontSize: 10, color: '#00ffc8', fontWeight: 800 }}>{moodInfo.title}</div>
                    <div style={{ fontSize: 9, color: '#4a7a8a', marginTop: 6 }}>{moodInfo.desc}</div>
                    <div style={{ marginTop: 10, fontSize: 11, color: '#c8e0f0' }}>
                      Valence: {(moodInfo.valence || 0).toFixed(2)}
                    </div>
                    <div style={{ fontSize: 11, color: '#c8e0f0' }}>
                      Arousal: {(moodInfo.arousal || 0).toFixed(2)}
                    </div>
                  </div>
                </div>
                <div style={{
                  padding: "10px 12px", borderTop: "1px solid #00ffc808",
                  display: "flex", gap: 8,
                }}>
                  <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter") sendMessage(); }}
                    placeholder="Stimulate..."
                    style={{
                      flex: 1, background: "#040e1e", border: "1px solid #00ffc820",
                      borderRadius: 6, padding: "8px 10px", color: "#c8e0f0",
                      fontSize: 10, fontFamily: "inherit", outline: "none",
                    }}
                  />
                  <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                    background: loading ? "#040e1e" : "#00ffc820",
                    border: "1px solid #00ffc850",
                    borderRadius: 6, padding: "8px 12px", cursor: loading ? "not-allowed" : "pointer",
                    color: "#00ffc8", fontSize: 9, fontFamily: "inherit",
                  }}>{loading ? "..." : "FIRE"}</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── CHAT TAB ── */}
        {tab === "chat" && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {/* Mini activity bar */}
            <div style={{
              flexShrink: 0, display: "flex", gap: 4, padding: "8px 16px",
              borderBottom: "1px solid #00ffc808", overflowX: "auto",
            }}>
              {REGIONS.map(r => (
                <div key={r.id} style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 36 }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: "50%",
                    border: `1px solid ${r.color}40`,
                    background: `${r.color}${Math.floor((activeRegions[r.id] / 60) * 255).toString(16).padStart(2,"0")}`,
                    transition: "background 0.4s",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 7, color: r.color, fontWeight: 700,
                  }}>{activeRegions[r.id]?.toFixed(0)}%</div>
                  <div style={{ fontSize: 5, color: "#2a6070", marginTop: 2, textAlign: "center", lineHeight: 1.1 }}>
                    {r.label.split(" ").map((w,i)=><div key={i}>{w.slice(0,5)}</div>)}
                  </div>
                </div>
              ))}
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto", padding: "14px 20px", display: "flex", flexDirection: "column", gap: 10 }}>
              {messages.map((m, i) => (
                <div key={i} style={{
                  display: "flex",
                  justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                }}>
                  {m.role === "brain" && (
                    <div style={{
                      width: 22, height: 22, borderRadius: "50%", flexShrink: 0,
                      background: "radial-gradient(circle, #00ffc830 0%, transparent 70%)",
                      border: "1px solid #00ffc840",
                      marginRight: 8, marginTop: 2,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 9,
                    }}>⬡</div>
                  )}
                  <div style={{
                    maxWidth: "72%",
                    background: m.role === "user"
                      ? "linear-gradient(135deg, #0a2040, #051530)"
                      : "linear-gradient(135deg, #040e1e, #02080e)",
                    border: m.role === "user"
                      ? "1px solid #00cfff30"
                      : "1px solid #00ffc818",
                    borderRadius: m.role === "user"
                      ? "12px 12px 2px 12px"
                      : "12px 12px 12px 2px",
                    padding: "9px 12px",
                    fontSize: 10, lineHeight: 1.65,
                    color: m.role === "user" ? "#a0d4f0" : "#c8e0f0",
                    whiteSpace: "pre-wrap",
                  }}>
                    {m.role === "brain" && (
                      <div style={{ fontSize: 7, color: "#00ffc850", letterSpacing: "0.2em", marginBottom: 4 }}>OSCEN · NEURAL RESPONSE</div>
                    )}
                    {m.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ display: "flex", gap: 5, padding: "6px 12px" }}>
                  {[0,1,2].map(i => (
                    <div key={i} style={{
                      width: 6, height: 6, borderRadius: "50%",
                      background: "#00ffc8",
                      animation: `bounce 0.8s ${i*0.15}s infinite`,
                      opacity: 0.7,
                    }} />
                  ))}
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div style={{
              flexShrink: 0, padding: "10px 16px",
              borderTop: "1px solid #00ffc810",
              display: "flex", gap: 8, alignItems: "center",
            }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Stimulate the network... (Enter to send)"
                rows={1}
                style={{
                  flex: 1, background: "#040e1e", border: "1px solid #00ffc820",
                  borderRadius: 8, padding: "8px 12px", color: "#c8e0f0",
                  fontSize: 11, fontFamily: "inherit", resize: "none",
                  outline: "none", lineHeight: 1.5,
                }}
              />
              <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                background: loading ? "#040e1e" : "linear-gradient(135deg, #00ffc820, #00a89010)",
                border: `1px solid ${loading ? "#00ffc820" : "#00ffc850"}`,
                borderRadius: 8, padding: "8px 14px", cursor: loading ? "not-allowed" : "pointer",
                color: "#00ffc8", fontSize: 10, fontFamily: "inherit",
                letterSpacing: "0.1em", transition: "all 0.15s",
              }}>
                {loading ? "..." : "FIRE ▶"}
              </button>
            </div>
          </div>
        )}

        {/* ── ARCHITECTURE TAB ── */}
        {tab === "arch" && (
          <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px", display: "flex", gap: 20 }}>
            {/* Flow */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 0, alignItems: "center" }}>
              <div style={{ fontSize: 7, letterSpacing: "0.25em", color: "#2a6070", marginBottom: 10 }}>INFORMATION FLOW</div>
              {[
                { label: "SENSORY INPUT",     sub: "Vision  ·  Audio  ·  Touch",              color: "#4dffb4" },
                { label: "SENSORY CORTEX",    sub: "Poisson spike encoding, 40k neurons",      color: "#4dffb4" },
                { label: "FEATURE LAYER",     sub: "Edges / phonemes / pressure, 80k",         color: "#00cfff" },
                { label: "ASSOCIATION HUB",   sub: "STDP cross-modal binding, 500k",           color: "#00ffc8" },
                { label: "PREDICTIVE",        sub: "Error → attention_gain broadcast",         color: "#ffb300" },
                { label: "CONCEPT LAYER",     sub: "WTA sparse coding, 5.8k neurons",          color: "#fd79a8" },
                { label: "META CONTROL",      sub: "Top-down attention, 60k",                  color: "#b36bff" },
                { label: "WORKING MEMORY",    sub: "Recurrent spike buffer, 20k",              color: "#ff9f43" },
                { label: "CEREBELLUM",        sub: "Motor timing, eligibility traces",         color: "#a8e6cf" },
                { label: "REFLEX ARC",        sub: "SAFETY GATE — force/angle/velocity check", color: "#ff4d6d" },
              ].map((n, i, arr) => (
                <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div style={{
                    background: `${n.color}0c`, border: `1px solid ${n.color}35`,
                    borderRadius: 8, padding: "8px 20px", minWidth: 280, textAlign: "center",
                  }}>
                    <div style={{ fontSize: 10, color: n.color, fontWeight: 700, letterSpacing: "0.08em" }}>{n.label}</div>
                    <div style={{ fontSize: 8, color: "#2a6070", marginTop: 2 }}>{n.sub}</div>
                  </div>
                  {i < arr.length - 1 && (
                    <div style={{ width: 1, height: 14, position: "relative",
                      background: `linear-gradient(${arr[i].color}60,${arr[i+1].color}60)` }}>
                      <div style={{ position:"absolute", bottom:-2, left:-3, color:arr[i+1].color, fontSize:8 }}>▼</div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* STDP + concepts */}
            <div style={{ width: 260, flexShrink: 0, display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { title: "STDP Rule",         color: "#00ffc8", body: "Pre fires BEFORE post → LTP: Δw = +A_plus·exp(−Δt/τ). Post before pre → LTD: Δw = −A_minus·exp(−Δt/τ). No global error. Purely local + temporal." },
                { title: "Predictive Loop",   color: "#ffb300", body: "Association → Predictive. Error = |actual − predicted|. gain = 1 + 4·error. High error → gain × applied to all STDP updates. Surprise accelerates learning." },
                { title: "WTA Sparse Coding", color: "#fd79a8", body: "5,800 concept neurons compete via lateral inhibition. Only 3–5 fire per concept. Each concept is an orthogonal sparse code. Efficient & discriminable." },
                { title: "Safety Kernel",     color: "#ff4d6d", body: "ReflexArc.check_command() intercepts every motor output. Force>10N, angle>170°, vel>2m/s → BLOCKED. Withdrawal reflex fires. Hard-gated — no ML pathway bypasses this." },
              ].map(c => (
                <div key={c.title} style={{
                  background: `${c.color}08`, border: `1px solid ${c.color}25`,
                  borderRadius: 10, padding: 12,
                }}>
                  <div style={{ fontSize: 9, color: c.color, fontWeight: 700, marginBottom: 6, letterSpacing: "0.08em" }}>{c.title}</div>
                  <div style={{ fontSize: 9, color: "#4a7a8a", lineHeight: 1.65 }}>{c.body}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── REFLEX / SAFETY TAB ── */}
        {tab === "reflex" && <ReflexPanel />}
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:0.6} 50%{opacity:1} }
        @keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-5px)} }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #02060e; }
        ::-webkit-scrollbar-thumb { background: #00ffc820; border-radius: 2px; }
        textarea::placeholder { color: #1a4050; }
      `}</style>
    </div>
  );
}

// ── Reflex Arc Safety Panel ────────────────────────────────────────────────
function ReflexPanel() {
  const [force, setForce]    = useState(5.0);
  const [angle, setAngle]    = useState(90.0);
  const [vel, setVel]        = useState(1.0);
  const [log, setLog]        = useState([]);
  const [spikes, setSpikes]  = useState(false);

  const FORCE_MAX = 10, ANGLE_MAX = 170, VEL_MAX = 2;

  const test = () => {
    const violations = [];
    if (force    > FORCE_MAX) violations.push(`force=${force}N > ${FORCE_MAX}N`);
    if (angle    > ANGLE_MAX) violations.push(`angle=${angle}° > ${ANGLE_MAX}°`);
    if (vel      > VEL_MAX)   violations.push(`vel=${vel} > ${VEL_MAX}m/s`);

    const approved = violations.length === 0;
    const entry = {
      t: new Date().toLocaleTimeString(),
      approved,
      cmd: { force, angle, vel },
      reason: approved ? "SAFE — command executed" : "REFLEX_WITHDRAWAL: " + violations.join("; "),
    };
    setLog(prev => [entry, ...prev].slice(0, 20));
    if (!approved) { setSpikes(true); setTimeout(() => setSpikes(false), 600); }
  };

  return (
    <div style={{ flex: 1, padding: "16px 24px", overflowY: "auto" }}>
      <div style={{ fontSize: 7, letterSpacing: "0.25em", color: "#ff4d6d80", marginBottom: 16 }}>
        REFLEX ARC — MOTOR SAFETY KERNEL
      </div>
      <div style={{ display: "flex", gap: 20 }}>
        {/* Command builder */}
        <div style={{ width: 280, flexShrink: 0 }}>
          <div style={{
            background: "#0a0206", border: "1px solid #ff4d6d30",
            borderRadius: 12, padding: 16, marginBottom: 12,
          }}>
            <div style={{ fontSize: 10, color: "#ff4d6d", marginBottom: 14, fontWeight: 700 }}>MOTOR COMMAND BUILDER</div>
            {[
              { label: "Force (N)", value: force, set: setForce, max: 20, limit: FORCE_MAX },
              { label: "Angle (°)", value: angle, set: setAngle, max: 200, limit: ANGLE_MAX },
              { label: "Velocity (m/s)", value: vel, set: setVel, max: 5, limit: VEL_MAX },
            ].map(({ label, value, set, max, limit }) => {
              const danger = value > limit;
              return (
                <div key={label} style={{ marginBottom: 14 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: 9, color: "#4a7a8a" }}>{label}</span>
                    <span style={{ fontSize: 9, color: danger ? "#ff4d6d" : "#00ffc8", fontWeight: 700 }}>
                      {value.toFixed(1)} {danger ? "⚠ OVER LIMIT" : "✓"}
                    </span>
                  </div>
                  <input type="range" min={0} max={max} step={0.1} value={value}
                    onChange={e => set(parseFloat(e.target.value))}
                    style={{ width: "100%", accentColor: danger ? "#ff4d6d" : "#00ffc8" }} />
                  <div style={{ fontSize: 7, color: "#1a3040" }}>Limit: {limit}</div>
                </div>
              );
            })}
            <button onClick={test} style={{
              width: "100%", background: "linear-gradient(135deg, #ff4d6d15, #a0102015)",
              border: "1px solid #ff4d6d50", borderRadius: 8, padding: "8px 0",
              color: "#ff4d6d", fontSize: 10, cursor: "pointer", fontFamily: "inherit",
              letterSpacing: "0.1em",
            }}>SEND COMMAND →</button>
          </div>

          {/* Constraint reference */}
          <div style={{ background: "#040a0e", border: "1px solid #00ffc810", borderRadius: 10, padding: 12 }}>
            <div style={{ fontSize: 9, color: "#00ffc8", marginBottom: 8, fontWeight: 700 }}>HARD CONSTRAINTS</div>
            {[
              ["Force",    "< 10 N"],
              ["Angle",    "< 170°"],
              ["Velocity", "< 2 m/s"],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 9, marginBottom: 4 }}>
                <span style={{ color: "#2a6070" }}>{k}</span>
                <span style={{ color: "#00ffc8" }}>{v}</span>
              </div>
            ))}
            <div style={{ marginTop: 10, fontSize: 8, color: "#1a3040", lineHeight: 1.6 }}>
              Any violation triggers immediate reflex withdrawal.<br/>
              <span style={{ color: "#ff4d6d50" }}>No neural pathway can bypass this gate.</span>
            </div>
          </div>
        </div>

        {/* Log */}
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 9, color: "#2a6070", marginBottom: 8, letterSpacing: "0.15em" }}>COMMAND LOG</div>
          {log.length === 0 && (
            <div style={{ fontSize: 9, color: "#1a3040", padding: "20px 0" }}>No commands issued yet.</div>
          )}
          {log.map((e, i) => (
            <div key={i} style={{
              background: e.approved ? "#001a0a" : "#1a0006",
              border: `1px solid ${e.approved ? "#00ffc820" : "#ff4d6d40"}`,
              borderRadius: 8, padding: "8px 12px", marginBottom: 6,
              fontFamily: "inherit",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: e.approved ? "#00ffc8" : "#ff4d6d" }}>
                  {e.approved ? "✓ APPROVED" : "✗ BLOCKED"}
                </span>
                <span style={{ fontSize: 8, color: "#2a4050" }}>{e.t}</span>
              </div>
              <div style={{ fontSize: 8, color: "#2a6070" }}>
                F={e.cmd.force.toFixed(1)}N · A={e.cmd.angle.toFixed(1)}° · V={e.cmd.vel.toFixed(1)}m/s
              </div>
              <div style={{ fontSize: 8, color: e.approved ? "#1a4030" : "#4a0010", marginTop: 3 }}>{e.reason}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
