import React, { useState, useEffect } from 'react';

export function DebugTab({ debugLogs, setDebugLogs, theme }) {
  const { accent, accentAlt, textMuted, surface } = theme;
  const [llmLogs, setLlmLogs] = useState([]);
  const [modelStats, setModelStats] = useState({});
  const [activeTab, setActiveTab] = useState('api');
  
  useEffect(() => {
    const fetchLlmLogs = async () => {
      try {
        const res = await fetch('/api/debug/llm_logs');
        if (res.ok) {
          const data = await res.json();
          setLlmLogs(data.logs || []);
        }
      } catch (err) {
        console.error('Failed to fetch LLM logs:', err);
      }
    };
    
    const fetchModelStats = async () => {
      try {
        const res = await fetch('/api/debug/llm_model_stats');
        if (res.ok) {
          const data = await res.json();
          setModelStats(data.model_stats || {});
        }
      } catch (err) {
        console.error('Failed to fetch model stats:', err);
      }
    };
    
    fetchLlmLogs();
    fetchModelStats();
    const interval = setInterval(() => {
      fetchLlmLogs();
      fetchModelStats();
    }, 3000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="debug-tab">
      <div className="debug-tabs">
        <button 
          className={`debug-tab-btn ${activeTab === 'api' ? 'active' : ''}`}
          onClick={() => setActiveTab('api')}
        >
          API LOGS
        </button>
        <button 
          className={`debug-tab-btn ${activeTab === 'llm' ? 'active' : ''}`}
          onClick={() => setActiveTab('llm')}
        >
          LLM COMM
        </button>
        <button 
          className={`debug-tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          MODEL STATS
        </button>
      </div>
      
      {activeTab === 'api' && (
        <>
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
        </>
      )}
      
      {activeTab === 'llm' && (
        <>
          {llmLogs.length === 0 ? (
            <div className="debug-empty">No LLM communication logged yet.</div>
          ) : (
            llmLogs.map((log, i) => (
              <div key={i} className="debug-entry">
                <div className="debug-entry-header">
                  <span className="debug-type llm">LLM</span>
                  <span className="debug-endpoint">{log.model || log.endpoint || 'generate'}</span>
                  <span className="debug-timestamp">{log.timestamp}</span>
                  <span className="debug-duration">{log.duration_ms}ms</span>
                </div>
                <div className="debug-section-title">PROMPT:</div>
                <pre className="debug-pre">{log.prompt}</pre>
                <div className="debug-section-title top">RESPONSE:</div>
                <pre className="debug-pre response">{log.response}</pre>
              </div>
            ))
          )}
        </>
      )}

      {activeTab === 'stats' && (
        <>
          {Object.keys(modelStats).length === 0 ? (
            <div className="debug-empty">No model statistics yet.</div>
          ) : (
            <>
              <table className="model-stats-table">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Calls</th>
                    <th>Avg Time (ms)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(modelStats)
                    .sort((a, b) => a[1].avg_time_ms - b[1].avg_time_ms)
                    .map(([model, stats], i) => (
                      <tr key={i} className={i === 0 ? 'fastest-model' : ''}>
                        <td>{model}</td>
                        <td>{stats.total_calls}</td>
                        <td>{stats.avg_time_ms} ms</td>
                      </tr>
                    ))}
                </tbody>
              </table>
              <button 
                className="clear-logs-btn" 
                onClick={async () => {
                  await fetch('/api/debug/llm_model_stats', { method: 'POST' });
                  setModelStats({});
                }}
              >
                CLEAR STATS
              </button>
            </>
          )}
        </>
      )}
    </div>
  );
}
