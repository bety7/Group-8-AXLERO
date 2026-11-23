# Iceberg table design

| Table | Purpose | Partitioned by |
|-------|---------|----------------|
| checkout_raw | Everything received from Kafka, good and bad (the lake archive) | event_date |
| checkout_events | Only records that passed quality rules (added Day 13) | event_date |
| checkout_dlq | Quarantined records with the reason (added Day 13) | quarantine_date |

## Why partition by date
Queries for one day read only that day's folder, and old days can be dropped cheaply.

## Format version 2
Allows row-level deletes and upserts.

## Schema evolution
Iceberg tracks columns by ID, not by name or position. Adding, renaming or
dropping a column never rewrites old data files. The producer's drift injection
(renamed and added columns) is why the raw table keeps a fixed schema and the
guard service (Day 13) quarantines records that do not match it.