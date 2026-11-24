# Target Lakehouse Stack: Flink + Iceberg

The runnable MVP uses Redpanda + a Python consumer and local JSONL snapshots to keep setup lightweight. This folder records the intended production mapping from the supplied brief.

## Target components

1. **Kafka / Redpanda** — checkout telemetry ingestion.
2. **Apache Flink** — stateful streaming validation and routing.
3. **Apache Iceberg** — ACID table format for trusted and quarantined records, with snapshot/time-travel support.
4. **Python / Great Expectations** — rule authoring and batch validation support.
5. **React Flow** — lineage and quarantine visualization.

## Example Flink SQL starter

The following is a conceptual Flink SQL starter. It assumes a Flink deployment with a Kafka connector and an Iceberg catalog already configured. Catalog and connector artifacts are deployment-specific and are not downloaded by the local MVP Compose stack.

```sql
CREATE TABLE checkout_events (
  event_id STRING,
  order_id STRING,
  event_time TIMESTAMP(3),
  amount DECIMAL(12, 2),
  currency STRING,
  customer_id STRING,
  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'checkout-events',
  'properties.bootstrap.servers' = 'redpanda:9092',
  'properties.group.id' = 'ice-stream-flink',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json'
);

-- In a configured Iceberg catalog, create trusted and quarantine tables
-- using the Iceberg connector and catalog-specific WITH properties.
```

## Mapping to the review plan

| Brief item | MVP implementation | Production target |
|---|---|---|
| Stream generation | `producer/generate_events.py` | E-commerce telemetry producers |
| Kafka ingestion | Redpanda Kafka API | Apache Kafka |
| Stream processing | Python consumer and validator | Apache Flink jobs |
| Lakehouse storage | JSONL files and snapshot copies | Apache Iceberg tables on object storage |
| Data quality rules | `backend/app/rules.py` | Great Expectations and Flink assertions |
| Circuit breaker | Rolling bad-rate threshold | Flink state + control topic |
| Quarantine / DLQ | `quarantine.jsonl`, `dlq.jsonl` | Iceberg quarantine table + Kafka DLQ |
| Lineage dashboard | React Flow | React Flow with lineage service |
| Time travel | Local snapshot copies | Iceberg snapshot/time-travel queries |

## Important review statement

The local stack proves the end-to-end observability behavior and dashboard interactions. It is not a full production Iceberg deployment. For a production build, configure an Iceberg REST/Hive catalog, object storage such as S3, and compatible Flink Kafka/Iceberg connector JARs, then replace the local JSONL sink with Iceberg table writes.
