# Project Review Notes — Ice Stream

## Problem
Traditional batch ETL can delay detection of bad data. Null values, invalid values, and schema drift can move downstream and reduce trust in analytics. The goal is to detect quality issues while the stream is running, quarantine bad records, and stop downstream serving when the configured bad-data threshold is crossed.

## Use case
An e-commerce platform streams checkout telemetry. A data-quality rule detects anomalies such as null `amount`, negative `amount`, or missing required fields. Valid records are served; invalid records are isolated in quarantine and a dead-letter queue. If the rolling bad-data rate exceeds 2%, the circuit breaker pauses serving.

## Modules
- Streaming ingestion: Kafka-compatible Redpanda broker.
- Stream processor: Python consumer in the runnable MVP; Apache Flink is the target engine.
- Lakehouse: local JSONL/snapshot demo; Apache Iceberg is the target table format.
- Observability rules: custom Python assertions.
- Lineage dashboard: React + React Flow.
- Incident management: event log, pause/resume controls, and time-travel snapshots.

## Demo acceptance checks
1. Valid event appears in `data/serving.jsonl`.
2. Invalid event appears in `data/quarantine.jsonl` and `data/dlq.jsonl`.
3. A bad-data rate above 2% changes pipeline status to `PAUSED`.
4. Dashboard displays the quarantined branch and circuit-breaker alert.
5. Operator can resume the pipeline.
6. Snapshot endpoint creates a point-in-time copy of served records.

## Limitations and next steps
- Replace local JSONL storage with Apache Iceberg tables.
- Move validation and stateful threshold logic into Apache Flink.
- Add authentication and role-based access for operator actions.
- Add unit/integration tests, metrics export, and deployment configuration.
