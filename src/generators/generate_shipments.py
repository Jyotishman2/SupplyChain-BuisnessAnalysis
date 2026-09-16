import io
import random
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from src.utils.database import get_connection


RANDOM_SEED = 42

SHIPPED_STATUSES = {
    "SHIPPED",
    "IN_TRANSIT",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
    "LOST",
}
WAREHOUSE_FALLBACK_CARRIERS = [
    "Delhivery",
    "Blue Dart",
    "Ecom Express",
    "XpressBees",
    "DTDC",
    "Shadowfax",
]


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


def choose_open_status(order_status):
    if order_status == "SHIPPED":
        return random.choices(
            ["IN_TRANSIT", "SHIPPED", "LOST"],
            weights=[84, 14, 2],
            k=1,
        )[0]

    if order_status == "PROCESSING":
        return random.choices(
            ["PACKED", "CREATED", "SHIPPED"],
            weights=[50, 35, 15],
            k=1,
        )[0]

    if order_status == "CONFIRMED":
        return random.choices(
            ["CREATED", "PACKED", "SHIPPED"],
            weights=[60, 30, 10],
            k=1,
        )[0]

    return random.choices(
        ["CREATED", "PACKED", "SHIPPED"],
        weights=[75, 20, 5],
        k=1,
    )[0]


def generate_shipments():
    random.seed(RANDOM_SEED)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM shipments;")
        existing_count = cursor.fetchone()[0]

        if existing_count:
            print(
                f"Shipments table already contains {existing_count} rows. "
                "No data inserted."
            )
            return

        cursor.execute("""
            SELECT order_id, warehouse_id, order_status, order_date,
                   promised_delivery_date, actual_delivery_date, order_value
            FROM orders
            ORDER BY order_id;
        """)
        orders = cursor.fetchall()

        cursor.execute("""
            SELECT warehouse_id
            FROM warehouses
            ORDER BY warehouse_id;
        """)
        warehouses = [row[0] for row in cursor.fetchall()]

        if not orders or not warehouses:
            raise RuntimeError("Orders and warehouses are required.")

        cursor.execute("SELECT nextval('public.shipments_shipment_id_seq');")
        first_shipment_id = cursor.fetchone()[0]

        shipment_rows = []

        for offset, (
            order_id,
            order_warehouse_id,
            order_status,
            order_date,
            promised_delivery_date,
            order_actual_delivery_date,
            order_value,
        ) in enumerate(orders):
            shipment_id = first_shipment_id + offset
            warehouse_id = order_warehouse_id or random.choice(warehouses)
            carrier = random.choice(WAREHOUSE_FALLBACK_CARRIERS)

            if order_status == "CANCELLED":
                shipment_status = "CANCELLED"
            elif order_status in ("DELIVERED", "RETURNED"):
                shipment_status = "DELIVERED"
            else:
                shipment_status = choose_open_status(order_status)

            if shipment_status in SHIPPED_STATUSES:
                shipped_at = order_date + timedelta(
                    days=random.randint(0, 2),
                    hours=random.randint(1, 8),
                )
                if shipment_status == "DELIVERED" and order_actual_delivery_date:
                    latest_shipped_at = order_actual_delivery_date - timedelta(
                        hours=4
                    )
                    shipped_at = min(shipped_at, latest_shipped_at)
            else:
                shipped_at = None

            if shipped_at is not None:
                estimated_delivery_date = shipped_at + timedelta(
                    days=random.randint(2, 7)
                )
            else:
                estimated_delivery_date = order_date + timedelta(
                    days=random.randint(2, 7)
                )

            actual_delivery_date = None
            if shipment_status == "DELIVERED":
                actual_delivery_date = order_actual_delivery_date
                if actual_delivery_date < shipped_at:
                    actual_delivery_date = shipped_at + timedelta(hours=4)

            order_value_decimal = Decimal(str(order_value))
            distance_factor = Decimal(str(random.uniform(0.85, 1.20)))
            shipping_cost = money(
                (Decimal("40.00") + order_value_decimal * Decimal("0.0015"))
                * distance_factor
            )

            shipment_rows.append((
                shipment_id,
                order_id,
                warehouse_id,
                carrier,
                shipment_status,
                shipped_at,
                estimated_delivery_date,
                actual_delivery_date,
                shipping_cost,
            ))

        cursor.copy_from(
            copy_buffer(shipment_rows),
            "shipments",
            columns=(
                "shipment_id",
                "order_id",
                "warehouse_id",
                "carrier",
                "shipment_status",
                "shipped_at",
                "estimated_delivery_date",
                "actual_delivery_date",
                "shipping_cost",
            ),
            sep="\t",
            null="\\N",
        )

        cursor.execute(
            "SELECT setval('public.shipments_shipment_id_seq', %s, true);",
            (shipment_rows[-1][0],),
        )
        connection.commit()
        print(f"Inserted {len(shipment_rows)} shipments.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_shipments()