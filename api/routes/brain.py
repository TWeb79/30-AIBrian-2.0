# Brain routes - /api/brain/status, /api/stimulate
import numpy as np
from fastapi import APIRouter
from api.config import brain
from api.models import StimulusRequest

router = APIRouter()

@router.get("/brain/status")
def status():
    """Get comprehensive brain state."""
    try:
        snap = brain.snapshot()
        snap["total_neurons"] = brain.total_neurons()
        snap["total_synapses"] = brain.total_synapses()
        
        vocab_stats = brain.phon_buffer.get_statistics(recent_count=10)
        vocab_stats["recent_words"] = vocab_stats.pop("recent_words", [])
        try:
            vocab_stats["vocabulary_size"] = brain.phon_buffer.get_vocabulary_size()
        except Exception:
            vocab_stats["vocabulary_size"] = 0
        
        snap["vocabulary"] = vocab_stats
        snap["memory"] = brain.hippocampus.get_statistics()
        snap["bypass"] = brain.bypass_monitor.get_statistics()
        snap["assemblies"] = brain.assembly_detector.get_statistics()
        snap["affect"] = vars(brain.affect.get_state())
        snap["drives"] = vars(brain.drives.state)
    except Exception as e:
        print(f"[API /brain/status] Error: {e}")
        snap = {"error": str(e)}
    return snap


@router.post("/stimulate")
def stimulate(req: StimulusRequest):
    """Inject sensory stimulus."""
    arr = np.array(req.data, dtype=np.float32)
    brain.stimulate_modality(req.modality, arr)
    return {"injected": len(arr), "modality": req.modality}