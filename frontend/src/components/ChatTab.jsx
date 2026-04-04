import React, { useEffect, useRef } from 'react';
import { REGIONS } from '../constants';

export function ChatTab({ 
  messages, loading, input, setInput, handleKey, sendMessage,
  sendFeedback, feedbackGiven, isDragging, handleDragOver, handleDragLeave, handleDrop,
  theme 
}) {
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const {
    textPrimary, textSecondary, textMuted, accent, chatBubbleUserBg, chatBubbleUserBorder,
    chatBubbleBrainBg, chatBubbleBrainBorder, inputBg, inputBorder
  } = theme;

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Ensure we scroll to bottom on initial mount as well
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Activity bar at top
  const totalActivity = Object.values({}).reduce((a,b)=>a+b,0);

  return (
    <div className="chat-tab">
      {/* Activity bar */}
      <div className="activity-bar">
        {REGIONS.map(r => (
          <div key={r.id} className="activity-region">
            <div 
              className="activity-circle"
              style={{ background: `${r.color}30`, borderColor: r.color }}
            >
              {r.label.charAt(0)}
            </div>
            <div className="activity-label">{r.label.split(" ")[0]}</div>
          </div>
        ))}
      </div>

      {/* Messages */}
      <div className="chat-messages-full">
        {messages.map((m, i) => (
          <div key={i} className={`message-row ${m.role}`}>
            {m.role === "brain" && (
              <>
                <div className="brain-avatar">⬡</div>
                <div className={`message-bubble ${m.role}`}>
                  {m.role === "brain" && m.isProactive && (
                    <div className="brain-label" style={{ fontStyle: 'italic', marginBottom: '3px' }}>
                      SPONTANEOUS THOUGHT
                    </div>
                  )}
                  {m.role === "brain" && !m.isProactive && (
                    <div className="brain-label">BRAIN 2.0 · NEURAL RESPONSE</div>
                  )}
                  {m.content}
                  {m.role === "brain" && !m.isProactive && (
                    <div style={{ display: "flex", gap: "6px", marginTop: "6px" }}>
                      <button 
                        className={`feedback-button ${feedbackGiven[i] === 1 ? 'active' : ''} ${feedbackGiven[i] === -1 ? 'disabled' : ''}`}
                        onClick={() => sendFeedback(1.0, i)}
                        disabled={feedbackGiven[i] !== undefined}
                        title={feedbackGiven[i] === 1 ? "Feedback given - Thank you!" : feedbackGiven[i] === -1 ? "Already gave negative feedback" : "This response was helpful - the brain will learn from this"}
                      >
                        👍
                      </button>
                      <button 
                        className={`feedback-button ${feedbackGiven[i] === -1 ? 'active' : ''} ${feedbackGiven[i] === 1 ? 'disabled' : ''}`}
                        onClick={() => sendFeedback(-1.0, i)}
                        disabled={feedbackGiven[i] !== undefined}
                        title={feedbackGiven[i] === -1 ? "Feedback given - will improve" : feedbackGiven[i] === 1 ? "Already gave positive feedback" : "This was incorrect - the brain will try to improve"}
                      >
                        👎
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
            {(m.role === "user" || m.role === "llm") && (
              <>
                <div className={`message-bubble ${m.role}`}>
                  {m.role === "llm" && (
                    <div className="llm-label">LLM ASSISTANT</div>
                  )}
                  {m.content}
                </div>
                <div className={m.role === "user" ? "user-avatar" : "llm-avatar"}>
                  {m.role === "user" ? "⌨️" : "🤖"}
                </div>
              </>
            )}
          </div>
        ))}
        {loading && (
          <div className="loading-dots">
            {[0,1,2].map(i => (
              <div key={i} className="loading-dot" />
            ))}
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div 
        className={`full-chat-input ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            // Ensure Enter sends the message, without inserting a newline
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
              return;
            }
            // Fallback to existing key handling for other keys
            if (typeof handleKey === 'function') {
              handleKey(e);
            }
          }}
          placeholder={isDragging ? "Drop file here..." : "Stimulate the network... (Enter to send)"}
          rows={1}
          className="chat-textarea"
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()} className="full-send-button">
          {loading ? "..." : "FIRE ▶"}
        </button>
      </div>
    </div>
  );
}