from src.utils.database import get_connection


def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'inventory'
        ORDER BY ordinal_position;
    """)

    columns = cur.fetchall()

    print("Inventory table structure:\n")

    if not columns:
        print("Inventory table not found.")
    else:
        for column_name, data_type, is_nullable in columns:
            print(
                f"- {column_name} | "
                f"{data_type} | "
                f"nullable={is_nullable}"
            )

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()