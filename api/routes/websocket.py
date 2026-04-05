# WebSocket route - /api/ws/stream
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.config import brain

router = APIRouter()

@router.websocket("/ws/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            # FIX: Read _last_snapshot directly without to_thread.
            # snapshot() previously called asyncio.to_thread(brain.snapshot) which
            # spawns a new OS thread blocked on brain._lock every 200ms. With the
            # frontend connected plus several chat requests, the thread pool fills
            # with blocked threads and the server stops responding entirely.
            #
            # _last_snapshot is a plain dict updated under brain._lock; reading it
            # here is safe under CPython's GIL (dict reference read is atomic).
            # If it's empty we do one full build, but that's rare (only on startup).
            snap = brain._last_snapshot
            if not snap:
                snap = await asyncio.to_thread(brain.snapshot)

            try:
                payload = json.dumps(snap)
            except (TypeError, ValueError):
                # Non-serialisable value crept in; send a minimal heartbeat instead
                payload = json.dumps({"step": snap.get("step", 0), "status": snap.get("status", "NEONATAL")})

            await ws.send_text(payload)
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        pass
    except Exception:
        # Don't let a single bad frame kill the connection handler
        pass