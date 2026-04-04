# LLM routes - /api/llm/status, /api/llm/chat, /api/llm/train
import asyncio
import requests
import time
from fastapi import APIRouter, HTTPException, Request
from api.config import brain, TRAINING_SESSIONS, TrainingSession
from api.models import TrainRequest

# NOTE: import debug logging lazily where used to avoid circular imports

router = APIRouter()

async def call_llm_direct(prompt: str) -> str:
    """Call LLM directly with a prompt - returns response text."""
    from config import LLM_CONFIG
    
    print(f"[DEBUG call_llm_direct] Calling LLM with prompt: {prompt[:80]}...")
    
    if not LLM_CONFIG.is_ollama_available():
        print("[DEBUG call_llm_direct] Ollama not available")
        raise HTTPException(status_code=503, detail="Ollama not available")
    
    model = LLM_CONFIG.get_default_model()
    ollama_url = LLM_CONFIG.ollama_base_url
    
    print(f"[DEBUG call_llm_direct] Using model: {model}, url: {ollama_url}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=(10, 120),
        )
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"[DEBUG call_llm_direct] Response status: {response.status_code}")
    except requests.exceptions.Timeout:
        print("[DEBUG call_llm_direct] Request timed out")
        raise HTTPException(status_code=504, detail="LLM request timed out")
    except requests.exceptions.ConnectionError as e:
        print(f"[DEBUG call_llm_direct] Connection error: {e}")
        raise HTTPException(status_code=502, detail=f"Cannot connect to Ollama: {e}")
    except Exception as e:
        print(f"[DEBUG call_llm_direct] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    if response.status_code == 200:
        result = response.json()
        llm_response = result.get("response", "")
        
        try:
            from api.routes.debug import log_llm_communication
            log_llm_communication(prompt, llm_response, "generate", elapsed_ms)
        except Exception:
            # Debug logging is optional; ignore failures to import/log
            pass
        
        print(f"[DEBUG call_llm_direct] Got response: {llm_response[:80]}...")
        return llm_response
    else:
        print(f"[DEBUG call_llm_direct] Error response: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"Ollama error: {response.status_code}")

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
                timeout=10,
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


@router.post("/llm/set_model")
async def llm_set_model(request: Request):
    """Set the LLM model to use.

    Accepts JSON body: { "backend": "local_ollama", "model": "modelname" }
    The Body(...) annotation ensures FastAPI treats the payload as JSON and
    provides clearer validation errors when the client sends invalid data.
    """
    from config import LLM_CONFIG

    # Read raw body and parse JSON to avoid FastAPI-level JSON decoding errors
    raw = await request.body()
    try:
        raw_text = raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else str(raw)
    except Exception:
        raw_text = str(raw)

    import json
    try:
        req = json.loads(raw_text) if raw_text else {}
    except Exception as e:
        print(f"[LLM SET_MODEL] JSON parse error: {e} -- raw body: {repr(raw_text)[:200]}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")

    # Defensive logging to help debug clients that fail to send proper JSON
    try:
        print(f"[LLM SET_MODEL] Received body: {req}")
    except Exception:
        print("[LLM SET_MODEL] Received non-serializable body")

    backend = req.get("backend", "local_ollama") if isinstance(req, dict) else "local_ollama"
    model = req.get("model", "") if isinstance(req, dict) else ""
    
    if not model:
        raise HTTPException(status_code=400, detail="No model provided")
    
    old_model = LLM_CONFIG.get_default_model()
    LLM_CONFIG.set_model(backend, model)
    new_model = LLM_CONFIG.get_default_model()
    
    print(f"[LLM] Model changed: {old_model} -> {new_model} (backend: {backend})")
    
    return {
        "status": "ok",
        "old_model": old_model,
        "new_model": new_model,
        "backend": backend,
    }


@router.post("/llm/chat")
async def llm_chat(req: dict):
    """Direct LLM prompt - bypasses brain processing."""
    from config import LLM_CONFIG
    
    prompt = req.get("prompt", "")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")
    
    llm_response = None
    model = ""
    
    try:
        if LLM_CONFIG.is_ollama_available():
            model = LLM_CONFIG.get_default_model()
            ollama_url = LLM_CONFIG.ollama_base_url
            
            start_time = time.time()
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
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "")
                
                try:
                    from api.routes.debug import log_llm_communication
                    log_llm_communication(prompt, llm_response, "generate", elapsed_ms, model)
                except Exception:
                    pass
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
        "tutor_responses": getattr(sess, 'tutor_responses', []),
        "new_words": getattr(sess, 'new_words', []),
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

        # If a briefing/prompt is provided, generate the next `n` responses from the brain
        # by feeding the briefing into the brain `n` times and collecting the assistant outputs.
        if session.briefing:
            generated = []
            for i in range(session.n or 1):
                try:
                    res = brain.process_input_v01(session.briefing)
                    if isinstance(res, dict):
                        generated.append(res.get('response', '') or '')
                except Exception as e:
                    print(f"[LLM TRAIN] Error generating brain response #{i}: {e}")
            learner_text = " ".join([g for g in generated if g])
        else:
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

        new_words = []
        tutor_responses = []

        if session.briefing:
            # For briefing mode: generate the brain's next `n` responses, call the LLM for each
            for i in range(session.n or 1):
                try:
                    brain_res = brain.process_input_v01(session.briefing)
                    brain_message = brain_res.get('response', '') if isinstance(brain_res, dict) else ''
                except Exception as e:
                    print(f"[LLM TRAIN] Error generating brain response #{i}: {e}")
                    brain_message = ''

                if not brain_message:
                    continue

                # Build per-iteration state for the LLM call
                per_state = {
                    "message": brain_message,
                    "history": brain.chat_history[-6:],
                    "memory_snippet": session.briefing or "",
                    "brain_stage": brain_stage,
                    "drives": brain.drives.state.__dict__ if hasattr(brain, 'drives') else {},
                    "affect": brain.affect.get_state() if hasattr(brain, 'affect') else {},
                    "chat_history": brain.chat_history[-6:],
                    "total_turns": getattr(brain.self_model, 'total_turns', 0) if hasattr(brain, 'self_model') else 0,
                    "vocabulary_size": brain.phon_buffer.get_vocabulary_size() if hasattr(brain, 'phon_buffer') else 0,
                }

                try:
                    res = codec.articulate(per_state, force_llm=True)
                    tutor = res.text if res else ''
                except Exception as e:
                    print(f"[LLM TRAIN] LLM call failed for iteration #{i}: {e}")
                    tutor = ''

                if tutor:
                    tutor_responses.append(tutor)
                    # append to chat history and feed back into brain for learning
                    try:
                        with brain._lock:
                            brain.chat_history.append({"role": "assistant", "content": tutor})
                    except Exception:
                        try:
                            brain.chat_history.append({"role": "assistant", "content": tutor})
                        except Exception:
                            pass

                    try:
                        r2 = brain.process_input_v01(tutor)
                        if isinstance(r2, dict):
                            new_words.extend(r2.get('new_words', []) or [])
                    except Exception as e:
                        print(f"[LLM TRAIN] Error training tutor response into brain: {e}")

                    try:
                        if hasattr(brain, 'persist_vocabulary') and new_words:
                            brain.persist_vocabulary()
                    except Exception as e:
                        print(f"[LLM TRAIN] Failed to persist vocabulary: {e}")

        else:
            # Default behavior: bundle learner_text into one LLM call
            try:
                result = codec.articulate(state, force_llm=True)
                tutor_response = result.text if result else ""
            except Exception as e:
                print(f"[LLM TRAIN] LLM call failed: {e}")
                tutor_response = ""

            if tutor_response:
                tutor_responses = [tutor_response]
                try:
                    with brain._lock:
                        brain.chat_history.append({"role": "assistant", "content": tutor_response})
                except Exception:
                    try:
                        brain.chat_history.append({"role": "assistant", "content": tutor_response})
                    except Exception:
                        pass

                try:
                    r2 = brain.process_input_v01(tutor_response)
                    if isinstance(r2, dict):
                        new_words = r2.get('new_words', []) or []
                except Exception as e:
                    print(f"[LLM TRAIN] Error training tutor response into brain: {e}")

                try:
                    if hasattr(brain, 'persist_vocabulary') and new_words:
                        brain.persist_vocabulary()
                except Exception as e:
                    print(f"[LLM TRAIN] Failed to persist vocabulary: {e}")

        # Persist overall brain state and finish session
        brain.persist()
        session.status = "done"
        # Save collected tutor responses and deduplicated new_words on session
        try:
            session.tutor_responses = tutor_responses
            # deduplicate new_words preserving order
            seen = set()
            uniq_new = []
            for w in new_words:
                if w not in seen:
                    seen.add(w)
                    uniq_new.append(w)
            session.new_words = uniq_new
        except Exception:
            session.tutor_responses = tutor_responses if tutor_responses else []
            session.new_words = list(set(new_words)) if new_words else []

        # Include new_words info in last_result for easy inspection (keep compatibility)
        if tutor_responses:
            snippet = tutor_responses[0][:200] if tutor_responses and tutor_responses[0] else ""
            nw_info = f" — new_words: {len(session.new_words)}" if session.new_words else ""
            session.last_result = snippet + nw_info
        else:
            session.last_result = ""

        session.updated_at = time.time()
        TRAINING_SESSIONS[session_id] = session
    except Exception as e:
        session.status = "error"
        session.last_result = f"Error: {e}"
        session.updated_at = time.time()
        TRAINING_SESSIONS[session_id] = session