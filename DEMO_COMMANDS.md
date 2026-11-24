# Demo Commands

```bash
# Start broker, API/consumer, and dashboard
docker compose up --build

# Generate mostly clean records (run from project root)
python producer/generate_events.py --count 200 --bad-rate 0.01

# Generate enough anomalies to demonstrate quarantine and circuit breaker
python producer/generate_events.py --count 300 --bad-rate 0.10

# Inspect status
curl http://localhost:8000/api/status

# Resume pipeline
curl -X POST http://localhost:8000/api/pipeline/resume

# Create a time-travel snapshot
curl -X POST http://localhost:8000/api/snapshots

# List snapshots
curl http://localhost:8000/api/snapshots
```

On Windows PowerShell, `curl` may be an alias. Use `Invoke-RestMethod` if needed:

```powershell
Invoke-RestMethod http://localhost:8000/api/status
Invoke-RestMethod -Method Post http://localhost:8000/api/pipeline/resume
Invoke-RestMethod -Method Post http://localhost:8000/api/snapshots
```
