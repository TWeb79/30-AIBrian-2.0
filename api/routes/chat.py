# Chat routes - /api/chat (main chat logic + all commands together)
import asyncio
import time
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from api.config import brain, app, _proactive_lock, _proactive_queue, TrainingSession, TRAINING_SESSIONS
from api.models import ChatRequest
from api.helpers import (
    get_stats_response, get_vocabulary_response, get_memory_response,
    get_bypass_response, get_assemblies_response, get_help_response,
    brain_respond_fallback
)

router = APIRouter()

async def _start_training_async(session_id: str):
    await asyncio.to_thread(_run_training_sync, session_id)

def _run_training_sync(session_id: str):
    from config import TRAINING_SESSIONS
    session = TRAINING_SESSIONS.get(session_id)
    if not session:
        return
    try:
        session.status = "running"
        session.updated_at = time.time()
        TRAINING_SESSIONS[session_id] = session
        
        hist = brain.chat_history
        learner_text = ""
        if session.include_user_inputs:
            slice_vals = hist[-(2 * session.n):]
            learner_text = "\n".join([f"{m.get('role','')}: {m.get('content','') or ''}" for m in slice_vals])
        else:
            assistants = [m for m in hist if m.get('role') == 'assistant']
            last_assistants = assistants[-session.n:] if len(assistants) >= session.n else assistants
            learner_text = " ".join([m.get('content','') for m in last_assistants])

        brain_stage = getattr(brain.self_model, 'brain_stage', 'NEONATAL') if hasattr(brain, 'self_model') else 'NEONATAL'
        state = {
            "message": learner_text,
            "history": brain.chat_history[-6:],
            "memory_snippet": session.briefing or "",
            "brain_stage": brain_stage,
            "drives": brain.drives.state.__dict__ if hasattr(brain, 'drives') else {},
            "affect": brain.affect.get_state() if hasattr(brain, 'affect') else {},
            "chat_history": brain.chat_history[-6:],
            "total_turns": getattr(brain.self_model, 'total_turns', 0) if hasattr(brain, 'self_model') else 0,
            "vocabulary_size": brain.phon_buffer.get_vocabulary_size() if hasattr(brain, 'phon_buffer') else 0,
        }

        from codec.llm_codec import LLMCodec
        codec = LLMCodec()
        result = codec.articulate(state, force_llm=True)
        tutor_response = result.text if result else ""

        if tutor_response:
            with brain._lock:
                brain.chat_history.append({"role": "assistant", "content": tutor_response})
        
        brain.persist()
        session.status = "done"
        session.last_result = tutor_response[:200] if tutor_response else ""
        session.updated_at = time.time()
        TRAINING_SESSIONS[session_id] = session
    except Exception as e:
        session.status = "error"
        session.last_result = f"Error: {e}"
        session.updated_at = time.time()
        TRAINING_SESSIONS[session_id] = session


@router.post("/chat")
async def chat(req: ChatRequest):
    """Process user message through the brain - all chat logic in one place."""
    brain.continuous_loop.notify_user_active()
    
    msg_text = req.message.strip() if req.message else ""
    
    # Handle /yt command (YouTube transcription with background job)
    if msg_text.startswith("/yt"):
        return await _handle_yt_command(msg_text)
    
    # Handle chat commands - all together
    if msg_text.startswith("/stats"):
        return {"response": get_stats_response(), "brain_state": brain.snapshot()}

    if msg_text.startswith("/vocabulary"):
        return {"response": get_vocabulary_response(), "brain_state": brain.snapshot()}

    if msg_text.startswith("/memory"):
        return {"response": get_memory_response(), "brain_state": brain.snapshot()}

    if msg_text.startswith("/bypass"):
        return {"response": get_bypass_response(), "brain_state": brain.snapshot()}

    if msg_text.startswith("/assemblies"):
        return {"response": get_assemblies_response(), "brain_state": brain.snapshot()}

    if msg_text.startswith("/llm"):
        prompt = msg_text[4:].strip()
        if not prompt:
            return {"response": "Usage: /llm <prompt>", "brain_state": brain.snapshot()}
        return {"response": f"[Calling LLM...]\n\n", "brain_state": brain.snapshot()}

    if msg_text.startswith("/llmtrain"):
        return await _handle_llmtrain_command(msg_text)

    if msg_text.startswith("/grep"):
        return _handle_grep_command(msg_text)

    if msg_text in ("/?", "/help", "/?"):
        return {"response": get_help_response(), "brain_state": brain.snapshot()}

    # Process regular message through brain
    result = brain.process_input_v01(req.message)
    snap = result.get("brain_state", {})
    reply = result.get("response", "[No response generated]")
    
    # Store in chat history
    try:
        with brain._lock:
            brain.chat_history.append({"role": "user", "content": req.message})
            brain.chat_history.append({"role": "assistant", "content": reply})
    except Exception:
        brain.chat_history.append({"role": "user", "content": req.message})
        brain.chat_history.append({"role": "assistant", "content": reply})
    
    regions = snap.get("regions", {})
    encoding_pct = regions.get("sensory", {}).get("activity_pct", 0)
    feature_pct = regions.get("feature", {}).get("activity_pct", 0)
    assoc_pct = regions.get("association", {}).get("activity_pct", 0)
    pred_pct = regions.get("predictive", {}).get("activity_pct", 0)
    concept_pct = regions.get("concept", {}).get("activity_pct", 0)
    
    return {
        "response": reply,
        "brain_state": snap,
        "concept_id": snap.get("regions", {}).get("concept", {}).get("active_concept_neuron", -1),
        "attention": snap.get("attention_gain", 1.0),
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


async def _handle_yt_command(msg_text: str):
    """Handle YouTube transcription command."""
    parts = msg_text.split()
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

    try:
        from yt_transcriber import get_video_chain, transcribe_url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription tools unavailable: {e}")

    if not hasattr(app.state, "yt_jobs"):
        app.state.yt_jobs = {}

    job_id = str(uuid4())
    app.state.yt_jobs[job_id] = {"status": "queued", "result": None, "error": None}

    asyncio.create_task(_run_youtube_job(job_id, url, n, msg_text))
    return {"job_id": job_id, "status": "queued", "message": "Transcription running in background — poll /api/yt_job/{job_id} for results"}


async def _run_youtube_job(jid: str, url: str, n_videos: int, user_msg: str):
    """Background job for YouTube transcription."""
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
            tr = await loop.run_in_executor(None, transcribe_url, video_url, ['de', 'en'])
            print(f"[YouTube Job {jid}] Transcript result: source={tr.get('source')}, len={len(tr.get('transcript', ''))}, error={tr.get('error')}")
            if tr.get("error") or not tr.get("transcript"):
                aggregated.append({"url": video_url, "title": video_title, "error": tr.get("error")})
                continue
            transcript = tr.get("transcript", "")
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
        await asyncio.to_thread(brain.persist)
        try:
            with brain._lock:
                brain.chat_history.append({"role": "user", "content": user_msg})
                for entry in aggregated:
                    snippet = entry.get("transcript", "")[:2000]
                    brain.chat_history.append({"role": "assistant", "content": f"[transcript] {entry.get('title','')}\n{snippet}"})
        except Exception:
            pass
        job.update({"status": "done", "result": {"videos_processed": len(aggregated), "results": aggregated, "vocabulary_size": brain.phon_buffer.get_vocabulary_size()}})
        try:
            with _proactive_lock:
                _proactive_queue.append(f"yt_job_done:{jid}")
        except Exception:
            pass
    except Exception as e:
        job.update({"status": "error", "error": str(e)})


async def _handle_llmtrain_command(msg_text: str):
    """Handle /llmtrain command."""
    parts = msg_text.split(maxsplit=2)
    n = 4
    briefing = ""
    if len(parts) >= 2:
        try:
            n = int(parts[1])
        except ValueError:
            return {"response": "Usage: /llmtrain [n] [briefing]\n  n: number of turns (default 4)\n  briefing: optional context", "brain_state": brain.snapshot()}
    if len(parts) >= 3:
        briefing = parts[2]
    try:
        session_id = str(uuid4())
        session = TrainingSession(
            id=session_id,
            n=n,
            briefing=briefing,
            include_user_inputs=False,
            status="queued",
        )
        TRAINING_SESSIONS[session_id] = session
        asyncio.create_task(_start_training_async(session_id))
        return {"response": f"[Training session started] session_id={session_id}\nProcessing {n} turns...", "brain_state": brain.snapshot()}
    except Exception as e:
        return {"response": f"[Error] {e}", "brain_state": brain.snapshot()}


def _handle_grep_command(msg_text: str):
    """Handle /grep command."""
    parts = msg_text.split(maxsplit=2)
    if len(parts) < 3:
        return {"response": "Usage: /grep <n> <url>", "brain_state": brain.snapshot()}
    try:
        n = int(parts[1])
        url = parts[2]
    except ValueError:
        return {"response": "Usage: /grep <n> <url>", "brain_state": brain.snapshot()}
    if n < 1 or n > 20:
        return {"response": "n must be between 1 and 20", "brain_state": brain.snapshot()}
    return {"response": f"[Crawling {n} pages from {url}...]\n\n", "brain_state": brain.snapshot()}


@router.get("/yt_job/{job_id}")
def yt_job_status(job_id: str):
    """Query background YouTube transcription job status."""
    if not hasattr(app.state, "yt_jobs"):
        raise HTTPException(status_code=404, detail="Job not found")
    job = app.state.yt_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job