# Stats routes - /api/vocabulary, /api/memory, /api/bypass, /api/assemblies
import asyncio
import os
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


@router.get("/vocabulary/export")
async def export_vocabulary():
    """Export all learned words to a text file for backup/reload."""
    try:
        vocab_data = await asyncio.to_thread(brain.phon_buffer.export_vocabulary)
        word_index = vocab_data.get("word_index", {})
        
        # Sort words alphabetically
        sorted_words = sorted(word_index.keys())
        
        # Create export directory
        export_dir = "/app/export" if os.path.exists("/app") else "export"
        os.makedirs(export_dir, exist_ok=True)
        
        # Write to text file (one word per line)
        export_path = os.path.join(export_dir, "vocabulary_export.txt")
        with open(export_path, "w", encoding="utf-8") as f:
            for word in sorted_words:
                f.write(word + "\n")
        
        return {
            "status": "success",
            "vocabulary_size": len(sorted_words),
            "export_path": export_path,
            "first_100": sorted_words[:100],
        }
    except Exception as e:
        print(f"[API /vocabulary/export] Error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/vocabulary/import")
async def import_vocabulary(file_path: str = "export/vocabulary_export.txt"):
    """Import words from a text file (one word per line)."""
    try:
        if not os.path.exists(file_path):
            # Try alternate paths
            alt_paths = [
                file_path,
                f"/app/{file_path}",
                f"/app/export/{os.path.basename(file_path)}",
                f"export/{os.path.basename(file_path)}",
            ]
            for path in alt_paths:
                if os.path.exists(path):
                    file_path = path
                    break
        
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}
        
        # Read words from file
        with open(file_path, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]
        
        # Add words to phonological buffer (skip if already exists)
        added = 0
        skipped = 0
        for word in words:
            if word in brain.phon_buffer.word_index:
                skipped += 1
            else:
                brain.phon_buffer.observe_pairing(word, concept_id=0)
                added += 1
        
        # Update vocabulary size
        brain.self_model.vocabulary_size = brain.phon_buffer.get_vocabulary_size()
        
        return {
            "status": "success",
            "total_words": len(words),
            "added": added,
            "skipped": skipped,
            "new_vocabulary_size": brain.self_model.vocabulary_size,
        }
    except Exception as e:
        print(f"[API /vocabulary/import] Error: {e}")
        return {"status": "error", "message": str(e)}


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