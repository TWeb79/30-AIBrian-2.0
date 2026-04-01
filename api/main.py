"""
api.py — OSCEN FastAPI REST Server
====================================
Exposes the brain simulation over HTTP so the React UI can
connect to it.  Run with:

    uvicorn api:app --host 0.0.0.0 --port 8000 --reload

Endpoints
---------
GET  /status          → brain snapshot (regions, stats, synapses)
GET  /health          → simple heartbeat
POST /stimulate       → inject sensory stimulus
POST /chat            → send text to brain (also proxies to Claude API)
POST /motor           → issue motor command (through reflex arc)
WS   /ws/stream       → real-time brain state stream (JSON, 5 Hz)
"""

from __future__ import annotations
import asyncio
import json
import os
import time
from typing import Any

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from brain import OSCENBrain

# ─── Boot brain ───────────────────────────────────────────────────────────────

SCALE = float(os.getenv("BRAIN_SCALE", "0.01"))   # 0.01 = fast CPU demo
brain = OSCENBrain(scale=SCALE)
brain.start_background_loop(steps_per_tick=100)

# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(title="OSCEN Brain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic models ──────────────────────────────────────────────────────────

class StimulusRequest(BaseModel):
    modality:   str            # "vision" | "audio" | "touch"
    data:       list[float]    # normalised [0,1] values

class ChatRequest(BaseModel):
    message:    str
    history:    list[dict] = []
    brainState: dict = {}

class MotorCommand(BaseModel):
    force:    float = 0.0
    angle:    float = 0.0
    velocity: float = 0.0
    joint:    str   = "arm"

class ReflexCheckRequest(BaseModel):
    force:    float
    angle:    float
    velocity: float

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "alive", "uptime_s": round(time.time() - brain.start_time, 1)}


@app.get("/api/brain/status")
def status():
    snap = brain.snapshot()
    snap["total_neurons"]  = brain.total_neurons()
    snap["total_synapses"] = brain.total_synapses()
    return snap


@app.post("/api/stimulate")
def stimulate(req: StimulusRequest):
    arr = np.array(req.data, dtype=np.float32)
    brain.stimulate_modality(req.modality, arr)
    return {"injected": len(arr), "modality": req.modality}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Process user message through the brain AND generate a response.
    The brain is stimulated with the text; the response is generated
    by reflecting the brain's current state back into natural language.
    """
    # Stimulate brain with user text
    brain.process_text(req.message)

    # Give brain time to process (a few hundred ms of sim)
    await asyncio.sleep(0.15)

    snap  = brain.snapshot()
    reply = _brain_respond(req.message, snap, req.history)

    # Store in brain's chat history
    brain.chat_history.append({"role": "user",      "content": req.message})
    brain.chat_history.append({"role": "assistant",  "content": reply})

    return {
        "response":        reply,
        "brain_state":  snap,
        "concept_id":   snap["regions"]["concept"]["active_concept_neuron"],
        "attention":    snap["attention_gain"],
        "prediction_error": snap["prediction_error"],
    }


@app.post("/api/reflex/check")
def reflex_check(req: ReflexCheckRequest):
    """Check if motor command passes safety constraints."""
    FORCE_MAX = 10
    ANGLE_MAX = 170
    VEL_MAX = 2
    
    violations = []
    if req.force > FORCE_MAX:
        violations.append(f"force={req.force}N > {FORCE_MAX}N")
    if req.angle > ANGLE_MAX:
        violations.append(f"angle={req.angle}° > {ANGLE_MAX}°")
    if req.velocity > VEL_MAX:
        violations.append(f"velocity={req.velocity}m/s > {VEL_MAX}m/s")
    
    approved = len(violations) == 0
    
    return {
        "approved": approved,
        "reason": "SAFE — command executed" if approved else f"REFLEX_WITHDRAWAL: {'; '.join(violations)}",
        "constraints": {
            "force_max": FORCE_MAX,
            "angle_max": ANGLE_MAX,
            "velocity_max": VEL_MAX
        }
    }


@app.post("/api/motor")
def motor(cmd: MotorCommand):
    result = brain.issue_motor_command(cmd.dict())
    return result


@app.post("/api/reflex/check")
def reflex_check(req: ReflexCheckRequest):
    """Check if motor command passes safety constraints."""
    FORCE_MAX = 10
    ANGLE_MAX = 170
    VEL_MAX = 2
    
    violations = []
    if req.force > FORCE_MAX:
        violations.append(f"force={req.force}N > {FORCE_MAX}N")
    if req.angle > ANGLE_MAX:
        violations.append(f"angle={req.angle}° > {ANGLE_MAX}°")
    if req.velocity > VEL_MAX:
        violations.append(f"velocity={req.velocity}m/s > {VEL_MAX}m/s")
    
    approved = len(violations) == 0
    
    return {
        "approved": approved,
        "reason": "SAFE — command executed" if approved else f"REFLEX_WITHDRAWAL: {'; '.join(violations)}",
        "constraints": {
            "force_max": FORCE_MAX,
            "angle_max": ANGLE_MAX,
            "velocity_max": VEL_MAX
        }
    }


@app.get("/api/synapses/{synapse_name}/weights")
def synapse_weights(synapse_name: str):
    for s in brain.all_synapses:
        if s.name == synapse_name:
            return {
                "name":     s.name,
                "n":        s.n_synapses,
                "mean":     round(s.mean_weight(), 4),
                "histogram": s.weight_histogram(bins=20),
            }
    return {"error": "not found"}


# ─── WebSocket stream ─────────────────────────────────────────────────────────

@app.websocket("/api/ws/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            snap = brain.snapshot()
            await ws.send_text(json.dumps(snap))
            await asyncio.sleep(0.2)    # 5 Hz update
    except WebSocketDisconnect:
        pass


# ─── Brain response generation ────────────────────────────────────────────────

def _brain_respond(message: str, snap: dict, history: list[dict]) -> str:
    """
    Generate a human-readable response that reflects brain state.
    This is called by the /chat endpoint.

    In production you would call the Anthropic API here with the
    brain snapshot as context.  We provide a structured template
    so the UI can display it without a separate API call.
    """
    regions  = snap.get("regions", {})
    gain     = snap.get("attention_gain", 1.0)
    err      = snap.get("prediction_error", 0.0)
    concept  = regions.get("concept", {}).get("active_concept_neuron", -1)
    status   = snap.get("status", "NEONATAL")
    step     = snap.get("step", 0)

    assoc_act  = regions.get("association",  {}).get("activity_pct", 0)
    pred_act   = regions.get("predictive",   {}).get("activity_pct", 0)
    concept_act= regions.get("concept",      {}).get("activity_pct", 0)

    # Build a state-aware reply string (the UI uses Claude API for richer replies)
    lines = [
        f"[OSCEN·{status}·step={step:,}]",
        f"",
        f"Processing: '{message}'",
        f"",
        f"Neural activity report:",
        f"  • Association hub:   {assoc_act:.1f}% active  (cross-modal binding)",
        f"  • Predictive cortex: {pred_act:.1f}% active  (error={err:.4f})",
        f"  • Concept layer:     {concept_act:.2f}% active  (WTA winner #{concept})",
        f"  • Attention gain:    ×{gain:.2f}  ({'HIGH — learning accelerated' if gain > 2 else 'normal'})",
        f"",
        f"The STDP synapses are {'strengthening rapidly' if gain > 2 else 'updating normally'} based on this input.",
    ]
    return "\n".join(lines)
