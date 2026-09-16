import io
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from src.utils.database import get_connection


PURCHASE_ORDER_COUNT = 20_000
START_DATE = date(2023, 1, 1)
END_DATE = date(2026, 8, 31)
RANDOM_SEED = 42


def money(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def copy_buffer(rows):
    buffer = io.StringIO()

    for row in rows:
        buffer.write(
            "\t".join("\\N" if value is None else str(value) for value in row)
            + "\n"
        )

    buffer.seek(0)
    return buffer


def choose_status(age_days, lead_time_days):
    if age_days < lead_time_days:
        return random.choices(
            ["CREATED", "CONFIRMED", "CANCELLED"],
            weights=[40, 50, 10],
            k=1,
        )[0]

    if age_days < lead_time_days + 5:
        return random.choices(
            ["CONFIRMED", "PARTIALLY_RECEIVED", "RECEIVED", "CANCELLED"],
            weights=[15, 35, 35, 15],
            k=1,
        )[0]

    return random.choices(
        ["RECEIVED", "PARTIALLY_RECEIVED", "CONFIRMED", "CANCELLED"],
        weights=[75, 17, 5, 3],
        k=1,
    )[0]


def generate_purchase_orders():
    random.seed(RANDOM_SEED)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM purchase_orders;")
        po_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM purchase_order_items;")
        item_count = cursor.fetchone()[0]

        if po_count or item_count:
            print(
                f"purchase_orders contains {po_count} rows and "
                f"purchase_order_items contains {item_count} rows. "
                "No data inserted."
            )
            return

        cursor.execute("""
            SELECT supplier_id, rating, default_lead_time_days
            FROM suppliers
            WHERE is_active = TRUE
            ORDER BY supplier_id;
        """)
        suppliers = cursor.fetchall()

        cursor.execute("""
            SELECT warehouse_id
            FROM warehouses
            ORDER BY warehouse_id;
        """)
        warehouses = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT product_id, supplier_id, unit_cost
            FROM products
            WHERE is_active = TRUE
            ORDER BY product_id;
        """)
        products = cursor.fetchall()

        if not suppliers or not warehouses or not products:
            raise RuntimeError(
                "Active suppliers, warehouses, and products are required."
            )

        products_by_supplier = {}
        for product in products:
            products_by_supplier.setdefault(product[1], []).append(product)

        cursor.execute("SELECT nextval('public.purchase_orders_po_id_seq');")
        first_po_id = cursor.fetchone()[0]
        cursor.execute(
            "SELECT nextval('public.purchase_order_items_po_item_id_seq');"
        )
        first_item_id = cursor.fetchone()[0]

        po_rows = []
        item_rows = []

        for po_offset in range(PURCHASE_ORDER_COUNT):
            po_id = first_po_id + po_offset
            supplier_id, rating, lead_time_days = random.choice(suppliers)
            po_day = START_DATE + timedelta(
                days=random.randint(0, (END_DATE - START_DATE).days)
            )
            po_datetime = datetime.combine(
                po_day,
                time(random.randint(8, 17), random.randint(0, 59)),
            )
            age_days = (END_DATE - po_day).days
            status = choose_status(age_days, lead_time_days)

            expected_days = lead_time_days + random.randint(-1, 3)
            expected_datetime = po_datetime + timedelta(
                days=max(1, expected_days)
            )
            actual_datetime = None

            if status in ("RECEIVED", "PARTIALLY_RECEIVED"):
                actual_datetime = po_datetime + timedelta(
                    days=lead_time_days + random.randint(0, 4)
                )

            supplier_products = products_by_supplier.get(supplier_id, [])
            item_count = random.randint(2, 6)
            selected_products = []

            for _ in range(item_count):
                source_products = (
                    supplier_products
                    if supplier_products and random.random() < 0.80
                    else products
                )
                selected_products.append(random.choice(source_products))

            for item_offset, (product_id, product_supplier_id, base_cost) in enumerate(selected_products):
                ordered_quantity = random.randint(5, 80)
                if status == "RECEIVED":
                    received_quantity = ordered_quantity
                elif status == "PARTIALLY_RECEIVED":
                    received_quantity = random.randint(1, ordered_quantity - 1)
                else:
                    received_quantity = 0

                rating_value = Decimal(rating or 3)
                supplier_variation = Decimal("1.06") - (rating_value * Decimal("0.01"))
                supplier_variation += Decimal(str(random.uniform(-0.02, 0.02)))
                unit_cost = money(base_cost * supplier_variation)

                item_rows.append((
                    first_item_id + len(item_rows),
                    po_id,
                    product_id,
                    ordered_quantity,
                    received_quantity,
                    unit_cost,
                ))

            po_rows.append((
                po_id,
                supplier_id,
                random.choice(warehouses),
                po_datetime,
                expected_datetime,
                actual_datetime,
                status,
            ))

        cursor.copy_from(
            copy_buffer(po_rows),
            "purchase_orders",
            columns=(
                "po_id",
                "supplier_id",
                "warehouse_id",
                "po_date",
                "expected_delivery_date",
                "actual_delivery_date",
                "po_status",
            ),
            sep="\t",
            null="\\N",
        )
        cursor.copy_from(
            copy_buffer(item_rows),
            "purchase_order_items",
            columns=(
                "po_item_id",
                "po_id",
                "product_id",
                "ordered_quantity",
                "received_quantity",
                "unit_cost",
            ),
            sep="\t",
            null="\\N",
        )

        cursor.execute(
            "SELECT setval('public.purchase_orders_po_id_seq', %s, true);",
            (po_rows[-1][0],),
        )
        cursor.execute(
            "SELECT setval('public.purchase_order_items_po_item_id_seq', %s, true);",
            (item_rows[-1][0],),
        )
        connection.commit()
        print(
            f"Inserted {len(po_rows)} purchase orders and "
            f"{len(item_rows)} purchase order items."
        )
        print(f"PO date range: {START_DATE} to {END_DATE}")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_purchase_orders()