# Training routes — bootstrap vocabulary / training endpoints
from fastapi import APIRouter, BackgroundTasks
from api.config import brain
import os

router = APIRouter()


@router.post("/train_vocabulary")
def train_vocabulary(
    background_tasks: BackgroundTasks,
    mode: str = "file",
    batch_size: int = 200,
    background: bool = True,
):
    """Train vocabulary from TrainingFile.md or resume previous run.

    mode: 'file' to stream TrainingFile.md, 'resume' to continue from last saved position.
    batch_size: number of lines/chunks per processing tick.
    If background is True, the ingestion runs in background thread via FastAPI BackgroundTasks.
    """
    # Allow tests / deployments to override the location
    training_path = os.getenv("TRAINING_FILE_PATH")
    if not training_path:
        training_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'TrainingFile.md')
    training_path = os.path.abspath(training_path)

    def _worker(path: str, batch: int):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                chunk = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    chunk.append(line)
                    if len(chunk) >= batch:
                        brain.process_input_v01(" ".join(chunk))
                        chunk = []
                if chunk:
                    brain.process_input_v01(" ".join(chunk))
            # Ensure learned vocabulary is persisted immediately
            if hasattr(brain, 'persist_vocabulary'):
                brain.persist_vocabulary()
        except Exception as e:
            print(f"[train_vocabulary] Error: {e}")

    if mode == 'file':
        if not os.path.exists(training_path):
            return {"error": "TrainingFile.md not found", "path": training_path}
        if background:
            # FastAPI injects BackgroundTasks
            background_tasks.add_task(_worker, training_path, batch_size)
            return {"status": "started", "mode": mode}
        else:
            _worker(training_path, batch_size)
            return {"status": "completed", "mode": mode}
    else:
        return {"error": "unsupported mode", "mode": mode}
