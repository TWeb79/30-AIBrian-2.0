import React, { useEffect, useRef } from 'react';
import { REGIONS } from '../constants';
import { NeuralCanvas } from '../NeuralCanvas';

function getMoodEmoji(valence, arousal) {
  if (arousal > 0.5 && valence > 0.3) return "😊";
  if (arousal > 0.5 && valence < -0.3) return "😠";
  if (arousal <= 0.5 && valence > 0.3) return "😌";
  if (arousal <= 0.5 && valence < -0.3) return "😔";
  return "😐";
}

function getMoodLabel(valence, arousal) {
  if (arousal > 0.5 && valence > 0.3) return "Excited";
  if (arousal > 0.5 && valence < -0.3) return "Stressed";
  if (arousal <= 0.5 && valence > 0.3) return "Calm";
  if (arousal <= 0.5 && valence < -0.3) return "Low";
  return "Neutral";
}

export function BrainTab({ 
  activeRegions, globalGain, selectedRegion, setSelected,
  messages, loading, input, setInput, handleKey, sendMessage,
  affect, drives, thoughts, isDragging, handleDragOver, handleDragLeave, handleDrop,
  sendFeedback, theme 
}) {
  const chatEndRef = useRef(null);
  // Anchor element to scroll chat to bottom
  const brainChatEndRef = useRef(null);
  const {
    textPrimary, textSecondary, textMuted, accent, accentAlt, accentSoft,
    llmOnlineColor, llmOfflineColor, surface, borderSubtle, panel, inputBg, inputBorder
  } = theme;
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  // Ensure the brain chat area scrolls to bottom on mount as well
  useEffect(() => {
    brainChatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const totalActivity = Object.values(activeRegions).reduce((a,b)=>a+b,0).toFixed(1);

  return (
    <div className="brain-tab">
      {/* Region list */}
      <div className="region-list">
        {REGIONS.map(r => {
          const act = activeRegions[r.id] || 0;
          const selected = selectedRegion === r.id;
          return (
            <button 
              key={r.id} 
              onClick={() => setSelected(r.id)} 
              className={`region-button ${selected ? 'selected' : ''}`}
            >
              <div className="region-header">
                <span className="region-name" style={{ color: selected ? r.color : undefined }}>
                  {r.label}
                </span>
                <span className="region-activity" style={{ color: r.color }}>
                  {act.toFixed(1)}%
                </span>
              </div>
              <div className="region-bar">
                <div 
                  className="region-bar-fill" 
                  style={{ 
                    width: `${(act / 60) * 100}%`, 
                    background: r.color, 
                    boxShadow: `0 0 6px ${r.color}80` 
                  }} 
                />
              </div>
              <div className="region-neurons">{r.neurons} neurons</div>
            </button>
          );
        })}
      </div>

      {/* Canvas + Chat */}
      <div className="canvas-container">
        <div className="canvas-wrapper">
          <NeuralCanvas activeRegions={activeRegions} globalGain={globalGain} />
          <div className="canvas-label">
            LIVE SPIKE ACTIVITY · {totalActivity}% TOTAL
          </div>
          <div className="canvas-legend">
            {REGIONS.map(r => (
              <div key={r.id} className="legend-item">
                <div className="legend-dot" style={{ background: r.color }} />
                <span className="legend-label">{r.label.split(" ")[0]}</span>
              </div>
            ))}
          </div>
          {globalGain > 2 && (
            <div className="attention-indicator">
              ⚡ HIGH ATTENTION · ×{globalGain}
            </div>
          )}
        </div>

        {/* Chat Panel */}
        <div className="chat-panel">
          <div className="chat-header">NEURAL CHAT</div>
          <div className="chat-messages">
            {messages.slice(-4).map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role}`}>
                <div className="bubble-content" style={{ color: m.role === 'user' ? textPrimary : textSecondary }}>
                  {m.isProactive && (
                    <div className="proactive-label">SPONTANEOUS THOUGHT</div>
                  )}
                  {m.content}
                  {m.role === 'brain' && !m.isProactive && (
                    <div className="feedback-buttons">
                      <button 
                        className="feedback-button" 
                        onClick={() => sendFeedback(1.0, messages.length - 4 + i)}
                        title="This response was helpful - the brain will learn from this"
                      >
                        👍
                      </button>
                      <button 
                        className="feedback-button" 
                        onClick={() => sendFeedback(-1.0, messages.length - 4 + i)}
                        title="This was incorrect - the brain will try to improve"
                      >
                        👎
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="loading-dots">
                {[0,1,2].map(i => (
                  <div key={i} className="loading-dot" />
                ))}
              </div>
            )}
            {/* anchor to scroll to bottom when messages update */}
            <div ref={brainChatEndRef} />
          </div>
          <div 
            className={`chat-input-area ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
              return;
            }
            if (typeof handleKey === 'function') {
              handleKey(e);
            }
          }}
          placeholder={isDragging ? "Drop file..." : "Talk to brain..."}
          className="chat-input"
        />
            <button onClick={sendMessage} disabled={loading || !input.trim()} className="send-button">
              {loading ? "..." : "▶"}
            </button>
          </div>
        </div>
      </div>

      {/* Right Sidebar */}
      <div className="right-sidebar">
        {/* Emotion Panel */}
        <div className="panel-section">
          <div className="panel-label">AFFECTIVE STATE</div>
          <div className="emoji-face">
            {getMoodEmoji(affect.valence, affect.arousal)}
          </div>
          <div className="mood-label">
            {getMoodLabel(affect.valence, affect.arousal)}
          </div>
          
          {/* Valence bar */}
          <div className="metric-bar">
            <div className="metric-header">
              <span>Valence</span>
              <span>{affect.valence.toFixed(2)}</span>
            </div>
            <div className="metric-track">
              <div style={{
                position: "absolute", top: 0,
                left: affect.valence < 0 ? `${50 + affect.valence * 50}%` : "50%",
                width: `${Math.abs(affect.valence) * 50}%`,
                height: "100%",
                background: affect.valence >= 0 ? accent : llmOfflineColor,
                borderRadius: "2px",
              }} />
              <div className="metric-center-line" />
            </div>
          </div>
          
          {/* Arousal bar */}
          <div className="metric-bar">
            <div className="metric-header">
              <span>Arousal</span>
              <span>{affect.arousal.toFixed(2)}</span>
            </div>
            <div className="metric-track">
              <div style={{
                height: "100%", width: `${affect.arousal * 100}%`,
                background: `linear-gradient(90deg, ${accent}, ${llmOfflineColor})`,
                borderRadius: "2px",
              }} />
            </div>
          </div>
          
          {/* Drives */}
          <div className="drives-section">
            <div className="drives-label">DRIVES</div>
            {[
              { label: "Curiosity", value: drives.curiosity, color: accent },
              { label: "Competence", value: drives.competence, color: accentAlt },
              { label: "Connection", value: drives.connection, color: llmOnlineColor },
            ].map(d => (
              <div key={d.label} className="drive-item">
                <span className="drive-label">{d.label}</span>
                <div className="drive-bar">
                  <div className="drive-fill" style={{ width: `${d.value * 100}%`, background: d.color }} />
                </div>
                <span className="drive-value">{(d.value * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Thinking Panel */}
        <div className="panel-section thinking">
          <div className="panel-label top">THINKING</div>
          <div className="thinking-list">
            {thoughts.length === 0 && (
              <div className="thinking-empty">Awaiting neural activity...</div>
            )}
            {thoughts.map((t, i) => (
              <div key={i} className={`thinking-item ${i === thoughts.length - 1 ? 'active' : 'old'}`}>
                {t}
              </div>
            ))}
          </div>
        </div>

        {/* Extended Panel */}
        <div className="extended-section">
          <div className="panel-label">EXTENDED</div>
          <div className="extended-placeholder">(reserved)</div>
        </div>
      </div>
    </div>
  );
}