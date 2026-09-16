from src.utils.database import get_connection


def fetch_scalar(cursor, query):
    cursor.execute(query)
    return cursor.fetchone()[0]


def validate_inventory_movements():
    connection = get_connection()
    cursor = connection.cursor()
    failures = []

    try:
        total_count = fetch_scalar(
            cursor,
            "SELECT COUNT(*) FROM inventory_movements;",
        )
        if total_count == 0:
            failures.append("inventory_movements is empty")

        checks = {
            "duplicate movement ids": """
                SELECT COUNT(*)
                FROM (
                    SELECT movement_id
                    FROM inventory_movements
                    GROUP BY movement_id
                    HAVING COUNT(*) > 1
                ) duplicates;
            """,
            "null required values": """
                SELECT COUNT(*)
                FROM inventory_movements
                WHERE movement_id IS NULL
                   OR warehouse_id IS NULL
                   OR product_id IS NULL
                   OR movement_type IS NULL
                   OR quantity IS NULL
                   OR movement_date IS NULL;
            """,
            "invalid movement types": """
                SELECT COUNT(*)
                FROM inventory_movements
                WHERE movement_type NOT IN (
                    'PURCHASE_RECEIPT', 'SALE', 'RETURN',
                    'TRANSFER_IN', 'TRANSFER_OUT', 'DAMAGE', 'ADJUSTMENT'
                );
            """,
            "non-positive quantities": """
                SELECT COUNT(*)
                FROM inventory_movements
                WHERE quantity <= 0;
            """,
            "orphan warehouses": """
                SELECT COUNT(*)
                FROM inventory_movements movement
                LEFT JOIN warehouses warehouse
                    ON warehouse.warehouse_id = movement.warehouse_id
                WHERE warehouse.warehouse_id IS NULL;
            """,
            "orphan products": """
                SELECT COUNT(*)
                FROM inventory_movements movement
                LEFT JOIN products product
                    ON product.product_id = movement.product_id
                WHERE product.product_id IS NULL;
            """,
            "invalid purchase references": """
                SELECT COUNT(*)
                FROM inventory_movements movement
                LEFT JOIN purchase_order_items item
                    ON movement.reference_id ~ '^PO-[0-9]+-[0-9]+$'
                   AND item.po_item_id = split_part(movement.reference_id, '-', 3)::bigint
                LEFT JOIN purchase_orders purchase_order
                    ON purchase_order.po_id = split_part(movement.reference_id, '-', 2)::bigint
                WHERE movement.movement_type = 'PURCHASE_RECEIPT'
                  AND (
                      movement.reference_id !~ '^PO-[0-9]+-[0-9]+$'
                      OR item.po_id IS NULL
                      OR purchase_order.po_id IS NULL
                      OR item.po_id <> purchase_order.po_id
                      OR item.product_id <> movement.product_id
                      OR item.received_quantity <> movement.quantity
                      OR purchase_order.warehouse_id <> movement.warehouse_id
                  );
            """,
            "invalid sale references": """
                SELECT COUNT(*)
                FROM inventory_movements movement
                LEFT JOIN order_items item
                    ON movement.reference_id ~ '^ORD-[0-9]+-[0-9]+$'
                   AND item.order_item_id = split_part(movement.reference_id, '-', 3)::bigint
                LEFT JOIN orders customer_order
                    ON customer_order.order_id = split_part(movement.reference_id, '-', 2)::bigint
                WHERE movement.movement_type = 'SALE'
                  AND (
                      movement.reference_id !~ '^ORD-[0-9]+-[0-9]+$'
                      OR item.order_id IS NULL
                      OR customer_order.order_id IS NULL
                      OR item.order_id <> customer_order.order_id
                      OR item.product_id <> movement.product_id
                      OR item.quantity <> movement.quantity
                      OR customer_order.warehouse_id <> movement.warehouse_id
                  );
            """,
            "invalid return references": """
                SELECT COUNT(*)
                FROM inventory_movements movement
                LEFT JOIN returns returned
                    ON movement.reference_id ~ '^RET-[0-9]+$'
                   AND returned.return_id = split_part(movement.reference_id, '-', 2)::bigint
                LEFT JOIN orders customer_order
                    ON customer_order.order_id = returned.order_id
                WHERE movement.movement_type = 'RETURN'
                  AND (
                      movement.reference_id !~ '^RET-[0-9]+$'
                      OR returned.return_id IS NULL
                      OR customer_order.order_id IS NULL
                      OR returned.product_id <> movement.product_id
                      OR returned.return_quantity <> movement.quantity
                      OR customer_order.warehouse_id <> movement.warehouse_id
                  );
            """,
            "unpaired transfers": """
                SELECT COUNT(*)
                FROM (
                    SELECT reference_id
                    FROM inventory_movements
                    WHERE movement_type IN ('TRANSFER_IN', 'TRANSFER_OUT')
                    GROUP BY reference_id
                    HAVING COUNT(*) <> 2
                        OR COUNT(*) FILTER (WHERE movement_type = 'TRANSFER_IN') <> 1
                        OR COUNT(*) FILTER (WHERE movement_type = 'TRANSFER_OUT') <> 1
                        OR MIN(product_id) <> MAX(product_id)
                        OR MIN(quantity) <> MAX(quantity)
                        OR MIN(warehouse_id) = MAX(warehouse_id)
                ) invalid_transfers;
            """,
            "invalid adjustment references": """
                SELECT COUNT(*)
                FROM inventory_movements
                WHERE movement_type = 'ADJUSTMENT'
                  AND reference_id !~ '^ADJ-(IN|OUT)-[0-9]+$';
            """,
        }

        for label, query in checks.items():
            count = fetch_scalar(cursor, query)
            if count:
                failures.append(f"{label}: {count}")

        cursor.execute("""
            SELECT movement_type, COUNT(*)
            FROM inventory_movements
            GROUP BY movement_type
            ORDER BY movement_type;
        """)
        type_counts = cursor.fetchall()
        print(f"Validated {total_count} inventory movements.")
        for movement_type, count in type_counts:
            print(f"{movement_type}: {count}")

        if failures:
            raise RuntimeError("; ".join(failures))

        print("Inventory movement validation passed.")
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    validate_inventory_movements()