import React from 'react';
import { REGIONS } from '../constants';

export function ArchTab({ theme }) {
  const { textMuted, accent, accentAlt } = theme;

  const flowItems = [
    { label: "SENSORY INPUT",     sub: "Vision  ·  Audio  ·  Touch",              color: REGIONS[0].color },
    { label: "SENSORY CORTEX",    sub: "Poisson spike encoding, 40k neurons",      color: REGIONS[0].color },
    { label: "FEATURE LAYER",     sub: "Edges / phonemes / pressure, 80k",         color: REGIONS[1].color },
    { label: "ASSOCIATION HUB",   sub: "STDP cross-modal binding, 500k",           color: accent },
    { label: "PREDICTIVE",        sub: "Error → attention_gain broadcast",         color: accentAlt },
    { label: "CONCEPT LAYER",     sub: "WTA sparse coding, 5.8k neurons",          color: REGIONS[4].color },
    { label: "META CONTROL",      sub: "Top-down attention, 60k",                  color: REGIONS[5].color },
    { label: "WORKING MEMORY",    sub: "Recurrent spike buffer, 20k",              color: REGIONS[6].color },
    { label: "CEREBELLUM",        sub: "Motor timing, eligibility traces",         color: REGIONS[7].color },
    { label: "REFLEX ARC",        sub: "SAFETY GATE — force/angle/velocity check", color: REGIONS[9].color },
  ];

  const infoCards = [
    { title: "STDP Rule",         color: accent, body: "Pre fires BEFORE post → LTP: Δw = +A_plus·exp(−Δt/τ). Post before pre → LTD: Δw = −A_minus·exp(−Δt/τ). No global error. Purely local + temporal." },
    { title: "Predictive Loop",   color: accentAlt, body: "Association → Predictive. Error = |actual − predicted|. gain = 1 + 4·error. High error → gain × applied to all STDP updates. Surprise accelerates learning." },
    { title: "WTA Sparse Coding", color: REGIONS[4].color, body: "5,800 concept neurons compete via lateral inhibition. Only 3–5 fire per concept. Each concept is an orthogonal sparse code. Efficient & discriminable." },
    { title: "Safety Kernel",     color: REGIONS[9].color, body: "ReflexArc.check_command() intercepts every motor output. Force>10N, angle>170°, vel>2m/s → BLOCKED. Withdrawal reflex fires. Hard-gated — no ML pathway bypasses this." },
  ];

  return (
    <div className="arch-tab">
      <div className="flow-column">
        <div className="arch-label">INFORMATION FLOW</div>
        {flowItems.map((n, i, arr) => (
          <div key={i} className="flow-item">
            <div 
              className="flow-box" 
              style={{ borderColor: `${n.color}35`, background: `${n.color}0c` }}
            >
              <div className="flow-title" style={{ color: n.color }}>{n.label}</div>
              <div className="flow-sub">{n.sub}</div>
            </div>
            {i < arr.length - 1 && (
              <div 
                className="flow-arrow" 
                style={{ background: `linear-gradient(${arr[i].color}60,${arr[i+1].color}60)` }}
              >
                <div className="flow-arrow-icon" style={{ color: arr[i+1].color }}>▼</div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="info-column">
        {infoCards.map(c => (
          <div 
            key={c.title} 
            className="info-card" 
            style={{ background: `${c.color}08`, borderColor: `${c.color}25` }}
          >
            <div className="info-title" style={{ color: c.color }}>{c.title}</div>
            <div className="info-body">{c.body}</div>
          </div>
        ))}
      </div>
    </div>
  );
}