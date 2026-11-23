CREATE TEMPORARY TABLE kafka_raw (
  order_id STRING,
  user_id INT,
  tax_amount DOUBLE,
  total DOUBLE,
  ts STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'checkout-events',
  'properties.bootstrap.servers' = 'kafka:29092',
  'properties.group.id' = 'flink-raw-archiver',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true'
);

INSERT INTO iceberg.ecommerce.checkout_raw
SELECT order_id, user_id, tax_amount, total, ts, SUBSTRING(ts, 1, 10)
FROM kafka_raw;