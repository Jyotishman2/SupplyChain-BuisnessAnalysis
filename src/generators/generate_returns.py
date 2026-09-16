import io
import random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from src.utils.database import get_connection


RANDOM_SEED = 42
RETURN_CUTOFF = datetime(2026, 9, 13, 23, 59)
BASE_RETURN_RATE = 0.07

RETURN_REASONS = [
    "DAMAGED",
    "DEFECTIVE",
    "WRONG_ITEM",
    "SIZE_ISSUE",
    "CUSTOMER_CHANGED_MIND",
    "LATE_DELIVERY",
    "NOT_AS_EXPECTED",
]
RETURN_REASON_WEIGHTS = [
    18,
    18,
    10,
    16,
    15,
    8,
    15,
]
RETURN_STATUSES = ["COMPLETED", "APPROVED", "PENDING"]
RETURN_STATUS_WEIGHTS = [70, 20, 10]

CATEGORY_RISK = {
    "Footwear": 1.35,
    "Beauty": 1.20,
    "Clothing": 1.30,
    "Cameras": 1.15,
    "Audio": 1.15,
    "Furniture": 0.85,
    "Beverages": 0.70,
    "Grocery": 0.65,
}
SEGMENT_RISK = {
    "VIP": 1.15,
    "Premium": 1.08,
    "Regular": 1.00,
}


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


def generate_returns():
    random.seed(RANDOM_SEED)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM returns;")
        existing_count = cursor.fetchone()[0]

        if existing_count:
            print(
                f"Returns table already contains {existing_count} rows. "
                "No data inserted."
            )
            return

        cursor.execute("""
            SELECT
                o.order_id,
                o.order_date,
                o.actual_delivery_date,
                c.customer_segment,
                oi.order_item_id,
                oi.product_id,
                oi.quantity,
                oi.unit_price,
                oi.discount,
                oi.total_amount,
                cat.category_name
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            JOIN order_items oi ON oi.order_id = o.order_id
            JOIN products p ON p.product_id = oi.product_id
            JOIN categories cat ON cat.category_id = p.category_id
            WHERE o.order_status = 'DELIVERED'
              AND o.actual_delivery_date IS NOT NULL
            ORDER BY o.order_id, oi.order_item_id;
        """)
        item_rows = cursor.fetchall()

        cursor.execute("SELECT nextval('public.returns_return_id_seq');")
        first_return_id = cursor.fetchone()[0]

        items_by_order = {}
        for row in item_rows:
            items_by_order.setdefault(row[0], []).append(row)

        return_rows = []

        for order_items in items_by_order.values():
            order_id, order_date, delivery_date, customer_segment = order_items[0][:4]
            max_item_risk = max(
                CATEGORY_RISK.get(item[10], 1.0)
                for item in order_items
            )
            segment_risk = SEGMENT_RISK.get(customer_segment, 1.0)
            return_probability = min(
                0.15,
                BASE_RETURN_RATE * (0.75 + max_item_risk * 0.25) * segment_risk,
            )

            if random.random() >= return_probability:
                continue

            selected_item = random.choices(
                order_items,
                weights=[
                    CATEGORY_RISK.get(item[10], 1.0) * item[6]
                    for item in order_items
                ],
                k=1,
            )[0]
            (
                _order_id,
                _order_date,
                _delivery_date,
                _customer_segment,
                order_item_id,
                product_id,
                purchased_quantity,
                unit_price,
                discount,
                total_amount,
                category_name,
            ) = selected_item

            max_return_days = (RETURN_CUTOFF.date() - delivery_date.date()).days
            return_delay_days = random.randint(1, min(30, max_return_days))
            return_date = delivery_date + timedelta(
                days=return_delay_days,
                hours=random.randint(1, 10),
            )
            return_date = min(return_date, RETURN_CUTOFF)
            return_quantity = random.choices(
                range(1, purchased_quantity + 1),
                weights=[
                    60 if quantity == 1 else 40
                    for quantity in range(1, purchased_quantity + 1)
                ],
                k=1,
            )[0]
            return_reason = random.choices(
                RETURN_REASONS,
                weights=RETURN_REASON_WEIGHTS,
                k=1,
            )[0]
            return_status = random.choices(
                RETURN_STATUSES,
                weights=RETURN_STATUS_WEIGHTS,
                k=1,
            )[0]
            refund_amount = money(
                (total_amount / purchased_quantity) * return_quantity
            )

            return_rows.append((
                first_return_id + len(return_rows),
                order_id,
                order_item_id,
                product_id,
                return_date,
                return_quantity,
                return_reason,
                refund_amount,
                return_status,
            ))

        if not return_rows:
            raise RuntimeError("No returns were generated.")

        cursor.copy_from(
            copy_buffer(return_rows),
            "returns",
            columns=(
                "return_id",
                "order_id",
                "order_item_id",
                "product_id",
                "return_date",
                "return_quantity",
                "return_reason",
                "refund_amount",
                "return_status",
            ),
            sep="\t",
            null="\\N",
        )
        cursor.execute(
            "SELECT setval('public.returns_return_id_seq', %s, true);",
            (return_rows[-1][0],),
        )
        connection.commit()
        print(f"Inserted {len(return_rows)} returns.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_returns()