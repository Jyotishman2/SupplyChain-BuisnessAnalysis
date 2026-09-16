from src.utils.database import get_connection


def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total_customers,
            COUNT(DISTINCT customer_id) AS unique_customers
        FROM customers;
    """)

    total, unique = cur.fetchone()

    print(f"Total customers: {total}")
    print(f"Unique customer IDs: {unique}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()