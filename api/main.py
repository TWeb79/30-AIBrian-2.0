"""
api.py — OSCEN FastAPI REST Server
====================================
Exposes the brain simulation over HTTP so the React UI can
connect to it.  Run with:

    uvicorn api:app --host 0.0.0.0 --port 8000 --reload

Endpoints
---------
GET  /status          → brain snapshot (regions, stats, synapses)
GET  /health          → simple heartbeat
POST /stimulate       → inject sensory stimulus
POST /chat            → send text to brain (also proxies to Claude API)
POST /motor           → issue motor command (through reflex arc)
WS   /ws/stream       → real-time brain state stream (JSON, 5 Hz)
"""

from __future__ import annotations
import asyncio
import json
import os
import re
import time
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urljoin, urlparse

import numpy as np
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from brain import OSCENBrain

# ─── Boot brain ───────────────────────────────────────────────────────────────

SCALE = float(os.getenv("BRAIN_SCALE", "0.01"))   # 0.01 = fast CPU demo
brain = OSCENBrain(scale=SCALE)
brain.start_background_loop(steps_per_tick=100)

# ─── FastAPI app ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    yield
    brain.stop()
    brain.persist()
    print("[API] Brain persisted on shutdown")

app = FastAPI(title="OSCEN Brain API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic models ──────────────────────────────────────────────────────────

class StimulusRequest(BaseModel):
    modality:   str            # "vision" | "audio" | "touch"
    data:       list[float]    # normalised [0,1] values

class ChatRequest(BaseModel):
    message:    str
    history:    list[dict] = []
    brainState: dict = {}

class MotorCommand(BaseModel):
    force:    float = 0.0
    angle:    float = 0.0
    velocity: float = 0.0
    joint:    str   = "arm"

class ReflexCheckRequest(BaseModel):
    force:    float
    angle:    float
    velocity: float

class GrepRequest(BaseModel):
    n: int
    url: str

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "alive", "uptime_s": round(time.time() - brain.start_time, 1)}


@app.get("/api/llm/status")
def llm_status():
    """Check if LLM is configured and available."""
    from config import LLM_CONFIG
    
    configured = bool(LLM_CONFIG.anthropic_api_key or LLM_CONFIG.openai_api_key or LLM_CONFIG.ollama_base_url)
    backend = LLM_CONFIG.backend
    
    # Actually check if Ollama is reachable
    ollama_available = False
    ollama_models = []
    if LLM_CONFIG.ollama_base_url:
        try:
            import requests
            response = requests.get(f"{LLM_CONFIG.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                ollama_available = True
                data = response.json()
                ollama_models = [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            pass
    
    return {
        "configured": configured,
        "backend": backend,
        "model": LLM_CONFIG.get_default_model() if configured else None,
        "ollama_available": ollama_available,
        "ollama_url": LLM_CONFIG.ollama_base_url,
        "ollama_models": ollama_models if ollama_available else LLM_CONFIG.ollama_models,
    }


@app.get("/api/brain/status")
def status():
    snap = brain.snapshot()
    snap["total_neurons"]  = brain.total_neurons()
    snap["total_synapses"] = brain.total_synapses()
    # v0.2: Include vocabulary, memory, and bypass stats
    snap["vocabulary"] = brain.phon_buffer.get_statistics()
    snap["memory"] = brain.hippocampus.get_statistics()
    snap["bypass"] = brain.bypass_monitor.get_statistics()
    snap["assemblies"] = brain.assembly_detector.get_statistics()
    return snap


@app.get("/api/vocabulary")
def vocabulary():
    """Return vocabulary learning statistics and word list."""
    stats = brain.phon_buffer.get_statistics()
    stats["words"] = sorted(brain.phon_buffer.word_index.keys())
    return stats


@app.get("/api/memory")
def memory():
    """Return episodic memory statistics and recent episodes."""
    stats = brain.hippocampus.get_statistics()
    recent = [
        {"topic": ep.topic, "valence": ep.valence, "timestamp": ep.timestamp}
        for ep in brain.hippocampus.get_recent(5)
    ]
    stats["recent_episodes"] = recent
    return stats


@app.get("/api/bypass")
def bypass():
    """Return LLM bypass rate and path distribution."""
    return brain.bypass_monitor.get_statistics()


@app.get("/api/assemblies")
def assemblies():
    """Return cell assembly statistics."""
    return brain.assembly_detector.get_statistics()


@app.post("/api/stimulate")
def stimulate(req: StimulusRequest):
    arr = np.array(req.data, dtype=np.float32)
    brain.stimulate_modality(req.modality, arr)
    return {"injected": len(arr), "modality": req.modality}


@app.post("/api/llm/chat")
async def llm_chat(req: dict):
    """
    Direct LLM prompt - bypasses brain processing and sends directly to LLM.
    Returns the raw LLM response.
    """
    from config import LLM_CONFIG
    
    prompt = req.get("prompt", "")
    
    if not prompt:
        return {"error": "No prompt provided"}, 400
    
    try:
        # Check if Ollama is available
        if LLM_CONFIG.is_ollama_available():
            model = LLM_CONFIG.get_best_available_model()
            ollama_url = LLM_CONFIG.ollama_base_url
            
            # Direct call to Ollama
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"response": result.get("response", "")}
            else:
                return {"error": f"Ollama error: {response.status_code}"}, response.status_code
        else:
            return {"error": "Ollama not available. Make sure Ollama is running."}, 503
    except Exception as e:
        print(f"[API /llm/chat] Error: {e}")
        return {"error": str(e)}, 500


@app.post("/api/grep")
async def grep(req: GrepRequest):
    """
    Web crawling endpoint - crawls n pages from the given URL.
    """
    from bs4 import BeautifulSoup
    
    n = req.n
    start_url = req.url
    
    if n < 1 or n > 20:
        return {"error": "n must be between 1 and 20"}, 400
    
    visited = set()
    results = []
    queue = [start_url]
    base_domain = urlparse(start_url).netloc
    
    while queue and len(results) < n:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        
        try:
            response = requests.get(url, timeout=10)
            status = response.status_code
            
            if response.ok:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                content = soup.get_text(separator=' ', strip=True)
                # Clean up whitespace
                content = ' '.join(content.split())
                
                # Find more links on the same domain
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)
                        if parsed.netloc == base_domain and full_url not in visited and len(queue) < 20:
                            queue.append(full_url)
            else:
                content = f"HTTP Error: {status}"
                
            results.append({
                "url": url,
                "status": status,
                "content": content[:5000]  # Limit content length
            })
        except Exception as e:
            results.append({
                "url": url,
                "status": 0,
                "error": str(e)
            })
    
    return {
        "requested": n,
        "crawled": len(results),
        "start_url": start_url,
        "results": results
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Process user message through the brain v0.1 architecture.
    Uses: process_input_v01() which integrates salience, drives, codec, and character encoding.
    """
    # Notify continuous loop of user activity
    brain.continuous_loop.notify_user_active()
    
    # Use v0.1 processing pipeline
    result = brain.process_input_v01(req.message)
    
    # Extract brain state snapshot
    snap = result.get("brain_state", {})
    reply = result.get("response", "[No response generated]")
    
    # Store in brain's chat history
    brain.chat_history.append({"role": "user",      "content": req.message})
    brain.chat_history.append({"role": "assistant",  "content": reply})
    
    # Calculate processing stages based on actual brain state
    regions = snap.get("regions", {})
    encoding_pct = regions.get("sensory", {}).get("activity_pct", 0)
    feature_pct = regions.get("feature", {}).get("activity_pct", 0)
    assoc_pct = regions.get("association", {}).get("activity_pct", 0)
    pred_pct = regions.get("predictive", {}).get("activity_pct", 0)
    concept_pct = regions.get("concept", {}).get("activity_pct", 0)
    
    return {
        "response":        reply,
        "brain_state":  snap,
        "concept_id":   snap.get("regions", {}).get("concept", {}).get("active_concept_neuron", -1),
        "attention":    snap.get("attention_gain", 1.0),
        "prediction_error": snap.get("prediction_error", 0.0),
        "processing_stage": "complete",
        "affect": {
            "valence": result.get("affect", {}).valence if result.get("affect") else 0.5,
            "arousal": result.get("affect", {}).arousal if result.get("affect") else 0.5,
        },
        "drives": result.get("drives", {}),
        "stages": {
            "encoding": f"{encoding_pct:.0f}%",
            "feature_extraction": f"{feature_pct:.0f}%",
            "association": f"{assoc_pct:.0f}%",
            "prediction": f"{pred_pct:.0f}%",
            "concept_activation": f"{concept_pct:.0f}%"
        }
    }


@app.post("/api/reflex/check")
def reflex_check(req: ReflexCheckRequest):
    """Check if motor command passes safety constraints."""
    FORCE_MAX = 10
    ANGLE_MAX = 170
    VEL_MAX = 2
    
    violations = []
    if req.force > FORCE_MAX:
        violations.append(f"force={req.force}N > {FORCE_MAX}N")
    if req.angle > ANGLE_MAX:
        violations.append(f"angle={req.angle}° > {ANGLE_MAX}°")
    if req.velocity > VEL_MAX:
        violations.append(f"velocity={req.velocity}m/s > {VEL_MAX}m/s")
    
    approved = len(violations) == 0
    
    return {
        "approved": approved,
        "reason": "SAFE — command executed" if approved else f"REFLEX_WITHDRAWAL: {'; '.join(violations)}",
        "constraints": {
            "force_max": FORCE_MAX,
            "angle_max": ANGLE_MAX,
            "velocity_max": VEL_MAX
        }
    }


@app.post("/api/motor")
def motor(cmd: MotorCommand):
    result = brain.issue_motor_command(cmd.dict())
    return result


@app.get("/api/synapses/{synapse_name}/weights")
def synapse_weights(synapse_name: str):
    for s in brain.all_synapses:
        if s.name == synapse_name:
            return {
                "name":     s.name,
                "n":        s.n_synapses,
                "mean":     round(s.mean_weight(), 4),
                "histogram": s.weight_histogram(bins=20),
            }
    return {"error": "not found"}


@app.get("/api")
def api_root(request: Request):
    """Return helpful API entry links (OpenAPI & docs)."""
    base = str(request.base_url)
    return {
        "openapi": base + "openapi.json",
        "docs": base + "docs",
    }


# ─── WebSocket stream ─────────────────────────────────────────────────────────

@app.websocket("/api/ws/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            snap = brain.snapshot()
            await ws.send_text(json.dumps(snap))
            await asyncio.sleep(0.2)    # 5 Hz update
    except WebSocketDisconnect:
        pass


# ─── Wiki lookup (Wikipedia snapshot via HuggingFace datasets) -----------------
def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "_", s.strip().lower())


def fetch_wikipedia_sync(topic: str, max_checked: int = 200000, timeout_seconds: int = 20) -> dict:
    """Search Wikipedia snapshot for a title match using datasets in streaming mode.

    This function is intentionally synchronous to run in a thread pool from FastAPI.
    It will perform a bounded scan and return the first exact-title match (case-insensitive)
    or the best contains-match found within the scanned items.
    """
    # Simple file cache to avoid repeated scans
    cache_dir = os.path.join("data", "wiki_cache")
    os.makedirs(cache_dir, exist_ok=True)
    slug = _slugify(topic)
    cache_path = os.path.join(cache_dir, f"{slug}.json")
    try:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        # ignore cache read errors
        pass

    # Lazy import so the server can start even if datasets isn't installed yet
    try:
        from datasets import load_dataset
    except Exception as e:
        return {"found": False, "error": f"datasets not available: {e}"}

    topic_norm = topic.strip().lower()
    best_candidate = None
    start = time.time()
    try:
        ds = load_dataset("wikipedia", "20220301.en", split="train", streaming=True)
        for i, rec in enumerate(ds):
            # Respect timeout
            if time.time() - start > timeout_seconds:
                break

            if i >= max_checked:
                break

            title = rec.get("title") or ""
            text = rec.get("text") or rec.get("content") or ""
            if not title:
                continue

            tnorm = title.strip().lower()
            if tnorm == topic_norm:
                result = {"found": True, "title": title, "text": text}
                # write cache
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False)
                except Exception:
                    pass
                return result

            # Keep a contains-match as fallback
            if topic_norm in tnorm or topic_norm in (text or "").lower():
                if not best_candidate:
                    best_candidate = {"found": True, "title": title, "text": text}

    except Exception as e:
        return {"found": False, "error": str(e)}

    if best_candidate:
        # cache and return fallback
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(best_candidate, f, ensure_ascii=False)
        except Exception:
            pass
        return best_candidate

    return {"found": False, "title": None, "text": ""}


@app.get("/api/wiki")
async def wiki(topic: str | None = None, persist: bool = False, max_chars: int = 50000):
    """Return Wikipedia article text for a given topic using the HF `wikipedia` snapshot.

    Query params:
      - topic (required): article title or search term
      - persist (optional, default false): if true, store the content under data/wiki_cache/
      - max_chars (optional): truncate returned text to this many characters
    """
    if not topic:
        return {"error": "topic query parameter is required"}, 400

    # Run the potentially blocking dataset scan in a threadpool
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, fetch_wikipedia_sync, topic)
    except Exception as e:
        return {"found": False, "error": str(e)}

    if not result.get("found"):
        return {"found": False, "message": "No article found", "error": result.get("error")}

    text = result.get("text") or ""
    if max_chars and len(text) > max_chars:
        text = text[:max_chars] + "\n\n[TRUNCATED]"

    out = {"found": True, "title": result.get("title"), "text": text, "source": "wikipedia_snapshot"}

    # If persist requested, ensure cached file exists (fetch_wikipedia_sync already writes cache on hit)
    if persist:
        # touch the cache file to ensure persistence
        slug = _slugify(topic)
        cache_dir = os.path.join("data", "wiki_cache")
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"{slug}.json")
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False)
        except Exception as e:
            print(f"[API /wiki] Failed to persist cache: {e}")

    return out


# ─── Brain response generation ────────────────────────────────────────────────

def _brain_respond(message: str, snap: dict, history: list[dict]) -> str:
    """
    Generate a human-readable response that reflects brain state.
    This is called by the /chat endpoint.
    
    Uses LLMCodec to call Ollama or other LLM backends for actual responses.
    """
    regions  = snap.get("regions", {})
    gain     = snap.get("attention_gain", 1.0)
    err      = snap.get("prediction_error", 0.0)
    concept  = regions.get("concept", {}).get("active_concept_neuron", -1)
    status   = snap.get("status", "NEONATAL")
    step     = snap.get("step", 0)

    assoc_act  = regions.get("association",  {}).get("activity_pct", 0)
    pred_act   = regions.get("predictive",   {}).get("activity_pct", 0)
    concept_act= regions.get("concept",      {}).get("activity_pct", 0)
    
    # Try to use LLM for response
    try:
        from codec.llm_codec import LLMCodec
        from config import LLM_CONFIG
        
        # Create a simple brain state dict for the codec
        brain_state = {
            "message": message,
            "history": history,
            "regions": {
                "association": {"activity_pct": assoc_act},
                "predictive": {"activity_pct": pred_act, "prediction_error": err},
                "concept": {"activity_pct": concept_act, "active_concept_neuron": concept},
            },
            "attention_gain": gain,
            "status": status,
            "step": step,
        }
        
        # Try to call the LLM
        codec = LLMCodec()
        
        # Check if Ollama is available and use best available model
        if LLM_CONFIG.is_ollama_available():
            # Use auto-detected best model
            model = LLM_CONFIG.get_best_available_model()
            print(f"[API] Using Ollama model: {model}")
            result = codec.articulate(brain_state, force_llm=True)
            if result and result.text:
                # Check if it's an error response
                if not result.text.startswith("[Ollama"):
                    return result.text
                else:
                    print(f"[API] Ollama error response: {result.text}")
                    # Don't silently fall through - raise to trigger fallback
                    raise ValueError(f"Ollama error: {result.text}")
        else:
            print("[API] Ollama not available - will use fallback")
    except Exception as e:
        # Log the error so we can see it
        print(f"[API] LLM call failed: {type(e).__name__}: {e}")
        # Continue to fallback - don't silently swallow
    
    # Fallback: Build a state-aware reply string
    lines = [
        f"[OSCEN·{status}·step={step:,}]",
        f"",
        f"Processing: '{message}'",
        f"",
        f"Neural activity report:",
        f"  • Association hub:   {assoc_act:.1f}% active  (cross-modal binding)",
        f"  • Predictive cortex: {pred_act:.1f}% active  (error={err:.4f})",
        f"  • Concept layer:     {concept_act:.2f}% active  (WTA winner #{concept})",
        f"  • Attention gain:    ×{gain:.2f}  ({'HIGH — learning accelerated' if gain > 2 else 'normal'})",
        f"",
        f"The STDP synapses are {'strengthening rapidly' if gain > 2 else 'updating normally'} based on this input.",
    ]
    return "\n".join(lines)
