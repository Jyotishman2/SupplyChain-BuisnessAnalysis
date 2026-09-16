select
    snapshot_date,
    warehouse_id,
    warehouse_name,
    warehouse_city,
    warehouse_state,
    count(*) as inventory_positions,
    sum(case when stock_status = 'STOCK_OUT' then 1 else 0 end) as stockout_positions,
    round(
        sum(case when stock_status = 'STOCK_OUT' then 1 else 0 end)::numeric / nullif(count(*), 0),
        4
    ) as stockout_rate,
    sum(available_stock) as available_units
from {{ ref('stg_inventory_snapshot') }}
group by 1, 2, 3, 4, 5
