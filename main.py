from __future__ import annotations

import asyncio
import json
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

app = FastAPI()


@app.get("/ping")
def ping() -> dict[str, object]:
    """Return a basic JSON response to verify plain HTTP works."""
    return {
        "ok": True,
        "kind": "http",
        "ts": time.time(),
    }


@app.get("/sse")
async def sse() -> StreamingResponse:
    """Stream a few SSE events to verify streaming works."""
    async def event_stream() -> asyncio.AsyncIterator[str]:
        for index in range(3):
            payload = {
                "ok": True,
                "kind": "sse",
                "index": index,
                "ts": time.time(),
            }
            yield f"event: tick\ndata: {json.dumps(payload)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.websocket("/ws")
async def ws(websocket: WebSocket) -> None:
    """Echo WebSocket messages.

    This should work locally on a normal ASGI server.
    On Vercel, this is the endpoint expected to fail if WebSocket server
    support is unavailable.
    """
    await websocket.accept()
    await websocket.send_json({"ok": True, "kind": "ws", "message": "connected"})

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"echo:{message}")
    except WebSocketDisconnect:
        return