SET 'execution.runtime-mode' = 'batch';
SELECT COUNT(*) AS total_rows FROM iceberg.ecommerce.checkout_raw;
SELECT event_date, COUNT(*) AS rows_per_day FROM iceberg.ecommerce.checkout_raw GROUP BY event_date;