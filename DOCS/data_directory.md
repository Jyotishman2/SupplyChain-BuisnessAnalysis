# Supply Chain & Inventory Intelligence Platform
# Data Dictionary

## 1. Overview

This document defines the data model for the NexaMart Supply Chain
& Inventory Intelligence Platform.

The model covers:

- Products
- Categories
- Suppliers
- Warehouses
- Customers
- Orders
- Order Items
- Purchase Orders
- Purchase Order Items
- Inventory
- Inventory Movements
- Shipments
- Returns

---

# 2. Entity Relationship Overview

Customers
    |
    v
Orders -----> Order Items <----- Products
    |                              |
    v                              |
Shipments                          |
    |                              |
    v                              |
Deliveries                         |
                                   |
Warehouses <---- Inventory --------+
    |
    v
Inventory Movements

Suppliers
    |
    v
Purchase Orders -----> Purchase Order Items <----- Products


# 3. Products

## Table: products

Stores information about products sold by NexaMart.

| Column | Data Type | Key | Description |
|---|---|---|---|
| product_id | BIGINT | PK | Unique product identifier |
| sku | VARCHAR(50) | UNIQUE | Stock keeping unit |
| product_name | VARCHAR(255) | | Product name |
| category_id | BIGINT | FK | Product category |
| brand | VARCHAR(100) | | Product brand |
| unit_cost | DECIMAL(12,2) | | Cost paid to supplier |
| selling_price | DECIMAL(12,2) | | Customer selling price |
| weight_kg | DECIMAL(10,2) | | Product weight |
| reorder_point | INT | | Inventory level triggering reorder |
| safety_stock | INT | | Minimum buffer inventory |
| supplier_id | BIGINT | FK | Primary supplier |
| is_active | BOOLEAN | | Whether product is currently sold |
| created_at | TIMESTAMP | | Product creation timestamp |


# 4. Categories

## Table: categories

Groups products into business categories.

| Column | Data Type | Key | Description |
|---|---|---|---|
| category_id | BIGINT | PK | Unique category ID |
| category_name | VARCHAR(100) | UNIQUE | Category name |
| department | VARCHAR(100) | | Higher-level department |


# 5. Suppliers

## Table: suppliers

Stores supplier information and expected performance characteristics.

| Column | Data Type | Key | Description |
|---|---|---|---|
| supplier_id | BIGINT | PK | Unique supplier ID |
| supplier_name | VARCHAR(255) | | Supplier name |
| country | VARCHAR(100) | | Supplier country |
| state | VARCHAR(100) | | Supplier state |
| city | VARCHAR(100) | | Supplier city |
| supplier_type | VARCHAR(100) | | Supplier classification |
| rating | DECIMAL(3,2) | | Supplier rating |
| default_lead_time_days | INT | | Expected delivery lead time |
| payment_terms | VARCHAR(50) | | Payment terms |
| is_active | BOOLEAN | | Supplier active status |
| created_at | TIMESTAMP | | Supplier creation timestamp |


# 6. Warehouses

## Table: warehouses

Stores information about fulfillment and storage facilities.

| Column | Data Type | Key | Description |
|---|---|---|---|
| warehouse_id | BIGINT | PK | Unique warehouse ID |
| warehouse_name | VARCHAR(255) | | Warehouse name |
| city | VARCHAR(100) | | Warehouse city |
| state | VARCHAR(100) | | Warehouse state |
| country | VARCHAR(100) | | Warehouse country |
| warehouse_type | VARCHAR(50) | | Warehouse classification |
| capacity_units | BIGINT | | Maximum inventory capacity |
| operating_cost_per_day | DECIMAL(12,2) | | Daily operating cost |
| latitude | DECIMAL(9,6) | | Geographic latitude |
| longitude | DECIMAL(9,6) | | Geographic longitude |
| opened_at | DATE | | Warehouse opening date |


# 7. Customers

## Table: customers

Stores non-sensitive customer information needed for analytics.

| Column | Data Type | Key | Description |
|---|---|---|---|
| customer_id | BIGINT | PK | Unique customer ID |
| customer_segment | VARCHAR(50) | | Customer classification |
| city | VARCHAR(100) | | Customer city |
| state | VARCHAR(100) | | Customer state |
| country | VARCHAR(100) | | Customer country |
| signup_date | DATE | | Customer registration date |


# 8. Orders

## Table: orders

Represents customer orders.

| Column | Data Type | Key | Description |
|---|---|---|---|
| order_id | BIGINT | PK | Unique order ID |
| customer_id | BIGINT | FK | Customer placing order |
| warehouse_id | BIGINT | FK | Warehouse fulfilling order |
| order_date | TIMESTAMP | | Order creation time |
| order_status | VARCHAR(30) | | Current order status |
| payment_method | VARCHAR(50) | | Payment method |
| order_value | DECIMAL(14,2) | | Total order value |
| shipping_city | VARCHAR(100) | | Delivery city |
| shipping_state | VARCHAR(100) | | Delivery state |
| promised_delivery_date | TIMESTAMP | | Expected delivery time |
| actual_delivery_date | TIMESTAMP | | Actual delivery time |


# 9. Order Items

## Table: order_items

Stores individual products contained within an order.

| Column | Data Type | Key | Description |
|---|---|---|---|
| order_item_id | BIGINT | PK | Unique order-item ID |
| order_id | BIGINT | FK | Parent order |
| product_id | BIGINT | FK | Ordered product |
| quantity | INT | | Quantity ordered |
| unit_price | DECIMAL(12,2) | | Selling price at order time |
| discount | DECIMAL(12,2) | | Discount amount |
| total_amount | DECIMAL(14,2) | | Final item amount |


# 10. Purchase Orders

## Table: purchase_orders

Represents orders placed with suppliers.

| Column | Data Type | Key | Description |
|---|---|---|---|
| po_id | BIGINT | PK | Unique purchase order ID |
| supplier_id | BIGINT | FK | Supplier |
| warehouse_id | BIGINT | FK | Receiving warehouse |
| po_date | TIMESTAMP | | Purchase order creation time |
| expected_delivery_date | TIMESTAMP | | Expected supplier delivery |
| actual_delivery_date | TIMESTAMP | | Actual delivery |
| po_status | VARCHAR(30) | | Purchase order status |


# 11. Purchase Order Items

## Table: purchase_order_items

Stores products and quantities ordered from suppliers.

| Column | Data Type | Key | Description |
|---|---|---|---|
| po_item_id | BIGINT | PK | Unique PO-item ID |
| po_id | BIGINT | FK | Parent purchase order |
| product_id | BIGINT | FK | Purchased product |
| ordered_quantity | INT | | Quantity ordered |
| received_quantity | INT | | Quantity received |
| unit_cost | DECIMAL(12,2) | | Supplier cost per unit |


# 12. Inventory

## Table: inventory

Stores inventory snapshots for products at warehouses.

Grain:

One row = one product at one warehouse on one date.

| Column | Data Type | Key | Description |
|---|---|---|---|
| inventory_id | BIGINT | PK | Unique inventory record |
| warehouse_id | BIGINT | FK | Warehouse |
| product_id | BIGINT | FK | Product |
| snapshot_date | DATE | | Inventory snapshot date |
| opening_stock | INT | | Stock at beginning of day |
| received_quantity | INT | | Quantity received |
| sold_quantity | INT | | Quantity sold |
| returned_quantity | INT | | Quantity returned |
| adjustment_quantity | INT | | Manual/system adjustment |
| closing_stock | INT | | Stock at end of day |
| reserved_quantity | INT | | Stock reserved for orders |


## Inventory Calculation

closing_stock should approximately follow:

opening_stock
+ received_quantity
+ returned_quantity
+ adjustment_quantity
- sold_quantity
= closing_stock


# 13. Inventory Movements

## Table: inventory_movements

Records individual inventory transactions.

| Column | Data Type | Key | Description |
|---|---|---|---|
| movement_id | BIGINT | PK | Unique movement ID |
| warehouse_id | BIGINT | FK | Warehouse |
| product_id | BIGINT | FK | Product |
| movement_type | VARCHAR(50) | | Type of inventory movement |
| quantity | INT | | Movement quantity |
| movement_date | TIMESTAMP | | Movement timestamp |
| reference_id | VARCHAR(100) | | Related order/PO/transfer ID |


## Movement Types

- PURCHASE_RECEIPT
- SALE
- RETURN
- TRANSFER_IN
- TRANSFER_OUT
- DAMAGE
- ADJUSTMENT


# 14. Shipments

## Table: shipments

Tracks the transportation of customer orders.

| Column | Data Type | Key | Description |
|---|---|---|---|
| shipment_id | BIGINT | PK | Unique shipment ID |
| order_id | BIGINT | FK | Customer order |
| warehouse_id | BIGINT | FK | Shipping warehouse |
| carrier | VARCHAR(100) | | Logistics carrier |
| shipment_status | VARCHAR(50) | | Shipment status |
| shipped_at | TIMESTAMP | | Shipment dispatch time |
| estimated_delivery_date | TIMESTAMP | | Estimated arrival |
| actual_delivery_date | TIMESTAMP | | Actual arrival |
| shipping_cost | DECIMAL(12,2) | | Shipping cost |


# 15. Returns

## Table: returns

Stores customer product returns.

| Column | Data Type | Key | Description |
|---|---|---|---|
| return_id | BIGINT | PK | Unique return ID |
| order_id | BIGINT | FK | Related customer order |
| order_item_id | BIGINT | FK | Related order item |
| product_id | BIGINT | FK | Returned product |
| return_date | TIMESTAMP | | Return date |
| return_quantity | INT | | Quantity returned |
| return_reason | VARCHAR(100) | | Reason for return |
| refund_amount | DECIMAL(14,2) | | Refunded amount |
| return_status | VARCHAR(50) | | Return processing status |


# 16. Status Values

## Order Status

- PLACED
- CONFIRMED
- PROCESSING
- SHIPPED
- DELIVERED
- CANCELLED
- RETURNED

## Shipment Status

- CREATED
- PACKED
- SHIPPED
- IN_TRANSIT
- OUT_FOR_DELIVERY
- DELIVERED
- LOST
- CANCELLED

## Purchase Order Status

- CREATED
- CONFIRMED
- PARTIALLY_RECEIVED
- RECEIVED
- CANCELLED


# 17. Return Reasons

- DAMAGED
- DEFECTIVE
- WRONG_ITEM
- SIZE_ISSUE
- CUSTOMER_CHANGED_MIND
- LATE_DELIVERY
- NOT_AS_EXPECTED


# 18. Important Relationships

products.category_id
    -> categories.category_id

products.supplier_id
    -> suppliers.supplier_id

orders.customer_id
    -> customers.customer_id

orders.warehouse_id
    -> warehouses.warehouse_id

order_items.order_id
    -> orders.order_id

order_items.product_id
    -> products.product_id

purchase_orders.supplier_id
    -> suppliers.supplier_id

purchase_orders.warehouse_id
    -> warehouses.warehouse_id

purchase_order_items.po_id
    -> purchase_orders.po_id

purchase_order_items.product_id
    -> products.product_id

inventory.warehouse_id
    -> warehouses.warehouse_id

inventory.product_id
    -> products.product_id

inventory_movements.warehouse_id
    -> warehouses.warehouse_id

inventory_movements.product_id
    -> products.product_id

shipments.order_id
    -> orders.order_id

shipments.warehouse_id
    -> warehouses.warehouse_id

returns.order_id
    -> orders.order_id

returns.order_item_id
    -> order_items.order_item_id

returns.product_id
    -> products.product_id