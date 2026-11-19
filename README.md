# Ice Stream — Real-Time Lakehouse Observability

A presentation-ready internship project prototype based on the supplied project brief.

## What this project demonstrates

- Streaming e-commerce checkout telemetry through a Kafka-compatible broker (Redpanda).
- Real-time data-quality checks for missing/null values, invalid amounts, and schema drift.
- Quarantine of invalid records instead of allowing bad data into the serving dataset.
- Circuit-breaker behavior: if the bad-record rate crosses the configured threshold, the pipeline pauses.
- A dead-letter queue (DLQ) for rejected records.
- A React Flow lineage dashboard showing Ingest → Process → Serve and the quarantined node.
- Incident events and pipeline status updates over WebSockets.
- Snapshot-based local time-travel demonstration.

> **Implementation note:** This repository is an executable MVP for a review/demo. It runs with Redpanda, a Python streaming consumer/API, and local JSONL snapshots so it can be started on a normal laptop. The brief names Apache Flink and Apache Iceberg as the target lakehouse stack; deployment notes and an Iceberg/Flink SQL starter are included under `lakehouse/`. The local demo does not claim that JSONL storage is Apache Iceberg.

## Architecture

```text
Python event generator
        |
        v
Redpanda (Kafka API :9092)
        |
        v
Python stream processor + rules engine
        |                         |
        | valid                    | invalid / schema drift
        v                         v
data/serving.jsonl          data/quarantine.jsonl
        |                         |
        v                         v
Serving API                  data/dlq.jsonl
        |
        v
FastAPI + WebSocket  <---->  React Flow lineage dashboard
        |
        +---- snapshots for local time-travel demo
```

## Requirements

- Docker Desktop with Docker Compose
- Python 3.10+ (only needed to run the producer outside Docker)
- Node.js 18+ (only needed to run the React UI outside Docker)

## Run the complete demo

From this project directory:

```bash
docker compose up --build
```

Open:
- Dashboard: http://localhost:5173
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/health

In a second terminal, generate events:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r producer/requirements.txt
python producer/generate_events.py --count 300 --bad-rate 0.04
```

The generator deliberately injects occasional null values, negative totals, and schema changes. You should see valid events in the serving file, invalid events in quarantine/DLQ, and the circuit breaker pause the pipeline when the rolling bad-data rate exceeds the configured threshold.

To stop:

```bash
docker compose down
```

To also remove the broker's persisted demo volume:

```bash
docker compose down -v
```

## Configuration

The backend reads these environment variables:

| Variable | Default | Meaning |
|---|---:|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `redpanda:9092` | Kafka-compatible broker |
| `KAFKA_TOPIC` | `checkout-events` | Input topic |
| `BAD_RATE_THRESHOLD` | `0.02` | Circuit-breaker threshold (2%) |
| `WINDOW_SIZE` | `100` | Number of recent records used for the bad-rate calculation |
| `DATA_DIR` | `/app/data` | Local demo lakehouse directory |

## Useful API endpoints

- `GET /health` — service health
- `GET /api/status` — current pipeline status and metrics
- `GET /api/events?limit=50` — recent processed events
- `GET /api/incidents` — incident history
- `POST /api/pipeline/resume` — manually resume after reviewing an incident
- `POST /api/snapshots` — create a local snapshot
- `GET /api/snapshots` — list snapshots
- `GET /api/time-travel/{snapshot_id}` — read the serving data captured in a snapshot
- `WS /ws` — live status updates

## Suggested presentation walkthrough

1. Start the stack and show the empty/healthy pipeline.
2. Run the event generator with `--bad-rate 0.01`; show records reaching the serving node.
3. Run it with `--bad-rate 0.10`; show bad records quarantined and the circuit breaker changing the pipeline to `PAUSED`.
4. Open the incidents panel and show the reason, bad-rate, and timestamp.
5. Resume the pipeline from the dashboard or API.
6. Create a snapshot and open it through the time-travel API.
7. Explain how the included Flink SQL/Iceberg starter maps the demo to the target production architecture.

## GitHub upload

Create a new GitHub repository, then from this folder run:

```bash
git init
git add .
git commit -m "Build Ice Stream real-time lakehouse observability MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ice-stream-lakehouse-observability.git
git push -u origin main
```

Do not commit `.env`, virtual environments, `node_modules`, or generated runtime data. The included `.gitignore` excludes them.

## Project structure

```text
ice_stream_lakehouse_observability/
├── backend/                 # FastAPI, Kafka consumer, rules, snapshots
├── producer/                # synthetic checkout event generator
├── frontend/                # React + React Flow dashboard
├── lakehouse/               # Flink SQL and Iceberg target-stack notes
├── data/                    # runtime output (gitignored)
├── docker-compose.yml
└── README.md
```
