import logging

from src.utils.database import get_connection


LOGGER = logging.getLogger(__name__)


REFERENTIAL_INTEGRITY_CHECKS = {
    "products without categories": """
        SELECT COUNT(*) FROM products p
        LEFT JOIN categories c ON c.category_id = p.category_id
        WHERE c.category_id IS NULL;
    """,
    "inventory without products": """
        SELECT COUNT(*) FROM inventory i
        LEFT JOIN products p ON p.product_id = i.product_id
        WHERE p.product_id IS NULL;
    """,
    "inventory without warehouses": """
        SELECT COUNT(*) FROM inventory i
        LEFT JOIN warehouses w ON w.warehouse_id = i.warehouse_id
        WHERE w.warehouse_id IS NULL;
    """,
    "orders without customers": """
        SELECT COUNT(*) FROM orders o
        LEFT JOIN customers c ON c.customer_id = o.customer_id
        WHERE c.customer_id IS NULL;
    """,
    "order_items without orders": """
        SELECT COUNT(*) FROM order_items oi
        LEFT JOIN orders o ON o.order_id = oi.order_id
        WHERE o.order_id IS NULL;
    """,
    "order_items without products": """
        SELECT COUNT(*) FROM order_items oi
        LEFT JOIN products p ON p.product_id = oi.product_id
        WHERE p.product_id IS NULL;
    """,
    "purchase_order_items without purchase_orders": """
        SELECT COUNT(*) FROM purchase_order_items poi
        LEFT JOIN purchase_orders po ON po.po_id = poi.po_id
        WHERE po.po_id IS NULL;
    """,
    "shipments without orders": """
        SELECT COUNT(*) FROM shipments s
        LEFT JOIN orders o ON o.order_id = s.order_id
        WHERE o.order_id IS NULL;
    """,
    "returns without orders": """
        SELECT COUNT(*) FROM returns r
        LEFT JOIN orders o ON o.order_id = r.order_id
        WHERE o.order_id IS NULL;
    """,
    "inventory_movements without products": """
        SELECT COUNT(*) FROM inventory_movements im
        LEFT JOIN products p ON p.product_id = im.product_id
        WHERE p.product_id IS NULL;
    """,
    "inventory_movements without warehouses": """
        SELECT COUNT(*) FROM inventory_movements im
        LEFT JOIN warehouses w ON w.warehouse_id = im.warehouse_id
        WHERE w.warehouse_id IS NULL;
    """,
}

MOVEMENT_CHECKS = {
    "inventory movements with null required fields": """
        SELECT COUNT(*) FROM inventory_movements
        WHERE movement_id IS NULL OR warehouse_id IS NULL
           OR product_id IS NULL OR movement_type IS NULL
           OR quantity IS NULL OR movement_date IS NULL;
    """,
    "duplicate inventory movement ids": """
        SELECT COUNT(*) FROM (
            SELECT movement_id FROM inventory_movements
            GROUP BY movement_id HAVING COUNT(*) > 1
        ) duplicate_ids;
    """,
    "invalid inventory movement types": """
        SELECT COUNT(*) FROM inventory_movements
        WHERE movement_type NOT IN (
            'PURCHASE_RECEIPT', 'SALE', 'RETURN', 'TRANSFER_IN',
            'TRANSFER_OUT', 'DAMAGE', 'ADJUSTMENT'
        );
    """,
    "invalid inventory movement quantities": """
        SELECT COUNT(*) FROM inventory_movements WHERE quantity <= 0;
    """,
    "invalid inventory movement timestamps": """
        SELECT COUNT(*) FROM inventory_movements
        WHERE movement_date > CURRENT_TIMESTAMP;
    """,
}


def validate_source_data_quality():
    LOGGER.info("[INFO] Running referential-integrity checks")
    connection = get_connection()
    cursor = connection.cursor()
    failures = []

    try:
        for label, query in {
            **REFERENTIAL_INTEGRITY_CHECKS,
            **MOVEMENT_CHECKS,
        }.items():
            cursor.execute(query)
            count = cursor.fetchone()[0]
            LOGGER.info("[INFO] %s: %s", label, count)
            if count:
                failures.append(f"{label}: {count}")

        if failures:
            raise RuntimeError(
                "Source data-quality validation failed: "
                + "; ".join(failures)
            )

        LOGGER.info("[INFO] Source data-quality validation passed")
    finally:
        cursor.close()
        connection.close()
