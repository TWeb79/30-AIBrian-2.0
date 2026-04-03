# Health routes - /api/health, /api/persist
import time
from fastapi import APIRouter, HTTPException
from api.config import brain

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