
-- 1. Categories
CREATE TABLE IF NOT EXISTS categories (
    category_id BIGSERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL
);


-- 2. Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id BIGSERIAL PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    city VARCHAR(100),
    supplier_type VARCHAR(100),
    rating NUMERIC(3,2),
    default_lead_time_days INTEGER NOT NULL,
    payment_terms VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_supplier_rating
        CHECK (rating IS NULL OR rating BETWEEN 0 AND 5),

    CONSTRAINT chk_supplier_lead_time
        CHECK (default_lead_time_days >= 0)
);

-- 3. Warehouses

CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id BIGSERIAL PRIMARY KEY,
    warehouse_name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'India',
    warehouse_type VARCHAR(50),
    capacity_units BIGINT NOT NULL,
    operating_cost_per_day NUMERIC(12,2) NOT NULL,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    opened_at DATE,

    CONSTRAINT chk_warehouse_capacity
        CHECK (capacity_units >= 0),

    CONSTRAINT chk_operating_cost
        CHECK (operating_cost_per_day >= 0)
);



-- 4. Products


CREATE TABLE IF NOT EXISTS products (
    product_id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(255) NOT NULL,
    category_id BIGINT NOT NULL,
    brand VARCHAR(100),
    unit_cost NUMERIC(12,2) NOT NULL,
    selling_price NUMERIC(12,2) NOT NULL,
    weight_kg NUMERIC(10,2),
    reorder_point INTEGER NOT NULL DEFAULT 0,
    safety_stock INTEGER NOT NULL DEFAULT 0,
    supplier_id BIGINT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_category
        FOREIGN KEY (category_id)
        REFERENCES categories(category_id),

    CONSTRAINT fk_product_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id),

    CONSTRAINT chk_product_cost
        CHECK (unit_cost >= 0),

    CONSTRAINT chk_product_price
        CHECK (selling_price >= 0),

    CONSTRAINT chk_product_weight
        CHECK (weight_kg IS NULL OR weight_kg >= 0),

    CONSTRAINT chk_reorder_point
        CHECK (reorder_point >= 0),

    CONSTRAINT chk_safety_stock
        CHECK (safety_stock >= 0)
);



-- 5. Customers

CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGSERIAL PRIMARY KEY,
    customer_segment VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'India',
    signup_date DATE NOT NULL
);



-- 6. Orders

CREATE TABLE IF NOT EXISTS orders (
    order_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    warehouse_id BIGINT,
    order_date TIMESTAMP NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    payment_method VARCHAR(50),
    order_value NUMERIC(14,2) NOT NULL DEFAULT 0,
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    promised_delivery_date TIMESTAMP,
    actual_delivery_date TIMESTAMP,

    CONSTRAINT fk_order_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_order_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(warehouse_id),

    CONSTRAINT chk_order_value
        CHECK (order_value >= 0),

    CONSTRAINT chk_order_status
        CHECK (
            order_status IN (
                'PLACED',
                'CONFIRMED',
                'PROCESSING',
                'SHIPPED',
                'DELIVERED',
                'CANCELLED',
                'RETURNED'
            )
        )
);


-- 7. Order Items


CREATE TABLE IF NOT EXISTS order_items (
    order_item_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    discount NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_amount NUMERIC(14,2) NOT NULL,

    CONSTRAINT fk_order_item_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_order_item_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT chk_order_item_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_order_item_price
        CHECK (unit_price >= 0),

    CONSTRAINT chk_order_item_discount
        CHECK (discount >= 0),

    CONSTRAINT chk_order_item_total
        CHECK (total_amount >= 0)
);



-- 8. Purchase Orders


CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL,
    warehouse_id BIGINT NOT NULL,
    po_date TIMESTAMP NOT NULL,
    expected_delivery_date TIMESTAMP NOT NULL,
    actual_delivery_date TIMESTAMP,
    po_status VARCHAR(30) NOT NULL,

    CONSTRAINT fk_po_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id),

    CONSTRAINT fk_po_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(warehouse_id),

    CONSTRAINT chk_po_status
        CHECK (
            po_status IN (
                'CREATED',
                'CONFIRMED',
                'PARTIALLY_RECEIVED',
                'RECEIVED',
                'CANCELLED'
            )
        )
);



-- 9. Purchase Order Items


CREATE TABLE IF NOT EXISTS purchase_order_items (
    po_item_id BIGSERIAL PRIMARY KEY,
    po_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    ordered_quantity INTEGER NOT NULL,
    received_quantity INTEGER NOT NULL DEFAULT 0,
    unit_cost NUMERIC(12,2) NOT NULL,

    CONSTRAINT fk_po_item_po
        FOREIGN KEY (po_id)
        REFERENCES purchase_orders(po_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_po_item_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT chk_ordered_quantity
        CHECK (ordered_quantity > 0),

    CONSTRAINT chk_received_quantity
        CHECK (
            received_quantity >= 0
            AND received_quantity <= ordered_quantity
        ),

    CONSTRAINT chk_po_unit_cost
        CHECK (unit_cost >= 0)
);



-- 10. Inventory


CREATE TABLE IF NOT EXISTS inventory (
    inventory_id BIGSERIAL PRIMARY KEY,
    warehouse_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    snapshot_date DATE NOT NULL,
    opening_stock INTEGER NOT NULL DEFAULT 0,
    received_quantity INTEGER NOT NULL DEFAULT 0,
    sold_quantity INTEGER NOT NULL DEFAULT 0,
    returned_quantity INTEGER NOT NULL DEFAULT 0,
    adjustment_quantity INTEGER NOT NULL DEFAULT 0,
    closing_stock INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT fk_inventory_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(warehouse_id),

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT uq_inventory_snapshot
        UNIQUE (warehouse_id, product_id, snapshot_date),

    CONSTRAINT chk_inventory_opening
        CHECK (opening_stock >= 0),

    CONSTRAINT chk_inventory_received
        CHECK (received_quantity >= 0),

    CONSTRAINT chk_inventory_sold
        CHECK (sold_quantity >= 0),

    CONSTRAINT chk_inventory_returned
        CHECK (returned_quantity >= 0),

    CONSTRAINT chk_inventory_closing
        CHECK (closing_stock >= 0),

    CONSTRAINT chk_inventory_reserved
        CHECK (reserved_quantity >= 0)
);


-- 11. Inventory Movements

CREATE TABLE IF NOT EXISTS inventory_movements (
    movement_id BIGSERIAL PRIMARY KEY,
    warehouse_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    movement_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    movement_date TIMESTAMP NOT NULL,
    reference_id VARCHAR(100),

    CONSTRAINT fk_movement_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(warehouse_id),

    CONSTRAINT fk_movement_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT chk_movement_type
        CHECK (
            movement_type IN (
                'PURCHASE_RECEIPT',
                'SALE',
                'RETURN',
                'TRANSFER_IN',
                'TRANSFER_OUT',
                'DAMAGE',
                'ADJUSTMENT'
            )
        ),

    CONSTRAINT chk_movement_quantity
        CHECK (quantity > 0)
);



-- 12. Shipments


CREATE TABLE IF NOT EXISTS shipments (
    shipment_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    warehouse_id BIGINT NOT NULL,
    carrier VARCHAR(100),
    shipment_status VARCHAR(50) NOT NULL,
    shipped_at TIMESTAMP,
    estimated_delivery_date TIMESTAMP,
    actual_delivery_date TIMESTAMP,
    shipping_cost NUMERIC(12,2) NOT NULL DEFAULT 0,

    CONSTRAINT fk_shipment_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT fk_shipment_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(warehouse_id),

    CONSTRAINT chk_shipment_status
        CHECK (
            shipment_status IN (
                'CREATED',
                'PACKED',
                'SHIPPED',
                'IN_TRANSIT',
                'OUT_FOR_DELIVERY',
                'DELIVERED',
                'LOST',
                'CANCELLED'
            )
        ),

    CONSTRAINT chk_shipping_cost
        CHECK (shipping_cost >= 0)
);



-- 13. Returns

CREATE TABLE IF NOT EXISTS returns (
    return_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    order_item_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    return_date TIMESTAMP NOT NULL,
    return_quantity INTEGER NOT NULL,
    return_reason VARCHAR(100) NOT NULL,
    refund_amount NUMERIC(14,2) NOT NULL,
    return_status VARCHAR(50) NOT NULL,

    CONSTRAINT fk_return_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT fk_return_order_item
        FOREIGN KEY (order_item_id)
        REFERENCES order_items(order_item_id),

    CONSTRAINT fk_return_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT chk_return_quantity
        CHECK (return_quantity > 0),

    CONSTRAINT chk_refund_amount
        CHECK (refund_amount >= 0),

    CONSTRAINT chk_return_reason
        CHECK (
            return_reason IN (
                'DAMAGED',
                'DEFECTIVE',
                'WRONG_ITEM',
                'SIZE_ISSUE',
                'CUSTOMER_CHANGED_MIND',
                'LATE_DELIVERY',
                'NOT_AS_EXPECTED'
            )
        )
);


