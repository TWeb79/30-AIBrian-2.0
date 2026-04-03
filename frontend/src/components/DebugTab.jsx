import React from 'react';

export function DebugTab({ debugLogs, setDebugLogs, theme }) {
  const { accent, accentAlt, textMuted, surface } = theme;

  return (
    <div className="debug-tab">
      <div className="debug-title">API DEBUG LOG</div>
      
      {debugLogs.length === 0 ? (
        <div className="debug-empty">No API calls logged yet.</div>
      ) : (
        debugLogs.map((log, i) => (
          <div key={i} className="debug-entry">
            <div className="debug-entry-header">
              <span className={`debug-type ${log.type === 'REQUEST' ? 'request' : 'response'}`}>
                {log.type}
              </span>
              <span className="debug-endpoint">{log.endpoint}</span>
              <span className="debug-timestamp">{log.timestamp}</span>
            </div>
            <div className="debug-section-title">REQUEST:</div>
            <pre className="debug-pre">{log.request}</pre>
            {log.response && (
              <>
                <div className="debug-section-title top">RESPONSE:</div>
                <pre className="debug-pre response">{log.response}</pre>
              </>
            )}
          </div>
        ))
      )}

      <button className="clear-logs-btn" onClick={() => setDebugLogs([])}>
        CLEAR LOGS
      </button>
    </div>
  );
}