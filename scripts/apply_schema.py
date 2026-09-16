from pathlib import Path

from src.utils.database import get_connection


def main():
    schema_path = Path("sql/schema.sql")

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema_sql = schema_path.read_text(encoding="utf-8")

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)

        conn.commit()
        print("Schema successfully applied to Supabase.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()