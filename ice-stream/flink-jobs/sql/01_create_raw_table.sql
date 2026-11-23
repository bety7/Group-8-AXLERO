CREATE DATABASE IF NOT EXISTS iceberg.ecommerce;

CREATE TABLE IF NOT EXISTS iceberg.ecommerce.checkout_raw (
  order_id STRING,
  user_id INT,
  tax_amount DOUBLE,
  total DOUBLE,
  ts STRING,
  event_date STRING
) PARTITIONED BY (event_date)
WITH ('format-version' = '2');