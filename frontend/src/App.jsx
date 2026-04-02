import React from 'react'
import { useState, useEffect, useRef, useCallback } from 'react'

const THEMES = {
  dark: {
    name: 'dark',
    fontFamily: "'JetBrains Mono', 'Cascadia Code', monospace",
    bgPrimary: '#09090b',
    bgSecondary: '#18181b',
    surface: '#0f172a',
    panel: '#0f172a',
    headerBg: 'linear-gradient(90deg, #020617 0%, #09090b 50%, #020617 100%)',
    textPrimary: '#f8fafc',
    textSecondary: '#94a3b8',
    textMuted: '#475569',
    border: 'rgba(255, 255, 255, 0.08)',
    borderSubtle: 'rgba(255, 255, 255, 0.05)',
    borderStrong: 'rgba(255, 255, 255, 0.12)',
    accent: '#22d3ee',
    accentAlt: '#fbbf24',
    accentSoft: '#22d3ee18',
    badgeBg: '#fbbf2415',
    badgeBorder: '#fbbf2440',
    llmOnlineBg: '#34d39915',
    llmOfflineBg: '#f8717110',
    llmOnlineColor: '#34d399',
    llmOfflineColor: '#f87171',
    chatBubbleUserBg: 'linear-gradient(135deg, #1e293b, #0f172a)',
    chatBubbleUserBorder: '#38bdf830',
    chatBubbleBrainBg: 'linear-gradient(135deg, #09090b, #020617)',
    chatBubbleBrainBorder: 'rgba(255, 255, 255, 0.08)',
    inputBg: '#0f172a',
    inputBorder: 'rgba(255, 255, 255, 0.10)',
  },
  light: {
    name: 'light',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    bgPrimary: '#f1f5f9',
    bgSecondary: '#e2e8f0',
    surface: '#ffffff',
    panel: '#ffffff',
    headerBg: '#ffffff',
    textPrimary: '#1e293b',
    textSecondary: '#475569',
    textMuted: '#64748b',
    border: '#cbd5e1',
    borderSubtle: '#e2e8f0',
    borderStrong: '#94a3b8',
    accent: '#0284c7',
    accentAlt: '#d97706',
    accentSoft: '#0284c718',
    badgeBg: '#d9770618',
    badgeBorder: '#d9770640',
    llmOnlineBg: '#10b98115',
    llmOfflineBg: '#ef444410',
    llmOnlineColor: '#059669',
    llmOfflineColor: '#dc2626',
    chatBubbleUserBg: '#0284c712',
    chatBubbleUserBorder: '#0284c740',
    chatBubbleBrainBg: '#ffffff',
    chatBubbleBrainBorder: '#cbd5e1',
    inputBg: '#f8fafc',
    inputBorder: '#cbd5e1',
  },
};

// ── Region definitions matching brain.py ───────────────────────────────────
const REGIONS = [
  { id: "sensory",      label: "Sensory Cortex",  color: "#38bdf8", baseAct: 10.1, neurons: "400",   desc: "Multimodal gateway. Encodes vision/audio/touch as Poisson spike trains." },
  { id: "feature",      label: "Feature Layer",   color: "#a78bfa", baseAct: 18.1, neurons: "800",   desc: "Extracts edges, textures, phonemes from raw sensory streams." },
  { id: "association",  label: "Association",     color: "#34d399", baseAct: 31.2, neurons: "5000",  desc: "Cross-modal STDP hub. Binds 'face seen + voice heard'. Largest region." },
  { id: "predictive",   label: "Predictive",      color: "#fb923c", baseAct: 15.6, neurons: "1000",  desc: "Continuously predicts next inputs. Error signal drives attention gain." },
  { id: "concept",      label: "Concept Layer",   color: "#f472b6", baseAct:  0.8, neurons: "100",   desc: "WTA sparse coding. 3–5 neurons fire per concept (e.g. 'dog')." },
  { id: "meta_control", label: "Meta Control",    color: "#818cf8", baseAct: 17.8, neurons: "600",   desc: "Top-down attention modulation across all regions." },
  { id: "working_memory",  label: "Working Memory",  color: "#6366f1", baseAct:  3.0, neurons: "200",   desc: "Short-term spike buffer. Recurrent activity for temporal context." },
  { id: "cerebellum",   label: "Cerebellum",      color: "#2dd4bf", baseAct:  1.5, neurons: "150",   desc: "Fine motor timing. Eligibility trace sequence learning." },
  { id: "brainstem",    label: "Brainstem",       color: "#fbbf24", baseAct:  1.5, neurons: "100",   desc: "Homeostatic regulation. Constant low-level arousal drive." },
  { id: "reflex_arc",   label: "Reflex Arc",      color: "#f87171", baseAct: 13.2, neurons: "300",   desc: "SAFETY KERNEL. Force/angle/velocity hard gate on motor output." },
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

      // Trail effect — dark background fade for obsidian feel
      ctx.fillStyle = "rgba(9,9,11,0.18)";
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

        // Draw axons — subtle semi-transparent lines, no glow
        nd.conn.forEach(ci => {
          const o = nodes[ci];
          const alpha = nd.spikeTimer > 0 ? 0.25 : 0.04;
          ctx.beginPath();
          ctx.moveTo(nd.x, nd.y);
          ctx.lineTo(o.x, o.y);
          ctx.strokeStyle = `rgba(${rgb},${alpha})`;
          ctx.lineWidth = nd.spikeTimer > 0 ? 0.6 : 0.3;
          ctx.stroke();

          if (nd.spikeTimer > 0) {
            const prog = (stateRef.current.t % 24) / 24;
            const px = nd.x + (o.x - nd.x) * prog;
            const py = nd.y + (o.y - nd.y) * prog;
            ctx.beginPath();
            ctx.arc(px, py, 1.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${rgb},0.9)`;
            ctx.fill();
          }
        });

        // Soma — glow only on active spikes, tight blur
        if (nd.spikeTimer > 0) {
          const grad = ctx.createRadialGradient(nd.x, nd.y, 0, nd.x, nd.y, 8);
          grad.addColorStop(0, `rgba(${rgb},0.6)`);
          grad.addColorStop(1, "rgba(0,0,0,0)");
          ctx.beginPath();
          ctx.arc(nd.x, nd.y, 8, 0, Math.PI * 2);
          ctx.fillStyle = grad;
          ctx.fill();
        }
        ctx.beginPath();
        ctx.arc(nd.x, nd.y, nd.r, 0, Math.PI * 2);
        ctx.fillStyle = nd.spikeTimer > 0 ? col : `rgba(${rgb},0.35)`;
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
function ReflexPanel({ theme }) {
  const { bgPrimary, bgSecondary, surface, panel, textPrimary, textSecondary, textMuted, border, borderSubtle, borderStrong, accent, accentAlt, accentSoft, llmOfflineColor, llmOnlineBg, llmOfflineBg } = theme;
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
      <div style={{ fontSize: "7px", letterSpacing: "0.25em", color: llmOfflineColor + "80", marginBottom: "16px" }}>
        REFLEX ARC — MOTOR SAFETY KERNEL
      </div>
      <div style={{ display: "flex", gap: "20px" }}>
        {/* Command builder */}
        <div style={{ width: "280px", flexShrink: 0 }}>
          <div style={{
            background: llmOfflineBg, border: `1px solid ${llmOfflineColor}30`,
            borderRadius: "12px", padding: "16px", marginBottom: "12px",
          }}>
            <div style={{ fontSize: "10px", color: llmOfflineColor, marginBottom: "14px", fontWeight: 700 }}>MOTOR COMMAND BUILDER</div>
            {[
              { label: "Force (N)", value: force, set: setForce, max: 20, limit: FORCE_MAX },
              { label: "Angle (°)", value: angle, set: setAngle, max: 200, limit: ANGLE_MAX },
              { label: "Velocity (m/s)", value: vel, set: setVel, max: 5, limit: VEL_MAX },
            ].map(({ label, value, set, max, limit }) => {
              const danger = value > limit;
              return (
                <div key={label} style={{ marginBottom: "14px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                    <span style={{ fontSize: "9px", color: textSecondary }}>{label}</span>
                    <span style={{ fontSize: "9px", color: danger ? llmOfflineColor : accent, fontWeight: 700 }}>
                      {value.toFixed(1)} {danger ? "⚠ OVER LIMIT" : "✓"}
                    </span>
                  </div>
                  <input type="range" min={0} max={max} step={0.1} value={value}
                    onChange={e => set(parseFloat(e.target.value))}
                    style={{ width: "100%", accentColor: danger ? llmOfflineColor : accent }} />
                  <div style={{ fontSize: "7px", color: textMuted }}>Limit: {limit}</div>
                </div>
              );
            })}
            <button onClick={test} style={{
              width: "100%", background: `linear-gradient(135deg, ${llmOfflineColor}15, ${llmOfflineColor}15)`,
              border: `1px solid ${llmOfflineColor}50`, borderRadius: "8px", padding: "8px 0",
              color: llmOfflineColor, fontSize: "10px", cursor: "pointer", fontFamily: "inherit",
              letterSpacing: "0.1em",
            }}>SEND COMMAND →</button>
          </div>

          {/* Constraint reference */}
          <div style={{ background: surface, border: `1px solid ${borderSubtle}`, borderRadius: "10px", padding: "12px" }}>
            <div style={{ fontSize: "9px", color: accent, marginBottom: "8px", fontWeight: 700 }}>HARD CONSTRAINTS</div>
            {[
              ["Force",    "< 10 N"],
              ["Angle",    "< 170°"],
              ["Velocity", "< 2 m/s"],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", marginBottom: "4px" }}>
                <span style={{ color: textMuted }}>{k}</span>
                <span style={{ color: accent }}>{v}</span>
              </div>
            ))}
            <div style={{ marginTop: "10px", fontSize: "8px", color: textMuted, lineHeight: 1.6 }}>
              Any violation triggers immediate reflex withdrawal.<br/>
              <span style={{ color: llmOfflineColor + "50" }}>No neural pathway can bypass this gate.</span>
            </div>
          </div>
        </div>

        {/* Log */}
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "9px", color: textMuted, marginBottom: "8px", letterSpacing: "0.15em" }}>COMMAND LOG</div>
          {log.length === 0 && (
            <div style={{ fontSize: "9px", color: textMuted, padding: "20px 0" }}>No commands issued yet.</div>
          )}
          {log.map((e, i) => (
            <div key={i} style={{
              background: e.approved ? llmOnlineBg : llmOfflineBg,
              border: `1px solid ${e.approved ? accent + "20" : llmOfflineColor + "40"}`,
              borderRadius: "8px", padding: "8px 12px", marginBottom: "6px",
              fontFamily: "inherit",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{ fontSize: "10px", fontWeight: 700, color: e.approved ? accent : llmOfflineColor }}>
                  {e.approved ? "✓ APPROVED" : "✗ BLOCKED"}
                </span>
                <span style={{ fontSize: "8px", color: textMuted }}>{e.t}</span>
              </div>
              <div style={{ fontSize: "8px", color: textMuted }}>
                F={e.cmd.force.toFixed(1)}N · A={e.cmd.angle.toFixed(1)}° · V={e.cmd.vel.toFixed(1)}m/s
              </div>
              <div style={{ fontSize: "8px", color: e.approved ? textMuted : llmOfflineColor + "80", marginTop: "3px" }}>{e.reason}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [themeName, setThemeName] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = window.localStorage.getItem('brain-theme');
      if (saved === 'light' || saved === 'dark') return saved;
    }
    return 'dark';
  });
  const theme = THEMES[themeName];
  const {
    fontFamily,
    bgPrimary,
    bgSecondary,
    surface,
    panel,
    headerBg,
    textPrimary,
    textSecondary,
    textMuted,
    border,
    borderSubtle,
    borderStrong,
    accent,
    accentAlt,
    accentSoft,
    badgeBg,
    badgeBorder,
    llmOnlineBg,
    llmOfflineBg,
    llmOnlineColor,
    llmOfflineColor,
    chatBubbleUserBg,
    chatBubbleUserBorder,
    chatBubbleBrainBg,
    chatBubbleBrainBorder,
    inputBg,
    inputBorder,
  } = theme;

  const toggleTheme = useCallback(() => {
    setThemeName(prev => (prev === 'dark' ? 'light' : 'dark'));
  }, []);
  const themeToggleLabel = theme.name === 'dark' ? '☀ LIGHT' : '☾ DARK';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('brain-theme', theme.name);
    }
    document.body.style.background = bgPrimary;
    document.body.style.color = textPrimary;
    document.body.style.fontFamily = fontFamily;
  }, [bgPrimary, fontFamily, textPrimary, theme]);

  const [tab, setTab]               = useState("brain");
  const [debugLogs, setDebugLogs]     = useState([]);

  // Helper to add debug logs
  const addDebugLog = useCallback((type, endpoint, request, response) => {
    setDebugLogs(prev => [{
      timestamp: new Date().toISOString(),
      type,
      endpoint,
      request: typeof request === 'string' ? request : JSON.stringify(request, null, 2),
      response: typeof response === 'string' ? response : JSON.stringify(response, null, 2),
    }, ...prev].slice(0, 50)); // Keep last 50 logs
  }, []);
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

  // Affect / drives / thoughts state
  const [affect, setAffect]       = useState({ valence: 0.0, arousal: 0.3 });
  const [drives, setDrives]       = useState({ curiosity: 0.5, competence: 0.5, connection: 0.5 });
  const [thoughts, setThoughts]   = useState([]);

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
          // Extract affect
          if (data.affect) {
            setAffect({ valence: data.affect.valence ?? 0, arousal: data.affect.arousal ?? 0.3 });
          }
          // Extract drives
          if (data.drives) {
            setDrives({
              curiosity: data.drives.curiosity ?? 0.5,
              competence: data.drives.competence ?? 0.5,
              connection: data.drives.connection ?? 0.5,
            });
          }
          // Generate a thought from current state — only when there is real activity
          if (data.regions) {
            const concept = data.regions.concept?.activity_pct || 0;
            const assoc = data.regions.association?.activity_pct || 0;
            const pred = data.prediction_error || 0;
            const gain = data.attention_gain || 1;
            const st = data.step || 0;
            const totalActivity = Object.values(data.regions).reduce((a, r) => a + (r.activity_pct || 0), 0);
            let thought = null;
            if (pred > 0.05) thought = `Prediction error: ${pred.toFixed(3)} — adjusting weights`;
            else if (concept > 5) thought = `Concept layer active: ${concept.toFixed(1)}%`;
            else if (gain > 2.5) thought = `High attention — gain ×${gain.toFixed(1)}`;
            else if (assoc > 5) thought = `Association forming: ${assoc.toFixed(1)}% activity`;
            else if (st % 1000 < 5) thought = `Step ${st.toLocaleString()} milestone`;
            // Only push a thought if there is real neural activity or a milestone
            if (thought && totalActivity > 0.1) {
              setThoughts(prev => [...prev.slice(-7), thought]);
            }
          }
        }
      } catch (err) {
        // Fall back to simulated data
        setStep(s => s + Math.floor(Math.random() * 4 + 1));
        setStepRate(parseFloat((0.4 + Math.random() * 0.3).toFixed(2)));
        setPredError(parseFloat((Math.random() * 0.05).toFixed(4)));
        setGlobalGain(parseFloat((1 + Math.random() * 0.8).toFixed(3)));
      }
      // Poll proactive messages
      try {
        const pRes = await fetch('/api/proactive');
        if (pRes.ok) {
          const pData = await pRes.json();
          if (pData.messages && pData.messages.length > 0) {
            setMessages(prev => [
              ...prev,
              ...pData.messages.map(m => ({ role: "brain", content: m, isProactive: true }))
            ]);
          }
        }
      } catch {}
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
      let reply;
      let processingProgress = 0;

      // Check for /grep command
      if (userMsg.startsWith('/grep')) {
        // Parse /grep <n> <url>
        const parts = userMsg.split(/\s+/);
        if (parts.length >= 3) {
          const n = parseInt(parts[1], 10);
          const url = parts.slice(2).join(' ');
          
          if (isNaN(n) || !url) {
            reply = `[GREP] Invalid syntax. Use: /grep <n> <url>\nExample: /grep 3 https://example.com`;
            processingProgress = 100;
          } else {
            // Call the grep API
            const grepRes = await fetch('/api/grep', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ n, url })
            });
            
            addDebugLog('REQUEST', '/api/grep', { n, url }, '');
            
            if (grepRes.ok) {
              const data = await grepRes.json();
              addDebugLog('RESPONSE', '/api/grep', { n, url }, data);
              reply = `[GREP] Crawled ${data.crawled} of ${data.requested} pages from ${data.start_url}\n\n`;
              
              data.results.forEach((r, i) => {
                if (r.error) {
                  reply += `${i+1}. ${r.url}: ERROR - ${r.error}\n\n`;
                } else {
                  reply += `${i+1}. ${r.url} (${r.status})\n`;
                  // Show first 500 chars of content
                  const content = r.content.substring(0, 500);
                  reply += `   ${content}${r.content.length > 500 ? '...' : ''}\n\n`;
                }
              });
              processingProgress = 100;
            } else {
              reply = `[GREP] API Error: ${grepRes.status}`;
              processingProgress = 50;
            }
          }
        } else {
          reply = `[GREP] Invalid syntax. Use: /grep <n> <url>\nExample: /grep 3 https://example.com`;
          processingProgress = 100;
        }
      } else if (userMsg.startsWith('/llm')) {
        // Parse /llm <prompt>
        const prompt = userMsg.substring(4).trim();
        
        if (!prompt) {
          reply = `[LLM] Invalid syntax. Use: /llm <prompt>\nExample: /llm What is the capital of France?`;
          processingProgress = 100;
        } else {
          // Call the LLM API directly
          const llmRes = await fetch('/api/llm/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
          });
          
          addDebugLog('REQUEST', '/api/llm/chat', { prompt }, '');
          
          if (llmRes.ok) {
            const data = await llmRes.json();
            addDebugLog('RESPONSE', '/api/llm/chat', { prompt }, data);
            reply = `[LLM] Response:\n\n${data.response || data.reply || data.message}`;
            processingProgress = 100;
          } else {
            reply = `[LLM] API Error: ${llmRes.status}. Make sure Ollama is running.`;
            processingProgress = 50;
          }
        }
      } else if (userMsg.startsWith('/yt')) {
        // Parse /yt <n> <url>
        const parts = userMsg.substring(3).trim().split(/\s+/);
        const n = parseInt(parts[0]) || 1;
        const url = parts.slice(1).join(' ');
        
        if (!url || !url.includes('youtube.com') && !url.includes('youtu.be')) {
          reply = `[YT] Invalid syntax. Use: /yt <n> <youtube_url>\nExample: /yt 2 https://www.youtube.com/watch?v=VIDEO_ID`;
          processingProgress = 100;
        } else {
          const ytRes = await fetch('/api/yt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, n: Math.min(n, 10) })
          });
          
          addDebugLog('REQUEST', '/api/yt', { url, n }, '');
          
          if (ytRes.ok) {
            const data = await ytRes.json();
            addDebugLog('RESPONSE', '/api/yt', { url, n }, data);
            
            const lines = [`[YT] Transcribed ${data.videos_processed} video(s) — Vocabulary: ${data.vocabulary_size} words\n`];
            data.results.forEach(r => {
              if (r.error) {
                lines.push(`✗ ${r.title}: ${r.error}`);
              } else {
                lines.push(`✓ ${r.title}`);
                lines.push(`  ${r.transcript_length} chars | ${r.words_learned} words learned | ${Math.round(r.duration)}s`);
              }
            });
            reply = lines.join('\n');
            processingProgress = 100;
          } else {
            reply = `[YT] API Error: ${ytRes.status}`;
            processingProgress = 50;
          }
        }
      } else if (userMsg.startsWith('/api')) {
        try {
          const apiRes = await fetch('/api');
          addDebugLog('REQUEST', '/api', {}, '');

          if (apiRes.ok) {
            const apiData = await apiRes.json();
            addDebugLog('RESPONSE', '/api', {}, apiData);
            reply = `🔗 API ENTRYPOINTS\nOpenAPI: ${apiData.openapi}\nDocs: ${apiData.docs}`;
            processingProgress = 100;
          } else {
            reply = `[API] Unable to fetch API links. Status: ${apiRes.status}`;
            processingProgress = 60;
          }
        } catch (err) {
          reply = `[API] Error fetching docs: ${err.message}`;
          processingProgress = 40;
        }
      } else if (userMsg.startsWith('/stats')) {
        // Generate brain statistics report
        const totalActivity = Object.values(activeRegions).reduce((a, b) => a + b, 0);
        const avgActivity = (totalActivity / Object.keys(activeRegions).length).toFixed(2);
        const mostActive = Object.entries(activeRegions).sort((a, b) => b[1] - a[1])[0];
        const leastActive = Object.entries(activeRegions).sort((a, b) => a[1] - b[1])[0];
        
        // Calculate learning indicators
        const stdpScore = (activeRegions.association + activeRegions.feature) / 2;
        const memoryLoad = activeRegions.working_mem;
        const predictionAccuracy = Math.max(0, 100 - predError * 10).toFixed(1);
        
        // Calculate processing efficiency
        const throughput = (stepRate * globalGain).toFixed(2);
        const neuralEfficiency = (totalActivity / (globalGain * 10) * 100).toFixed(1);
        
        // Generate region breakdown
        let regionStats = '\n📊 REGION ACTIVITY BREAKDOWN:\n';
        REGIONS.forEach(r => {
          const activity = activeRegions[r.id] || 0;
          const bar = '█'.repeat(Math.floor(activity / 5)) + '░'.repeat(12 - Math.floor(activity / 5));
          const percentage = ((activity / 60) * 100).toFixed(1);
          regionStats += `   ${r.label.padEnd(18)} [${bar}] ${percentage}%\n`;
        });
        
        // Calculate spike statistics
        const totalSpikes = Math.floor(step * globalGain * 0.1);
        const spikesPerSecond = Math.floor(stepRate * globalGain);
        
        // Memory and concept formation stats
        const conceptDensity = (activeRegions.concept / 60 * 100).toFixed(1);
        const workingMemoryLoad = (activeRegions.working_mem / 60 * 100).toFixed(1);
        
        reply = `🧠 BRAIN 2.0 STATISTICS REPORT
═══════════════════════════════════════════

⏱️  SIMULATION METRICS:
   Current Step: ${step.toLocaleString()}
   Step Rate: ${stepRate} steps/sec
   Global Gain: ${globalGain}
   Prediction Error: ${predError.toFixed(4)}

⚡ PROCESSING PERFORMANCE:
   Neural Throughput: ${throughput} spikes/sec
   Processing Efficiency: ${neuralEfficiency}%
   System Load: ${(globalGain * 100 / 5).toFixed(1)}%

🧠 CORTICAL ACTIVITY:
   Total Activity: ${totalActivity.toFixed(2)} units
   Average Activity: ${avgActivity}%
   Most Active: ${mostActive[0]} (${mostActive[1].toFixed(1)})
   Least Active: ${leastActive[0]} (${leastActive[1].toFixed(1)})

${regionStats}
📈 LEARNING INDICATORS:
   STDP Synaptic Plasticity: ${stdpScore.toFixed(1)}%
   Concept Formation: ${conceptDensity}%
   Working Memory Load: ${workingMemoryLoad}%
   Prediction Accuracy: ${predictionAccuracy}%

💬 CONVERSATION HISTORY:
   Total Messages: ${messages.length}
   User Messages: ${messages.filter(m => m.role === 'user').length}
   Brain Responses: ${messages.filter(m => m.role === 'brain').length}

🔬 TECHNICAL PARAMETERS:
   Spike Trains: Poisson (λ=${globalGain.toFixed(2)})
   STDP Window: 20ms (LTP) / 20ms (LTD)
   Refractory Period: 2ms
   Membrane Time Constant: 20ms

Status: ${brainStatus}
══════════════════════════════════════════════`;
        processingProgress = 100;
      } else if (userMsg === '/vocabulary') {
        // Show learned vocabulary
        try {
          const vocabRes = await fetch('/api/vocabulary');
          if (vocabRes.ok) {
            const data = await vocabRes.json();
            const asmRes = await fetch('/api/assemblies');
            const asmData = asmRes.ok ? await asmRes.json() : {};
            
            const words = data.words || [];
            reply = `📚 BRAIN 2.0 VOCABULARY
══════════════════════════════════════════════

Words learned: ${data.vocabulary_size || 0}
Assemblies: ${data.assembly_coverage || 0}
Total generations: ${data.total_generations || 0}
Successful: ${data.successful_generations || 0}
Success rate: ${((data.success_rate || 0) * 100).toFixed(1)}%

Vocabulary:
${words.length > 0 ? words.join(', ') : '(no words learned yet)'}
`;
            if (asmData.total_assemblies > 0) {
              reply += `\nStable assemblies: ${asmData.total_assemblies}`;
              reply += `\nTotal activations: ${asmData.total_activations || 0}`;
            }
            reply += `\n══════════════════════════════════════════════`;
          } else {
            reply = `[VOCAB] API Error: ${vocabRes.status}`;
          }
        } catch (e) {
          reply = `[VOCAB] Error: ${e.message}`;
        }
        processingProgress = 100;
      } else if (userMsg === '/?' || userMsg === '/help') {
        // Show all available commands
        reply = `📋 BRAIN 2.0 COMMAND REFERENCE
══════════════════════════════════════════════

Available Commands:

1. /stats
   Displays comprehensive brain statistics including:
   - Simulation metrics (step, rate, gain)
   - Cortical activity breakdown per region
   - Learning indicators (STDP, concepts)
   - Processing efficiency metrics

2. /vocabulary
   Shows learned vocabulary and assembly stats.
   - Words learned by the SNN
   - Assembly count and activation stats
   - Generation success rate

3. /grep <n> <url>
   Crawls web pages and extracts content.
   - <n>: Number of pages to crawl (1-10)
   - <url>: Starting URL for crawl
   Example: /grep 3 https://example.com

4. /llm <prompt>
   Sends direct query to LLM (Ollama).
   - <prompt>: Your question or command
   Example: /llm What is neural plasticity?

5. /yt <n> <url>
   Transcribes YouTube videos and teaches the brain.
   - <n>: Number of videos to process (1-10)
   - <url>: YouTube video URL
   Supports playlists and video chains.
   Example: /yt 3 https://youtube.com/watch?v=VIDEO_ID

6. /api
   Returns direct links to OpenAPI JSON and FastAPI docs.

7. /? or /help
   Shows this command reference.

8. Any other text
   Sends message to brain for processing.
   The brain will analyze and respond using
   its neural network architecture.

══════════════════════════════════════════════
Tip: Use /stats to monitor brain performance!`;
        processingProgress = 100;
      } else {
        // Normal chat message - send to Python API
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
        
        addDebugLog('REQUEST', '/api/chat', { message: userMsg }, '');
        
        if (res.ok) {
          const data = await res.json();
          addDebugLog('RESPONSE', '/api/chat', { message: userMsg }, data);
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
      }

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
      fontFamily,
      background: bgPrimary,
      color: textPrimary,
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      transition: "background 0.3s ease, color 0.3s ease",
    }}>
      <header style={{
        padding: "10px 20px",
        borderBottom: `1px solid ${border}`,
        display: "flex",
        alignItems: "center",
        gap: "16px",
        background: headerBg,
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: "18px", fontWeight: 800, color: accent, letterSpacing: "0.12em" }}>BRAIN 2.0</div>
          <div style={{ fontSize: "7px", letterSpacing: "0.3em", color: textMuted, marginTop: "1px" }}>NEUROMORPHIC INTELLIGENCE · SNN RUNTIME</div>
        </div>

        <div style={{ flex: 1 }} />

        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          {[["NEURONS", "~858k"], ["SYNAPSES", "~80M"], ["STEP", fmt(step)], ["RATE", `${stepRate} st/s`]].map(([k, v]) => (
            <div key={k} style={{ textAlign: "center", minWidth: "60px" }}>
              <div style={{ fontSize: "6px", letterSpacing: "0.2em", color: textMuted }}>{k}</div>
              <div style={{ fontSize: "11px", fontWeight: 700, color: accent }}>{v}</div>
            </div>
          ))}

          <div style={{
            padding: "3px 10px",
            border: `1px solid ${llmStatus.configured && llmStatus.ollama_available ? accent : borderStrong}`,
            borderRadius: "20px",
            fontSize: "8px",
            letterSpacing: "0.15em",
            color: (llmStatus.configured && llmStatus.ollama_available) ? llmOnlineColor : llmOfflineColor,
            background: (llmStatus.configured && llmStatus.ollama_available) ? llmOnlineBg : llmOfflineBg,
          }}>
            ◉ LLM {llmStatus.ollama_available ? `ONLINE (${llmStatus.ollama_models?.length || 0} models)` : llmStatus.configured ? "CONFIGURED" : "OFFLINE"}
          </div>
        </div>
      </header>

      {/* ── TABS ── */}
      <div style={{
        display: "flex", borderBottom: `1px solid ${borderSubtle}`,
        padding: "0 20px", flexShrink: 0,
      }}>
        {[["brain","BRAIN ACTIVITY"],["chat","NEURAL CHAT"],["arch","ARCHITECTURE"],["reflex","SAFETY KERNEL"],["debug","DEBUG"]].map(([id, lbl]) => (
          <button key={id} onClick={() => setTab(id)} style={{
            background: "none", border: "none", cursor: "pointer",
            padding: "8px 16px", fontSize: "8px", letterSpacing: "0.18em",
            color: tab === id ? accent : textMuted,
            borderBottom: tab === id ? `2px solid ${accent}` : "2px solid transparent",
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
              borderRight: `1px solid ${borderSubtle}`, overflowY: "auto",
              display: "flex", flexDirection: "column", gap: "5px",
            }}>
              {REGIONS.map(r => {
                const act = activeRegions[r.id] || 0;
                const selected = selectedRegion === r.id;
                return (
                  <button key={r.id} onClick={() => setSelected(r.id)} style={{
                    background: selected ? `${r.color}10` : surface,
                    border: `1px solid ${selected ? r.color + "50" : borderSubtle}`,
                    borderRadius: "8px", padding: "7px 9px", cursor: "pointer", textAlign: "left",
                    transition: "all 0.15s",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                      <span style={{ fontSize: "9px", fontWeight: 700, color: selected ? r.color : textSecondary }}>{r.label}</span>
                      <span style={{ fontSize: "9px", color: r.color, opacity: 0.85 }}>{act.toFixed(1)}%</span>
                    </div>
                    <div style={{ height: "2px", background: borderSubtle, borderRadius: "2px", overflow: "hidden" }}>
                      <div style={{
                        height: "100%", width: `${(act / 60) * 100}%`,
                        background: r.color, borderRadius: "2px",
                        transition: "width 0.4s ease",
                        boxShadow: `0 0 6px ${r.color}80`,
                      }} />
                    </div>
                    <div style={{ fontSize: "7px", color: textMuted, marginTop: "2px" }}>{r.neurons} neurons</div>
                  </button>
                );
              })}
            </div>

            {/* Canvas + Chat (flex: 1) */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
              {/* Canvas */}
              <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
                <NeuralCanvas activeRegions={activeRegions} globalGain={globalGain} />
                <div style={{
                  position: "absolute", top: "12px", left: "14px",
                  fontSize: "8px", letterSpacing: "0.2em", color: `${accent}50`,
                }}>LIVE SPIKE ACTIVITY · {Object.values(activeRegions).reduce((a,b)=>a+b,0).toFixed(1)}% TOTAL</div>
                {/* Region legend */}
                <div style={{
                  position: "absolute", top: "12px", right: "14px",
                  display: "flex", flexDirection: "column", gap: "2px",
                  background: `${bgPrimary}cc`, backdropFilter: "blur(8px)",
                  borderRadius: "6px", padding: "6px 8px",
                  border: `1px solid ${borderSubtle}`,
                }}>
                  {REGIONS.map(r => (
                    <div key={r.id} style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                      <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: r.color }} />
                      <span style={{ fontSize: "7px", color: textMuted, letterSpacing: "0.05em" }}>{r.label.split(" ")[0]}</span>
                    </div>
                  ))}
                </div>
                {/* Region legend */}
                <div style={{
                  position: "absolute", top: "12px", right: "14px",
                  display: "flex", flexDirection: "column", gap: "2px",
                  background: `${bgPrimary}cc`, backdropFilter: "blur(8px)",
                  borderRadius: "6px", padding: "6px 8px",
                  border: `1px solid ${borderSubtle}`,
                }}>
                  {REGIONS.map(r => (
                    <div key={r.id} style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                      <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: r.color }} />
                      <span style={{ fontSize: "7px", color: textMuted, letterSpacing: "0.05em" }}>{r.label.split(" ")[0]}</span>
                    </div>
                  ))}
                </div>
                {globalGain > 2 && (
                  <div style={{
                    position: "absolute", top: "12px", right: "14px",
                    fontSize: "8px", color: accentAlt, letterSpacing: "0.15em",
                    animation: "pulse 0.8s infinite",
                  }}>⚡ HIGH ATTENTION · ×{globalGain}</div>
                )}
              </div>
              {/* Chat Panel - Integrated */}
              <div style={{
                flexShrink: 0, height: "200px", display: "flex", flexDirection: "column",
                borderTop: `1px solid ${borderSubtle}`, background: panel,
              }}>
                {/* Chat header */}
                <div style={{
                  padding: "6px 12px", borderBottom: `1px solid ${borderSubtle}`,
                  fontSize: "7px", letterSpacing: "0.2em", color: `${accent}50`,
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
                          ? chatBubbleUserBg
                          : chatBubbleBrainBg,
                        border: m.role === "user"
                          ? chatBubbleUserBorder
                          : chatBubbleBrainBorder,
                        borderRadius: m.role === "user"
                          ? "8px 8px 2px 8px"
                          : "8px 8px 8px 2px",
                        padding: "5px 8px",
                        fontSize: "9px", lineHeight: 1.4,
                        color: m.role === "user" ? textPrimary : textSecondary,
                        whiteSpace: "pre-wrap",
                      }}>
                        {m.content}
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div style={{ display: "flex", gap: "4px", padding: "4px 8px" }}>
                      {[0,1,2].map(i => (
                        <div key={i} style={{
                          width: "5px", height: "5px", borderRadius: "50%",
                          background: accent,
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
                  borderTop: `1px solid ${borderSubtle}`,
                  display: "flex", gap: "6px",
                }}>
                  <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKey}
                    placeholder="Talk to brain..."
                    style={{
                      flex: 1, background: inputBg, border: `1px solid ${inputBorder}`,
                      borderRadius: "6px", padding: "6px 10px", color: textPrimary,
                      fontSize: "10px", outline: "none",
                    }}
                  />
                  <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                    background: loading ? inputBg : accentSoft,
                    border: `1px solid ${loading ? "#00ffc820" : "#00ffc850"}`,
                    borderRadius: "6px", padding: "6px 10px", cursor: loading ? "not-allowed" : "pointer",
                    color: accent, fontSize: "9px",
                    letterSpacing: "0.1em",
                  }}>
                    {loading ? "..." : "▶"}
                  </button>
                </div>
              </div>
            </div>

            {/* ── Right Column (180px): Emotion / Thinking / Extended ── */}
            <div style={{
              width: "180px", flexShrink: 0,
              borderLeft: `1px solid ${borderSubtle}`,
              display: "flex", flexDirection: "column",
              overflow: "hidden",
            }}>
              {/* Emotion Panel (1/3) */}
              <div style={{
                flex: 1, padding: "10px 12px",
                borderBottom: `1px solid ${borderSubtle}`,
                display: "flex", flexDirection: "column", alignItems: "center",
                justifyContent: "center", gap: "6px",
              }}>
                <div style={{ fontSize: "7px", letterSpacing: "0.2em", color: `${accent}50`, marginBottom: "2px" }}>
                  AFFECTIVE STATE
                </div>
                {/* Face emoji from valence/arousal quadrant */}
                <div style={{ fontSize: "32px", lineHeight: 1 }}>
                  {(() => {
                    const v = affect.valence;
                    const a = affect.arousal;
                    if (a > 0.5 && v > 0.3) return "😊";
                    if (a > 0.5 && v < -0.3) return "😠";
                    if (a <= 0.5 && v > 0.3) return "😌";
                    if (a <= 0.5 && v < -0.3) return "😔";
                    return "😐";
                  })()}
                </div>
                {/* Mood label */}
                <div style={{ fontSize: "8px", color: textSecondary }}>
                  {(() => {
                    const v = affect.valence;
                    const a = affect.arousal;
                    if (a > 0.5 && v > 0.3) return "Excited";
                    if (a > 0.5 && v < -0.3) return "Stressed";
                    if (a <= 0.5 && v > 0.3) return "Calm";
                    if (a <= 0.5 && v < -0.3) return "Low";
                    return "Neutral";
                  })()}
                </div>
                {/* Valence bar */}
                <div style={{ width: "100%", marginTop: "2px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "6px", color: textMuted, marginBottom: "2px" }}>
                    <span>Valence</span>
                    <span>{affect.valence.toFixed(2)}</span>
                  </div>
                  <div style={{ height: "4px", background: borderSubtle, borderRadius: "2px", overflow: "hidden", position: "relative" }}>
                    <div style={{
                      position: "absolute", top: 0,
                      left: affect.valence < 0 ? `${50 + affect.valence * 50}%` : "50%",
                      width: `${Math.abs(affect.valence) * 50}%`,
                      height: "100%",
                      background: affect.valence >= 0 ? accent : llmOfflineColor,
                      borderRadius: "2px",
                      transition: "all 0.4s ease",
                    }} />
                    <div style={{
                      position: "absolute", top: 0, left: "50%",
                      width: "1px", height: "100%", background: borderStrong,
                    }} />
                  </div>
                </div>
                {/* Arousal bar */}
                <div style={{ width: "100%", marginTop: "2px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "6px", color: textMuted, marginBottom: "2px" }}>
                    <span>Arousal</span>
                    <span>{affect.arousal.toFixed(2)}</span>
                  </div>
                  <div style={{ height: "4px", background: borderSubtle, borderRadius: "2px", overflow: "hidden" }}>
                    <div style={{
                      height: "100%", width: `${affect.arousal * 100}%`,
                      background: `linear-gradient(90deg, ${accent}, ${llmOfflineColor})`,
                      borderRadius: "2px",
                      transition: "width 0.4s ease",
                    }} />
                  </div>
                </div>
                {/* Drive indicators */}
                <div style={{ width: "100%", marginTop: "6px" }}>
                  <div style={{ fontSize: "6px", color: textMuted, marginBottom: "3px", letterSpacing: "0.1em" }}>DRIVES</div>
                  {[
                    { label: "Curiosity", value: drives.curiosity, color: accent },
                    { label: "Competence", value: drives.competence, color: accentAlt },
                    { label: "Connection", value: drives.connection, color: llmOnlineColor },
                  ].map(d => (
                    <div key={d.label} style={{ display: "flex", alignItems: "center", gap: "4px", marginBottom: "2px" }}>
                      <span style={{ fontSize: "6px", color: textMuted, width: "50px" }}>{d.label}</span>
                      <div style={{ flex: 1, height: "3px", background: borderSubtle, borderRadius: "2px", overflow: "hidden" }}>
                        <div style={{ height: "100%", width: `${d.value * 100}%`, background: d.color, borderRadius: "2px", transition: "width 0.4s" }} />
                      </div>
                      <span style={{ fontSize: "6px", color: textMuted, width: "24px", textAlign: "right" }}>{(d.value * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Thinking Panel (1/3) */}
              <div style={{
                flex: 1, padding: "10px 12px",
                borderBottom: `1px solid ${borderSubtle}`,
                display: "flex", flexDirection: "column",
                overflow: "hidden",
              }}>
                <div style={{ fontSize: "7px", letterSpacing: "0.2em", color: `${accent}50`, marginBottom: "6px" }}>
                  THINKING
                </div>
                <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "4px" }}>
                  {thoughts.length === 0 && (
                    <div style={{ fontSize: "8px", color: textMuted, padding: "8px 0" }}>
                      Awaiting neural activity...
                    </div>
                  )}
                  {thoughts.map((t, i) => (
                    <div key={i} style={{
                      fontSize: "8px",
                      color: i === thoughts.length - 1 ? textPrimary : textSecondary,
                      padding: "3px 6px",
                      background: i === thoughts.length - 1 ? accentSoft : "transparent",
                      borderRadius: "4px",
                      borderLeft: i === thoughts.length - 1 ? `2px solid ${accent}40` : "2px solid transparent",
                      transition: "all 0.3s ease",
                      lineHeight: 1.4,
                    }}>
                      {t}
                    </div>
                  ))}
                </div>
              </div>

              {/* Empty / Extended Panel (1/3) */}
              <div style={{
                flex: 1, padding: "10px 12px",
                display: "flex", flexDirection: "column", alignItems: "center",
                justifyContent: "flex-start",
              }}>
                <div style={{ fontSize: "7px", letterSpacing: "0.2em", color: `${accent}50`, marginBottom: "4px" }}>
                  EXTENDED
                </div>
                <div style={{ fontSize: "7px", color: textMuted }}>(reserved)</div>
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
              borderBottom: `1px solid ${borderSubtle}`, overflowX: "auto",
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
                  <div style={{ fontSize: "5px", color: textMuted, marginTop: "2px", textAlign: "center", lineHeight: 1.1 }}>
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
                      background: `radial-gradient(circle, ${accent}30 0%, transparent 70%)`,
                      border: `1px solid ${accent}40`,
                      marginRight: "8px", marginTop: "2px",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: "9px",
                    }}>⬡</div>
                  )}
                  <div style={{
                    maxWidth: "72%",
                    background: m.role === "user"
                      ? chatBubbleUserBg
                      : chatBubbleBrainBg,
                    border: m.role === "user"
                      ? chatBubbleUserBorder
                      : chatBubbleBrainBorder,
                    borderRadius: m.role === "user"
                      ? "12px 12px 2px 12px"
                      : "12px 12px 12px 2px",
                    padding: "9px 12px",
                    fontSize: "10px", lineHeight: 1.65,
                    color: m.role === "user" ? textPrimary : textSecondary,
                    whiteSpace: "pre-wrap",
                  }}>
                    {m.role === "brain" && m.isProactive && (
                      <div style={{ fontSize: "6px", color: textMuted, letterSpacing: "0.15em", marginBottom: "3px", fontStyle: "italic" }}>SPONTANEOUS THOUGHT</div>
                    )}
                    {m.role === "brain" && !m.isProactive && (
                      <div style={{ fontSize: "7px", color: `${accent}50`, letterSpacing: "0.2em", marginBottom: "4px" }}>BRAIN 2.0 · NEURAL RESPONSE</div>
                    )}
                    {m.content}
                    {m.role === "brain" && !m.isProactive && (
                      <div style={{ display: "flex", gap: "6px", marginTop: "6px" }}>
                        <button onClick={() => sendFeedback(1.0)} aria-label="Good response" style={{
                          background: "none", border: "none", cursor: "pointer",
                          fontSize: "11px", opacity: 0.4, padding: "2px 4px", borderRadius: "4px",
                          transition: "opacity 0.2s",
                        }} onMouseEnter={e => e.target.style.opacity = 0.8} onMouseLeave={e => e.target.style.opacity = 0.4}>👍</button>
                        <button onClick={() => sendFeedback(-1.0)} aria-label="Bad response" style={{
                          background: "none", border: "none", cursor: "pointer",
                          fontSize: "11px", opacity: 0.4, padding: "2px 4px", borderRadius: "4px",
                          transition: "opacity 0.2s",
                        }} onMouseEnter={e => e.target.style.opacity = 0.8} onMouseLeave={e => e.target.style.opacity = 0.4}>👎</button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ display: "flex", gap: "5px", padding: "6px 12px" }}>
                  {[0,1,2].map(i => (
                    <div key={i} style={{
                      width: "6px", height: "6px", borderRadius: "50%",
                      background: accent,
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
              borderTop: `1px solid ${borderSubtle}`,
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
                  flex: 1, background: inputBg, border: `1px solid ${inputBorder}`,
                  borderRadius: "8px", padding: "8px 12px", color: textPrimary,
                  fontSize: "11px", fontFamily: "inherit", resize: "none",
                  outline: "none", lineHeight: 1.5,
                }}
              />
              <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                background: loading ? inputBg : accentSoft,
                border: `1px solid ${loading ? "#00ffc820" : "#00ffc850"}`,
                borderRadius: "8px", padding: "8px 14px", cursor: loading ? "not-allowed" : "pointer",
                color: accent, fontSize: "10px", fontFamily: "inherit",
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
              <div style={{ fontSize: "7px", letterSpacing: "0.25em", color: textMuted, marginBottom: "10px" }}>INFORMATION FLOW</div>
              {[
                { label: "SENSORY INPUT",     sub: "Vision  ·  Audio  ·  Touch",              color: REGIONS[0].color },
                { label: "SENSORY CORTEX",    sub: "Poisson spike encoding, 40k neurons",      color: REGIONS[0].color },
                { label: "FEATURE LAYER",     sub: "Edges / phonemes / pressure, 80k",         color: REGIONS[1].color },
                { label: "ASSOCIATION HUB",   sub: "STDP cross-modal binding, 500k",           color: accent },
                { label: "PREDICTIVE",        sub: "Error → attention_gain broadcast",         color: accentAlt },
                { label: "CONCEPT LAYER",     sub: "WTA sparse coding, 5.8k neurons",          color: REGIONS[4].color },
                { label: "META CONTROL",      sub: "Top-down attention, 60k",                  color: REGIONS[5].color },
                { label: "WORKING MEMORY",    sub: "Recurrent spike buffer, 20k",              color: REGIONS[6].color },
                { label: "CEREBELLUM",        sub: "Motor timing, eligibility traces",         color: REGIONS[7].color },
                { label: "REFLEX ARC",        sub: "SAFETY GATE — force/angle/velocity check", color: llmOfflineColor },
              ].map((n, i, arr) => (
                <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div style={{
                    background: `${n.color}0c`, border: `1px solid ${n.color}35`,
                    borderRadius: "8px", padding: "8px 20px", minWidth: "280px", textAlign: "center",
                  }}>
                    <div style={{ fontSize: "10px", color: n.color, fontWeight: 700, letterSpacing: "0.08em" }}>{n.label}</div>
                    <div style={{ fontSize: "8px", color: textMuted, marginTop: "2px" }}>{n.sub}</div>
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
                { title: "STDP Rule",         color: accent, body: "Pre fires BEFORE post → LTP: Δw = +A_plus·exp(−Δt/τ). Post before pre → LTD: Δw = −A_minus·exp(−Δt/τ). No global error. Purely local + temporal." },
                { title: "Predictive Loop",   color: accentAlt, body: "Association → Predictive. Error = |actual − predicted|. gain = 1 + 4·error. High error → gain × applied to all STDP updates. Surprise accelerates learning." },
                { title: "WTA Sparse Coding", color: REGIONS[4].color, body: "5,800 concept neurons compete via lateral inhibition. Only 3–5 fire per concept. Each concept is an orthogonal sparse code. Efficient & discriminable." },
                { title: "Safety Kernel",     color: llmOfflineColor, body: "ReflexArc.check_command() intercepts every motor output. Force>10N, angle>170°, vel>2m/s → BLOCKED. Withdrawal reflex fires. Hard-gated — no ML pathway bypasses this." },
              ].map(c => (
                <div key={c.title} style={{
                  background: `${c.color}08`, border: `1px solid ${c.color}25`,
                  borderRadius: "10px", padding: "12px",
                }}>
                  <div style={{ fontSize: "9px", color: c.color, fontWeight: 700, marginBottom: "6px", letterSpacing: "0.08em" }}>{c.title}</div>
                  <div style={{ fontSize: "9px", color: textSecondary, lineHeight: 1.65 }}>{c.body}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── REFLEX / SAFETY TAB ── */}
        {tab === "reflex" && <ReflexPanel theme={theme} />}

        {/* ── DEBUG TAB ── */}
        {tab === "debug" && (
          <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
            <div style={{ fontSize: '10px', letterSpacing: '0.2em', color: accent, marginBottom: '12px' }}>
              API DEBUG LOG
            </div>
            
            {debugLogs.length === 0 ? (
              <div style={{ color: textMuted, fontSize: '9px' }}>No API calls logged yet.</div>
            ) : (
              debugLogs.map((log, i) => (
                <div key={i} style={{
                  background: surface,
                  border: `1px solid ${accent}20`,
                  borderRadius: '6px',
                  padding: '10px',
                  marginBottom: '8px',
                  fontFamily: 'monospace',
                  fontSize: '8px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ color: log.type === 'REQUEST' ? accentAlt : accent, fontWeight: 'bold' }}>
                      {log.type}
                    </span>
                    <span style={{ color: textMuted }}>{log.endpoint}</span>
                    <span style={{ color: textMuted }}>{log.timestamp}</span>
                  </div>
                  <div style={{ color: textSecondary, marginBottom: '4px' }}>REQUEST:</div>
                  <pre style={{ color: textPrimary, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '100px', overflow: 'auto' }}>
                    {log.request}
                  </pre>
                  {log.response && (
                    <>
                      <div style={{ color: textSecondary, marginTop: '8px', marginBottom: '4px' }}>RESPONSE:</div>
                      <pre style={{ color: accent, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '200px', overflow: 'auto' }}>
                        {log.response}
                      </pre>
                    </>
                  )}
                </div>
              ))
            )}

            <button onClick={() => setDebugLogs([])} style={{
              marginTop: '12px',
              padding: '6px 12px',
              background: `${llmOfflineColor}20`,
              border: `1px solid ${llmOfflineColor}50`,
              borderRadius: '4px',
              color: llmOfflineColor,
              fontSize: '8px',
              cursor: 'pointer',
            }}>
              CLEAR LOGS
            </button>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:0.6} 50%{opacity:1} }
        @keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-5px)} }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: ${bgPrimary}; }
        ::-webkit-scrollbar-thumb { background: ${accent}20; border-radius: 2px; }
        textarea::placeholder { color: ${textMuted}; }
        *:focus-visible { outline: 2px solid ${accent}; outline-offset: 2px; }
      `}</style>

      {/* ── FOOTER ── */}
      <footer style={{
        padding: "8px 16px",
        borderTop: `1px solid ${borderSubtle}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexShrink: 0,
        position: "relative",
      }}>
        {/* Theme toggle button - bottom left */}
        <div style={{
          position: "absolute",
          bottom: "8px",
          left: "16px",
        }}>
          <button
            onClick={toggleTheme}
            style={{
              padding: "4px 10px",
              borderRadius: "12px",
              border: `1px solid ${accent}`,
              background: accentSoft,
              color: accent,
              fontSize: "9px",
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              cursor: "pointer",
              transition: "background 0.2s ease, color 0.2s ease, border 0.2s ease",
            }}
          >
            {themeToggleLabel}
          </button>
        </div>
        <div style={{
          fontSize: "7px",
          letterSpacing: "0.15em",
          color: textMuted,
        }}>
          BRAIN 2.0 © 2026
        </div>
      </footer>
    </div>
  );
}
