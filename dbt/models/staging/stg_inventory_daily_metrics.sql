select
    warehouse_id,
    warehouse_name,
    product_id,
    sku,
    product_name,
    category_id,
    category_name,
    movement_date,
    movement_year,
    movement_month,
    inbound_quantity,
    outbound_quantity,
    net_quantity,
    movement_count
from {{ source('analytics_staging', 'inventory_daily_metrics') }}
