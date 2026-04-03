import React, { useState } from 'react';

export function ReflexPanel({ theme }) {
  const { surface, accent, textSecondary, textMuted, accentAlt, llmOfflineColor, llmOnlineBg, llmOfflineBg } = theme;
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

          <div style={{ background: surface, border: `1px solid ${theme.borderSubtle}`, borderRadius: "10px", padding: "12px" }}>
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