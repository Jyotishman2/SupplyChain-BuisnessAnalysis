import io
import random
from datetime import datetime, timedelta

from src.utils.database import get_connection


RANDOM_SEED = 42
SNAPSHOT_DATE = datetime(2026, 9, 1, 12, 0)
DAMAGE_MOVEMENT_COUNT = 500
TRANSFER_PAIR_COUNT = 1_000
ADJUSTMENT_MOVEMENT_COUNT = 500

MOVEMENT_TYPES = {
    "PURCHASE_RECEIPT",
    "SALE",
    "RETURN",
    "TRANSFER_IN",
    "TRANSFER_OUT",
    "DAMAGE",
    "ADJUSTMENT",
}


def copy_buffer(rows):
    buffer = io.StringIO()

    for row in rows:
        buffer.write(
            "\t".join("\\N" if value is None else str(value) for value in row)
            + "\n"
        )

    buffer.seek(0)
    return buffer


def fetch_rows(connection, cursor_name, query):
    source_cursor = connection.cursor(name=cursor_name)
    source_cursor.itersize = 10_000
    source_cursor.execute(query)
    rows = []

    while True:
        batch = source_cursor.fetchmany(10_000)
        if not batch:
            break
        rows.extend(batch)

    source_cursor.close()
    return rows


def generate_inventory_movements():
    random.seed(RANDOM_SEED)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM inventory_movements;")
        existing_count = cursor.fetchone()[0]

        if existing_count:
            print(
                f"Inventory movements already contains {existing_count} rows. "
                "No data inserted."
            )
            return

        purchase_receipts = fetch_rows(connection, "movement_purchase_receipts", """
            SELECT po.warehouse_id,
                   poi.product_id,
                   poi.received_quantity,
                   COALESCE(po.actual_delivery_date, po.expected_delivery_date),
                   po.po_id,
                   poi.po_item_id
            FROM purchase_order_items poi
            JOIN purchase_orders po ON po.po_id = poi.po_id
            WHERE poi.received_quantity > 0
            ORDER BY poi.po_item_id;
        """)

        sales = fetch_rows(connection, "movement_sales", """
            SELECT o.warehouse_id,
                   oi.product_id,
                   oi.quantity,
                   o.order_date,
                   o.order_id,
                   oi.order_item_id
            FROM order_items oi
            JOIN orders o ON o.order_id = oi.order_id
                        WHERE o.order_status <> 'CANCELLED'
                            AND o.warehouse_id IS NOT NULL
            ORDER BY oi.order_item_id;
        """)

        returns = fetch_rows(connection, "movement_returns", """
            SELECT o.warehouse_id,
                   r.product_id,
                   r.return_quantity,
                   r.return_date,
                   r.return_id
            FROM returns r
            JOIN orders o ON o.order_id = r.order_id
            WHERE o.warehouse_id IS NOT NULL
            ORDER BY r.return_id;
        """)

        cursor.execute("""
            SELECT warehouse_id, product_id, closing_stock
            FROM inventory
                        WHERE snapshot_date = %s
              AND closing_stock >= 10
            ORDER BY inventory_id;
                """, (SNAPSHOT_DATE.date(),))
        inventory_candidates = cursor.fetchall()

        cursor.execute("""
            SELECT warehouse_id
            FROM warehouses
            ORDER BY warehouse_id;
        """)
        warehouse_ids = [row[0] for row in cursor.fetchall()]

        if not purchase_receipts or not sales or not returns:
            raise RuntimeError(
                "Purchase receipts, sales, and returns are required."
            )
        if len(inventory_candidates) < DAMAGE_MOVEMENT_COUNT + ADJUSTMENT_MOVEMENT_COUNT:
            raise RuntimeError("Not enough inventory candidates for derived events.")
        if len(inventory_candidates) < TRANSFER_PAIR_COUNT:
            raise RuntimeError("Not enough inventory candidates for transfers.")
        if len(warehouse_ids) < 2:
            raise RuntimeError("At least two warehouses are required for transfers.")

        cursor.execute(
            "SELECT nextval('public.inventory_movements_movement_id_seq');"
        )
        first_movement_id = cursor.fetchone()[0]
        movement_rows = []

        for warehouse_id, product_id, quantity, movement_date, po_id, po_item_id in purchase_receipts:
            movement_rows.append((
                first_movement_id + len(movement_rows),
                warehouse_id,
                product_id,
                "PURCHASE_RECEIPT",
                quantity,
                movement_date,
                f"PO-{po_id}-{po_item_id}",
            ))

        for warehouse_id, product_id, quantity, movement_date, order_id, order_item_id in sales:
            movement_rows.append((
                first_movement_id + len(movement_rows),
                warehouse_id,
                product_id,
                "SALE",
                quantity,
                movement_date,
                f"ORD-{order_id}-{order_item_id}",
            ))

        for warehouse_id, product_id, quantity, movement_date, return_id in returns:
            movement_rows.append((
                first_movement_id + len(movement_rows),
                warehouse_id,
                product_id,
                "RETURN",
                quantity,
                movement_date,
                f"RET-{return_id}",
            ))

        damage_candidates = random.sample(
            inventory_candidates,
            DAMAGE_MOVEMENT_COUNT,
        )
        for event_number, (warehouse_id, product_id, closing_stock) in enumerate(
            damage_candidates,
            start=1,
        ):
            quantity = random.randint(1, min(3, max(1, closing_stock // 20)))
            movement_rows.append((
                first_movement_id + len(movement_rows),
                warehouse_id,
                product_id,
                "DAMAGE",
                quantity,
                SNAPSHOT_DATE - timedelta(days=random.randint(0, 90)),
                f"DAMAGE-{event_number:06d}",
            ))

        transfer_candidates = random.sample(
            inventory_candidates,
            TRANSFER_PAIR_COUNT,
        )
        for event_number, (source_warehouse_id, product_id, closing_stock) in enumerate(
            transfer_candidates,
            start=1,
        ):
            destination_options = [
                warehouse_id
                for warehouse_id in warehouse_ids
                if warehouse_id != source_warehouse_id
            ]
            destination_warehouse_id = random.choice(destination_options)
            quantity = random.randint(1, min(10, max(1, closing_stock // 10)))
            movement_date = SNAPSHOT_DATE - timedelta(
                days=random.randint(0, 60),
                hours=random.randint(0, 12),
            )
            reference_id = f"TRANSFER-{event_number:06d}"

            movement_rows.append((
                first_movement_id + len(movement_rows),
                source_warehouse_id,
                product_id,
                "TRANSFER_OUT",
                quantity,
                movement_date,
                reference_id,
            ))
            movement_rows.append((
                first_movement_id + len(movement_rows),
                destination_warehouse_id,
                product_id,
                "TRANSFER_IN",
                quantity,
                movement_date,
                reference_id,
            ))

        adjustment_candidates = random.sample(
            inventory_candidates,
            ADJUSTMENT_MOVEMENT_COUNT,
        )
        for event_number, (warehouse_id, product_id, closing_stock) in enumerate(
            adjustment_candidates,
            start=1,
        ):
            quantity = random.randint(1, min(5, max(1, closing_stock // 15)))
            direction = random.choice(("IN", "OUT"))
            movement_rows.append((
                first_movement_id + len(movement_rows),
                warehouse_id,
                product_id,
                "ADJUSTMENT",
                quantity,
                SNAPSHOT_DATE - timedelta(days=random.randint(0, 30)),
                f"ADJ-{direction}-{event_number:06d}",
            ))

        invalid_types = [
            row for row in movement_rows if row[3] not in MOVEMENT_TYPES
        ]
        if invalid_types:
            raise RuntimeError("Generated an invalid movement type.")

        cursor.copy_from(
            copy_buffer(movement_rows),
            "inventory_movements",
            columns=(
                "movement_id",
                "warehouse_id",
                "product_id",
                "movement_type",
                "quantity",
                "movement_date",
                "reference_id",
            ),
            sep="\t",
            null="\\N",
        )
        cursor.execute(
            "SELECT setval('public.inventory_movements_movement_id_seq', %s, true);",
            (movement_rows[-1][0],),
        )
        connection.commit()
        print(f"Inserted {len(movement_rows)} inventory movements.")
        print("ADJUSTMENT direction is encoded by reference_id: ADJ-IN or ADJ-OUT.")
    except Exception:
        if not connection.closed:
            connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_inventory_movements()