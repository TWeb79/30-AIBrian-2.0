/**
 * BRAIN 2.0 - Light Theme Alternative
 * A clean, modern light design for the neural interface
 * Use this as an alternative to the default dark theme
 */

import React, { useState, useEffect, useRef } from 'react';

// Light theme colors
const LIGHT_THEME = {
  bg: {
    primary: '#f8fafc',
    secondary: '#f1f5f9',
    card: '#ffffff',
    header: '#ffffff',
  },
  text: {
    primary: '#0f172a',
    secondary: '#475569',
    muted: '#94a3b8',
  },
  accent: {
    primary: '#0ea5e9',      // Sky blue
    secondary: '#6366f1',    // Indigo
    success: '#10b981',      // Emerald
    warning: '#f59e0b',      // Amber
    error: '#ef4444',        // Red
  },
  border: '#e2e8f0',
  regionColors: {
    sensory: '#0ea5e9',
    feature: '#8b5cf6',
    association: '#10b981',
    predictive: '#f59e0b',
    concept: '#ec4899',
    working_mem: '#6366f1',
    reflex_arc: '#ef4444',
    cerebellum: '#14b8a6',
  },
};

// REGIONS configuration
const REGIONS = [
  { id: "sensory", label: "SENSORY", color: LIGHT_THEME.regionColors.sensory, neurons: "120k" },
  { id: "feature", label: "FEATURE", color: LIGHT_THEME.regionColors.feature, neurons: "240k" },
  { id: "association", label: "ASSOCIATION", color: LIGHT_THEME.regionColors.association, neurons: "500k" },
  { id: "predictive", label: "PREDICTIVE", color: LIGHT_THEME.regionColors.predictive, neurons: "180k" },
  { id: "concept", label: "CONCEPT", color: LIGHT_THEME.regionColors.concept, neurons: "5.8k" },
  { id: "working_mem", label: "WORKING MEM", color: LIGHT_THEME.regionColors.working_mem, neurons: "42k" },
  { id: "reflex_arc", label: "REFLEX", color: LIGHT_THEME.regionColors.reflex_arc, neurons: "8k" },
  { id: "cerebellum", label: "CEREBELLUM", color: LIGHT_THEME.regionColors.cerebellum, neurons: "65k" },
];

// Neural Canvas Component - Light version
function LightNeuralCanvas({ activeRegions, globalGain, zoom }) {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const spikesRef = useRef([]);

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
      
      // Light background
      ctx.fillStyle = LIGHT_THEME.bg.primary;
      ctx.fillRect(0, 0, w, h);

      // Draw grid
      ctx.strokeStyle = LIGHT_THEME.border;
      ctx.lineWidth = 0.5;
      const gridSize = 40 * zoom;
      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Draw region circles
      const centerX = w / 2;
      const centerY = h / 2;
      const maxRadius = Math.min(w, h) * 0.35;
      
      const total = Object.values(activeRegions).reduce((a, b) => a + b, 0) || 1;
      
      REGIONS.forEach((r, i) => {
        const angle = (i / REGIONS.length) * Math.PI * 2 - Math.PI / 2;
        const radius = maxRadius * (activeRegions[r.id] || 0) / 60;
        const x = centerX + Math.cos(angle) * maxRadius * 0.6;
        const y = centerY + Math.sin(angle) * maxRadius * 0.6;
        
        // Glow effect
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
        gradient.addColorStop(0, r.color + '40');
        gradient.addColorStop(1, r.color + '00');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
        
        // Region label
        ctx.fillStyle = LIGHT_THEME.text.secondary;
        ctx.font = '8px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        ctx.fillText(r.label, x, y + radius + 12);
      });

      // Central hub
      const hubSize = 30 + globalGain * 5;
      const hubGradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, hubSize);
      hubGradient.addColorStop(0, '#6366f120');
      hubGradient.addColorStop(1, '#6366f100');
      ctx.fillStyle = hubGradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, hubSize, 0, Math.PI * 2);
      ctx.fill();

      // Random spikes
      if (frame % 3 === 0) {
        const numSpikes = Math.floor(Math.random() * 5) + 1;
        for (let i = 0; i < numSpikes; i++) {
          spikesRef.current.push({
            x: centerX + (Math.random() - 0.5) * maxRadius * 1.5,
            y: centerY + (Math.random() - 0.5) * maxRadius * 1.5,
            vx: (Math.random() - 0.5) * 2,
            vy: (Math.random() - 0.5) * 2,
            life: 1,
            color: ['#0ea5e9', '#10b981', '#6366f1', '#f59e0b'][Math.floor(Math.random() * 4)],
          });
        }
      }

      // Update and draw spikes
      spikesRef.current = spikesRef.current.filter(s => {
        s.x += s.vx;
        s.y += s.vy;
        s.life -= 0.02;
        
        if (s.life > 0) {
          ctx.fillStyle = s.color + Math.floor(s.life * 255).toString(16).padStart(2, '0');
          ctx.beginPath();
          ctx.arc(s.x, s.y, 2, 0, Math.PI * 2);
          ctx.fill();
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
  }, [activeRegions, globalGain, zoom]);

  return (
    <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
  );
}

// Main Light Theme Component
export default function OSCENBrainLight() {
  const [tab, setTab] = useState('brain');
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
  const [selectedRegion, setSelectedRegion] = useState('association');
  
  // Chat state
  const [messages, setMessages] = useState([
    { role: 'brain', content: 'Neural system online. Ready for input.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setStep(s => s + stepRate);
      setPredError(e => Math.max(0.001, e + (Math.random() - 0.5) * 0.005));
      
      // Random region activity
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

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      background: LIGHT_THEME.bg.primary,
      color: LIGHT_THEME.text.primary,
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <header style={{
        padding: '12px 24px',
        borderBottom: `1px solid ${LIGHT_THEME.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        background: LIGHT_THEME.bg.header,
        flexShrink: 0,
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        <div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: LIGHT_THEME.accent.primary }}>OSCEN</div>
          <div style={{ fontSize: '10px', color: LIGHT_THEME.text.muted }}>Neural Network Runtime</div>
        </div>
        <div style={{ flex: 1 }} />
        
        {/* Stats */}
        {[
          ['Neurons', '858k'],
          ['Step', fmt(step)],
          ['Rate', `${stepRate}/s`],
          ['Gain', `×${globalGain.toFixed(1)}`],
        ].map(([k, v]) => (
          <div key={k} style={{ textAlign: 'center', minWidth: 60 }}>
            <div style={{ fontSize: '9px', color: LIGHT_THEME.text.muted, textTransform: 'uppercase' }}>{k}</div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: LIGHT_THEME.text.primary }}>{v}</div>
          </div>
        ))}
      </header>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: `1px solid ${LIGHT_THEME.border}`,
        background: LIGHT_THEME.bg.secondary,
        padding: '0 16px',
      }}>
        {[['brain', 'Brain Activity'], ['chat', 'Neural Chat'], ['arch', 'Architecture']].map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)} style={{
            background: 'none',
            border: 'none',
            padding: '12px 20px',
            fontSize: '13px',
            fontWeight: 500,
            color: tab === id ? LIGHT_THEME.accent.primary : LIGHT_THEME.text.secondary,
            borderBottom: tab === id ? `2px solid ${LIGHT_THEME.accent.primary}` : '2px solid transparent',
            cursor: 'pointer',
          }}>
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {tab === 'brain' && (
          <div style={{ flex: 1, display: 'flex', gap: 0 }}>
            {/* Regions */}
            <div style={{
              width: 180,
              borderRight: `1px solid ${LIGHT_THEME.border}`,
              padding: '12px',
              background: LIGHT_THEME.bg.secondary,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}>
              {REGIONS.map(r => (
                <button key={r.id} onClick={() => setSelectedRegion(r.id)} style={{
                  padding: '10px 12px',
                  borderRadius: 8,
                  border: selectedRegion === r.id ? `2px solid ${r.color}` : `1px solid ${LIGHT_THEME.border}`,
                  background: selectedRegion === r.id ? `${r.color}10` : LIGHT_THEME.bg.card,
                  cursor: 'pointer',
                  textAlign: 'left',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: r.color }}>{r.label}</span>
                    <span style={{ fontSize: 11, fontWeight: 600 }}>{activeRegions[r.id]?.toFixed(0) || 0}%</span>
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <div style={{
                      height: 4,
                      background: LIGHT_THEME.border,
                      borderRadius: 2,
                      overflow: 'hidden',
                    }}>
                      <div style={{
                        width: `${activeRegions[r.id] || 0}%`,
                        background: r.color,
                        height: '100%',
                      }} />
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Canvas */}
            <div style={{ flex: 1, position: 'relative' }}>
              <LightNeuralCanvas activeRegions={activeRegions} globalGain={globalGain} zoom={zoom} />
              <div style={{
                position: 'absolute', top: 12, left: 14,
                fontSize: 10, color: LIGHT_THEME.text.muted,
              }}>
                Total Activity: {Object.values(activeRegions).reduce((a,b)=>a+b,0).toFixed(0)}%
              </div>
              <div style={{
                position: 'absolute', bottom: 12, right: 14,
                display: 'flex', gap: 6,
              }}>
                <button onClick={() => setZoom(z => Math.max(0.5, z - 0.25))} style={{
                  width: 28, height: 28, borderRadius: 6,
                  background: LIGHT_THEME.bg.card, border: `1px solid ${LIGHT_THEME.border}`,
                  color: LIGHT_THEME.text.secondary, fontSize: 16, cursor: 'pointer',
                }}>−</button>
                <div style={{
                  minWidth: 40, height: 28, borderRadius: 6,
                  background: LIGHT_THEME.bg.card, border: `1px solid ${LIGHT_THEME.border}`,
                  color: LIGHT_THEME.text.secondary, fontSize: 11, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                }}>{zoom.toFixed(1)}×</div>
                <button onClick={() => setZoom(z => Math.min(3, z + 0.25))} style={{
                  width: 28, height: 28, borderRadius: 6,
                  background: LIGHT_THEME.bg.card, border: `1px solid ${LIGHT_THEME.border}`,
                  color: LIGHT_THEME.text.secondary, fontSize: 16, cursor: 'pointer',
                }}>+</button>
              </div>
            </div>

            {/* Chat */}
            <div style={{
              width: 300,
              borderLeft: `1px solid ${LIGHT_THEME.border}`,
              display: 'flex', flexDirection: 'column',
              background: LIGHT_THEME.bg.card,
            }}>
              <div style={{
                padding: '10px 14px',
                fontSize: 11, fontWeight: 600,
                borderBottom: `1px solid ${LIGHT_THEME.border}`,
                color: LIGHT_THEME.accent.primary,
              }}>
                Neural Chat
              </div>
              <div style={{
                flex: 1, overflowY: 'auto', padding: '12px',
                display: 'flex', flexDirection: 'column', gap: 8,
              }}>
                {messages.slice(-6).map((m, i) => (
                  <div key={i} style={{ fontSize: 12, lineHeight: 1.5 }}>
                    <span style={{ 
                      fontWeight: 600, 
                      color: m.role === 'user' ? LIGHT_THEME.accent.primary : LIGHT_THEME.accent.secondary 
                    }}>
                      {m.role === 'user' ? 'You: ' : 'OSCEN: '}
                    </span>
                    <span style={{ color: LIGHT_THEME.text.secondary }}>{m.content}</span>
                  </div>
                ))}
                {loading && (
                  <div style={{ fontSize: 11, color: LIGHT_THEME.text.muted }}>
                    Processing...
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
              <div style={{
                padding: '10px 12px', borderTop: `1px solid ${LIGHT_THEME.border}`,
                display: 'flex', gap: 8,
              }}>
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') sendMessage(); }}
                  placeholder="Enter message..."
                  style={{
                    flex: 1, background: LIGHT_THEME.bg.secondary,
                    border: `1px solid ${LIGHT_THEME.border}`,
                    borderRadius: 6, padding: '8px 10px', color: LIGHT_THEME.text.primary,
                    fontSize: 12, outline: 'none',
                  }}
                />
                <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                  background: loading ? LIGHT_THEME.bg.secondary : LIGHT_THEME.accent.primary,
                  border: 'none', borderRadius: 6, padding: '8px 14px',
                  color: '#fff', fontSize: 11, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
                }}>
                  {loading ? '...' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        )}

        {tab === 'chat' && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 20 }}>
            <div style={{ flex: 1, overflowY: 'auto' }}>
              {messages.map((m, i) => (
                <div key={i} style={{ marginBottom: 16 }}>
                  <div style={{ 
                    fontWeight: 600, 
                    color: m.role === 'user' ? LIGHT_THEME.accent.primary : LIGHT_THEME.accent.secondary,
                    marginBottom: 4,
                  }}>
                    {m.role === 'user' ? 'You' : 'OSCEN'}
                  </div>
                  <div style={{ 
                    padding: '12px 16px', 
                    background: m.role === 'user' ? `${LIGHT_THEME.accent.primary}10` : LIGHT_THEME.bg.card,
                    borderRadius: 12,
                    color: LIGHT_THEME.text.secondary,
                    fontSize: 14,
                    lineHeight: 1.6,
                  }}>
                    {m.content}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') sendMessage(); }}
                placeholder="Type a message..."
                style={{
                  flex: 1, background: LIGHT_THEME.bg.card,
                  border: `1px solid ${LIGHT_THEME.border}`,
                  borderRadius: 8, padding: '12px 16px', color: LIGHT_THEME.text.primary,
                  fontSize: 14, outline: 'none',
                }}
              />
              <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
                background: LIGHT_THEME.accent.primary,
                border: 'none', borderRadius: 8, padding: '12px 24px',
                color: '#fff', fontSize: 14, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
              }}>
                Send
              </button>
            </div>
          </div>
        )}

        {tab === 'arch' && (
          <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Architecture</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 16 }}>
              {REGIONS.map(r => (
                <div key={r.id} style={{
                  padding: 16,
                  background: LIGHT_THEME.bg.card,
                  borderRadius: 12,
                  border: `1px solid ${LIGHT_THEME.border}`,
                }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: r.color, marginBottom: 8 }}>{r.label}</div>
                  <div style={{ fontSize: 11, color: LIGHT_THEME.text.muted }}>{r.neurons} neurons</div>
                  <div style={{ marginTop: 8 }}>
                    <div style={{
                      height: 4, background: LIGHT_THEME.border, borderRadius: 2,
                      overflow: 'hidden',
                    }}>
                      <div style={{ width: `${activeRegions[r.id] || 0}%`, background: r.color, height: '100%' }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}