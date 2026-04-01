/**
 * BRAIN 2.0 - Unified UI with Theme Switcher
 * Single component with Dark/Light theme toggle
 */

import React, { useState, useEffect, useRef } from 'react';

// Theme definitions
const DARK_THEME = {
  name: 'dark',
  bg: { primary: '#02060e', secondary: '#040d1c', card: '#040e1e', header: '#02060e' },
  text: { primary: '#c8e0f0', secondary: '#a0d4f0', muted: '#2a6070' },
  accent: '#00ffc8',
  accentAlt: '#ffb300',
  border: '#00ffc818',
  regionColors: {
    sensory: '#00cfff', feature: '#8b5cf6', association: '#00ffc8',
    predictive: '#ffb300', concept: '#ec4899', working_mem: '#6366f1',
    reflex_arc: '#ff4d6d', cerebellum: '#14b8a6',
  },
};

const LIGHT_THEME = {
  name: 'light',
  bg: { primary: '#f8fafc', secondary: '#f1f5f9', card: '#ffffff', header: '#ffffff' },
  text: { primary: '#0f172a', secondary: '#475569', muted: '#94a3b8' },
  accent: '#0ea5e9',
  accentAlt: '#f59e0b',
  border: '#e2e8f0',
  regionColors: {
    sensory: '#0ea5e9', feature: '#8b5cf6', association: '#10b981',
    predictive: '#f59e0b', concept: '#ec4899', working_mem: '#6366f1',
    reflex_arc: '#ef4444', cerebellum: '#14b8a6',
  },
};

// REGIONS configuration
const REGIONS = [
  { id: "sensory", label: "SENSORY", color: null, neurons: "120k" },
  { id: "feature", label: "FEATURE", color: null, neurons: "240k" },
  { id: "association", label: "ASSOCIATION", color: null, neurons: "500k" },
  { id: "predictive", label: "PREDICTIVE", color: null, neurons: "180k" },
  { id: "concept", label: "CONCEPT", color: null, neurons: "5.8k" },
  { id: "working_mem", label: "WORKING MEM", color: null, neurons: "42k" },
  { id: "reflex_arc", label: "REFLEX", color: null, neurons: "8k" },
  { id: "cerebellum", label: "CEREBELLUM", color: null, neurons: "65k" },
];

// Neural Canvas Component
function NeuralCanvas({ activeRegions, globalGain, zoom, theme }) {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const spikesRef = useRef([]);

  const colors = theme.regionColors;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener('resize', resize);

    let frame = 0;
    const animate = () => {
      frame++;
      const w = canvas.width / dpr;
      const h = canvas.height / dpr;
      
      // Background
      ctx.fillStyle = theme.bg.primary;
      ctx.fillRect(0, 0, w, h);

      // Grid
      ctx.strokeStyle = theme.border;
      ctx.lineWidth = 0.5;
      const gridSize = 40 * zoom;
      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
      }

      // Region circles
      const centerX = w / 2;
      const centerY = h / 2;
      const maxRadius = Math.min(w, h) * 0.35;
      
      REGIONS.forEach((r, i) => {
        const color = colors[r.id];
        const angle = (i / REGIONS.length) * Math.PI * 2 - Math.PI / 2;
        const radius = maxRadius * (activeRegions[r.id] || 0) / 60;
        const x = centerX + Math.cos(angle) * maxRadius * 0.6;
        const y = centerY + Math.sin(angle) * maxRadius * 0.6;
        
        // Glow
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
        gradient.addColorStop(0, color + '40');
        gradient.addColorStop(1, color + '00');
        ctx.fillStyle = gradient;
        ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.fill();
        
        // Label
        ctx.fillStyle = theme.text.muted;
        ctx.font = '8px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(r.label, x, y + radius + 12);
      });

      // Central hub
      const hubSize = 30 + globalGain * 5;
      const hubColor = theme.name === 'dark' ? '#6366f1' : '#6366f1';
      const hubGradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, hubSize);
      hubGradient.addColorStop(0, hubColor + '20');
      hubGradient.addColorStop(1, hubColor + '00');
      ctx.fillStyle = hubGradient;
      ctx.beginPath(); ctx.arc(centerX, centerY, hubSize, 0, Math.PI * 2); ctx.fill();

      // Spikes
      if (frame % 3 === 0) {
        const spikeColors = Object.values(colors);
        const numSpikes = Math.floor(Math.random() * 5) + 1;
        for (let i = 0; i < numSpikes; i++) {
          spikesRef.current.push({
            x: centerX + (Math.random() - 0.5) * maxRadius * 1.5,
            y: centerY + (Math.random() - 0.5) * maxRadius * 1.5,
            vx: (Math.random() - 0.5) * 2,
            vy: (Math.random() - 0.5) * 2,
            life: 1,
            color: spikeColors[Math.floor(Math.random() * spikeColors.length)],
          });
        }
      }

      spikesRef.current = spikesRef.current.filter(s => {
        s.x += s.vx; s.y += s.vy; s.life -= 0.02;
        if (s.life > 0) {
          ctx.fillStyle = s.color + Math.floor(s.life * 255).toString(16).padStart(2, '0');
          ctx.beginPath(); ctx.arc(s.x, s.y, 2, 0, Math.PI * 2); ctx.fill();
          return true;
        }
        return false;
      });

      animationRef.current = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener('resize', resize);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [activeRegions, globalGain, zoom, theme, colors]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />;
}

// Main Component
export default function OSCENBrain() {
  const [theme, setTheme] = useState(DARK_THEME);
  const [activeRegions, setActive] = useState(() => {
    const initial = {};
    REGIONS.forEach(r => { initial[r.id] = 20; });
    return initial;
  });
  const [step, setStep] = useState(0);
  const [stepRate, setStepRate] = useState(120);
  const [brainStatus, setBrainStatus] = useState('RUNNING');
  const [predError, setPredError] = useState(0.0123);
  const [globalGain, setGlobalGain] = useState(1.0);
  const [zoom, setZoom] = useState(1);
  const [tab, setTab] = useState('brain');
  const [selectedRegion, setSelectedRegion] = useState('association');
  
  // Chat state
  const [messages, setMessages] = useState([
    { role: 'brain', content: 'Neural system online. Ready for input.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Theme toggle
  const toggleTheme = () => setTheme(t => t.name === 'dark' ? LIGHT_THEME : DARK_THEME);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  useEffect(() => {
    const interval = setInterval(() => {
      setStep(s => s + stepRate);
      setPredError(e => Math.max(0.001, e + (Math.random() - 0.5) * 0.005));
      const updated = { ...activeRegions };
      ['sensory', 'feature', 'association', 'predictive'].forEach(k => {
        updated[k] = Math.min(60, (activeRegions[k] || 0) + Math.random() * 20 + 10);
      });
      setActive(updated);
      setGlobalGain(parseFloat((2 + Math.random() * 2).toFixed(2)));
    }, 1000);
    return () => clearInterval(interval);
  }, [stepRate, activeRegions]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input;
    setInput('');
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      const reply = data.response || data.brain_state?.response || '[No response]';
      setMessages(prev => [...prev, { role: 'brain', content: reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'brain', content: `[Error] ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const fmt = n => n >= 1e9 ? (n/1e9).toFixed(2)+'B' : n >= 1e6 ? (n/1e6).toFixed(2)+'M' : n >= 1e3 ? (n/1e3).toFixed(1)+'k' : n;
  const region = REGIONS.find(r => r.id === selectedRegion) || REGIONS[0];

  // Apply region colors to REGIONS array
  const coloredRegions = REGIONS.map(r => ({ ...r, color: theme.regionColors[r.id] }));

  return (
    <div style={{
      fontFamily: theme.name === 'dark' ? "'JetBrains Mono', monospace" : "'Inter', -apple-system, sans-serif",
      background: theme.bg.primary,
      color: theme.text.primary,
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <header style={{
        padding: '10px 20px',
        borderBottom: `1px solid ${theme.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        background: theme.name === 'dark' 
          ? 'linear-gradient(90deg, #02060e 0%, #040d1c 50%, #02060e 100%)' 
          : theme.bg.header,
        flexShrink: 0,
        boxShadow: theme.name === 'light' ? '0 1px 3px rgba(0,0,0,0.05)' : 'none',
      }}>
        <div>
          <div style={{ fontSize: '18px', fontWeight: 800, color: theme.accent, letterSpacing: '0.12em' }}>OSCEN</div>
          <div style={{ fontSize: '7px', letterSpacing: '0.3em', color: theme.text.muted, marginTop: '1px' }}>
            NEUROMORPHIC INTELLIGENCE · SNN RUNTIME
          </div>
        </div>
        <div style={{ flex: 1 }} />
        
        {/* Stats */}
        {[
          ['NEURONS', '~858k'],
          ['SYNAPSES', '~80M'],
          ['STEP', fmt(step)],
          ['RATE', `${stepRate} st/s`],
          ['GAIN', `×${globalGain}`],
          ['Δerr', predError.toFixed(4)],
        ].map(([k, v]) => (
          <div key={k} style={{ textAlign: 'center', minWidth: 60 }}>
            <div style={{ fontSize: '6px', letterSpacing: '0.2em', color: theme.text.muted }}>{k}</div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: k === 'GAIN' && globalGain > 2 ? theme.accentAlt : theme.accent }}>{v}</div>
          </div>
        ))}

        {/* Theme Toggle */}
        <button onClick={toggleTheme} style={{
          padding: '6px 12px',
          borderRadius: 16,
          border: `1px solid ${theme.border}`,
          background: theme.bg.card,
          color: theme.accent,
          fontSize: '10px',
          fontWeight: 600,
          cursor: 'pointer',
          letterSpacing: '0.1em',
        }}>
          {theme.name === 'dark' ? '☀ LIGHT' : '☾ DARK'}
        </button>
      </header>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: `1px solid ${theme.border}`,
        background: theme.bg.secondary,
        padding: '0 20px',
      }}>
        {[['brain', 'BRAIN ACTIVITY'], ['chat', 'NEURAL CHAT'], ['arch', 'ARCHITECTURE'], ['reflex', 'SAFETY KERNEL']].map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)} style={{
            background: 'none', border: 'none',
            padding: '10px 16px',
            fontSize: '10px', fontWeight: 700, letterSpacing: '0.15em',
            color: tab === id ? theme.accent : theme.text.muted,
            borderBottom: tab === id ? `2px solid ${theme.accent}` : '2px solid transparent',
            cursor: 'pointer',
          }}>
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {tab === 'brain' && (
          <div style={{ flex: 1, display: 'flex', gap: 0, overflow: 'hidden' }}>
            {/* Regions */}
            <div style={{
              width: 160,
              borderRight: `1px solid ${theme.border}`,
              overflowY: 'auto',
              background: theme.bg.secondary,
              display: 'flex', flexDirection: 'column', gap: 5,
              padding: '8px',
            }}>
              {coloredRegions.map(r => (
                <button key={r.id} onClick={() => setSelectedRegion(r.id)} style={{
                  padding: '8px 10px', borderRadius: 6,
                  border: selectedRegion === r.id ? `1px solid ${r.color}` : `1px solid ${theme.border}`,
                  background: selectedRegion === r.id ? `${r.color}15` : 'transparent',
                  cursor: 'pointer', textAlign: 'left',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                    <span style={{ fontSize: 9, fontWeight: 700, color: selectedRegion === r.id ? r.color : theme.text.muted }}>{r.label}</span>
                    <span style={{ fontSize: 10, color: theme.text.secondary }}>{(activeRegions[r.id] || 0).toFixed(0)}%</span>
                  </div>
                  <div style={{ height: 3, background: theme.border, borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ width: `${activeRegions[r.id] || 0}%`, background: r.color, transition: 'width 0.4s' }} />
                  </div>
                </button>
              ))}
            </div>

            {/* Canvas */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
                <NeuralCanvas activeRegions={activeRegions} globalGain={globalGain} zoom={zoom} theme={theme} />
                <div style={{
                  position: 'absolute', top: 12, left: 14,
                  fontSize: 8, letterSpacing: '0.2em', color: theme.text.muted,
                }}>
                  LIVE SPIKE ACTIVITY · {Object.values(activeRegions).reduce((a,b)=>a+b,0).toFixed(1)}% TOTAL
                </div>
                {globalGain > 2 && (
                  <div style={{
                    position: 'absolute', top: 12, right: 14,
                    fontSize: 8, color: theme.accentAlt, letterSpacing: '0.15em',
                  }}>
                    ⚡ HIGH ATTENTION · ×{globalGain}
                  </div>
                )}
                <div style={{ position: 'absolute', bottom: 12, right: 14, display: 'flex', gap: 6 }}>
                  <button onClick={() => setZoom(z => Math.max(0.5, z - 0.25))} style={{
                    width: 28, height: 28, borderRadius: 6,
                    background: theme.bg.card, border: `1px solid ${theme.border}`,
                    color: theme.accent, fontSize: 14, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>−</button>
                  <div style={{
                    minWidth: 40, height: 28, borderRadius: 6,
                    background: theme.bg.card, border: `1px solid ${theme.border}`,
                    color: theme.accent, fontSize: 9, display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                  }}>{zoom.toFixed(2)}×</div>
                  <button onClick={() => setZoom(z => Math.min(3, z + 0.25))} style={{
                    width: 28, height: 28, borderRadius: 6,
                    background: theme.bg.card, border: `1px solid ${theme.border}`,
                    color: theme.accent, fontSize: 14, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>+</button>
                </div>
              </div>
            </div>

            {/* Chat Panel */}
            <div style={{
              width: 280, flexShrink: 0, borderLeft: `1px solid ${theme.border}`,
              display: 'flex', flexDirection: 'column',
              background: theme.bg.primary,
            }}>
              <div style={{
                padding: '8px 12px', fontSize: 7, letterSpacing: '0.2em',
                color: theme.text.muted, borderBottom: `1px solid ${theme.border}`,
              }}>
                <span>⬡</span> NEURAL CHAT
              </div>
              <div style={{
                flex: 1, overflowY: 'auto', padding: '10px 12px',
                display: 'flex', flexDirection: 'column', gap: 8,
              }}>
                {messages.slice(-5).map((m, i) => (
                  <div key={i} style={{ fontSize: 9, lineHeight: 1.4 }}>
                    {m.role === 'user' && (
                      <span style={{ color: theme.name === 'dark' ? '#00cfff' : '#0ea5e9', fontWeight: 700 }}>you: </span>
                    )}
                    {m.role === 'brain' && (
                      <span style={{ color: theme.accent, fontWeight: 700 }}>OSCEN: </span>
                    )}
                    <span style={{ color: m.role === 'user' ? theme.text.secondary : theme.text.primary }}>
                      {m.content.length > 100 ? m.content.slice(0, 100) + '...' : m.content}
                    </span>
                  </div>
                ))}
              </div>
              <div style={{
                padding: '10px 12px', borderTop: `1px solid ${theme.border}`,
                display: 'flex', gap: 8,
              }}>
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') sendMessage(); }}
                  placeholder="Stimulate..."
                  style={{
                    flex: 1, background: theme.bg.card, border: `1px solid ${theme.border}`,
                    borderRadius: 6, padding: '8px 10px', color: theme.text.primary,
                    fontSize: 10, fontFamily: 'inherit', outline: 'none',
                  }}
                />
                <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                  background: loading ? theme.bg.card : theme.accent + '20',
                  border: `1px solid ${theme.accent}50`,
                  borderRadius: 6, padding: '8px 12px', cursor: loading ? 'not-allowed' : 'pointer',
                  color: theme.accent, fontSize: 9, fontFamily: 'inherit',
                }}>{loading ? '...' : 'FIRE'}</button>
              </div>
            </div>
          </div>
        )}

        {tab === 'chat' && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ flex: 1, overflowY: 'auto', padding: '14px 20px', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {messages.map((m, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                  <div style={{
                    maxWidth: '70%',
                    padding: '10px 14px', borderRadius: 12,
                    background: m.role === 'user' 
                      ? (theme.name === 'dark' ? '#00ffc815' : '#0ea5e915')
                      : theme.bg.card,
                    border: `1px solid ${theme.border}`,
                    fontSize: 12, lineHeight: 1.5,
                  }}>
                    <div style={{ fontSize: 8, color: theme.text.muted, marginBottom: 4, fontWeight: 600 }}>
                      {m.role === 'user' ? 'YOU' : 'OSCEN'}
                    </div>
                    {m.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ display: 'flex', gap: 5, padding: '6px 12px' }}>
                  {[0,1,2].map(i => (
                    <div key={i} style={{
                      width: 6, height: 6, borderRadius: '50%',
                      background: theme.accent, opacity: 0.5,
                      animation: 'pulse 1s infinite',
                    }} />
                  ))}
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div style={{
              padding: '12px 16px', borderTop: `1px solid ${theme.border}`,
              display: 'flex', gap: 10,
            }}>
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') sendMessage(); }}
                placeholder="Type message..."
                style={{
                  flex: 1, background: theme.bg.card, border: `1px solid ${theme.border}`,
                  borderRadius: 8, padding: '10px 14px', color: theme.text.primary,
                  fontSize: 12, outline: 'none',
                }}
              />
              <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                background: theme.accent, border: 'none', borderRadius: 8,
                padding: '10px 20px', color: '#fff', fontSize: 11, fontWeight: 700,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}>
                SEND
              </button>
            </div>
          </div>
        )}

        {tab === 'arch' && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', gap: 20 }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 0, alignItems: 'center' }}>
              <div style={{ fontSize: 7, letterSpacing: '0.25em', color: theme.text.muted, marginBottom: 10 }}>INFORMATION FLOW</div>
              {[
                { label: 'SENSORY CORTEX', desc: 'Multimodal input, Poisson spike encoding' },
                { label: 'FEATURE LAYER', desc: 'Edge, texture, phoneme detection' },
                { label: 'ASSOCIATION', desc: 'Cross-modal binding, STDP learning' },
                { label: 'PREDICTIVE', desc: 'Error calculation, attention modulation' },
                { label: 'CONCEPT LAYER', desc: 'WTA sparse coding, assembly formation' },
              ].map((n, i, arr) => (
                <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{
                    padding: '8px 16px', borderRadius: 6, border: `1px solid ${theme.border}`,
                    background: theme.bg.card, fontSize: 10, fontWeight: 700, color: theme.accent,
                  }}>{n.label}</div>
                  {i < arr.length - 1 && (
                    <div style={{ width: 1, height: 20, background: theme.border }} />
                  )}
                </div>
              ))}
            </div>
            <div style={{ width: 260, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ fontSize: 8, letterSpacing: '0.2em', color: theme.text.muted }}>LEARNING RULES</div>
              {[
                ['STDP', 'Hebbian temporal learning'],
                ['WTA', 'Winner-take-all competition'],
                ['Prediction Error', 'Attention modulation'],
              ].map(([k, v]) => (
                <div key={k} style={{ padding: 10, background: theme.bg.card, borderRadius: 6, border: `1px solid ${theme.border}` }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: theme.accent }}>{k}</div>
                  <div style={{ fontSize: 9, color: theme.text.muted, marginTop: 2 }}>{v}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'reflex' && (
          <div style={{ flex: 1, padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: theme.accent }}>SAFETY KERNEL - REFLEX ARC</div>
            <div style={{ padding: 16, background: theme.bg.card, borderRadius: 8, border: `1px solid ${theme.border}` }}>
              <div style={{ fontSize: 10, color: theme.text.muted, marginBottom: 8 }}>HARD LIMITS</div>
              {[
                ['Force', '< 10N'],
                ['Angle', '< 170°'],
                ['Velocity', '< 2 m/s'],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: `1px solid ${theme.border}` }}>
                  <span style={{ fontSize: 11, color: theme.text.secondary }}>{k}</span>
                  <span style={{ fontSize: 11, fontWeight: 700, color: theme.accent }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}