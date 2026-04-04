import React, { useState, useEffect } from 'react';
import { REGIONS } from '../constants';

function fmt(n) {
  if (!Number.isFinite(n)) return "0";
  return n >= 1e9 ? (n / 1e9).toFixed(1) + "B"
       : n >= 1e6 ? (n / 1e6).toFixed(1) + "M"
       : n >= 1e3 ? (n / 1e3).toFixed(1) + "k"
       : String(n);
}

export function Header({ step, wordCount, stepRate, llmStatus, theme, toggleTheme, themeToggleLabel, apiStatus }) {
  const { accent } = theme;
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [modelOptions, setModelOptions] = useState([]);
  
  const apiDisplay = apiStatus.online 
    ? `API ${apiStatus.responseTime}ms`
    : apiStatus.lastError 
      ? `API ${apiStatus.lastError}` 
      : "API OFFLINE";
  
  useEffect(() => {
    if (llmStatus.ollama_models && llmStatus.ollama_models.length > 0) {
      setModelOptions(llmStatus.ollama_models);
    }
  }, [llmStatus.ollama_models]);
  
  const currentModel = llmStatus.model || '';
  
  const handleModelSelect = async (model) => {
    try {
      const res = await fetch('/api/llm/set_model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backend: 'local_ollama', model })
      });
      if (res.ok) {
        const data = await res.json();
        console.log('[LLM] Model changed to:', data.new_model);
        setShowModelSelector(false);
      }
    } catch (err) {
      console.error('Failed to set model:', err);
    }
  };
  
  const llmDisplay = llmStatus.ollama_available 
    ? `◉ LLM ${currentModel || 'ONLINE'}`
    : llmStatus.configured ? "◉ LLM CONFIGURED" : "◉ LLM OFFLINE";
  
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

        <div className={`llm-status ${apiStatus.online ? 'online' : 'offline'}`}>
          {apiDisplay}
        </div>

        <div className="llm-status-container" style={{ position: 'relative' }}>
          <div 
            className={`llm-status ${llmStatus.ollama_available ? 'online' : 'offline'}`}
            onClick={() => setShowModelSelector(!showModelSelector)}
            style={{ cursor: 'pointer' }}
          >
            {llmDisplay}
          </div>
          
          {showModelSelector && modelOptions.length > 0 && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: '4px',
              background: 'var(--bg-primary)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              maxHeight: '200px',
              overflowY: 'auto',
              zIndex: 1000,
              minWidth: '180px',
            }}>
              {modelOptions.map((model) => (
                <div
                  key={model}
                  onClick={() => handleModelSelect(model)}
                  style={{
                    padding: '8px 12px',
                    cursor: 'pointer',
                    background: model === currentModel ? 'var(--accent)' : 'transparent',
                    color: model === currentModel ? 'var(--text-inverse)' : 'var(--text)',
                  }}
                  onMouseEnter={(e) => e.target.style.background = model === currentModel ? 'var(--accent)' : 'var(--bg-hover)'}
                  onMouseLeave={(e) => e.target.style.background = model === currentModel ? 'var(--accent)' : 'transparent'}
                >
                  {model}
                </div>
              ))}
            </div>
          )}
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
