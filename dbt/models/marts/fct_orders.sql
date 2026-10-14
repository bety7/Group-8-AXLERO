-- Mart layer: one row per order. Cube.dev reads this table.
-- Revenue is defined ONCE here; margin / cost roll-ups are defined in the semantic layer.
select
    order_id,
    order_date,
    region,
    country,
    product_category,
    customer_segment,
    shipping_mode,
    units,
    unit_price,
    discount_pct,
    round(units * unit_price * (1 - discount_pct), 2) as revenue,
    material_cost,
    shipping_cost
from {{ ref('stg_orders') }}
