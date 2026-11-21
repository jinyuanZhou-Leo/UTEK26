import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from sentinel.core.loop import Engine
from sentinel.models import to_json_dict

engine: Engine | None = None
clients: list[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(engine.run())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/metrics")
def metrics():
    if engine.latest is None:
        return {"status": "starting"}
    return to_json_dict(engine.latest)

@app.get("/health")
def health():
    if engine.latest is None:
        sensors = {}
    else:
        sensors = engine.latest.sensors
    return {"ok": True, "sensors": sensors}


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)