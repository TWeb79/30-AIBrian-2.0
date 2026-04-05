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
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import Request
import traceback

from brain import BRAIN20Brain

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

brain = BRAIN20Brain(scale=SCALE)
# FIX: Do NOT call brain.start_background_loop() here.
# BRAIN20Brain.__init__ already calls self.continuous_loop.start() which handles
# background stepping. Running both causes constant lock contention that starves
# the API, fills the thread pool, and eventually deadlocks the server.

@asynccontextmanager
async def lifespan(app):
    yield
    brain.stop()
    brain.persist()
    print("[API] Brain persisted on shutdown")

app = FastAPI(title="BRAIN20 Brain API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    try:
        detail = exc.detail
    except Exception:
        detail = str(exc)
    return JSONResponse(status_code=exc.status_code, content={"error": "http_error", "message": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "validation_error", "message": str(exc)})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"[API ERROR] Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"error": "internal_server_error", "message": "Internal server error"})