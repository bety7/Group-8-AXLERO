# Ice Stream: Real-Time Lakehouse Observability

A self-healing data pipeline: Kafka to Flink to Apache Iceberg, with real-time
data quality monitoring, a circuit breaker, and a live lineage dashboard.

## Planned architecture

    Producer -> Kafka -> Flink -> Iceberg (MinIO / S3)
                          |
        Rules engine + Circuit breaker -> Dead Letter Queue
                          |
        FastAPI WebSocket -> React Flow dashboard