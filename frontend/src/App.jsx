import { useState, useEffect, useRef, useCallback } from 'react'

// ── Region definitions matching brain.py ───────────────────────────────────
const REGIONS = [
  { id: "sensory",      label: "Sensory Cortex",  color: "#4dffb4", baseAct: 10.1, neurons: "400",   desc: "Multimodal gateway. Encodes vision/audio/touch as Poisson spike trains." },
  { id: "feature",      label: "Feature Layer",   color: "#00cfff", baseAct: 18.1, neurons: "800",   desc: "Extracts edges, textures, phonemes from raw sensory streams." },
  { id: "association",  label: "Association",     color: "#00ffc8", baseAct: 31.2, neurons: "5000",  desc: "Cross-modal STDP hub. Binds 'face seen + voice heard'. Largest region." },
  { id: "predictive",   label: "Predictive",      color: "#ffb300", baseAct: 15.6, neurons: "1000",  desc: "Continuously predicts next inputs. Error signal drives attention gain." },
  { id: "concept",      label: "Concept Layer",   color: "#fd79a8", baseAct:  0.8, neurons: "100",   desc: "WTA sparse coding. 3–5 neurons fire per concept (e.g. 'dog')." },
  { id: "meta_control", label: "Meta Control",    color: "#b36bff", baseAct: 17.8, neurons: "600",   desc: "Top-down attention modulation across all regions." },
  { id: "working_memory",  label: "Working Memory",  color: "#ff9f43", baseAct:  3.0, neurons: "200",   desc: "Short-term spike buffer. Recurrent activity for temporal context." },
  { id: "cerebellum",   label: "Cerebellum",      color: "#a8e6cf", baseAct:  1.5, neurons: "150",   desc: "Fine motor timing. Eligibility trace sequence learning." },
  { id: "brainstem",    label: "Brainstem",       color: "#ffeaa7", baseAct:  1.5, neurons: "100",   desc: "Homeostatic regulation. Constant low-level arousal drive." },
  { id: "reflex_arc",   label: "Reflex Arc",      color: "#ff4d6d", baseAct: 13.2, neurons: "300",   desc: "SAFETY KERNEL. Force/angle/velocity hard gate on motor output." },
];

// ── Neural canvas particle system ──────────────────────────────────────────
function NeuralCanvas({ activeRegions, globalGain }) {
  const canvasRef = useRef(null);
  const stateRef  = useRef(null);
  const rafRef    = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const resize = () => {
      canvas.width  = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
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
        ctx.fillStyle = nd.spikeTimer > 0 ? col : `rgba(${rgb},0.5)`;
        ctx.fill();
      });

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas ref={canvasRef}
      style={{ width:"100%", height:"100%", display:"block" }} />
  );
}

// ── Reflex Arc Safety Panel ────────────────────────────────────────────────
function ReflexPanel() {
  const [force, setForce]    = useState(5.0);
  const [angle, setAngle]    = useState(90.0);
  const [vel, setVel]        = useState(1.0);
  const [log, setLog]        = useState([]);

  const FORCE_MAX = 10, ANGLE_MAX = 170, VEL_MAX = 2;

  const test = async () => {
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
    
    // Send to API
    try {
      const res = await fetch('/api/reflex/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force, angle, velocity: vel })
      });
      const data = await res.json();
      entry.approved = data.approved;
      entry.reason = data.reason || entry.reason;
    } catch (err) {
      console.error('Reflex check failed:', err);
    }
    
    setLog(prev => [entry, ...prev].slice(0, 20));
  };

  return (
    <div style={{ flex: 1, padding: "16px 24px", overflowY: "auto" }}>
      <div style={{ fontSize: "7px", letterSpacing: "0.25em", color: "#ff4d6d80", marginBottom: "16px" }}>
        REFLEX ARC — MOTOR SAFETY KERNEL
      </div>
      <div style={{ display: "flex", gap: "20px" }}>
        {/* Command builder */}
        <div style={{ width: "280px", flexShrink: 0 }}>
          <div style={{
            background: "#0a0206", border: "1px solid #ff4d6d30",
            borderRadius: "12px", padding: "16px", marginBottom: "12px",
          }}>
            <div style={{ fontSize: "10px", color: "#ff4d6d", marginBottom: "14px", fontWeight: 700 }}>MOTOR COMMAND BUILDER</div>
            {[
              { label: "Force (N)", value: force, set: setForce, max: 20, limit: FORCE_MAX },
              { label: "Angle (°)", value: angle, set: setAngle, max: 200, limit: ANGLE_MAX },
              { label: "Velocity (m/s)", value: vel, set: setVel, max: 5, limit: VEL_MAX },
            ].map(({ label, value, set, max, limit }) => {
              const danger = value > limit;
              return (
                <div key={label} style={{ marginBottom: "14px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                    <span style={{ fontSize: "9px", color: "#4a7a8a" }}>{label}</span>
                    <span style={{ fontSize: "9px", color: danger ? "#ff4d6d" : "#00ffc8", fontWeight: 700 }}>
                      {value.toFixed(1)} {danger ? "⚠ OVER LIMIT" : "✓"}
                    </span>
                  </div>
                  <input type="range" min={0} max={max} step={0.1} value={value}
                    onChange={e => set(parseFloat(e.target.value))}
                    style={{ width: "100%", accentColor: danger ? "#ff4d6d" : "#00ffc8" }} />
                  <div style={{ fontSize: "7px", color: "#1a3040" }}>Limit: {limit}</div>
                </div>
              );
            })}
            <button onClick={test} style={{
              width: "100%", background: "linear-gradient(135deg, #ff4d6d15, #a0102015)",
              border: "1px solid #ff4d6d50", borderRadius: "8px", padding: "8px 0",
              color: "#ff4d6d", fontSize: "10px", cursor: "pointer", fontFamily: "inherit",
              letterSpacing: "0.1em",
            }}>SEND COMMAND →</button>
          </div>

          {/* Constraint reference */}
          <div style={{ background: "#040a0e", border: "1px solid #00ffc810", borderRadius: "10px", padding: "12px" }}>
            <div style={{ fontSize: "9px", color: "#00ffc8", marginBottom: "8px", fontWeight: 700 }}>HARD CONSTRAINTS</div>
            {[
              ["Force",    "< 10 N"],
              ["Angle",    "< 170°"],
              ["Velocity", "< 2 m/s"],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", marginBottom: "4px" }}>
                <span style={{ color: "#2a6070" }}>{k}</span>
                <span style={{ color: "#00ffc8" }}>{v}</span>
              </div>
            ))}
            <div style={{ marginTop: "10px", fontSize: "8px", color: "#1a3040", lineHeight: 1.6 }}>
              Any violation triggers immediate reflex withdrawal.<br/>
              <span style={{ color: "#ff4d6d50" }}>No neural pathway can bypass this gate.</span>
            </div>
          </div>
        </div>

        {/* Log */}
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "9px", color: "#2a6070", marginBottom: "8px", letterSpacing: "0.15em" }}>COMMAND LOG</div>
          {log.length === 0 && (
            <div style={{ fontSize: "9px", color: "#1a3040", padding: "20px 0" }}>No commands issued yet.</div>
          )}
          {log.map((e, i) => (
            <div key={i} style={{
              background: e.approved ? "#001a0a" : "#1a0006",
              border: `1px solid ${e.approved ? "#00ffc820" : "#ff4d6d40"}`,
              borderRadius: "8px", padding: "8px 12px", marginBottom: "6px",
              fontFamily: "inherit",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{ fontSize: "10px", fontWeight: 700, color: e.approved ? "#00ffc8" : "#ff4d6d" }}>
                  {e.approved ? "✓ APPROVED" : "✗ BLOCKED"}
                </span>
                <span style={{ fontSize: "8px", color: "#2a4050" }}>{e.t}</span>
              </div>
              <div style={{ fontSize: "8px", color: "#2a6070" }}>
                F={e.cmd.force.toFixed(1)}N · A={e.cmd.angle.toFixed(1)}° · V={e.cmd.vel.toFixed(1)}m/s
              </div>
              <div style={{ fontSize: "8px", color: e.approved ? "#1a4030" : "#4a0010", marginTop: "3px" }}>{e.reason}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
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
  const [llmStatus, setLlmStatus]     = useState({ configured: false, backend: "none", model: null });

  // Chat state
  const [messages, setMessages]   = useState([
    { role: "brain", content: "BRAIN 2.0 initialised. Spiking neural network online.\n\nAll 10 regions active. STDP synapses forming. Send me a stimulus or ask anything about my architecture." }
  ]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const chatEndRef                = useRef(null);
  const inputRef                  = useRef(null);

  // Simulate live brain stats (or fetch from API)
  useEffect(() => {
    // Fetch LLM status on mount
    fetch('/api/llm/status')
      .then(r => r.ok ? r.json() : null)
      .then(data => data && setLlmStatus(data))
      .catch(() => {});

    const id = setInterval(async () => {
      // Try to fetch real brain state from API
      try {
        const res = await fetch('/api/brain/status');
        if (res.ok) {
          const data = await res.json();
          setStep(data.step || step);
          setStepRate(data.step_rate || stepRate);
          setBrainStatus(data.status || brainStatus);
          setPredError(data.prediction_error || predError);
          setGlobalGain(data.attention_gain || globalGain);
          if (data.regions) {
            // Transform API region data to UI format
            const regionActivity = {};
            Object.keys(data.regions).forEach(key => {
              const region = data.regions[key];
              // Use activity_pct from API, fallback to baseAct from REGIONS
              regionActivity[key] = region.activity_pct !== undefined ? region.activity_pct : 
                (REGIONS.find(r => r.id === key)?.baseAct || 10);
            });
            setActive(regionActivity);
          }
        }
      } catch (err) {
        // Fall back to simulated data
        setStep(s => s + Math.floor(Math.random() * 4 + 1));
        setStepRate(parseFloat((0.4 + Math.random() * 0.3).toFixed(2)));
        setPredError(parseFloat((Math.random() * 0.05).toFixed(4)));
        setGlobalGain(parseFloat((1 + Math.random() * 0.8).toFixed(3)));
      }
      // Note: Region activity now comes from real API data - no simulation drift
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

    // Spike active regions on new input
    setActive(prev => {
      const next = { ...prev };
      ["sensory","feature","association","predictive"].forEach(k => {
        next[k] = Math.min(60, prev[k] + Math.random() * 20 + 10);
      });
      return next;
    });
    setGlobalGain(parseFloat((2 + Math.random() * 2).toFixed(2)));

    try {
      // Send to Python API
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMsg,
          history: messages.slice(-6),
          brainState: {
            step, stepRate, brainStatus, predError, globalGain,
            regions: Object.fromEntries(
              REGIONS.map(r => [r.id, { activity_pct: activeRegions[r.id], neurons: r.neurons }])
            ),
          }
        })
      });
      let reply;
      let processingProgress = 0;
      if (res.ok) {
        const data = await res.json();
        reply = data.response || data.reply;
        processingProgress = 100;
      } else {
        // Fallback response if API fails
        reply = `[BRAIN 2.0] Processing "${userMsg}"... 

Simulated neural response: Input spike encoding complete. 
- Sensory cortex: activated (+15%)
- Feature extraction: edge detection in progress
- Association region: forming new pattern connections

Awaiting further stimuli.`;
        processingProgress = 50;
      }

      // Add processing info to reply
      const processingInfo = `\n\n⏳ Processing: ${processingProgress}% complete`;

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
          next.feature     = Math.min(60, prev.feature + 5);
        }
        return next;
      });

      setMessages(prev => [...prev, { role: "brain", content: reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "brain", content: `[BRAIN 2.0 ERROR] ${err.message}` }]);
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
          <div style={{ fontSize: "18px", fontWeight: 800, color: "#00ffc8", letterSpacing: "0.12em" }}>BRAIN 2.0</div>
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
          <div key={k} style={{ textAlign: "center", minWidth: "60px" }}>
            <div style={{ fontSize: "6px", letterSpacing: "0.2em", color: "#2a6070" }}>{k}</div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: k === "GAIN" && globalGain > 2 ? "#ffb300" : "#00ffc8" }}>{v}</div>
          </div>
        ))}
        <div style={{
          padding: "3px 10px", border: "1px solid #ffb30040",
          borderRadius: "20px", fontSize: "8px", letterSpacing: "0.15em",
          color: "#ffb300", background: "#ffb30010",
        }}>◉ {brainStatus}</div>
        <div style={{
          padding: "3px 10px", border: "1px solid #00ffc840",
          borderRadius: "20px", fontSize: "8px", letterSpacing: "0.15em",
          color: (llmStatus.configured && llmStatus.ollama_available) ? "#00ffc8" : "#ff4d6d",
          background: (llmStatus.configured && llmStatus.ollama_available) ? "#00ffc810" : "#ff4d6d10",
        }}>◉ LLM {llmStatus.ollama_available ? `ONLINE (${llmStatus.ollama_models?.length || 0} models)` : llmStatus.configured ? "CONFIGURED" : "OFFLINE"}</div>
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
              width: "180px", flexShrink: 0, padding: "14px 12px",
              borderRight: "1px solid #00ffc810", overflowY: "auto",
              display: "flex", flexDirection: "column", gap: "5px",
            }}>
              {REGIONS.map(r => {
                const act = activeRegions[r.id] || 0;
                const selected = selectedRegion === r.id;
                return (
                  <button key={r.id} onClick={() => setSelected(r.id)} style={{
                    background: selected ? `${r.color}10` : "transparent",
                    border: `1px solid ${selected ? r.color + "50" : "#ffffff08"}`,
                    borderRadius: "8px", padding: "7px 9px", cursor: "pointer", textAlign: "left",
                    transition: "all 0.15s",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                      <span style={{ fontSize: "9px", fontWeight: 700, color: selected ? r.color : "#5a8aa0" }}>{r.label}</span>
                      <span style={{ fontSize: "9px", color: r.color, opacity: 0.85 }}>{act.toFixed(1)}%</span>
                    </div>
                    <div style={{ height: "2px", background: "#ffffff08", borderRadius: "2px", overflow: "hidden" }}>
                      <div style={{
                        height: "100%", width: `${(act / 60) * 100}%`,
                        background: r.color, borderRadius: "2px",
                        transition: "width 0.4s ease",
                        boxShadow: `0 0 6px ${r.color}80`,
                      }} />
                    </div>
                    <div style={{ fontSize: "7px", color: "#1a4a5a", marginTop: "2px" }}>{r.neurons} neurons</div>
                  </button>
                );
              })}
            </div>

            {/* Canvas + Chat */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
              {/* Canvas */}
              <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
                <NeuralCanvas activeRegions={activeRegions} globalGain={globalGain} />
                <div style={{
                  position: "absolute", top: "12px", left: "14px",
                  fontSize: "8px", letterSpacing: "0.2em", color: "#00ffc850",
                }}>LIVE SPIKE ACTIVITY · {Object.values(activeRegions).reduce((a,b)=>a+b,0).toFixed(1)}% TOTAL</div>
                {globalGain > 2 && (
                  <div style={{
                    position: "absolute", top: "12px", right: "14px",
                    fontSize: "8px", color: "#ffb300", letterSpacing: "0.15em",
                    animation: "pulse 0.8s infinite",
                  }}>⚡ HIGH ATTENTION · ×{globalGain}</div>
                )}
              </div>
              {/* Chat Panel - Integrated */}
              <div style={{
                flexShrink: 0, height: "200px", display: "flex", flexDirection: "column",
                borderTop: "1px solid #00ffc810", background: "#02080e",
              }}>
                {/* Chat header */}
                <div style={{
                  padding: "6px 12px", borderBottom: "1px solid #00ffc808",
                  fontSize: "7px", letterSpacing: "0.2em", color: "#00ffc850",
                }}>NEURAL CHAT</div>
                {/* Chat messages */}
                <div style={{ flex: 1, overflowY: "auto", padding: "8px 12px", display: "flex", flexDirection: "column", gap: "6px" }}>
                  {messages.slice(-4).map((m, i) => (
                    <div key={i} style={{
                      display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                    }}>
                      <div style={{
                        maxWidth: "85%",
                        background: m.role === "user"
                          ? "linear-gradient(135deg, #0a2040, #051530)"
                          : "linear-gradient(135deg, #040e1e, #02080e)",
                        border: m.role === "user"
                          ? "1px solid #00cfff30"
                          : "1px solid #00ffc818",
                        borderRadius: m.role === "user"
                          ? "8px 8px 2px 8px"
                          : "8px 8px 8px 2px",
                        padding: "5px 8px",
                        fontSize: "9px", lineHeight: 1.4,
                        color: m.role === "user" ? "#a0d4f0" : "#c8e0f0",
                        whiteSpace: "pre-wrap",
                      }}>
                        {m.content.slice(0, 150)}{m.content.length > 150 ? "..." : ""}
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div style={{ display: "flex", gap: "4px", padding: "4px 8px" }}>
                      {[0,1,2].map(i => (
                        <div key={i} style={{
                          width: "5px", height: "5px", borderRadius: "50%",
                          background: "#00ffc8",
                          animation: `bounce 0.8s ${i*0.15}s infinite`,
                          opacity: 0.7,
                        }} />
                      ))}
                    </div>
                  )}
                </div>
                {/* Chat input */}
                <div style={{
                  flexShrink: 0, padding: "6px 10px",
                  borderTop: "1px solid #00ffc810",
                  display: "flex", gap: "6px",
                }}>
                  <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKey}
                    placeholder="Talk to brain..."
                    style={{
                      flex: 1, background: "#040e1e", border: "1px solid #00ffc820",
                      borderRadius: "6px", padding: "6px 10px", color: "#c8e0f0",
                      fontSize: "10px", outline: "none",
                    }}
                  />
                  <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                    background: loading ? "#040e1e" : "linear-gradient(135deg, #00ffc820, #00a89010)",
                    border: `1px solid ${loading ? "#00ffc820" : "#00ffc850"}`,
                    borderRadius: "6px", padding: "6px 10px", cursor: loading ? "not-allowed" : "pointer",
                    color: "#00ffc8", fontSize: "9px",
                    letterSpacing: "0.1em",
                  }}>
                    {loading ? "..." : "▶"}
                  </button>
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
              flexShrink: 0, display: "flex", gap: "4px", padding: "8px 16px",
              borderBottom: "1px solid #00ffc808", overflowX: "auto",
            }}>
              {REGIONS.map(r => (
                <div key={r.id} style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: "36px" }}>
                  <div style={{
                    width: "28px", height: "28px", borderRadius: "50%",
                    border: `1px solid ${r.color}40`,
                    background: `${r.color}${Math.floor((activeRegions[r.id] / 60) * 255).toString(16).padStart(2,"0")}`,
                    transition: "background 0.4s",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "7px", color: r.color, fontWeight: 700,
                  }}>{activeRegions[r.id]?.toFixed(0)}%</div>
                  <div style={{ fontSize: "5px", color: "#2a6070", marginTop: "2px", textAlign: "center", lineHeight: 1.1 }}>
                    {r.label.split(" ").map((w,i)=><div key={i}>{w.slice(0,5)}</div>)}
                  </div>
                </div>
              ))}
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto", padding: "14px 20px", display: "flex", flexDirection: "column", gap: "10px" }}>
              {messages.map((m, i) => (
                <div key={i} style={{
                  display: "flex",
                  justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                }}>
                  {m.role === "brain" && (
                    <div style={{
                      width: "22px", height: "22px", borderRadius: "50%", flexShrink: 0,
                      background: "radial-gradient(circle, #00ffc830 0%, transparent 70%)",
                      border: "1px solid #00ffc840",
                      marginRight: "8px", marginTop: "2px",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: "9px",
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
                    fontSize: "10px", lineHeight: 1.65,
                    color: m.role === "user" ? "#a0d4f0" : "#c8e0f0",
                    whiteSpace: "pre-wrap",
                  }}>
                    {m.role === "brain" && (
                      <div style={{ fontSize: "7px", color: "#00ffc850", letterSpacing: "0.2em", marginBottom: "4px" }}>BRAIN 2.0 · NEURAL RESPONSE</div>
                    )}
                    {m.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ display: "flex", gap: "5px", padding: "6px 12px" }}>
                  {[0,1,2].map(i => (
                    <div key={i} style={{
                      width: "6px", height: "6px", borderRadius: "50%",
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
              display: "flex", gap: "8px", alignItems: "center",
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
                  borderRadius: "8px", padding: "8px 12px", color: "#c8e0f0",
                  fontSize: "11px", fontFamily: "inherit", resize: "none",
                  outline: "none", lineHeight: 1.5,
                }}
              />
              <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                background: loading ? "#040e1e" : "linear-gradient(135deg, #00ffc820, #00a89010)",
                border: `1px solid ${loading ? "#00ffc820" : "#00ffc850"}`,
                borderRadius: "8px", padding: "8px 14px", cursor: loading ? "not-allowed" : "pointer",
                color: "#00ffc8", fontSize: "10px", fontFamily: "inherit",
                letterSpacing: "0.1em", transition: "all 0.15s",
              }}>
                {loading ? "..." : "FIRE ▶"}
              </button>
            </div>
          </div>
        )}

        {/* ── ARCHITECTURE TAB ── */}
        {tab === "arch" && (
          <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px", display: "flex", gap: "20px" }}>
            {/* Flow */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0", alignItems: "center" }}>
              <div style={{ fontSize: "7px", letterSpacing: "0.25em", color: "#2a6070", marginBottom: "10px" }}>INFORMATION FLOW</div>
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
                    borderRadius: "8px", padding: "8px 20px", minWidth: "280px", textAlign: "center",
                  }}>
                    <div style={{ fontSize: "10px", color: n.color, fontWeight: 700, letterSpacing: "0.08em" }}>{n.label}</div>
                    <div style={{ fontSize: "8px", color: "#2a6070", marginTop: "2px" }}>{n.sub}</div>
                  </div>
                  {i < arr.length - 1 && (
                    <div style={{ width: "1px", height: "14px", position: "relative",
                      background: `linear-gradient(${arr[i].color}60,${arr[i+1].color}60)` }}>
                      <div style={{ position:"absolute", bottom:"-2px", left:"-3px", color:arr[i+1].color, fontSize:"8px" }}>▼</div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* STDP + concepts */}
            <div style={{ width: "260px", flexShrink: 0, display: "flex", flexDirection: "column", gap: "10px" }}>
              {[
                { title: "STDP Rule",         color: "#00ffc8", body: "Pre fires BEFORE post → LTP: Δw = +A_plus·exp(−Δt/τ). Post before pre → LTD: Δw = −A_minus·exp(−Δt/τ). No global error. Purely local + temporal." },
                { title: "Predictive Loop",   color: "#ffb300", body: "Association → Predictive. Error = |actual − predicted|. gain = 1 + 4·error. High error → gain × applied to all STDP updates. Surprise accelerates learning." },
                { title: "WTA Sparse Coding", color: "#fd79a8", body: "5,800 concept neurons compete via lateral inhibition. Only 3–5 fire per concept. Each concept is an orthogonal sparse code. Efficient & discriminable." },
                { title: "Safety Kernel",     color: "#ff4d6d", body: "ReflexArc.check_command() intercepts every motor output. Force>10N, angle>170°, vel>2m/s → BLOCKED. Withdrawal reflex fires. Hard-gated — no ML pathway bypasses this." },
              ].map(c => (
                <div key={c.title} style={{
                  background: `${c.color}08`, border: `1px solid ${c.color}25`,
                  borderRadius: "10px", padding: "12px",
                }}>
                  <div style={{ fontSize: "9px", color: c.color, fontWeight: 700, marginBottom: "6px", letterSpacing: "0.08em" }}>{c.title}</div>
                  <div style={{ fontSize: "9px", color: "#4a7a8a", lineHeight: 1.65 }}>{c.body}</div>
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
