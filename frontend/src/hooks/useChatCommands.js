import { useState, useCallback, useRef } from 'react';

export function useChatCommands(addDebugLog, activeRegions) {
  const [loading, setLoading] = useState(false);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const userMessagesRef = useRef([]);

  const processCommand = useCallback(async (userMsg) => {
    let reply = null;
    let progress = 0;

    if (userMsg.startsWith('/grep')) {
      const parts = userMsg.split(/\s+/);
      if (parts.length >= 3) {
        const n = parseInt(parts[1], 10);
        const url = parts.slice(2).join(' ');
        
        if (isNaN(n) || !url) {
          reply = `[GREP] Invalid syntax. Use: /grep <n> <url>\nExample: /grep 3 https://example.com`;
          progress = 100;
        } else {
          const res = await fetch('/api/grep', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ n, url })
          });
          
          addDebugLog('REQUEST', '/api/grep', { n, url }, '');
          
          if (res.ok) {
            const data = await res.json();
            addDebugLog('RESPONSE', '/api/grep', { n, url }, data);
            reply = `[GREP] Crawled ${data.crawled} of ${data.requested} pages from ${data.start_url}\n\n`;
            
            data.results.forEach((r, i) => {
              if (r.error) {
                reply += `${i+1}. ${r.url}: ERROR - ${r.error}\n\n`;
              } else {
                reply += `${i+1}. ${r.url} (${r.status})\n`;
                const content = r.content.substring(0, 500);
                reply += `   ${content}${r.content.length > 500 ? '...' : ''}\n\n`;
              }
            });
            progress = 100;
          } else {
            reply = `[GREP] API Error: ${res.status}`;
            progress = 50;
          }
        }
      } else {
        reply = `[GREP] Invalid syntax. Use: /grep <n> <url>\nExample: /grep 3 https://example.com`;
        progress = 100;
      }
    } else if (userMsg.startsWith('/llm')) {
      const prompt = userMsg.substring(4).trim();
      
      if (!prompt) {
        reply = `[LLM] Invalid syntax. Use: /llm <prompt>\nExample: /llm What is the capital of France?`;
        progress = 100;
      } else {
        const res = await fetch('/api/llm/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt })
        });
        
        addDebugLog('REQUEST', '/api/llm/chat', { prompt }, '');
        
        if (res.ok) {
          const data = await res.json();
          addDebugLog('RESPONSE', '/api/llm/chat', { prompt }, data);
          reply = `[LLM] Response:\n\n${data.response || data.reply || data.message}`;
          progress = 100;
        } else {
          reply = `[LLM] API Error: ${res.status}. Make sure Ollama is running.`;
          progress = 50;
        }
      }
    } else if (userMsg.startsWith('/yt')) {
      const parts = userMsg.substring(3).trim().split(/\s+/);
      const n = parseInt(parts[0]) || 1;
      const url = parts.slice(1).join(' ');
      
      if (!url || !url.includes('youtube.com') && !url.includes('youtu.be')) {
        reply = `[YT] Invalid syntax. Use: /yt <n> <youtube_url>\nExample: /yt 2 https://www.youtube.com/watch?v=VIDEO_ID`;
        progress = 100;
      } else {
        const res = await fetch('/api/yt', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, n: Math.min(n, 10) })
        });
        
        addDebugLog('REQUEST', '/api/yt', { url, n }, '');
        
        if (res.ok) {
          const data = await res.json();
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
          progress = 100;
        } else {
          reply = `[YT] API Error: ${res.status}`;
          progress = 50;
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
          progress = 100;
        } else {
          reply = `[API] Unable to fetch API links. Status: ${apiRes.status}`;
          progress = 60;
        }
      } catch (err) {
        reply = `[API] Error fetching docs: ${err.message}`;
        progress = 40;
      }
    } else if (userMsg.startsWith('/stats')) {
      const totalActivity = Object.values(activeRegions).reduce((a, b) => a + b, 0);
      const avgActivity = (totalActivity / Object.keys(activeRegions).length).toFixed(2);
      const mostActive = Object.entries(activeRegions).sort((a, b) => b[1] - a[1])[0];
      const leastActive = Object.entries(activeRegions).sort((a, b) => a[1] - b[1])[0];
      
      const stdpScore = (activeRegions.association + activeRegions.feature) / 2;
      const conceptScore = activeRegions.concept || 0;
      const memoryScore = (activeRegions.working_mem || 0) + (activeRegions.meta_control || 0) / 2;
      
      reply = `🧠 BRAIN STATISTICS REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIMULATION
  Steps: ${(await fetch('/api/brain/status').then(r => r.json()).then(d => d.step || 0).catch(() => 0)).toLocaleString()}
  Rate: ${(await fetch('/api/brain/status').then(r => r.json()).then(d => d.step_rate || 0).catch(() => 0)).toFixed(2)}k steps/s

CORTICAL ACTIVITY
  Total: ${totalActivity.toFixed(1)}%
  Average: ${avgActivity}%
  Peak: ${mostActive[0]} @ ${mostActive[1].toFixed(1)}%
  Lowest: ${leastActive[0]} @ ${leastActive[1].toFixed(1)}%

LEARNING INDICATORS
  STDP Activity: ${stdpScore.toFixed(1)}% (Association+Feature)
  Concept Formation: ${conceptScore.toFixed(1)}%
  Working Memory: ${memoryScore.toFixed(1)}%

PROCESSING STATUS
  Regions: 10 active
  Synapses: STDP learning enabled
  Prediction: Error-driven attention`;
      progress = 100;
    } else if (userMsg.startsWith('/vocabulary')) {
      try {
        const res = await fetch('/api/vocabulary');
        const data = await res.json();
        const words = data.words || [];
        const asmCount = data.assembly_count || 0;
        reply = `📚 VOCABULARY STATUS
━━━━━━━━━━━━━━━━━━━━━━
Total Words: ${data.vocabulary_size || 0}
Stable Assemblies: ${asmCount}

${words.length > 0 ? 'Learned Words:\n' + words.slice(0, 30).join(', ') + (words.length > 30 ? '...' : '') : 'No words learned yet.'}`;
        progress = 100;
      } catch {
        reply = `[VOCABULARY] API Error`;
        progress = 50;
      }
    } else if (userMsg === '/?' || userMsg === '/help') {
      reply = `📖 AVAILABLE COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
/stats    — Brain statistics report
/vocabulary — Learned vocabulary
/grep <n> <url> — Crawl web pages
/llm <prompt> — Direct LLM query
/yt <n> <url> — YouTube transcription
/api     — Show API endpoints
/?       — This help message`;
      progress = 100;
    }

    return { reply, progress };
  }, [addDebugLog, activeRegions]);

  const handleHistoryNav = useCallback((e, userMessages) => {
    if (userMessages.length === 0) return;
    if (e.key === "ArrowUp") {
      e.preventDefault();
      const newIndex = historyIndex < userMessages.length - 1 ? historyIndex + 1 : historyIndex;
      setHistoryIndex(newIndex);
      return userMessages[userMessages.length - 1 - newIndex] || "";
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      const newIndex = historyIndex > -1 ? historyIndex - 1 : -1;
      setHistoryIndex(newIndex);
      return newIndex >= 0 ? userMessages[userMessages.length - 1 - newIndex] : "";
    }
    return null;
  }, [historyIndex]);

  return {
    loading, setLoading,
    processCommand,
    handleHistoryNav,
    setHistoryIndex,
    userMessagesRef
  };
}