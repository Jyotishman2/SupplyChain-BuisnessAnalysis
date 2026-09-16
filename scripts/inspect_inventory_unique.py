from src.utils.database import get_connection


def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            conname,
            pg_get_constraintdef(oid)
        FROM pg_constraint
        WHERE conrelid = 'public.inventory'::regclass
        ORDER BY conname;
    """)

    rows = cur.fetchall()

    print("Inventory constraint definitions:\n")

    for name, definition in rows:
        print(f"- {name}: {definition}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()