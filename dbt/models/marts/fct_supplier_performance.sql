with purchase_order_items as (
    select
        po_id,
        sum(ordered_quantity) as ordered_quantity,
        sum(received_quantity) as received_quantity
    from {{ source('public', 'purchase_order_items') }}
    group by 1
)

select
    supplier.supplier_id,
    supplier.supplier_name,
    count(purchase_order.po_id) as purchase_order_count,
    count(purchase_order.actual_delivery_date) as delivered_purchase_order_count,
    sum(case when purchase_order.actual_delivery_date <= purchase_order.expected_delivery_date then 1 else 0 end) as on_time_purchase_order_count,
    round(
        sum(case when purchase_order.actual_delivery_date <= purchase_order.expected_delivery_date then 1 else 0 end)::numeric
        / nullif(count(purchase_order.actual_delivery_date), 0),
        4
    ) as on_time_delivery_rate,
    sum(coalesce(purchase_order_items.ordered_quantity, 0)) as ordered_units,
    sum(coalesce(purchase_order_items.received_quantity, 0)) as received_units,
    round(
        sum(coalesce(purchase_order_items.received_quantity, 0))::numeric
        / nullif(sum(coalesce(purchase_order_items.ordered_quantity, 0)), 0),
        4
    ) as receipt_fill_rate
from {{ source('public', 'suppliers') }} as supplier
left join {{ source('public', 'purchase_orders') }} as purchase_order
    on supplier.supplier_id = purchase_order.supplier_id
left join purchase_order_items
    on purchase_order.po_id = purchase_order_items.po_id
group by 1, 2
