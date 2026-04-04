# Utility routes - /api/proactive, /api/feedback, /api/synapses, /api
from fastapi import APIRouter, HTTPException, Request
from api.config import brain, _proactive_lock, _proactive_queue
from api.models import ProactiveRequest, FeedbackRequest

router = APIRouter()

@router.get("/proactive")
def get_proactive():
    """Return and drain pending proactive messages."""
    with _proactive_lock:
        messages = list(_proactive_queue)
        _proactive_queue.clear()
    return {"messages": messages}


@router.post("/proactive")
def post_proactive(req: ProactiveRequest):
    """Queue a proactive message."""
    msg = req.message if getattr(req, 'message', None) else ""
    if msg:
        with _proactive_lock:
            _proactive_queue.append(msg)
    with _proactive_lock:
        queued = len(_proactive_queue)
    return {"queued": queued}


@router.post("/feedback")
def feedback(req: FeedbackRequest):
    """Process user feedback."""
    valence = max(-1.0, min(1.0, req.valence))
    brain.on_user_feedback(
        valence,
        message_id=req.message_id,
        response_text=req.response_text
    )
    brain.store.save_self_model(brain.self_model)
    return {
        "acknowledged": True,
        "new_mood": brain.self_model.mood,
        "new_confidence": brain.self_model.confidence,
        "drives": vars(brain.drives.state),
        "user_sentiment": brain.self_model.user_sentiment_avg,
    }


@router.get("/synapses/{synapse_name}/weights")
def synapse_weights(synapse_name: str):
    """Get synapse weight distribution."""
    for s in brain.all_synapses:
        if s.name == synapse_name:
            ltp = getattr(s, 'total_ltp_events', 0)
            ltd = getattr(s, 'total_ltd_events', 0)
            return {
                "name": s.name,
                "n": s.n_synapses,
                "mean": round(s.mean_weight(), 4),
                "histogram": s.weight_histogram(bins=20),
                "total_ltp_events": ltp,
                "total_ltd_events": ltd,
                "ltp_ltd_ratio": round(ltp / max(1, ltd), 3),
            }
    return {"error": "not found"}


@router.get("")
def api_root(request: Request):
    """Return helpful API entry links."""
    base = str(request.base_url)
    return {
        "openapi": base + "openapi.json",
        "docs": base + "docs",
    }