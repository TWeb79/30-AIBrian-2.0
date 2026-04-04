import React, { useState, useEffect, useCallback, useRef } from 'react'
import { THEMES, REGIONS } from './constants'
import { useBrainStatus, useThoughts } from './hooks'
import { Header, TabNav, BrainTab, ChatTab, ArchTab, DebugTab, ReflexPanel } from './components'

function fmt(n) {
  if (!Number.isFinite(n)) return "0";
  return n >= 1e9 ? (n/1e9).toFixed(1)+"B" :
         n >= 1e6 ? (n/1e6).toFixed(1)+"M" :
         n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
}

export default function App() {
  const [themeName, setThemeName] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = window.localStorage.getItem('brain-theme');
      if (saved === 'light' || saved === 'dark') return saved;
    }
    return 'dark';
  });
  const theme = THEMES[themeName];
  const toggleTheme = useCallback(() => {
    setThemeName(prev => (prev === 'dark' ? 'light' : 'dark'));
  }, []);
  const themeToggleLabel = theme.name === 'dark' ? '☀ LIGHT' : '☾ DARK';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('brain-theme', theme.name);
      document.documentElement.setAttribute('data-theme', theme.name);
    }
  }, [theme]);

  const [tab, setTab] = useState("brain");
  const [debugLogs, setDebugLogs] = useState([]);
  const addDebugLog = useCallback((type, endpoint, request, response) => {
    setDebugLogs(prev => [{
      timestamp: new Date().toISOString(),
      type, endpoint,
      request: typeof request === 'string' ? request : JSON.stringify(request, null, 2),
      response: typeof response === 'string' ? response : JSON.stringify(response, null, 2),
    }, ...prev].slice(0, 50));
  }, []);

  const [selectedRegion, setSelected] = useState("association");
  
  const {
    step, stepRate, wordCount, brainStatus, predError, globalGain,
    activeRegions, affect, drives, llmStatus, spikeRegions, apiStatus,
    setLlmStatus
  } = useBrainStatus();

  const { thoughts } = useThoughts();

  const [messages, setMessages] = useState([
    { role: "brain", content: "BRAIN 2.0 initialised. Spiking neural network online.\n\nAll 10 regions active. STDP synapses forming. Send me a stimulus or ask anything about my architecture." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [feedbackGiven, setFeedbackGiven] = useState({}); // { messageIndex: 1 or -1 }
  const chatEndRef = useRef(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);
  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);
  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    for (const file of files) {
      try {
        const content = await file.text();
        setInput(`[FILE: ${file.name}]\n${content}`);
        setHistoryIndex(-1);
      } catch (err) {
        console.error("Error reading file:", err);
      }
    }
  }, []);

  const sendFeedback = useCallback(async (valence, messageIndex) => {
    // Prevent multiple feedback on same message
    if (feedbackGiven[messageIndex] !== undefined) {
      console.log(`[Feedback] Already gave feedback for message ${messageIndex}`);
      return;
    }
    
    const responseText = messageIndex !== undefined ? messages[messageIndex]?.content?.substring(0, 200) : null;
    const feedbackType = valence > 0 ? "POSITIVE (👍)" : "NEGATIVE (👎)";
    console.log(`[Feedback] ${feedbackType} for message ${messageIndex}: "${responseText?.substring(0, 50)}..."`);
    
    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ valence, message_id: messageIndex, response_text: responseText }),
      });
      // Mark feedback as given for this message
      setFeedbackGiven(prev => ({ ...prev, [messageIndex]: valence }));
    } catch (e) {
      console.log(`[Feedback] Error: ${e}`);
    }
  }, [messages, feedbackGiven]);

  const userMessagesRef = useRef([]);
  useEffect(() => {
    userMessagesRef.current = messages.filter(m => m.role === "user").map(m => m.content);
  }, [messages]);

  const handleKey = useCallback((e) => {
    const userMessages = userMessagesRef.current;
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
      return;
    }
    if (userMessages.length === 0) return;
    if (e.key === "ArrowUp") {
      e.preventDefault();
      const newIndex = historyIndex < userMessages.length - 1 ? historyIndex + 1 : historyIndex;
      setHistoryIndex(newIndex);
      setInput(userMessages[userMessages.length - 1 - newIndex] || "");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      const newIndex = historyIndex > -1 ? historyIndex - 1 : -1;
      setHistoryIndex(newIndex);
      setInput(newIndex >= 0 ? userMessages[userMessages.length - 1 - newIndex] : "");
    }
  }, [historyIndex]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setHistoryIndex(-1);
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);
    spikeRegions();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      
      addDebugLog('REQUEST', '/api/chat', { message: userMsg }, '');
      
      if (res.ok) {
        const data = await res.json();
        addDebugLog('RESPONSE', '/api/chat', { message: userMsg }, data);
        
        if (data.messages && Array.isArray(data.messages)) {
          for (const msg of data.messages) {
            setMessages(prev => [...prev, { role: msg.role, content: msg.content }]);
          }
        } else {
          setMessages(prev => [...prev, { role: "brain", content: data.response || data.message }]);
        }
      } else {
        setMessages(prev => [...prev, { role: "brain", content: `[ERROR] ${res.status}` }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: "brain", content: `[ERROR] ${err.message}` }]);
    }
    
    setLoading(false);
  }, [input, loading, spikeRegions, addDebugLog]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, tab]);

  return (
    <div className="app-container">
      <Header
        step={step} wordCount={wordCount} stepRate={stepRate}
        llmStatus={llmStatus} setLlmStatus={setLlmStatus}
        theme={theme} toggleTheme={toggleTheme}
        themeToggleLabel={themeToggleLabel} apiStatus={apiStatus}
      />
      <TabNav tab={tab} setTab={setTab} />
      <div className="main-content">
        {tab === "brain" && (
          <BrainTab
            activeRegions={activeRegions} globalGain={globalGain}
            brainStatus={brainStatus}
            selectedRegion={selectedRegion} setSelected={setSelected}
            messages={messages} loading={loading} input={input} setInput={setInput}
            handleKey={handleKey} sendMessage={sendMessage}
            affect={affect} drives={drives} thoughts={thoughts}
            isDragging={isDragging} handleDragOver={handleDragOver}
            handleDragLeave={handleDragLeave} handleDrop={handleDrop}
            sendFeedback={sendFeedback} feedbackGiven={feedbackGiven} theme={theme}
          />
        )}
        {tab === "chat" && (
          <ChatTab
            messages={messages} loading={loading} input={input} setInput={setInput}
            handleKey={handleKey} sendMessage={sendMessage}
            sendFeedback={sendFeedback} feedbackGiven={feedbackGiven} isDragging={isDragging}
            handleDragOver={handleDragOver} handleDragLeave={handleDragLeave}
            handleDrop={handleDrop} theme={theme}
          />
        )}
        {tab === "arch" && <ArchTab theme={theme} />}
        {tab === "reflex" && <ReflexPanel theme={theme} />}
        {tab === "debug" && <DebugTab debugLogs={debugLogs} setDebugLogs={setDebugLogs} theme={theme} />}
      </div>
      <footer className="app-footer">
        <div className="footer-copyright">BRAIN 2.0 © 2026</div>
      </footer>
    </div>
  );
}