# API Configuration - App init, lifespan, CORS middleware
import os
import time
import asyncio
from contextlib import asynccontextmanager
from collections import deque
import threading

SCALE = float(os.getenv("BRAIN_SCALE", "0.01"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass, field

from brain import OSCENBrain

@dataclass
class TrainingSession:
    id: str
    n: int
    briefing: str
    include_user_inputs: bool
    status: str = "queued"
    consumed: int = 0
    last_result: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

TRAINING_SESSIONS: dict[str, TrainingSession] = {}

_proactive_lock = threading.Lock()
_proactive_queue: deque[str] = deque(maxlen=20)

brain = OSCENBrain(scale=SCALE)
brain.start_background_loop(steps_per_tick=100)

@asynccontextmanager
async def lifespan(app):
    yield
    brain.stop()
    brain.persist()
    print("[API] Brain persisted on shutdown")

app = FastAPI(title="OSCEN Brain API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)