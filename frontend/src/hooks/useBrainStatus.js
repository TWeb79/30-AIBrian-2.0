import { useState, useEffect, useCallback } from 'react';
// Import REGIONS from the central constants module
import { REGIONS } from '../constants';

export function useBrainStatus(pollInterval = 1200) {
  const [step, setStep] = useState(2_000_000);
  const [stepRate, setStepRate] = useState(0.54);
  const [wordCount, setWordCount] = useState(0);
  const [brainStatus, setBrainStatus] = useState("JUVENILE");
  const [predError, setPredError] = useState(0.0);
  const [globalGain, setGlobalGain] = useState(1.0);
  const [activeRegions, setActive] = useState(() =>
    Object.fromEntries(REGIONS.map(r => [r.id, r.baseAct]))
  );
  const [affect, setAffect] = useState({ valence: 0.0, arousal: 0.3 });
  const [drives, setDrives] = useState({ curiosity: 0.5, competence: 0.5, connection: 0.5 });
  const [llmStatus, setLlmStatus] = useState({ configured: false, backend: "none", model: null });

  useEffect(() => {
    // Fetch LLM status on mount
    fetch('/api/llm/status')
      .then(r => r.ok ? r.json() : null)
      .then(data => data && setLlmStatus(data))
      .catch(() => {});

    const id = setInterval(async () => {
      try {
        const res = await fetch('/api/brain/status');
        if (res.ok) {
          const data = await res.json();
          setStep(data.step || 0);
          setStepRate(data.step_rate || 0);
          setBrainStatus(data.status || "NEONATAL");
          setPredError(data.prediction_error || 0);
          setGlobalGain(data.attention_gain || 1);
          
          if (data.vocabulary) {
            const vocabSize = Number(data.vocabulary.vocabulary_size);
            setWordCount(Number.isFinite(vocabSize) ? Math.max(0, Math.floor(vocabSize)) : 0);
          }
          
          if (data.regions) {
            const regionActivity = {};
            Object.keys(data.regions).forEach(key => {
              const region = data.regions[key];
              regionActivity[key] = region.activity_pct !== undefined ? region.activity_pct : 
                (REGIONS.find(r => r.id === key)?.baseAct || 10);
            });
            setActive(regionActivity);
          }
          
          if (data.affect) {
            setAffect({ valence: data.affect.valence ?? 0, arousal: data.affect.arousal ?? 0.3 });
          }
          
          if (data.drives) {
            setDrives({
              curiosity: data.drives.curiosity ?? 0.5,
              competence: data.drives.competence ?? 0.5,
              connection: data.drives.connection ?? 0.5,
            });
          }
        }
      } catch {}
    }, pollInterval);
    
    return () => clearInterval(id);
  }, [pollInterval]);

  const spikeRegions = useCallback(() => {
    setActive(prev => {
      const next = { ...prev };
      ["sensory","feature","association","predictive"].forEach(k => {
        next[k] = Math.min(60, prev[k] + Math.random() * 20 + 10);
      });
      return next;
    });
    setGlobalGain(parseFloat((2 + Math.random() * 2).toFixed(2)));
  }, []);

  return {
    step, stepRate, wordCount, brainStatus, predError, globalGain,
    activeRegions, affect, drives, llmStatus,
    spikeRegions, setStep, setStepRate, setPredError, setGlobalGain
  };
}

export function useThoughts(pollInterval = 1200) {
  const [thoughts, setThoughts] = useState([]);
  
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const res = await fetch('/api/brain/status');
        if (!res.ok) return;
        const data = await res.json();
        
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
          
          const candidates = [];
          if (pred > 0.05) candidates.push(`Prediction error detected — adjusting synaptic weights`);
          if (concept > 15) candidates.push(`New concept forming in sparse coding layer`);
          if (concept > 5 && concept <= 15) candidates.push(`Strengthening concept representation`);
          if (sensory > 20 && feature > 15) candidates.push(`Processing sensory patterns — extracting features`);
          if (sensory > 30) candidates.push(`Receiving fresh sensory input`);
          if (assoc > 20) candidates.push(`Cross-modal associations forming`);
          if (gain > 2.0) candidates.push(`High attention — filtering noise`);
          if (working > 15) candidates.push(`Holding information in working memory`);
          if (working > 30) candidates.push(`Buffering temporal sequence`);
          if (data.vocabulary?.vocabulary_size > 0 && Math.random() < 0.1) {
            candidates.push(`Recall: ${Math.min(5, data.vocabulary.vocabulary_size)} words in memory`);
          }
          if (data.assemblies?.total_assemblies > 0 && Math.random() < 0.1) {
            candidates.push(`${data.assemblies.total_assemblies} stable assemblies detected`);
          }
          if (st % 50000 < 10) {
            candidates.push(`Milestone: ${(st/1000).toFixed(0)}k steps completed`);
          }
          
          let thought = null;
          if (candidates.length > 0) {
            const weights = candidates.map((_, i) => i < 3 ? 3 : 1);
            const totalWeight = weights.reduce((a, b) => a + b, 0);
            let r = Math.random() * totalWeight;
            for (let i = 0; i < weights.length; i++) {
              r -= weights[i];
              if (r <= 0) {
                thought = candidates[i];
                break;
              }
            }
            if (!thought) thought = candidates[0];
          }
          
          if (thought && totalActivity > 0.1) {
            setThoughts(prev => [...prev.slice(-7), thought]);
          }
        }
      } catch {}
    }, pollInterval);
    
    return () => clearInterval(id);
  }, [pollInterval]);

  return { thoughts };
}