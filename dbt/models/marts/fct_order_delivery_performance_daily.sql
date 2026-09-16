select
    actual_delivery_date::date as delivery_date,
    count(*) as delivered_order_count,
    count(promised_delivery_date) as orders_with_promised_date,
    sum(case when actual_delivery_date <= promised_delivery_date then 1 else 0 end) as on_time_order_count,
    round(
        sum(case when actual_delivery_date <= promised_delivery_date then 1 else 0 end)::numeric
        / nullif(count(promised_delivery_date), 0),
        4
    ) as on_time_delivery_rate,
    round(avg(extract(epoch from (actual_delivery_date - order_date)) / 86400.0), 2) as average_order_cycle_days
from {{ source('public', 'orders') }}
where actual_delivery_date is not null
group by 1
