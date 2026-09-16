import logging

from src.utils.database import get_connection


LOGGER = logging.getLogger(__name__)

REQUIRED_TABLES = (
    "categories",
    "suppliers",
    "warehouses",
    "products",
    "customers",
    "inventory",
    "orders",
    "order_items",
    "purchase_orders",
    "purchase_order_items",
    "shipments",
    "returns",
    "inventory_movements",
)

NON_EMPTY_TABLES = (
    "products",
    "inventory",
    "orders",
    "purchase_orders",
    "shipments",
    "returns",
    "inventory_movements",
)


def validate_source_database():
    LOGGER.info("[INFO] Connecting to source database")
    connection = get_connection()
    cursor = connection.cursor()

    try:
        LOGGER.info("[INFO] Checking required tables")
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = ANY(%s);
            """,
            (list(REQUIRED_TABLES),),
        )
        available_tables = {row[0] for row in cursor.fetchall()}
        missing_tables = sorted(set(REQUIRED_TABLES) - available_tables)
        if missing_tables:
            raise RuntimeError(
                "Required source tables are missing: "
                + ", ".join(missing_tables)
            )

        counts = {}
        for table_name in REQUIRED_TABLES:
            cursor.execute(
                f"SELECT COUNT(*) FROM public.{table_name};"
            )
            counts[table_name] = cursor.fetchone()[0]
            LOGGER.info(
                "[INFO] %s row count: %s",
                table_name,
                counts[table_name],
            )

        empty_tables = [
            table_name
            for table_name in NON_EMPTY_TABLES
            if counts[table_name] == 0
        ]
        if empty_tables:
            raise RuntimeError(
                "Critical source tables are empty: "
                + ", ".join(empty_tables)
            )

        LOGGER.info(
            "[INFO] Source validation passed; inventory_movements row count: %s",
            counts["inventory_movements"],
        )
        return counts
    finally:
        cursor.close()
        connection.close()
