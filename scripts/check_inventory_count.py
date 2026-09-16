from src.utils.database import get_connection


def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM inventory
        WHERE snapshot_date = %s;
    """, ("2026-09-01",))

    count = cur.fetchone()[0]

    print(f"Inventory rows: {count}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()