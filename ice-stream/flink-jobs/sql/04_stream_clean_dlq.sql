CREATE TEMPORARY TABLE kafka_clean (
  order_id STRING,
  user_id INT,
  tax_amount DOUBLE,
  total DOUBLE,
  ts STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'checkout-clean',
  'properties.bootstrap.servers' = 'kafka:29092',
  'properties.group.id' = 'flink-clean-writer',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true'
);

CREATE TEMPORARY TABLE kafka_dlq (
  error_reason STRING,
  breaker_state STRING,
  quarantined_at STRING,
  raw_payload STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'checkout-dlq',
  'properties.bootstrap.servers' = 'kafka:29092',
  'properties.group.id' = 'flink-dlq-writer',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true'
);

EXECUTE STATEMENT SET
BEGIN
  INSERT INTO iceberg.ecommerce.checkout_events
  SELECT order_id, user_id, tax_amount, total, ts, SUBSTRING(ts, 1, 10) FROM kafka_clean;

  INSERT INTO iceberg.ecommerce.checkout_dlq
  SELECT error_reason, breaker_state, quarantined_at, raw_payload, SUBSTRING(quarantined_at, 1, 10)
  FROM kafka_dlq;
END;