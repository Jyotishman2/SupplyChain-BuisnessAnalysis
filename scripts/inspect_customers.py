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
          AND table_name = 'customers'
        ORDER BY ordinal_position;
    """)

    rows = cur.fetchall()

    print("Customers table structure:\n")

    for column_name, data_type, nullable in rows:
        print(
            f"- {column_name} | "
            f"{data_type} | "
            f"nullable={nullable}"
        )

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()