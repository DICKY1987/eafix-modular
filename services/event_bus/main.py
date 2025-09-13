from __future__ import annotations

import asyncio
import json
from typing import Dict, List, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse


class Hub:
    def __init__(self) -> None:
        self.clients: Set[WebSocket] = set()
        self.queue: asyncio.Queue[str] = asyncio.Queue(maxsize=1000)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.clients.discard(ws)

    async def broadcast(self, message: Dict) -> None:
        data = json.dumps(message)
        try:
            self.queue.put_nowait(data)
        except asyncio.QueueFull:
            # drop oldest
            _ = await self.queue.get()
            await self.queue.put(data)

    async def pump(self) -> None:
        while True:
            data = await self.queue.get()
            dead: List[WebSocket] = []
            for ws in list(self.clients):
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws)


hub = Hub()
app = FastAPI()


@app.on_event("startup")
async def _startup():
    asyncio.create_task(hub.pump())


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await hub.connect(ws)
    try:
        while True:
            await ws.receive_text()  # ignore client messages
    except WebSocketDisconnect:
        hub.disconnect(ws)


@app.post("/publish")
async def publish(message: Dict):
    await hub.broadcast(message)
    return {"ok": True}


@app.get("/health")
async def health():
    return PlainTextResponse("ok")

