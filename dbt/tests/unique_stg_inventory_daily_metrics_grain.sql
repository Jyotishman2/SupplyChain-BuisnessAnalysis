select
    warehouse_id,
    product_id,
    movement_date
from {{ ref('stg_inventory_daily_metrics') }}
group by 1, 2, 3
having count(*) > 1
