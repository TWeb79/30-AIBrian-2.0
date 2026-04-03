# LLM routes - /api/llm/status, /api/llm/chat, /api/llm/train
import asyncio
import requests
import time
from fastapi import APIRouter, HTTPException
from api.config import brain, TRAINING_SESSIONS, TrainingSession
from api.models import TrainRequest

router = APIRouter()

@router.get("/llm/status")
def llm_status():
    """Check if LLM is configured and available."""
    from config import LLM_CONFIG
    
    configured = bool(LLM_CONFIG.anthropic_api_key or LLM_CONFIG.openai_api_key or LLM_CONFIG.ollama_base_url)
    backend = LLM_CONFIG.backend
    
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


@router.post("/llm/chat")
async def llm_chat(req: dict):
    """Direct LLM prompt - bypasses brain processing."""
    from config import LLM_CONFIG
    
    prompt = req.get("prompt", "")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")
    
    llm_response = None
    
    try:
        if LLM_CONFIG.is_ollama_available():
            model = LLM_CONFIG.get_best_available_model()
            ollama_url = LLM_CONFIG.ollama_base_url
            
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
    
    await asyncio.to_thread(brain.process_input_v01, prompt)
    if llm_response:
        await asyncio.to_thread(brain.process_input_v01, llm_response)
    
    return {"response": llm_response}


@router.post("/llm/train")
async def llm_train(req: TrainRequest):
    """Create a new training session."""
    from uuid import uuid4
    
    session_id = str(uuid4())
    session = TrainingSession(
        id=session_id,
        n=req.n or 4,
        briefing=req.briefing or "",
        include_user_inputs=req.include_user_inputs if req.include_user_inputs is not None else False,
        status="queued",
    )
    TRAINING_SESSIONS[session_id] = session
    
    asyncio.create_task(_start_training_async(session_id))
    return {"session_id": session_id, "status": "queued"}


@router.get("/llm/train/{session_id}")
def llm_train_status(session_id: str):
    """Return status for a given training session."""
    sess = TRAINING_SESSIONS.get(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Training session not found")
    return {
        "session_id": sess.id,
        "n": sess.n,
        "briefing": sess.briefing,
        "include_user_inputs": sess.include_user_inputs,
        "status": sess.status,
        "consumed": sess.consumed,
        "last_result": sess.last_result,
        "created_at": sess.created_at,
        "updated_at": sess.updated_at,
    }


async def _start_training_async(session_id: str):
    from config import TRAINING_SESSIONS
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