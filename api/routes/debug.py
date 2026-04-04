# Debug routes - /api/debug/llm_logs
import time
import json
import os
from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()

_llm_logs: List[Dict[str, Any]] = []
MAX_LOGS = 50
MODEL_STATS_FILE = "data/llm_model_stats.json"


def _load_model_stats() -> Dict[str, Dict[str, Any]]:
    """Load model stats from persistent file."""
    try:
        if os.path.exists(MODEL_STATS_FILE):
            with open(MODEL_STATS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_model_stats(stats: Dict[str, Dict[str, Any]]):
    """Save model stats to persistent file."""
    try:
        os.makedirs("data", exist_ok=True)
        with open(MODEL_STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass


_model_stats = _load_model_stats()


def log_llm_communication(prompt: str, response: str, endpoint: str = "generate", duration_ms: float = 0, model: str = ""):
    """Log LLM communication for debugging."""
    _llm_logs.append({
        "timestamp": time.strftime("%H:%M:%S"),
        "prompt": prompt[:500] if prompt else "",
        "response": response[:500] if response else "",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 1),
        "model": model,
    })
    if len(_llm_logs) > MAX_LOGS:
        _llm_logs.pop(0)
    
    if model:
        if model not in _model_stats:
            _model_stats[model] = {"total_calls": 0, "total_time_ms": 0, "avg_time_ms": 0}
        _model_stats[model]["total_calls"] += 1
        _model_stats[model]["total_time_ms"] += duration_ms
        _model_stats[model]["avg_time_ms"] = round(
            _model_stats[model]["total_time_ms"] / _model_stats[model]["total_calls"], 1
        )
        _save_model_stats(_model_stats)


@router.get("/debug/llm_logs")
def get_llm_logs():
    """Get LLM communication logs."""
    return {"logs": _llm_logs}


@router.get("/debug/llm_model_stats")
def get_llm_model_stats():
    """Get LLM model response time statistics."""
    return {"model_stats": _model_stats}


@router.post("/debug/llm_logs")
def clear_llm_logs():
    """Clear LLM logs."""
    _llm_logs.clear()
    return {"status": "cleared"}


@router.post("/debug/llm_model_stats")
def clear_llm_model_stats():
    """Clear LLM model stats."""
    global _model_stats
    _model_stats = {}
    _save_model_stats(_model_stats)
    return {"status": "cleared"}
