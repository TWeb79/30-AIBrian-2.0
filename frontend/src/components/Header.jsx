import React, { useState, useEffect } from 'react';
import { REGIONS } from '../constants';

function fmt(n) {
  if (!Number.isFinite(n)) return "0";
  return n >= 1e9 ? (n / 1e9).toFixed(1) + "B"
       : n >= 1e6 ? (n / 1e6).toFixed(1) + "M"
       : n >= 1e3 ? (n / 1e3).toFixed(1) + "k"
       : String(n);
}

export function Header({ step, wordCount, stepRate, llmStatus, setLlmStatus, theme, toggleTheme, themeToggleLabel, apiStatus }) {
  const { accent } = theme;
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [modelOptions, setModelOptions] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  
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
  
  // Initialize selected model when dropdown opens
  const handleOpenSelector = () => {
    // Prefer the currently selected model, fall back to first available option
    setSelectedModel(currentModel || (modelOptions.length > 0 ? modelOptions[0] : ''));
    setShowModelSelector(true);
  };
  
  const handleSaveModel = async () => {
    if (!selectedModel || selectedModel === currentModel) {
      setShowModelSelector(false);
      return;
    }
    
    try {
      const API_ORIGIN = (typeof window !== 'undefined' && window.__API_ORIGIN__) ? window.__API_ORIGIN__ : 'http://localhost:8030';
      const backendToUse = llmStatus?.backend || 'local_ollama';
      const res = await fetch(`${API_ORIGIN}/api/llm/set_model`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backend: backendToUse, model: selectedModel })
      });
      if (res.ok) {
        const data = await res.json();
        console.log('[LLM] Model saved:', data.new_model);
        // Immediately refresh LLM status and notify other components so UI updates
        try {
          const st = await fetch(`${API_ORIGIN}/api/llm/status`);
          if (st.ok) {
            const llmData = await st.json();
            // update local hook state directly if available
            if (typeof setLlmStatus === 'function') setLlmStatus(llmData);
            // If the server status didn't yet reflect our new selection, ensure UI shows it immediately
            try {
              const patched = { ...(llmData || {}), backend: backendToUse, model: selectedModel };
              if (!patched.ollama_models) patched.ollama_models = [];
              if (!patched.ollama_models.includes(selectedModel)) patched.ollama_models = [selectedModel, ...patched.ollama_models];
              if (typeof setLlmStatus === 'function') setLlmStatus(patched);
            } catch (e) {}
            const ev = new CustomEvent('llm_status_changed', { detail: llmData });
            window.dispatchEvent(ev);
          }
        } catch (e) {
          // Non-fatal - we already saved on server
          console.warn('[LLM] Failed to refresh status after save', e);
        }
        setShowModelSelector(false);
      } else {
        console.error('Failed to save model:', res.status);
      }
    } catch (err) {
      console.error('Failed to save model:', err);
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
            onClick={handleOpenSelector}
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
              zIndex: 1000,
              minWidth: '220px',
              padding: '8px',
            }}>
              <div style={{ 
                marginBottom: '8px', 
                paddingBottom: '8px', 
                borderBottom: '1px solid var(--border)',
                fontSize: '10px',
                color: 'var(--text-muted)'
              }}>
                SELECT MODEL
              </div>
              
              {modelOptions.map((model) => (
                <div
                  key={model}
                  onClick={() => setSelectedModel(model)}
                  style={{
                    padding: '6px 10px',
                    cursor: 'pointer',
                    background: model === selectedModel ? 'var(--accent)' : 'transparent',
                    color: model === selectedModel ? 'var(--text-inverse)' : 'var(--text)',
                    borderRadius: '3px',
                    marginBottom: '2px',
                  }}
                >
                  {model}
                </div>
              ))}
              
              <div style={{ 
                display: 'flex', 
                gap: '8px', 
                marginTop: '10px',
                paddingTop: '8px',
                borderTop: '1px solid var(--border)'
              }}>
                <button 
                  onClick={() => setShowModelSelector(false)}
                  style={{
                    flex: 1,
                    padding: '6px 10px',
                    background: 'transparent',
                    border: '1px solid var(--border)',
                    color: 'var(--text)',
                    borderRadius: '3px',
                    cursor: 'pointer',
                    fontSize: '10px',
                  }}
                >
                  CANCEL
                </button>
                <button 
                  onClick={handleSaveModel}
                  style={{
                    flex: 1,
                    padding: '6px 10px',
                    background: 'var(--accent)',
                    border: 'none',
                    color: 'var(--text-inverse)',
                    borderRadius: '3px',
                    cursor: 'pointer',
                    fontSize: '10px',
                    fontWeight: 'bold',
                  }}
                >
                  SAVE
                </button>
              </div>
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
