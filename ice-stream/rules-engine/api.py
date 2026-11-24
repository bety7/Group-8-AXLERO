import asyncio
import json
import threading
from contextlib import asynccontextmanager

from confluent_kafka import Consumer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

clients: set = set()
current = {"state": "CLOSED", "error_rate": 0.0}


async def broadcast(message: dict):
    dead = []
    for ws in list(clients):
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)


def handle_event(event: dict):
    if event.get("type") == "breaker":
        current["state"] = event["to"]
        current["error_rate"] = event.get("error_rate", 0.0)


def kafka_loop(loop):
    consumer = Consumer({
        "bootstrap.servers": "localhost:9092",
        "group.id": "ice-api",
        "auto.offset.reset": "latest",
    })
    consumer.subscribe(["breaker-events"])
    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        try:
            event = json.loads(msg.value())
        except json.JSONDecodeError:
            continue
        handle_event(event)
        asyncio.run_coroutine_threadsafe(broadcast(event), loop)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    threading.Thread(target=kafka_loop, args=(loop,), daemon=True).start()
    yield


app = FastAPI(title="Ice Stream API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"ok": True, "breaker": current}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    await websocket.send_json({"type": "snapshot", **current})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.discard(websocket)