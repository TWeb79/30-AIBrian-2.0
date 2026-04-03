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
import threading
from collections import deque
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urljoin, urlparse

import numpy as np
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from brain import OSCENBrain
from uuid import uuid4

# ─── Boot brain ───────────────────────────────────────────────────────────────

SCALE = float(os.getenv("BRAIN_SCALE", "0.01"))   # 0.01 = fast CPU demo
brain = OSCENBrain(scale=SCALE)
brain.start_background_loop(steps_per_tick=100)

# ─── Proactive message queue (thread-safe) ───────────────────────────────────
_proactive_lock = threading.Lock()
_proactive_queue: deque[str] = deque(maxlen=20)

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
    history:    list[dict] = Field(default_factory=list)
    brainState: dict = Field(default_factory=dict)

class ProactiveRequest(BaseModel):
    message: str

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

class FeedbackRequest(BaseModel):
    valence: float

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "alive", "uptime_s": round(time.time() - brain.start_time, 1)}


@app.post("/api/persist")
def persist():
    """Force immediate persistence of brain state."""
    try:
        brain.persist()
        return {"status": "persisted", "vocabulary_size": brain.phon_buffer.get_vocabulary_size()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            response = requests.get(
                f"{LLM_CONFIG.ollama_base_url}/api/tags",
                timeout=5,
                headers={"User-Agent": "OSCEN/0.1"},
            )
            if response.status_code == 200:
                ollama_available = True
                data = response.json()
                ollama_models = [m.get("name", "") for m in data.get("models", [])]
        except Exception:
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
    try:
        snap = brain.snapshot()
        snap["total_neurons"]  = brain.total_neurons()
        snap["total_synapses"] = brain.total_synapses()
        # v0.2: Include vocabulary, memory, and bypass stats
        vocab_stats = brain.phon_buffer.get_statistics(recent_count=10)
        vocab_stats["recent_words"] = vocab_stats.pop("recent_words", [])
        snap["vocabulary"] = vocab_stats
        snap["memory"] = brain.hippocampus.get_statistics()
        snap["bypass"] = brain.bypass_monitor.get_statistics()
        snap["assemblies"] = brain.assembly_detector.get_statistics()
        # v0.3: Affective state and intrinsic drives
        snap["affect"] = vars(brain.affect.get_state())
        snap["drives"] = vars(brain.drives.state)
    except Exception as e:
        print(f"[API /brain/status] Error: {e}")
        snap = {"error": str(e)}
    return snap


@app.get("/api/vocabulary")
def vocabulary():
    """Return vocabulary learning statistics and recent word list."""
    try:
        stats = brain.phon_buffer.get_statistics(recent_count=50)
        stats["words"] = stats.pop("recent_words", [])
    except Exception as e:
        print(f"[API /vocabulary] Error: {e}")
        stats = {"vocabulary_size": 0, "words": [], "error": str(e)}
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


@app.get("/api/proactive")
def get_proactive():
    """Return and drain pending proactive messages from the continuous loop."""
    with _proactive_lock:
        messages = list(_proactive_queue)
        _proactive_queue.clear()
    return {"messages": messages}


@app.post("/api/proactive")
def post_proactive(req: ProactiveRequest):
    """Called by the continuous loop or internal processes to queue a proactive message."""
    msg = req.message if getattr(req, 'message', None) else ""
    if msg:
        with _proactive_lock:
            _proactive_queue.append(msg)
    with _proactive_lock:
        queued = len(_proactive_queue)
    return {"queued": queued}


@app.post("/api/feedback")
def feedback(req: FeedbackRequest):
    valence = max(-1.0, min(1.0, req.valence))
    brain.on_user_feedback(valence)
    brain.store.save_self_model(brain.self_model)
    return {
        "acknowledged": True,
        "new_mood": brain.self_model.mood,
        "new_confidence": brain.self_model.confidence,
        "drives": vars(brain.drives.state),
    }


@app.post("/api/stimulate")
def stimulate(req: StimulusRequest):
    arr = np.array(req.data, dtype=np.float32)
    brain.stimulate_modality(req.modality, arr)
    return {"injected": len(arr), "modality": req.modality}


@app.post("/api/llm/chat")
async def llm_chat(req: dict):
    """
    Direct LLM prompt - bypasses brain processing and sends directly to LLM.
    Returns the raw LLM response. Also trains the brain from the interaction.
    """
    from config import LLM_CONFIG
    
    prompt = req.get("prompt", "")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")
    
    llm_response = None
    
    try:
        # Check if Ollama is available
        if LLM_CONFIG.is_ollama_available():
            model = LLM_CONFIG.get_best_available_model()
            ollama_url = LLM_CONFIG.ollama_base_url
            
            # Direct call to Ollama
            response = await asyncio.to_thread(
                requests.post,
                f"{ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=180,
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "")
            else:
                raise HTTPException(status_code=response.status_code, detail=f"Ollama error: {response.status_code}")
        else:
            raise HTTPException(status_code=503, detail="Ollama not available. Make sure Ollama is running.")
    except Exception as e:
        print(f"[API /llm/chat] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Train the brain from this interaction — learn words from prompt and response
    # process_input_v01 can be blocking; run in thread to avoid blocking the event loop
    await asyncio.to_thread(brain.process_input_v01, prompt)
    if llm_response:
        await asyncio.to_thread(brain.process_input_v01, llm_response)
    
    return {"response": llm_response}


class YTRequest(BaseModel):
    url: str
    n: int = 1


@app.post("/api/yt")
async def yt_transcribe(req: YTRequest):
    """
    YouTube transcription endpoint.
    Downloads audio from n videos starting at the given URL,
    transcribes speech to text using Whisper,
    and teaches the brain from each transcript.
    """
    from yt_transcriber import transcribe_url, get_video_chain

    url = req.url
    n = min(max(req.n, 1), 10)  # clamp 1-10

    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    results = []
    
    # Get video chain (playlist or related videos) — run in thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        videos = await loop.run_in_executor(None, get_video_chain, url, n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video chain: {e}")

    loop = asyncio.get_event_loop()
    async def _process_single_video(video: dict) -> dict:
        video_url = video["url"]
        video_title = video.get("title", "Unknown")
        try:
            # Prefer direct youtube-transcript-api tier for speed when available
            try:
                from yt_transcriber import _fetch_via_transcript_api, extract_video_id
            except Exception:
                _fetch_via_transcript_api = None

            result = None
            if _fetch_via_transcript_api:
                vid = extract_video_id(video_url)
                if vid:
                    text = await loop.run_in_executor(None, _fetch_via_transcript_api, vid, ['de', 'en'])
                    if text:
                        result = {"title": video_title or vid, "url": video_url, "video_id": vid, "duration": 0, "transcript": text, "source": "captions_api", "error": None}

            if result is None:
                # Fall back to the full transcribe_url which will try yt-dlp and other tiers
                result = await loop.run_in_executor(None, transcribe_url, video_url, ['de', 'en'])

            if result.get("error"):
                return {"title": video_title, "url": video_url, "error": result["error"], "transcript_length": 0, "words_learned": 0}

            transcript = result.get("transcript", "")

            # Train the brain from transcript in a thread to avoid blocking the event loop
            chunk_size = 200
            words = transcript.split()
            words_learned = 0
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                await asyncio.to_thread(brain.process_input_v01, chunk)
                words_learned = brain.phon_buffer.get_vocabulary_size()

            # Persist in thread
            await asyncio.to_thread(brain.persist)

            # Append short transcript to chat_history
            try:
                with brain._lock:
                    brain.chat_history.append({"role": "assistant", "content": f"[transcript] {video_title}\n{transcript[:2000]}"})
            except Exception:
                try:
                    brain.chat_history.append({"role": "assistant", "content": video_title})
                except Exception:
                    pass

            return {"title": video_title, "url": video_url, "duration": result.get("duration", 0), "transcript_length": len(transcript), "words_learned": words_learned}
        except Exception as e:
            return {"title": video_title, "url": video_url, "error": str(e), "transcript_length": 0, "words_learned": 0}

    # Process videos concurrently in executor-bound tasks but limited concurrency
    sem = asyncio.Semaphore(4)
    async def _bounded_process(v):
        async with sem:
            return await _process_single_video(v)

    tasks = [asyncio.create_task(_bounded_process(v)) for v in videos]
    results = await asyncio.gather(*tasks)

    # Persist after learning from videos (run in thread)
    await asyncio.to_thread(brain.persist)

    return {
        "videos_processed": len(results),
        "results": results,
        "vocabulary_size": brain.phon_buffer.get_vocabulary_size(),
    }


@app.post("/api/grep")
async def grep(req: GrepRequest):
    """
    Web crawling endpoint - crawls n pages from the given URL.
    """
    from bs4 import BeautifulSoup
    
    n = req.n
    start_url = req.url
    
    if n < 1 or n > 20:
        raise HTTPException(status_code=400, detail="n must be between 1 and 20")
    
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
            response = await asyncio.to_thread(
                requests.get,
                url,
                timeout=10,
                headers={"User-Agent": "OSCEN/0.1"},
            )
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
                        if (
                            parsed.netloc == base_domain
                            and full_url not in visited
                            and full_url not in queue
                            and len(queue) < 20
                        ):
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
    
    # Support command-style shortcuts in chat, e.g. "/yt <n> <url>" or "/yt <url>" to fetch YouTube transcript(s)
    msg_text = req.message.strip() if req.message else ""
    if msg_text.startswith("/yt"):
        parts = msg_text.split()
        # Accept: /yt <url>  or  /yt <n> <url>
        if len(parts) == 2:
            n = 1
            url = parts[1]
        elif len(parts) == 3:
            try:
                n = int(parts[1])
                url = parts[2]
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid syntax. Use: /yt <n> <youtube_url> or /yt <youtube_url>")
        else:
            raise HTTPException(status_code=400, detail="Invalid syntax. Use: /yt <n> <youtube_url> or /yt <youtube_url>")

        # Long-running transcriptions are executed in background jobs to avoid blocking HTTP requests.
        try:
            from yt_transcriber import get_video_chain, transcribe_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription tools unavailable: {e}")

        # Build a simple job store (in-memory). For production, replace with persistent store.
        if not hasattr(app.state, "yt_jobs"):
            app.state.yt_jobs = {}

        job_id = str(uuid4())
        app.state.yt_jobs[job_id] = {"status": "queued", "result": None, "error": None}

        async def _run_youtube_job(jid: str, url: str, n_videos: int, user_msg: str):
            job = app.state.yt_jobs.get(jid)
            print(f"[YouTube Job {jid}] Starting job for URL: {url}")
            try:
                loop = asyncio.get_event_loop()
                videos = await loop.run_in_executor(None, get_video_chain, url, n_videos)
                print(f"[YouTube Job {jid}] Got {len(videos)} videos")
                aggregated = []
                for v in videos:
                    video_url = v.get("url")
                    video_title = v.get("title") or video_url
                    print(f"[YouTube Job {jid}] Transcribing: {video_title}")
                    # run transcription in threadpool (may be blocking/slow)
                    tr = await loop.run_in_executor(None, transcribe_url, video_url, ['de', 'en'])
                    print(f"[YouTube Job {jid}] Transcript result: source={tr.get('source')}, len={len(tr.get('transcript', ''))}, error={tr.get('error')}")
                    if tr.get("error") or not tr.get("transcript"):
                        aggregated.append({"url": video_url, "title": video_title, "error": tr.get("error")})
                        continue
                    transcript = tr.get("transcript", "")
                    # Teach brain from transcript in chunks (off main loop)
                    chunk_size = 200
                    words = transcript.split()
                    for i in range(0, len(words), chunk_size):
                        chunk = " ".join(words[i:i + chunk_size])
                        await asyncio.to_thread(brain.process_input_v01, chunk)
                    words_learned = brain.phon_buffer.get_vocabulary_size()
                    aggregated.append({
                        "url": video_url,
                        "title": video_title,
                        "duration": tr.get("duration", 0),
                        "transcript_length": len(transcript),
                        "words_learned": words_learned,
                        "transcript": transcript,
                    })
                # Persist brain state after job completes
                await asyncio.to_thread(brain.persist)
                # Append to chat history: record the original user command and assistant transcript
                try:
                    with brain._lock:
                        brain.chat_history.append({"role": "user", "content": user_msg})
                        # store a short assistant entry summarising the transcription (avoid massive chat entries)
                        for entry in aggregated:
                            # add a truncated assistant message per video
                            snippet = entry.get("transcript", "")[:2000]
                            brain.chat_history.append({"role": "assistant", "content": f"[transcript] {entry.get('title','')}\n{snippet}"})
                except Exception:
                    # best-effort fallback
                    for entry in aggregated:
                        try:
                            brain.chat_history.append({"role": "assistant", "content": entry.get("title", "")})
                        except Exception:
                            pass

                job.update({"status": "done", "result": {"videos_processed": len(aggregated), "results": aggregated, "vocabulary_size": brain.phon_buffer.get_vocabulary_size()}})
                # Notify proactive queue so front-end can pick up the completed job
                try:
                    with _proactive_lock:
                        _proactive_queue.append(f"yt_job_done:{jid}")
                except Exception:
                    pass
            except Exception as e:
                job.update({"status": "error", "error": str(e)})

        # Schedule background job (fire-and-forget) and pass the original chat message so it can be
        # recorded in chat_history when the transcription completes.
        user_msg = msg_text
        asyncio.create_task(_run_youtube_job(job_id, url, n, user_msg))

        return {"job_id": job_id, "status": "queued", "message": "Transcription running in background — poll /api/yt_job/{job_id} for results"}

    # Use v0.1 processing pipeline for non-command messages
    result = brain.process_input_v01(req.message)
    
    # Extract brain state snapshot
    snap = result.get("brain_state", {})
    reply = result.get("response", "[No response generated]")
    
    # Store in brain's chat history
    # Make chat_history append thread-safe
    try:
        with brain._lock:
            brain.chat_history.append({"role": "user",      "content": req.message})
            brain.chat_history.append({"role": "assistant",  "content": reply})
    except Exception:
        # Fallback: best-effort append
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
        "new_words": result.get("new_words", []),
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


@app.get("/api/yt_job/{job_id}")
def yt_job_status(job_id: str):
    """Query background YouTube transcription job status and results."""
    if not hasattr(app.state, "yt_jobs"):
        raise HTTPException(status_code=404, detail="Job not found")
    job = app.state.yt_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


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
    # Use pydantic v2 model dump
    try:
        cmd_data = cmd.model_dump()
    except Exception:
        cmd_data = cmd.dict()
    result = brain.issue_motor_command(cmd_data)
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
        raise HTTPException(status_code=400, detail="topic query parameter is required")

    # Run the potentially blocking dataset scan in a threadpool
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, fetch_wikipedia_sync, topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
