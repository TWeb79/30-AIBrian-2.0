# Stats routes - /api/vocabulary, /api/memory, /api/bypass, /api/assemblies
import asyncio
from fastapi import APIRouter
from api.config import brain

router = APIRouter()

@router.get("/vocabulary")
async def vocabulary():
    """Return vocabulary learning statistics and recent word list."""
    try:
        stats = await asyncio.to_thread(
            brain.phon_buffer.get_statistics, recent_count=50
        )
        stats["words"] = stats.pop("recent_words", [])
    except Exception as e:
        print(f"[API /vocabulary] Error: {e}")
        stats = {"vocabulary_size": 0, "words": [], "error": str(e)}
    return stats


@router.get("/memory")
async def memory():
    """Return episodic memory statistics and recent episodes."""
    stats = await asyncio.to_thread(brain.hippocampus.get_statistics)
    recent = await asyncio.to_thread(
        lambda: [
            {"topic": ep.topic, "valence": ep.valence, "timestamp": ep.timestamp}
            for ep in brain.hippocampus.get_recent(5)
        ]
    )
    stats["recent_episodes"] = recent
    return stats


@router.get("/bypass")
async def bypass():
    """Return LLM bypass rate and path distribution."""
    return await asyncio.to_thread(brain.bypass_monitor.get_statistics)


@router.get("/assemblies")
async def assemblies():
    """Return cell assembly statistics."""
    return await asyncio.to_thread(brain.assembly_detector.get_statistics)