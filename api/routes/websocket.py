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
            snap = brain.snapshot()
            await ws.send_text(json.dumps(snap))
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        pass