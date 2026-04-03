import React, { useState } from 'react';
import { REGIONS } from '../constants';

const SAFETY_LIMITS = {
  force: { max: 15, safe: 10, unit: 'N' },
  angle: { max: 180, safe: 170, unit: '°' },
  velocity: { max: 3, safe: 2, unit: 'm/s' }
};

export const ReflexPanel = ({ theme }) => {
  const [command, setCommand] = useState({ force: 5, angle: 90, velocity: 0.5 });
  const [logs, setLogs] = useState([]);
  const [commandHistory, setCommandHistory] = useState([]);

  const getStatus = (key) => {
    const limit = SAFETY_LIMITS[key];
    return command[key] > limit.safe ? 'danger' : 'ok';
  };

  const handleSendCommand = async () => {
    const cmd = { ...command, timestamp: new Date().toISOString() };
    
    try {
      const resp = await fetch('/api/reflex/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cmd),
      });
      const result = await resp.json();
      
      const entry = {
        id: Date.now(),
        command: cmd,
        approved: result.approved,
        reason: result.reason || (result.approved ? 'Within safety limits' : 'EXCEEDS SAFETY LIMIT'),
        time: new Date().toLocaleTimeString(),
      };
      
      setLogs(prev => [entry, ...prev].slice(0, 20));
      setCommandHistory(prev => [cmd, ...prev].slice(0, 50));
    } catch (e) {
      const entry = {
        id: Date.now(),
        command: cmd,
        approved: false,
        reason: 'Connection error - blocked by default',
        time: new Date().toLocaleTimeString(),
      };
      setLogs(prev => [entry, ...prev].slice(0, 20));
    }
  };

  const {
    textPrimary, textSecondary, textMuted, accent, accentAlt,
    llmOfflineColor, surface, borderSubtle
  } = theme;

  const style = {
    panel: { flex: 1, padding: 16, overflowY: 'auto' },
    title: { fontSize: 7, letterSpacing: '0.25em', color: llmOfflineColor, marginBottom: 16 },
    content: { display: 'flex', gap: 20 },
    builder: { width: 280, flexShrink: 0 },
    motorBox: { 
      background: 'rgba(248, 113, 113, 0.08)', 
      border: '1px solid rgba(248, 113, 113, 0.3)', 
      borderRadius: 12, 
      padding: 16, 
      marginBottom: 12 
    },
    builderTitle: { fontSize: 10, fontWeight: 700, color: llmOfflineColor, marginBottom: 14 },
    sliderGroup: { marginBottom: 14 },
    sliderHeader: { display: 'flex', justifyContent: 'space-between', marginBottom: 4 },
    sliderLabel: { fontSize: 9, color: textSecondary },
    sliderVal: { fontSize: 9, fontWeight: 700, color: getStatus('force') === 'danger' ? llmOfflineColor : accent },
    sliderInput: { width: '100%', cursor: 'pointer' },
    sliderLimit: { fontSize: 7, color: textMuted },
    sendBtn: { 
      width: '100%', 
      background: 'linear-gradient(135deg, rgba(248, 113, 113, 0.15), rgba(248, 113, 113, 0.1))', 
      border: '1px solid rgba(248, 113, 113, 0.5)', 
      borderRadius: 8, 
      padding: '8px 0', 
      color: llmOfflineColor, 
      fontSize: 10, 
      cursor: 'pointer', 
      letterSpacing: '0.1em',
      fontWeight: 700
    },
    constraintsBox: { background: surface, border: '1px solid ' + borderSubtle, borderRadius: 10, padding: 12 },
    constraintsTitle: { fontSize: 9, fontWeight: 700, color: accent, marginBottom: 8 },
    constraintRow: { display: 'flex', justifyContent: 'space-between', fontSize: 9, marginBottom: 4 },
    constraintKey: { color: textMuted },
    constraintVal: { color: accent },
    constraintsNote: { marginTop: 10, fontSize: 8, color: textMuted, lineHeight: 1.6 },
    logBox: { flex: 1 },
    logTitle: { fontSize: 9, color: textMuted, marginBottom: 8, letterSpacing: '0.15em' },
    logEmpty: { fontSize: 9, color: textMuted, padding: '20px 0' },
    logEntry: { 
      background: surface, 
      borderRadius: 8, 
      padding: '8px 12px', 
      marginBottom: 6,
      border: '1px solid ' + borderSubtle
    },
    logEntryApproved: { 
      background: 'rgba(52, 211, 153, 0.08)', 
      border: '1px solid rgba(52, 211, 153, 0.3)' 
    },
    logEntryBlocked: { 
      background: 'rgba(248, 113, 113, 0.1)', 
      border: '1px solid rgba(248, 113, 113, 0.4)' 
    },
    logHeader: { display: 'flex', justifyContent: 'space-between', marginBottom: 4 },
    logStatus: { fontSize: 10, fontWeight: 700 },
    logStatusApproved: { color: accent },
    logStatusBlocked: { color: llmOfflineColor },
    logTime: { fontSize: 8, color: textMuted },
    logCmd: { fontSize: 8, color: textMuted },
    logReason: { fontSize: 8, marginTop: 3, color: textSecondary },
    infoBox: { marginTop: 16, padding: 12, background: 'rgba(248, 113, 113, 0.05)', borderRadius: 8, border: '1px solid rgba(248, 113, 113, 0.2)' },
    infoTitle: { fontSize: 9, fontWeight: 700, color: llmOfflineColor, marginBottom: 8 },
    infoText: { fontSize: 8, color: textSecondary, lineHeight: 1.6 },
    infoHighlight: { color: llmOfflineColor, fontWeight: 700 }
  };

  return (
    <div style={style.panel}>
      <div style={style.title}>SAFETY KERNEL // REFLEX ARC</div>
      
      <div style={style.content}>
        <div style={style.builder}>
          <div style={style.motorBox}>
            <div style={style.builderTitle}>MOTOR COMMAND BUILDER</div>
            
            {Object.entries(SAFETY_LIMITS).map(([key, limit]) => (
              <div key={key} style={style.sliderGroup}>
                <div style={style.sliderHeader}>
                  <span style={style.sliderLabel}>{key.toUpperCase()}</span>
                  <span style={style.sliderVal}>
                    {command[key]}{limit.unit}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max={limit.max}
                  step="0.5"
                  value={command[key]}
                  onChange={(e) => setCommand({ ...command, [key]: parseFloat(e.target.value) })}
                  style={style.sliderInput}
                />
                <div style={style.sliderLimit}>Safe: ≤{limit.safe}{limit.unit} | Max: {limit.max}{limit.unit}</div>
              </div>
            ))}
            
            <button style={style.sendBtn} onClick={handleSendCommand}>
              EXECUTE COMMAND
            </button>
          </div>
          
          <div style={style.constraintsBox}>
            <div style={style.constraintsTitle}>SAFETY CONSTRAINTS</div>
            {Object.entries(SAFETY_LIMITS).map(([key, limit]) => (
              <div key={key} style={style.constraintRow}>
                <span style={style.constraintKey}>{key.toUpperCase()}</span>
                <span style={style.constraintVal}>≤ {limit.safe}{limit.unit}</span>
              </div>
            ))}
            <div style={style.constraintsNote}>
              Hard limits enforced by ReflexArc.check_command(). 
              No ML pathway can bypass these constraints.
            </div>
          </div>
          
          <div style={style.infoBox}>
            <div style={style.infoTitle}>WHAT IS THE SAFETY KERNEL?</div>
            <div style={style.infoText}>
              The Safety Kernel (ReflexArc) is a <span style={style.infoHighlight}>hard-gated safety layer</span> that intercepts every motor command before it reaches actuators.
              <br/><br/>
              Unlike ML pathways which learn and can make mistakes, this is a <span style={style.infoHighlight}>deterministic safety gate</span> with fixed thresholds:
              <br/>• Force: {SAFETY_LIMITS.force.safe}N max
              <br/>• Joint angle: {SAFETY_LIMITS.angle.safe}° max  
              <br/>• Velocity: {SAFETY_LIMITS.velocity.safe}m/s max
              <br/><br/>
              If any threshold is exceeded, the command is <span style={style.infoHighlight}>BLOCKED</span> and a withdrawal reflex is triggered instead.
              <br/><br/>
              This is inspired by the <span style={style.infoHighlight}>spinal reflex arc</span> in biological nervous systems — a fast, low-level protective mechanism that operates independently of higher cognitive processing.
            </div>
          </div>
        </div>
        
        <div style={style.logBox}>
          <div style={style.logTitle}>COMMAND LOG</div>
          {logs.length === 0 ? (
            <div style={style.logEmpty}>No commands sent yet. Build a command and click Execute.</div>
          ) : (
            logs.map(log => (
              <div 
                key={log.id} 
                style={{
                  ...style.logEntry,
                  ...(log.approved ? style.logEntryApproved : style.logEntryBlocked)
                }}
              >
                <div style={style.logHeader}>
                  <span style={{
                    ...style.logStatus,
                    ...(log.approved ? style.logStatusApproved : style.logStatusBlocked)
                  }}>
                    {log.approved ? '✓ APPROVED' : '✕ BLOCKED'}
                  </span>
                  <span style={style.logTime}>{log.time}</span>
                </div>
                <div style={style.logCmd}>
                  Force: {log.command.force}N | Angle: {log.command.angle}° | Velocity: {log.command.velocity}m/s
                </div>
                <div style={style.logReason}>{log.reason}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
