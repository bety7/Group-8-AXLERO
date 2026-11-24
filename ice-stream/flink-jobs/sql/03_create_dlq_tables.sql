CREATE TABLE IF NOT EXISTS iceberg.ecommerce.checkout_events (
  order_id STRING,
  user_id INT,
  tax_amount DOUBLE,
  total DOUBLE,
  ts STRING,
  event_date STRING
) PARTITIONED BY (event_date)
WITH ('format-version' = '2');

CREATE TABLE IF NOT EXISTS iceberg.ecommerce.checkout_dlq (
  error_reason STRING,
  breaker_state STRING,
  quarantined_at STRING,
  raw_payload STRING,
  quarantine_date STRING
) PARTITIONED BY (quarantine_date)
WITH ('format-version' = '2');