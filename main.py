import json, os, threading, asyncio, uuid, shutil
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from .rules import validate_event, utc_now
from .state import STATE, DATA_DIR

app = FastAPI(title="Ice Stream Observability API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
clients = set()
THRESHOLD = float(os.getenv("BAD_RATE_THRESHOLD", "0.02"))
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "checkout-events")

def record_incident(kind, message, bad_rate=None):
    incident = {"id": str(uuid.uuid4())[:8], "type": kind, "message": message,
                "bad_rate": bad_rate, "timestamp": utc_now()}
    STATE.incidents.append(incident)
    STATE.append_jsonl("incidents.jsonl", incident)

def process_event(event):
    ok, errors = validate_event(event)
    with STATE.lock:
        STATE.total += 1
        STATE.recent.append(0 if ok else 1)
        bad_rate = sum(STATE.recent) / len(STATE.recent)
        if ok:
            if STATE.status != "PAUSED":
                STATE.valid += 1
                STATE.append_jsonl("serving.jsonl", event)
                STATE.events.append({"event": event, "result": "SERVED", "timestamp": utc_now()})
            else:
                # Do not silently serve while the circuit breaker is open.
                STATE.append_jsonl("quarantine.jsonl", {"event": event, "errors": ["PIPELINE_PAUSED"], "timestamp": utc_now()})
                STATE.quarantined += 1
        else:
            STATE.bad += 1
            STATE.quarantined += 1
            row = {"event": event, "errors": errors, "timestamp": utc_now()}
            STATE.append_jsonl("quarantine.jsonl", row)
            STATE.append_jsonl("dlq.jsonl", row)
            STATE.events.append({"event": event, "result": "QUARANTINED", "errors": errors, "timestamp": utc_now()})
        if len(STATE.recent) >= min(10, STATE.recent.maxlen) and bad_rate > THRESHOLD and STATE.status != "PAUSED":
            STATE.status = "PAUSED"
            STATE.paused_reason = f"Bad-data rate {bad_rate:.1%} exceeded threshold {THRESHOLD:.1%}"
            record_incident("CIRCUIT_BREAKER_OPEN", STATE.paused_reason, round(bad_rate, 4))
        elif STATE.status != "PAUSED":
            STATE.status = "HEALTHY"
    return STATE.snapshot()

def consume():
    while True:
        try:
            consumer = KafkaConsumer(
                TOPIC, bootstrap_servers=BOOTSTRAP, auto_offset_reset="latest",
                enable_auto_commit=True, group_id="ice-stream-observability",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                consumer_timeout_ms=1000
            )
            for msg in consumer:
                process_event(msg.value)
            consumer.close()
        except Exception as exc:
            with STATE.lock:
                if STATE.status != "PAUSED":
                    STATE.status = "DEGRADED"
            threading.Event().wait(3)

@app.on_event("startup")
def startup():
    threading.Thread(target=consume, daemon=True).start()

@app.get("/health")
def health():
    return {"ok": True, "service": "ice-stream-api"}

@app.get("/api/status")
def status():
    return STATE.snapshot()

@app.get("/api/events")
def events(limit: int = 50):
    return STATE.snapshot()["events"][-max(1, min(limit, 200)):]

@app.get("/api/incidents")
def incidents():
    return list(reversed(STATE.incidents))

@app.post("/api/pipeline/resume")
def resume():
    with STATE.lock:
        STATE.status = "HEALTHY"
        STATE.paused_reason = None
        record_incident("MANUAL_RESUME", "Pipeline manually resumed by operator", None)
    return {"status": "HEALTHY", "message": "Pipeline resumed"}

@app.post("/api/snapshots")
def create_snapshot():
    snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + str(uuid.uuid4())[:6]
    src = DATA_DIR / "serving.jsonl"
    dest = DATA_DIR / "snapshots" / f"{snapshot_id}.jsonl"
    if src.exists():
        shutil.copyfile(src, dest)
    else:
        dest.write_text("", encoding="utf-8")
    metadata = {"snapshot_id": snapshot_id, "created_at": utc_now(), "records": sum(1 for _ in dest.open(encoding="utf-8"))}
    with (DATA_DIR / "snapshots" / "metadata.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(metadata) + "\n")
    return metadata

@app.get("/api/snapshots")
def snapshots():
    path = DATA_DIR / "snapshots" / "metadata.jsonl"
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()][::-1]

@app.get("/api/time-travel/{snapshot_id}")
def time_travel(snapshot_id: str):
    path = DATA_DIR / "snapshots" / f"{snapshot_id}.jsonl"
    if not path.exists(): return {"error": "Snapshot not found"}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {"snapshot_id": snapshot_id, "records": rows, "count": len(rows)}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.send_json(STATE.snapshot())
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        clients.discard(ws)
