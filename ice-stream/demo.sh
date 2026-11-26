#!/usr/bin/env bash
# Starts the whole Ice Stream stack. Run from Git Bash:  bash demo.sh
# Stop everything with:                                  bash demo.sh stop
cd "$(dirname "$0")"
COMPOSE="docker compose -f infra/docker-compose.yml"

if [ "$1" = "stop" ]; then
  pkill -f "guard.py" 2>/dev/null || true
  pkill -f "uvicorn api:app" 2>/dev/null || true
  $COMPOSE down
  exit 0
fi

set -e
if [ -f rules-engine/.venv/Scripts/python.exe ]; then PY=rules-engine/.venv/Scripts/python.exe; else PY=rules-engine/.venv/bin/python; fi

echo "==> Starting containers"
bash infra/flink/download-jars.sh
$COMPOSE up -d --build

echo "==> Waiting for Flink"
until curl -s localhost:8081/overview | grep -q '"taskmanagers":1'; do sleep 3; done

echo "==> Creating topics"
for t in checkout-events checkout-clean checkout-dlq breaker-events; do
  MSYS_NO_PATHCONV=1 $COMPOSE exec -T kafka /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --topic $t --bootstrap-server localhost:9092
done

echo "==> Creating tables and submitting Flink jobs"
for f in 01_create_raw_table.sql 03_create_dlq_tables.sql 02_stream_raw.sql 04_stream_clean_dlq.sql; do
  bash run-sql.sh $f
done

echo "==> Starting guard and API in the background"
(cd rules-engine && ../$PY guard.py > ../guard.log 2>&1 &)
(cd rules-engine && ../$PY -m uvicorn api:app --port 8000 > ../api.log 2>&1 &)

cat <<'EOF'

Stack is up.
  Flink UI    http://localhost:8081
  Kafka UI    http://localhost:8080
  Storage     http://localhost:9001   (admin / password)
  API         http://localhost:8000/health

Next, in two more terminals:
  DASH:      cd dashboard && npm run dev      then open http://localhost:5173
  PRODUCER:  cd producer && source .venv/Scripts/activate
             python main.py --eps 200 --null-rate 0.1      (watch the breaker trip)
             python main.py --eps 200                      (watch it recover)

Logs: guard.log and api.log.  Stop everything with:  bash demo.sh stop
EOF