# Debug routes - /api/debug/llm_logs
import time
from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()

_llm_logs: List[Dict[str, Any]] = []
MAX_LOGS = 50


def log_llm_communication(prompt: str, response: str, endpoint: str = "generate", duration_ms: float = 0):
    """Log LLM communication for debugging."""
    _llm_logs.append({
        "timestamp": time.strftime("%H:%M:%S"),
        "prompt": prompt[:500] if prompt else "",
        "response": response[:500] if response else "",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 1),
    })
    if len(_llm_logs) > MAX_LOGS:
        _llm_logs.pop(0)


@router.get("/debug/llm_logs")
def get_llm_logs():
    """Get LLM communication logs."""
    return {"logs": _llm_logs}


@router.post("/debug/llm_logs")
def clear_llm_logs():
    """Clear LLM logs."""
    _llm_logs.clear()
    return {"status": "cleared"}
