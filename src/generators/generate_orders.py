import io
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from src.utils.database import get_connection


ORDER_COUNT = 100_000
START_DATE = date(2023, 1, 1)
END_DATE = date(2026, 8, 31)
RANDOM_SEED = 42

STATUS_VALUES = [
    "DELIVERED",
    "SHIPPED",
    "PROCESSING",
    "CONFIRMED",
    "PLACED",
    "CANCELLED",
    "RETURNED",
]
STATUS_WEIGHTS = [65, 12, 7, 6, 3, 5, 2]

PAYMENT_METHODS = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Net Banking",
    "Cash on Delivery",
    "Wallet",
]
PAYMENT_WEIGHTS = [35, 25, 15, 10, 8, 7]


def as_copy_buffer(rows):
    buffer = io.StringIO()

    for row in rows:
        buffer.write(
            "\t".join("\\N" if value is None else str(value) for value in row)
            + "\n"
        )

    buffer.seek(0)
    return buffer


def money(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_orders():
    random.seed(RANDOM_SEED)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM orders;")
        order_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM order_items;")
        item_count = cursor.fetchone()[0]

        if order_count or item_count:
            print(
                f"Orders table contains {order_count} rows and "
                f"order_items contains {item_count} rows. No data inserted."
            )
            return

        cursor.execute("""
            SELECT customer_id, city, state, signup_date
            FROM customers
            ORDER BY customer_id;
        """)
        customers = cursor.fetchall()

        cursor.execute("""
            SELECT product_id, selling_price
            FROM products
            WHERE is_active = TRUE
            ORDER BY product_id;
        """)
        products = cursor.fetchall()

        cursor.execute("""
            SELECT warehouse_id
            FROM warehouses
            ORDER BY warehouse_id;
        """)
        warehouses = [row[0] for row in cursor.fetchall()]

        if not customers or not products or not warehouses:
            raise RuntimeError(
                "Customers, active products, and warehouses are required."
            )

        cursor.execute("SELECT nextval('public.orders_order_id_seq');")
        first_order_id = cursor.fetchone()[0]

        order_rows = []
        item_rows = []
        next_item_id = None
        date_range = (END_DATE - START_DATE).days

        for order_offset in range(ORDER_COUNT):
            order_id = first_order_id + order_offset
            customer_id, city, state, signup_date = random.choice(customers)
            earliest_order_date = max(START_DATE, signup_date)
            order_day = earliest_order_date + timedelta(
                days=random.randint(0, (END_DATE - earliest_order_date).days)
            )
            order_datetime = datetime.combine(
                order_day,
                time(random.randint(8, 21), random.randint(0, 59)),
            )
            status = random.choices(
                STATUS_VALUES,
                weights=STATUS_WEIGHTS,
                k=1,
            )[0]
            promised_datetime = order_datetime + timedelta(
                days=random.randint(2, 7)
            )
            actual_datetime = None

            if status in ("DELIVERED", "RETURNED"):
                actual_datetime = order_datetime + timedelta(
                    days=random.randint(2, 9)
                )

            selected_products = random.sample(
                products,
                k=random.randint(1, min(5, len(products))),
            )
            order_value = Decimal("0.00")

            if next_item_id is None:
                cursor.execute(
                    "SELECT nextval('public.order_items_order_item_id_seq');"
                )
                next_item_id = cursor.fetchone()[0]

            for product_id, unit_price in selected_products:
                quantity = random.randint(1, 5)
                discount_rate = random.choices(
                    [Decimal("0.00"), Decimal("0.05"), Decimal("0.10"), Decimal("0.15")],
                    weights=[55, 25, 15, 5],
                    k=1,
                )[0]
                gross_amount = unit_price * quantity
                discount = money(gross_amount * discount_rate)
                total_amount = money(gross_amount - discount)
                order_value += total_amount

                item_rows.append((
                    next_item_id,
                    order_id,
                    product_id,
                    quantity,
                    money(unit_price),
                    discount,
                    total_amount,
                ))
                next_item_id += 1

            order_rows.append((
                order_id,
                customer_id,
                random.choice(warehouses),
                order_datetime,
                status,
                random.choices(
                    PAYMENT_METHODS,
                    weights=PAYMENT_WEIGHTS,
                    k=1,
                )[0],
                money(order_value),
                city,
                state,
                promised_datetime,
                actual_datetime,
            ))

        cursor.copy_from(
            as_copy_buffer(order_rows),
            "orders",
            columns=(
                "order_id",
                "customer_id",
                "warehouse_id",
                "order_date",
                "order_status",
                "payment_method",
                "order_value",
                "shipping_city",
                "shipping_state",
                "promised_delivery_date",
                "actual_delivery_date",
            ),
            sep="\t",
            null="\\N",
        )

        cursor.copy_from(
            as_copy_buffer(item_rows),
            "order_items",
            columns=(
                "order_item_id",
                "order_id",
                "product_id",
                "quantity",
                "unit_price",
                "discount",
                "total_amount",
            ),
            sep="\t",
            null="\\N",
        )

        cursor.execute(
            "SELECT setval('public.orders_order_id_seq', %s, true);",
            (order_rows[-1][0],),
        )
        cursor.execute(
            "SELECT setval('public.order_items_order_item_id_seq', %s, true);",
            (item_rows[-1][0],),
        )
        connection.commit()
        print(f"Inserted {len(order_rows)} orders and {len(item_rows)} order items.")
        print(f"Order date range: {START_DATE} to {END_DATE}")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_orders()