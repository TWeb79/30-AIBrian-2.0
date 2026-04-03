import React from 'react'
import { useState, useEffect, useRef, useCallback } from 'react'
import { THEMES, REGIONS } from './constants'
import { NeuralCanvas } from './NeuralCanvas'
import { ReflexPanel } from './ReflexPanel'


// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [themeName, setThemeName] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = window.localStorage.getItem('brain-theme');
      if (saved === 'light' || saved === 'dark') return saved;
    }
    return 'dark';
  });
  const theme = THEMES[themeName];
  const {
    fontFamily,
    bgPrimary,
    bgSecondary,
    surface,
    panel,
    headerBg,
    textPrimary,
    textSecondary,
    textMuted,
    border,
    borderSubtle,
    borderStrong,
    accent,
    accentAlt,
    accentSoft,
    badgeBg,
    badgeBorder,
    llmOnlineBg,
    llmOfflineBg,
    llmOnlineColor,
    llmOfflineColor,
    chatBubbleUserBg,
    chatBubbleUserBorder,
    chatBubbleBrainBg,
    chatBubbleBrainBorder,
    inputBg,
    inputBorder,
  } = theme;

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

  const [tab, setTab]               = useState("brain");
  const [debugLogs, setDebugLogs]     = useState([]);

  // Helper to add debug logs
  const addDebugLog = useCallback((type, endpoint, request, response) => {
    setDebugLogs(prev => [{
      timestamp: new Date().toISOString(),
      type,
      endpoint,
      request: typeof request === 'string' ? request : JSON.stringify(request, null, 2),
      response: typeof response === 'string' ? response : JSON.stringify(response, null, 2),
    }, ...prev].slice(0, 50)); // Keep last 50 logs
  }, []);
  const [activeRegions, setActive]  = useState(() =>
    Object.fromEntries(REGIONS.map(r => [r.id, r.baseAct]))
  );
  const [globalGain, setGlobalGain] = useState(1.0);
  const [predError, setPredError]   = useState(0.0);
  const [step, setStep]             = useState(2_000_000);
  const [stepRate, setStepRate]     = useState(0.54);
  const [wordCount, setWordCount]   = useState(0);
  const [brainStatus, setBrainStatus] = useState("JUVENILE");
  const [selectedRegion, setSelected] = useState("association");
  const [llmStatus, setLlmStatus]     = useState({ configured: false, backend: "none", model: null });

  // Chat state
  const [messages, setMessages]   = useState([
    { role: "brain", content: "BRAIN 2.0 initialised. Spiking neural network online.\n\nAll 10 regions active. STDP synapses forming. Send me a stimulus or ask anything about my architecture." }
  ]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const chatEndRef                = useRef(null);
  const inputRef                  = useRef(null);

  // Message history navigation (arrow keys)
  const [historyIndex, setHistoryIndex] = useState(-1);
  const userMessagesRef = useRef([]);
  useEffect(() => {
    userMessagesRef.current = messages.filter(m => m.role === "user").map(m => m.content);
  }, [messages]);

  const handleHistoryNav = useCallback((e) => {
    const userMessages = userMessagesRef.current;
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

  // Reset history index when user types
  const handleInputChange = useCallback((e) => {
    setInput(e.target.value);
    setHistoryIndex(-1);
  }, []);

  // File drag and drop
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;

    for (const file of files) {
      try {
        const content = await file.text();
        const fileMsg = `[FILE: ${file.name}]\n${content}`;
        setInput(fileMsg);
        setHistoryIndex(-1);
      } catch (err) {
        console.error("Error reading file:", err);
      }
    }
  }, []);

  // Affect / drives / thoughts state
  const [affect, setAffect]       = useState({ valence: 0.0, arousal: 0.3 });
  const [drives, setDrives]       = useState({ curiosity: 0.5, competence: 0.5, connection: 0.5 });
  const [thoughts, setThoughts]   = useState([]);

  // Feedback handler
  const sendFeedback = useCallback(async (valence, messageIndex) => {
    const responseText = messageIndex !== undefined ? messages[messageIndex]?.content?.substring(0, 200) : null;
    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          valence,
          message_id: messageIndex,
          response_text: responseText
        }),
      });
    } catch (_) {}
  }, [messages]);

  // Simulate live brain stats (or fetch from API)
  useEffect(() => {
    // Fetch LLM status on mount
    fetch('/api/llm/status')
      .then(r => r.ok ? r.json() : null)
      .then(data => data && setLlmStatus(data))
      .catch(() => {});

    const id = setInterval(async () => {
      // Try to fetch real brain state from API
      try {
        const res = await fetch('/api/brain/status');
        if (res.ok) {
          const data = await res.json();
          setStep(data.step || step);
          setStepRate(data.step_rate || stepRate);
          setBrainStatus(data.status || brainStatus);
          setPredError(data.prediction_error || predError);
          setGlobalGain(data.attention_gain || globalGain);
          if (data.vocabulary) {
            const vocabSize = Number(data.vocabulary.vocabulary_size);
            setWordCount(Number.isFinite(vocabSize) ? Math.max(0, Math.floor(vocabSize)) : 0);
          }
          if (data.regions) {
            // Transform API region data to UI format
            const regionActivity = {};
            Object.keys(data.regions).forEach(key => {
              const region = data.regions[key];
              // Use activity_pct from API, fallback to baseAct from REGIONS
              regionActivity[key] = region.activity_pct !== undefined ? region.activity_pct : 
                (REGIONS.find(r => r.id === key)?.baseAct || 10);
            });
            setActive(regionActivity);
          }
          // Extract affect
          if (data.affect) {
            setAffect({ valence: data.affect.valence ?? 0, arousal: data.affect.arousal ?? 0.3 });
          }
          // Extract drives
          if (data.drives) {
            setDrives({
              curiosity: data.drives.curiosity ?? 0.5,
              competence: data.drives.competence ?? 0.5,
              connection: data.drives.connection ?? 0.5,
            });
          }
          // Generate meaningful thought from current brain state
          if (data.regions) {
            const concept = data.regions.concept?.activity_pct || 0;
            const assoc = data.regions.association?.activity_pct || 0;
            const pred = data.prediction_error || 0;
            const gain = data.attention_gain || 1;
            const st = data.step || 0;
            const sensory = data.regions.sensory?.activity_pct || 0;
            const feature = data.regions.feature?.activity_pct || 0;
            const working = data.regions.working_mem?.activity_pct || 0;
            const totalActivity = Object.values(data.regions).reduce((a, r) => a + (r.activity_pct || 0), 0);
            
            // Generate cognitively meaningful thoughts
            const thoughtCandidates = [];
            
            if (pred > 0.05) {
              thoughtCandidates.push(`Prediction error detected — adjusting synaptic weights`);
            }
            if (concept > 15) {
              thoughtCandidates.push(`New concept forming in sparse coding layer`);
            }
            if (concept > 5 && concept <= 15) {
              thoughtCandidates.push(`Strengthening concept representation`);
            }
            if (sensory > 20 && feature > 15) {
              thoughtCandidates.push(`Processing sensory patterns — extracting features`);
            }
            if (sensory > 30) {
              thoughtCandidates.push(`Receiving fresh sensory input`);
            }
            if (assoc > 20) {
              thoughtCandidates.push(`Cross-modal associations forming`);
            }
            if (gain > 2.0) {
              thoughtCandidates.push(`High attention — filtering noise`);
            }
            if (working > 15) {
              thoughtCandidates.push(`Holding information in working memory`);
            }
            if (working > 30) {
              thoughtCandidates.push(`Buffering temporal sequence`);
            }
            if (data.vocabulary?.vocabulary_size > 0 && Math.random() < 0.1) {
              thoughtCandidates.push(`Recall: ${Math.min(5, data.vocabulary.vocabulary_size)} words in memory`);
            }
            if (data.assemblies?.total_assemblies > 0 && Math.random() < 0.1) {
              thoughtCandidates.push(`${data.assemblies.total_assemblies} stable assemblies detected`);
            }
            if (st % 50000 < 10) {
              thoughtCandidates.push(`Milestone: ${(st/1000).toFixed(0)}k steps completed`);
            }
            
            // Pick a thought, prioritizing more interesting ones
            let thought = null;
            if (thoughtCandidates.length > 0) {
              // Weight more interesting thoughts higher
              const weights = thoughtCandidates.map((_, i) => i < 3 ? 3 : 1);
              const totalWeight = weights.reduce((a, b) => a + b, 0);
              let r = Math.random() * totalWeight;
              for (let i = 0; i < weights.length; i++) {
                r -= weights[i];
                if (r <= 0) {
                  thought = thoughtCandidates[i];
                  break;
                }
              }
              if (!thought) thought = thoughtCandidates[0];
            }
            
            // Only push a thought if there is real neural activity
            if (thought && totalActivity > 0.1) {
              setThoughts(prev => [...prev.slice(-7), thought]);
            }
          }
        }
      } catch (err) {
        // Fall back to simulated data
        setStep(s => s + Math.floor(Math.random() * 4 + 1));
        setStepRate(parseFloat((0.4 + Math.random() * 0.3).toFixed(2)));
        setPredError(parseFloat((Math.random() * 0.05).toFixed(4)));
        setGlobalGain(parseFloat((1 + Math.random() * 0.8).toFixed(3)));
      }
      // Poll proactive messages
      try {
        const pRes = await fetch('/api/proactive');
        if (pRes.ok) {
          const pData = await pRes.json();
          if (pData.messages && pData.messages.length > 0) {
            setMessages(prev => [
              ...prev,
              ...pData.messages.map(m => ({ role: "brain", content: m, isProactive: true }))
            ]);
          }
        }
      } catch {}
      // Note: Region activity now comes from real API data - no simulation drift
    }, 1200);
    return () => clearInterval(id);
  }, []);

  // Auto-scroll chat when messages change or tab switches to chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Scroll to bottom when switching to chat tab
  useEffect(() => {
    if (tab === "chat" || tab === "brain") {
      setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 50);
    }
  }, [tab]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setHistoryIndex(-1);
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    // Spike active regions on new input
    setActive(prev => {
      const next = { ...prev };
      ["sensory","feature","association","predictive"].forEach(k => {
        next[k] = Math.min(60, prev[k] + Math.random() * 20 + 10);
      });
      return next;
    });
    setGlobalGain(parseFloat((2 + Math.random() * 2).toFixed(2)));

    try {
      let reply;
      let processingProgress = 0;

      // Check for /grep command
      if (userMsg.startsWith('/grep')) {
        // Parse /grep <n> <url>
        const parts = userMsg.split(/\s+/);
        if (parts.length >= 3) {
          const n = parseInt(parts[1], 10);
          const url = parts.slice(2).join(' ');
          
          if (isNaN(n) || !url) {
            reply = `[GREP] Invalid syntax. Use: /grep <n> <url>\nExample: /grep 3 https://example.com`;
            processingProgress = 100;
          } else {
            // Call the grep API
            const grepRes = await fetch('/api/grep', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ n, url })
            });
            
            addDebugLog('REQUEST', '/api/grep', { n, url }, '');
            
            if (grepRes.ok) {
              const data = await grepRes.json();
              addDebugLog('RESPONSE', '/api/grep', { n, url }, data);
              reply = `[GREP] Crawled ${data.crawled} of ${data.requested} pages from ${data.start_url}\n\n`;
              
              data.results.forEach((r, i) => {
                if (r.error) {
                  reply += `${i+1}. ${r.url}: ERROR - ${r.error}\n\n`;
                } else {
                  reply += `${i+1}. ${r.url} (${r.status})\n`;
                  // Show first 500 chars of content
                  const content = r.content.substring(0, 500);
                  reply += `   ${content}${r.content.length > 500 ? '...' : ''}\n\n`;
                }
              });
              processingProgress = 100;
            } else {
              reply = `[GREP] API Error: ${grepRes.status}`;
              processingProgress = 50;
            }
          }
        } else {
          reply = `[GREP] Invalid syntax. Use: /grep <n> <url>\nExample: /grep 3 https://example.com`;
          processingProgress = 100;
        }
      } else if (userMsg.startsWith('/llm')) {
        // Parse /llm <prompt>
        const prompt = userMsg.substring(4).trim();
        
        if (!prompt) {
          reply = `[LLM] Invalid syntax. Use: /llm <prompt>\nExample: /llm What is the capital of France?`;
          processingProgress = 100;
        } else {
          // Call the LLM API directly
          const llmRes = await fetch('/api/llm/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
          });
          
          addDebugLog('REQUEST', '/api/llm/chat', { prompt }, '');
          
          if (llmRes.ok) {
            const data = await llmRes.json();
            addDebugLog('RESPONSE', '/api/llm/chat', { prompt }, data);
            reply = `[LLM] Response:\n\n${data.response || data.reply || data.message}`;
            processingProgress = 100;
          } else {
            reply = `[LLM] API Error: ${llmRes.status}. Make sure Ollama is running.`;
            processingProgress = 50;
          }
        }
      } else if (userMsg.startsWith('/yt')) {
        // Parse /yt <n> <url>
        const parts = userMsg.substring(3).trim().split(/\s+/);
        const n = parseInt(parts[0]) || 1;
        const url = parts.slice(1).join(' ');
        
        if (!url || !url.includes('youtube.com') && !url.includes('youtu.be')) {
          reply = `[YT] Invalid syntax. Use: /yt <n> <youtube_url>\nExample: /yt 2 https://www.youtube.com/watch?v=VIDEO_ID`;
          processingProgress = 100;
        } else {
          const ytRes = await fetch('/api/yt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, n: Math.min(n, 10) })
          });
          
          addDebugLog('REQUEST', '/api/yt', { url, n }, '');
          
          if (ytRes.ok) {
            const data = await ytRes.json();
            addDebugLog('RESPONSE', '/api/yt', { url, n }, data);
            
            const lines = [`[YT] Transcribed ${data.videos_processed} video(s) — Vocabulary: ${data.vocabulary_size} words\n`];
            data.results.forEach(r => {
              if (r.error) {
                lines.push(`✗ ${r.title}: ${r.error}`);
              } else {
                lines.push(`✓ ${r.title}`);
                lines.push(`  ${r.transcript_length} chars | ${r.words_learned} words learned | ${Math.round(r.duration)}s`);
              }
            });
            reply = lines.join('\n');
            processingProgress = 100;
          } else {
            reply = `[YT] API Error: ${ytRes.status}`;
            processingProgress = 50;
          }
        }
      } else if (userMsg.startsWith('/api')) {
        try {
          const apiRes = await fetch('/api');
          addDebugLog('REQUEST', '/api', {}, '');

          if (apiRes.ok) {
            const apiData = await apiRes.json();
            addDebugLog('RESPONSE', '/api', {}, apiData);
            reply = `🔗 API ENTRYPOINTS\nOpenAPI: ${apiData.openapi}\nDocs: ${apiData.docs}`;
            processingProgress = 100;
          } else {
            reply = `[API] Unable to fetch API links. Status: ${apiRes.status}`;
            processingProgress = 60;
          }
        } catch (err) {
          reply = `[API] Error fetching docs: ${err.message}`;
          processingProgress = 40;
        }
      } else if (userMsg.startsWith('/stats')) {
        // Generate brain statistics report
        try {
          const totalActivity = Object.values(activeRegions).reduce((a, b) => a + b, 0);
          const avgActivity = (totalActivity / Object.keys(activeRegions).length).toFixed(2);
          const mostActive = Object.entries(activeRegions).sort((a, b) => b[1] - a[1])[0];
          const leastActive = Object.entries(activeRegions).sort((a, b) => a[1] - b[1])[0];
          
          // Calculate learning indicators
          const stdpScore = (activeRegions.association + activeRegions.feature) / 2;
          const memoryLoad = activeRegions.working_mem;
          const predictionAccuracy = Math.max(0, 100 - predError * 10).toFixed(1);
          
          // Calculate processing efficiency
          const throughput = (stepRate * globalGain).toFixed(2);
          const neuralEfficiency = (totalActivity / (globalGain * 10) * 100).toFixed(1);
          
          // Get vocabulary from API (need to fetch)
          let vocabSize = 0;
          let bypassRate = 0;
          try {
            const vs = await fetch('/api/brain/status');
            if (vs.ok) {
              const bd = await vs.json();
              // Defensive: ensure numbers are valid
              const vs = Number(bd?.vocabulary?.vocabulary_size);
              vocabSize = (vs && vs > 0) ? Math.floor(vs) : 0;
              const br = Number(bd?.bypass?.bypass_rate);
              bypassRate = (br && br > 0) ? br : 0;
            }
          } catch (e) { 
            console.error('/stats fetch error:', e);
          }
          
        // Learning stages with validation
        const NEONATAL_MAX = 50;
        const IMMATURE_MAX = 200;
        let stage = 'NEONATAL';
        let progress = 0;
        vocabSize = Math.max(0, vocabSize);
        // Clamp progress to valid range to avoid negative repeats
        if (vocabSize < NEONATAL_MAX) {
          stage = 'NEONATAL';
          progress = (vocabSize / NEONATAL_MAX) * 100;
        } else if (vocabSize < IMMATURE_MAX) {
          stage = 'IMMATURE';
          progress = ((vocabSize - NEONATAL_MAX) / (IMMATURE_MAX - NEONATAL_MAX)) * 100;
        } else {
          stage = 'MATURITY';
          progress = Math.min(100, 50 + (vocabSize - IMMATURE_MAX) / 100);
          if (progress > 100) progress = 100;
        }
        // Progress bar
        const barWidth = 20;
        const filled = Math.max(0, Math.min(barWidth, Math.floor((progress / 100) * barWidth)));
        const empty = Math.max(0, barWidth - filled);
        const bar = '█'.repeat(filled) + '░'.repeat(empty);
          
          // Generate region breakdown
          let regionStats = '\n📊 REGION ACTIVITY BREAKDOWN:\n';
          REGIONS.forEach(r => {
            const activity = activeRegions[r.id] || 0;
            const rbar = '█'.repeat(Math.floor(activity / 5)) + '░'.repeat(12 - Math.floor(activity / 5));
            const percentage = ((activity / 60) * 100).toFixed(1);
            regionStats += `   ${r.label.padEnd(18)} [${rbar}] ${percentage}%\n`;
          });
          
          // Calculate spike statistics
          const totalSpikes = Math.floor(step * globalGain * 0.1);
          const spikesPerSecond = Math.floor(stepRate * globalGain);
          
          // Memory and concept formation stats
          const conceptDensity = (activeRegions.concept / 60 * 100).toFixed(1);
          const workingMemoryLoad = (activeRegions.working_mem / 60 * 100).toFixed(1);
          
          reply = `🧠 BRAIN 2.0 STATISTICS REPORT
══════════════════════════════════════════

⏱️  SIMULATION METRICS:
   Current Step: ${step.toLocaleString()}
   Step Rate: ${stepRate} steps/sec
   Global Gain: ${globalGain}
   Prediction Error: ${predError.toFixed(4)}

🎯 LEARNING STAGE PROGRESS
   Stage: ${stage}
   Vocabulary: ${vocabSize} words
   [${bar}] ${progress.toFixed(0)}%

⚡ PROCESSING PERFORMANCE:
   Neural Throughput: ${throughput} spikes/sec
   Processing Efficiency: ${neuralEfficiency}%
   System Load: ${(globalGain * 100 / 5).toFixed(1)}%
   Local Generation: ${(bypassRate * 100).toFixed(1)}%

🧠 CORTICAL ACTIVITY:
   Total Activity: ${totalActivity.toFixed(2)} units
   Average Activity: ${avgActivity}%
   Most Active: ${mostActive[0]} (${mostActive[1].toFixed(1)})
   Least Active: ${leastActive[0]} (${leastActive[1].toFixed(1)})

${regionStats}
📈 LEARNING INDICATORS:
   STDP Synaptic Plasticity: ${stdpScore.toFixed(1)}%
   Concept Formation: ${conceptDensity}%
   Working Memory Load: ${workingMemoryLoad}%
   Prediction Accuracy: ${predictionAccuracy}%

💬 CONVERSATION HISTORY:
   Total Messages: ${messages.length}
   User Messages: ${messages.filter(m => m.role === 'user').length}
   Brain Responses: ${messages.filter(m => m.role === 'brain').length}

🔬 TECHNICAL PARAMETERS:
   Spike Trains: Poisson (λ=${globalGain.toFixed(2)})
   STDP Window: 20ms (LTP) / 20ms (LTD)
   Refractory Period: 2ms
   Membrane Time Constant: 20ms

Status: ${brainStatus}
══════════════════════════════════════════════`;
          processingProgress = 100;
        } catch (e) {
          const stack = e?.stack || e?.message || String(e);
          reply = `⚠️ /stats error\n\n${stack}`;
          processingProgress = 100;
        }
} else if (userMsg === '/vocabulary') {
        // Show learned vocabulary
        try {
          const vocabRes = await fetch('/api/vocabulary');
          if (vocabRes.ok) {
            const data = await vocabRes.json();
            const asmRes = await fetch('/api/assemblies');
            const asmData = asmRes.ok ? await asmRes.json() : {};
            
            const words = data.words || [];
            const totalWords = data.vocabulary_size || 0;
            
            // Group words by first letter for better UX
            const grouped = words.reduce((acc, w) => {
              const first = w[0]?.toUpperCase() || '#';
              if (!acc[first]) acc[first] = [];
              acc[first].push(w);
              return acc;
            }, {});
            
            const groupedLines = Object.entries(grouped)
              .sort((a, b) => a[0].localeCompare(b[0]))
              .map(([letter, ws]) => `  ${letter}: ${ws.join(', ')}`)
              .join('\n');
            
            reply = `📚 BRAIN 2.0 VOCABULARY
═════════════════════════════════════════════

Total words learned: ${totalWords}
Recent words shown: ${words.length}
Assemblies: ${data.assembly_coverage || 0}
Total generations: ${data.total_generations || 0}
Successful: ${data.successful_generations || 0}
Success rate: ${((data.success_rate || 0) * 100).toFixed(1)}%

Recent words (last ${words.length}):
${groupedLines}
`;
            if (asmData.total_assemblies > 0) {
              reply += `\nStable assemblies: ${asmData.total_assemblies}`;
              reply += `\nTotal activations: ${asmData.total_activations || 0}`;
            }
            reply += `\n═════════════════════════════════════════════`;
          } else {
            reply = `[VOCAB] API Error: ${vocabRes.status}`;
          }
        } catch (e) {
          reply = `[VOCAB] Error: ${e.message}`;
        }
        processingProgress = 100;
      } else if (userMsg === '/?' || userMsg === '/help') {
        // Show all available commands
        reply = `📋 BRAIN 2.0 COMMAND REFERENCE
══════════════════════════════════════════════

Available Commands:

1. /stats
   Displays comprehensive brain statistics including:
   - Simulation metrics (step, rate, gain)
   - Cortical activity breakdown per region
   - Learning indicators (STDP, concepts)
   - Processing efficiency metrics

2. /vocabulary
   Shows learned vocabulary and assembly stats.
   - Words learned by the SNN
   - Assembly count and activation stats
   - Generation success rate

3. /grep <n> <url>
   Crawls web pages and extracts content.
   - <n>: Number of pages to crawl (1-10)
   - <url>: Starting URL for crawl
   Example: /grep 3 https://example.com

4. /llm <prompt>
   Sends direct query to LLM (Ollama).
   - <prompt>: Your question or command
   Example: /llm What is neural plasticity?

5. /yt <n> <url>
   Transcribes YouTube videos and teaches the brain.
   - <n>: Number of videos to process (1-10)
   - <url>: YouTube video URL
   Supports playlists and video chains.
   Example: /yt 3 https://youtube.com/watch?v=VIDEO_ID

6. /api
   Returns direct links to OpenAPI JSON and FastAPI docs.

7. /? or /help
   Shows this command reference.

8. Any other text
   Sends message to brain for processing.
   The brain will analyze and respond using
   its neural network architecture.

══════════════════════════════════════════════
Tip: Use /stats to monitor brain performance!`;
        processingProgress = 100;
      } else {
        // Normal chat message - send to Python API
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            message: userMsg,
            history: messages.slice(-6),
            brainState: {
              step, stepRate, brainStatus, predError, globalGain,
              regions: Object.fromEntries(
                REGIONS.map(r => [r.id, { activity_pct: activeRegions[r.id], neurons: r.neurons }])
              ),
            }
          })
        });
        
        addDebugLog('REQUEST', '/api/chat', { message: userMsg }, '');
        
        if (res.ok) {
          const data = await res.json();
          addDebugLog('RESPONSE', '/api/chat', { message: userMsg }, data);
          reply = data.response || data.reply;
          
          // Add new words learned notification
          if (data.new_words && data.new_words.length > 0) {
            reply += '\n\n✓ Learned: ' + data.new_words.join(', ');
          }
          
          processingProgress = 100;
        } else {
          // Fallback response if API fails
          reply = `[BRAIN 2.0] Processing "${userMsg}"... 

Simulated neural response: Input spike encoding complete. 
- Sensory cortex: activated (+15%)
- Feature extraction: edge detection in progress
- Association region: forming new pattern connections

Awaiting further stimuli.`;
          processingProgress = 50;
        }
      }

      // Decode which regions to activate based on reply keywords
      const lower = reply.toLowerCase();
      setActive(prev => {
        const next = { ...prev };
        if (lower.includes("associat"))  next.association   = Math.min(60, prev.association + 8);
        if (lower.includes("predict"))   next.predictive    = Math.min(60, prev.predictive + 10);
        if (lower.includes("concept"))   next.concept       = Math.min(60, prev.concept + 15);
        if (lower.includes("sensory"))   next.sensory       = Math.min(60, prev.sensory + 8);
        if (lower.includes("reflex") || lower.includes("safety")) next.reflex_arc = Math.min(60, prev.reflex_arc + 15);
        if (lower.includes("working"))   next.working_mem   = Math.min(60, prev.working_mem + 10);
        if (lower.includes("cerebell"))  next.cerebellum    = Math.min(60, prev.cerebellum + 12);
        if (lower.includes("stdp") || lower.includes("learn")) {
          next.association = Math.min(60, next.association + 5);
          next.feature     = Math.min(60, prev.feature + 5);
        }
        return next;
      });

      setMessages(prev => [...prev, { role: "brain", content: reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "brain", content: `[BRAIN 2.0 ERROR] ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, messages, step, stepRate, brainStatus, predError, globalGain, activeRegions]);

  const handleKey = e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    else if (e.key === "ArrowUp" || e.key === "ArrowDown") {
      handleHistoryNav(e);
    }
  };

  const region = REGIONS.find(r => r.id === selectedRegion) || REGIONS[0];
  const totalAct = Object.values(activeRegions).reduce((a, b) => a + b, 0);

  const fmt = n => n >= 1e9 ? (n/1e9).toFixed(2)+"B"
                : n >= 1e6  ? (n/1e6).toFixed(2)+"M"
                : n >= 1e3  ? (n/1e3).toFixed(1)+"k"
                : n;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-title">
          <h1>BRAIN 2.0</h1>
          <div className="header-subtitle">NEUROMORPHIC INTELLIGENCE · SNN RUNTIME</div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginLeft: 'auto' }}>
          <div className="header-stats">
            {[["NEURONS", "~858k"], ["WORDS", fmt(wordCount)], ["SYNAPSES", "~80M"], ["STEP", fmt(step)], ["RATE", `${stepRate} st/s`]].map(([k, v]) => (
              <div key={k} className="stat-item">
                <div className="stat-label">{k}</div>
                <div className="stat-value">{v}</div>
              </div>
            ))}
          </div>

          <div className={`llm-status ${llmStatus.ollama_available ? 'online' : 'offline'}`}>
            ◉ LLM {llmStatus.ollama_available ? `ONLINE (${llmStatus.ollama_models?.length || 0} models)` : llmStatus.configured ? "CONFIGURED" : "OFFLINE"}
          </div>

          <button className="header-theme-btn" onClick={toggleTheme}>
            {themeToggleLabel}
          </button>
        </div>
      </header>

      {/* ── TABS ── */}
      <div className="tabs">
        {[["brain","BRAIN ACTIVITY"],["chat","NEURAL CHAT"],["arch","ARCHITECTURE"],["reflex","SAFETY KERNEL"],["debug","DEBUG"]].map(([id, lbl]) => (
          <button key={id} onClick={() => setTab(id)} className={`tab-button ${tab === id ? 'active' : ''}`}>{lbl}</button>
        ))}
      </div>

      {/* ── BODY ── */}
      <div className="main-content">

        {/* ── BRAIN ACTIVITY TAB ── */}
        {tab === "brain" && (
          <div className="brain-tab">
            {/* Region list */}
            <div className="region-list">
              {REGIONS.map(r => {
                const act = activeRegions[r.id] || 0;
                const selected = selectedRegion === r.id;
                return (
                  <button key={r.id} onClick={() => setSelected(r.id)} className={`region-button ${selected ? 'selected' : ''}`}>
                    <div className="region-header">
                      <span className="region-name" style={{ color: selected ? r.color : undefined }}>{r.label}</span>
                      <span className="region-activity" style={{ color: r.color }}>{act.toFixed(1)}%</span>
                    </div>
                    <div className="region-bar">
                      <div className="region-bar-fill" style={{ width: `${(act / 60) * 100}%`, background: r.color, boxShadow: `0 0 6px ${r.color}80` }} />
                    </div>
                    <div className="region-neurons">{r.neurons} neurons</div>
                  </button>
                );
              })}
            </div>

            {/* Canvas + Chat (flex: 1) */}
            <div className="canvas-container">
              {/* Canvas */}
              <div className="canvas-wrapper">
                <NeuralCanvas activeRegions={activeRegions} globalGain={globalGain} />
                <div className="canvas-label">LIVE SPIKE ACTIVITY · {Object.values(activeRegions).reduce((a,b)=>a+b,0).toFixed(1)}% TOTAL</div>
                {/* Region legend */}
                <div className="canvas-legend">
                  {REGIONS.map(r => (
                    <div key={r.id} className="legend-item">
                      <div className="legend-dot" style={{ background: r.color }} />
                      <span className="legend-label">{r.label.split(" ")[0]}</span>
                    </div>
                  ))}
                </div>
                {globalGain > 2 && (
                  <div className="attention-indicator">⚡ HIGH ATTENTION · ×{globalGain}</div>
                )}
              </div>
              {/* Chat Panel - Integrated */}
              <div className="chat-panel">
                {/* Chat header */}
                <div className="chat-header">NEURAL CHAT</div>
                {/* Chat messages */}
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
                            <button className="feedback-button" onClick={() => sendFeedback(1.0, i)} title="This response was helpful - the brain will learn from this">👍</button>
                            <button className="feedback-button" onClick={() => sendFeedback(-1.0, i)} title="This was incorrect - the brain will try to improve">👎</button>
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
                </div>
                {/* Chat input */}
                <div className={`chat-input-area ${isDragging ? 'dragging' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                >
                  <input
                    type="text"
                    value={input}
                    onChange={handleInputChange}
                    onKeyDown={handleKey}
                    placeholder={isDragging ? "Drop file..." : "Talk to brain..."}
                    className="chat-input"
                  />
                  <button onClick={sendMessage} disabled={loading || !input.trim()} className="send-button">
                    {loading ? "..." : "▶"}
                  </button>
                </div>
              </div>
            </div>

            {/* ── Right Column (180px): Emotion / Thinking / Extended ── */}
            <div className="right-sidebar">
              {/* Emotion Panel (1/3) */}
              <div className="panel-section">
                <div className="panel-label">AFFECTIVE STATE</div>
                {/* Face emoji from valence/arousal quadrant */}
                <div className="emoji-face">
                  {(() => {
                    const v = affect.valence;
                    const a = affect.arousal;
                    if (a > 0.5 && v > 0.3) return "😊";
                    if (a > 0.5 && v < -0.3) return "😠";
                    if (a <= 0.5 && v > 0.3) return "😌";
                    if (a <= 0.5 && v < -0.3) return "😔";
                    return "😐";
                  })()}
                </div>
                {/* Mood label */}
                <div className="mood-label">
                  {(() => {
                    const v = affect.valence;
                    const a = affect.arousal;
                    if (a > 0.5 && v > 0.3) return "Excited";
                    if (a > 0.5 && v < -0.3) return "Stressed";
                    if (a <= 0.5 && v > 0.3) return "Calm";
                    if (a <= 0.5 && v < -0.3) return "Low";
                    return "Neutral";
                  })()}
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
                      background: affect.valence >= 0 ? 'var(--accent)' : 'var(--llm-offline-color)',
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
                      background: `linear-gradient(90deg, var(--accent), var(--llm-offline-color))`,
                      borderRadius: "2px",
                    }} />
                  </div>
                </div>
                {/* Drive indicators */}
                <div className="drives-section">
                  <div className="drives-label">DRIVES</div>
              {[
                { label: "Curiosity", value: drives.curiosity, color: 'var(--accent)' },
                { label: "Competence", value: drives.competence, color: 'var(--accent-alt)' },
                { label: "Connection", value: drives.connection, color: 'var(--llm-online-color)' },
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

              {/* Thinking Panel (1/3) */}
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

              {/* Empty / Extended Panel (1/3) */}
              <div className="extended-section">
                <div className="panel-label">EXTENDED</div>
                <div className="extended-placeholder">(reserved)</div>
              </div>
            </div>
          </div>
        )}

        {/* ── CHAT TAB ── */}
        {tab === "chat" && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {/* Mini activity bar */}
            <div style={{
              flexShrink: 0, display: "flex", gap: "4px", padding: "8px 16px",
              borderBottom: `1px solid ${borderSubtle}`, overflowX: "auto",
            }}>
              {REGIONS.map(r => (
                <div key={r.id} style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: "36px" }}>
                  <div style={{
                    width: "28px", height: "28px", borderRadius: "50%",
                    border: `1px solid ${r.color}40`,
                    background: `${r.color}${Math.floor((activeRegions[r.id] / 60) * 255).toString(16).padStart(2,"0")}`,
                    transition: "background 0.4s",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "7px", color: r.color, fontWeight: 700,
                  }}>{activeRegions[r.id]?.toFixed(0)}%</div>
                  <div style={{ fontSize: "5px", color: textMuted, marginTop: "2px", textAlign: "center", lineHeight: 1.1 }}>
                    {r.label.split(" ").map((w,i)=><div key={i}>{w.slice(0,5)}</div>)}
                  </div>
                </div>
              ))}
            </div>

            {/* Messages */}
            <div className="chat-messages-full">
              {messages.map((m, i) => (
                <div key={i} className={`message-row ${m.role}`}>
                  {m.role === "brain" && (
                    <div className="brain-avatar">⬡</div>
                  )}
                  <div className={`message-bubble ${m.role}`}>
                    {m.role === "brain" && m.isProactive && (
                      <div className="brain-label" style={{ fontStyle: 'italic', marginBottom: '3px' }}>SPONTANEOUS THOUGHT</div>
                    )}
                    {m.role === "brain" && !m.isProactive && (
                      <div className="brain-label">BRAIN 2.0 · NEURAL RESPONSE</div>
                    )}
                    {m.content}
                    {m.role === "brain" && !m.isProactive && (
                      <div style={{ display: "flex", gap: "6px", marginTop: "6px" }}>
                        <button className="feedback-button" onClick={() => sendFeedback(1.0, i)} title="This response was helpful - the brain will learn from this">👍</button>
                        <button className="feedback-button" onClick={() => sendFeedback(-1.0, i)} title="This was incorrect - the brain will try to improve">👎</button>
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
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div className={`full-chat-input ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            >
              <textarea
                ref={inputRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKey}
                placeholder={isDragging ? "Drop file here..." : "Stimulate the network... (Enter to send)"}
                rows={1}
                className="chat-textarea"
              />
              <button onClick={sendMessage} disabled={loading || !input.trim()} className="full-send-button">
                {loading ? "..." : "FIRE ▶"}
              </button>
            </div>
          </div>
        )}

        {/* ── ARCHITECTURE TAB ── */}
        {tab === "arch" && (
          <div className="arch-tab">
            {/* Flow */}
            <div className="flow-column">
              <div className="arch-label">INFORMATION FLOW</div>
              {[
                { label: "SENSORY INPUT",     sub: "Vision  ·  Audio  ·  Touch",              color: REGIONS[0].color },
                { label: "SENSORY CORTEX",    sub: "Poisson spike encoding, 40k neurons",      color: REGIONS[0].color },
                { label: "FEATURE LAYER",     sub: "Edges / phonemes / pressure, 80k",         color: REGIONS[1].color },
                { label: "ASSOCIATION HUB",   sub: "STDP cross-modal binding, 500k",           color: accent },
                { label: "PREDICTIVE",        sub: "Error → attention_gain broadcast",         color: accentAlt },
                { label: "CONCEPT LAYER",     sub: "WTA sparse coding, 5.8k neurons",          color: REGIONS[4].color },
                { label: "META CONTROL",      sub: "Top-down attention, 60k",                  color: REGIONS[5].color },
                { label: "WORKING MEMORY",    sub: "Recurrent spike buffer, 20k",              color: REGIONS[6].color },
                { label: "CEREBELLUM",        sub: "Motor timing, eligibility traces",         color: REGIONS[7].color },
                { label: "REFLEX ARC",        sub: "SAFETY GATE — force/angle/velocity check", color: llmOfflineColor },
              ].map((n, i, arr) => (
                <div key={i} className="flow-item">
                  <div className="flow-box" style={{ borderColor: `${n.color}35`, background: `${n.color}0c` }}>
                    <div className="flow-title" style={{ color: n.color }}>{n.label}</div>
                    <div className="flow-sub">{n.sub}</div>
                  </div>
                  {i < arr.length - 1 && (
                    <div className="flow-arrow" style={{ background: `linear-gradient(${arr[i].color}60,${arr[i+1].color}60)` }}>
                      <div className="flow-arrow-icon" style={{ color: arr[i+1].color }}>▼</div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* STDP + concepts */}
            <div className="info-column">
              {[
                { title: "STDP Rule",         color: accent, body: "Pre fires BEFORE post → LTP: Δw = +A_plus·exp(−Δt/τ). Post before pre → LTD: Δw = −A_minus·exp(−Δt/τ). No global error. Purely local + temporal." },
                { title: "Predictive Loop",   color: accentAlt, body: "Association → Predictive. Error = |actual − predicted|. gain = 1 + 4·error. High error → gain × applied to all STDP updates. Surprise accelerates learning." },
                { title: "WTA Sparse Coding", color: REGIONS[4].color, body: "5,800 concept neurons compete via lateral inhibition. Only 3–5 fire per concept. Each concept is an orthogonal sparse code. Efficient & discriminable." },
                { title: "Safety Kernel",     color: llmOfflineColor, body: "ReflexArc.check_command() intercepts every motor output. Force>10N, angle>170°, vel>2m/s → BLOCKED. Withdrawal reflex fires. Hard-gated — no ML pathway bypasses this." },
              ].map(c => (
                <div key={c.title} className="info-card" style={{ background: `${c.color}08`, borderColor: `${c.color}25` }}>
                  <div className="info-title" style={{ color: c.color }}>{c.title}</div>
                  <div className="info-body">{c.body}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── REFLEX / SAFETY TAB ── */}
        {tab === "reflex" && <ReflexPanel theme={theme} />}

        {/* ── DEBUG TAB ── */}
        {tab === "debug" && (
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
        )}
      </div>

      {/* ── FOOTER ── */}
      <footer className="app-footer">
        <div className="footer-copyright">
          BRAIN 2.0 © 2026
        </div>
      </footer>
    </div>
  );
}
