from src.utils.database import get_connection


def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)

    tables = cur.fetchall()

    print("Tables in Supabase:\n")

    if not tables:
        print("No tables found.")
    else:
        for table in tables:
            print(f"- {table[0]}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()