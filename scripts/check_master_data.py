from src.utils.database import get_connection


TABLES = [
    "categories",
    "suppliers",
    "warehouses",
]


def main():
    conn = get_connection()
    cur = conn.cursor()

    print("Supabase master data counts:\n")

    for table in TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"{table}: {count}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()