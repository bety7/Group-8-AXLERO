from collections import deque
from threading import Lock
from pathlib import Path
import json, os

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "snapshots").mkdir(parents=True, exist_ok=True)

class PipelineState:
    def __init__(self):
        self.lock = Lock()
        self.recent = deque(maxlen=int(os.getenv("WINDOW_SIZE", "100")))
        self.status = "STARTING"
        self.paused_reason = None
        self.total = 0
        self.valid = 0
        self.bad = 0
        self.quarantined = 0
        self.incidents = []
        self.events = []

    def append_jsonl(self, filename, row):
        with (DATA_DIR / filename).open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")

    def snapshot(self):
        with self.lock:
            return {
                "status": self.status, "paused_reason": self.paused_reason,
                "total": self.total, "valid": self.valid, "bad": self.bad,
                "quarantined": self.quarantined,
                "bad_rate": round(sum(self.recent) / len(self.recent), 4) if self.recent else 0,
                "window_size": len(self.recent),
                "threshold": float(__import__("os").getenv("BAD_RATE_THRESHOLD", "0.02")),
                "incidents": self.incidents[-20:], "events": self.events[-30:]
            }

STATE = PipelineState()
