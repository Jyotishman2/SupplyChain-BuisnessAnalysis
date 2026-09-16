import io
import random
from datetime import date

from src.utils.database import get_connection


SNAPSHOT_DATE = date(2026, 9, 1)

random.seed(42)


def generate_inventory():

    connection = get_connection()
    cursor = connection.cursor()

    # Get products
    cursor.execute("""
        SELECT
            product_id,
            reorder_point,
            safety_stock
        FROM products
        WHERE is_active = TRUE
        ORDER BY product_id;
    """)

    products = cursor.fetchall()

    if not products:
        raise RuntimeError("No active products found.")

    # Get warehouses
    cursor.execute("""
        SELECT warehouse_id
        FROM warehouses
        ORDER BY warehouse_id;
    """)

    warehouses = cursor.fetchall()

    if not warehouses:
        raise RuntimeError("No warehouses found.")

    # Generate only records that don't already exist.
    cursor.execute("""
        SELECT warehouse_id, product_id
        FROM inventory
        WHERE snapshot_date = %s;
    """, (SNAPSHOT_DATE,))

    existing = set(cursor.fetchall())

    print(f"Existing records: {len(existing)}")

    rows = []

    for warehouse_id, in warehouses:

        for product_id, reorder_point, safety_stock in products:

            if (warehouse_id, product_id) in existing:
                continue

            opening_stock = random.randint(
                max(1, reorder_point),
                max(2, reorder_point * 6),
            )

            received_quantity = random.choices(
                [0, random.randint(20, 500)],
                weights=[25, 75],
                k=1,
            )[0]

            sold_quantity = random.randint(
                0,
                max(1, reorder_point // 2),
            )

            returned_quantity = random.choices(
                [0, random.randint(1, 20)],
                weights=[90, 10],
                k=1,
            )[0]

            adjustment_quantity = random.choices(
                [0, random.randint(-10, 10)],
                weights=[95, 5],
                k=1,
            )[0]

            closing_stock = max(
                0,
                opening_stock
                + received_quantity
                - sold_quantity
                + returned_quantity
                + adjustment_quantity,
            )

            reserved_quantity = random.randint(
                0,
                min(closing_stock, max(1, reorder_point)),
            )

            rows.append((
                warehouse_id,
                product_id,
                SNAPSHOT_DATE,
                opening_stock,
                received_quantity,
                sold_quantity,
                returned_quantity,
                adjustment_quantity,
                closing_stock,
                reserved_quantity,
            ))

    if not rows:
        print("No new inventory records to insert.")
        cursor.close()
        connection.close()
        return

    # Build CSV data in memory.
    buffer = io.StringIO()

    for row in rows:
        buffer.write(
            "\t".join(
                "\\N" if value is None else str(value)
                for value in row
            )
            + "\n"
        )

    buffer.seek(0)

    # Bulk load using PostgreSQL COPY.
    cursor.copy_from(
        buffer,
        "inventory",
        columns=(
            "warehouse_id",
            "product_id",
            "snapshot_date",
            "opening_stock",
            "received_quantity",
            "sold_quantity",
            "returned_quantity",
            "adjustment_quantity",
            "closing_stock",
            "reserved_quantity",
        ),
        sep="\t",
        null="\\N",
    )

    connection.commit()

    print(f"Inserted {len(rows)} new inventory records.")
    print(f"Snapshot date: {SNAPSHOT_DATE}")

    cursor.close()
    connection.close()


if __name__ == "__main__":
    generate_inventory()