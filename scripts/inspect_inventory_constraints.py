from src.utils.database import get_connection


def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name
        FROM information_schema.table_constraints AS tc
        LEFT JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public'
          AND tc.table_name = 'inventory'
        ORDER BY tc.constraint_name, kcu.ordinal_position;
    """)

    rows = cur.fetchall()

    print("Inventory constraints:\n")

    for constraint_name, constraint_type, column_name in rows:
        print(
            f"- {constraint_name} | "
            f"{constraint_type} | "
            f"{column_name}"
        )

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()