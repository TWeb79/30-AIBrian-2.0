import React from 'react';
import { REGIONS } from '../constants';

function fmt(n) {
  if (!Number.isFinite(n)) return "0";
  return n >= 1e9 ? (n / 1e9).toFixed(1) + "B"
       : n >= 1e6 ? (n / 1e6).toFixed(1) + "M"
       : n >= 1e3 ? (n / 1e3).toFixed(1) + "k"
       : String(n);
}

export function Header({ step, wordCount, stepRate, llmStatus, theme, toggleTheme, themeToggleLabel }) {
  const { accent } = theme;
  
  return (
    <header className="app-header">
      <div className="header-title">
        <h1>BRAIN 2.0</h1>
        <div className="header-subtitle">NEUROMORPHIC INTELLIGENCE · SNN RUNTIME</div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginLeft: 'auto' }}>
        <div className="header-stats">
          {[
            ["NEURONS", "~858k"],
            ["WORDS", fmt(wordCount)],
            ["SYNAPSES", "~80M"],
            ["STEP", fmt(step)],
            ["RATE", `${stepRate} st/s`]
          ].map(([k, v]) => (
            <div key={k} className="stat-item">
              <div className="stat-label">{k}</div>
              <div className="stat-value">{v}</div>
            </div>
          ))}
        </div>

        <div className={`llm-status ${llmStatus.ollama_available ? 'online' : 'offline'}`}>
          ◉ LLM {llmStatus.ollama_available 
            ? `ONLINE (${llmStatus.ollama_models?.length || 0} models)` 
            : llmStatus.configured ? "CONFIGURED" : "OFFLINE"}
        </div>

        <button className="header-theme-btn" onClick={toggleTheme}>
          {themeToggleLabel}
        </button>
      </div>
    </header>
  );
}

export function TabNav({ tab, setTab }) {
  const tabs = [
    ["brain", "BRAIN ACTIVITY"],
    ["chat", "NEURAL CHAT"],
    ["arch", "ARCHITECTURE"],
    ["reflex", "SAFETY KERNEL"],
    ["debug", "DEBUG"]
  ];
  
  return (
    <div className="tabs">
      {tabs.map(([id, lbl]) => (
        <button 
          key={id} 
          onClick={() => setTab(id)} 
          className={`tab-button ${tab === id ? 'active' : ''}`}
        >
          {lbl}
        </button>
      ))}
    </div>
  );
}