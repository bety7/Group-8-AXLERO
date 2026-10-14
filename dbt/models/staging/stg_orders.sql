-- Staging layer: rename / cast only. No business logic here.
select
    order_id,
    cast(order_date as date)            as order_date,
    region,
    country,
    product_category,
    customer_segment,
    shipping_mode,
    cast(units as integer)              as units,
    cast(unit_price as numeric(12, 2))  as unit_price,
    cast(discount_pct as numeric(5, 4)) as discount_pct,
    cast(material_cost as numeric(14, 2)) as material_cost,
    cast(shipping_cost as numeric(14, 2)) as shipping_cost
from {{ ref('raw_orders') }}
