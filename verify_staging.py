import os
import psycopg2

conn = psycopg2.connect(
    host=os.environ["SUPABASE_DB_HOST"],
    port=os.environ.get("SUPABASE_DB_PORT", "5432"),
    dbname=os.environ.get("SUPABASE_DB_NAME", "postgres"),
    user=os.environ["SUPABASE_DB_USER"],
    password=os.environ["SUPABASE_DB_PASSWORD"],
    sslmode=os.environ.get("SUPABASE_DB_SSLMODE", "require"),
)

cur = conn.cursor()

checks = [
    ("inventory_movements_processed",
     "SELECT COUNT(*) FROM analytics_staging.inventory_movements_processed"),

    ("inventory_daily_metrics",
     "SELECT COUNT(*) FROM analytics_staging.inventory_daily_metrics"),

    ("inventory_snapshot_enriched",
     "SELECT COUNT(*) FROM analytics_staging.inventory_snapshot_enriched"),

    ("source_inventory_movements",
     "SELECT COUNT(*) FROM public.inventory_movements"),

    ("temporary_load_tables",
     """
     SELECT COUNT(*)
     FROM information_schema.tables
     WHERE table_schema = 'analytics_staging'
       AND table_type = 'BASE TABLE'
       AND table_name LIKE '_load_%'
     """),
]

for name, sql in checks:
    cur.execute(sql)
    print(f"{name}: {cur.fetchone()[0]}")

cur.close()
conn.close()
