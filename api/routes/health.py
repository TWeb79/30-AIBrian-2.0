# Health routes - /api/health, /api/persist, /api/brain/health
import time
from fastapi import APIRouter, HTTPException
from api.config import brain
from config import LLM_CONFIG

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "alive", "uptime_s": round(time.time() - brain.start_time, 1)}

@router.post("/persist")
def persist():
    """Force immediate persistence of brain state."""
    try:
        brain.persist()
        return {"status": "persisted", "vocabulary_size": brain.phon_buffer.get_vocabulary_size()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brain/health")
def brain_health():
    """Rich brain health endpoint for single-glance operational status."""
    return {
        "status": "alive",
        "brain_stage": brain.self_model.brain_stage,
        "total_steps": brain.self_model.total_steps,
        "vocabulary_size": brain.phon_buffer.get_vocabulary_size(),
        "bypass_rate": brain.bypass_monitor.get_bypass_rate(),
        "memory_episodes": brain.hippocampus.get_episode_count(),
        "assemblies": brain.assembly_detector.get_assembly_count(),
        "persist_dir": brain.store.BASE_DIR,
        "state_size_bytes": brain.store.get_state_size(),
        "ollama_available": LLM_CONFIG.is_ollama_available(),
        "auto_training": getattr(brain, '_auto_training', False),
        "uptime_s": round(time.time() - brain.start_time, 1),
    }