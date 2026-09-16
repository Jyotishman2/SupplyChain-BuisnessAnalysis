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

relations = [
    ("stg_inventory_movements",
     "SELECT COUNT(*) FROM analytics.stg_inventory_movements"),
    ("stg_inventory_daily_metrics",
     "SELECT COUNT(*) FROM analytics.stg_inventory_daily_metrics"),
    ("stg_inventory_snapshot",
     "SELECT COUNT(*) FROM analytics.stg_inventory_snapshot"),
    ("fct_inventory_stockout_daily",
     "SELECT COUNT(*) FROM analytics.fct_inventory_stockout_daily"),
    ("fct_supplier_performance",
     "SELECT COUNT(*) FROM analytics.fct_supplier_performance"),
    ("fct_order_delivery_performance_daily",
     "SELECT COUNT(*) FROM analytics.fct_order_delivery_performance_daily"),
]

print("=== ANALYTICS RELATION COUNTS ===")
for name, sql in relations:
    cur.execute(sql)
    print(f"{name}: {cur.fetchone()[0]}")

checks = [
    ("duplicate_stg_inventory_movements",
     """SELECT COUNT(*) FROM (
          SELECT movement_id
          FROM analytics.stg_inventory_movements
          GROUP BY movement_id
          HAVING COUNT(*) > 1
        ) x"""),

    ("duplicate_stg_inventory_daily_metrics",
     """SELECT COUNT(*) FROM (
          SELECT warehouse_id, product_id, movement_date
          FROM analytics.stg_inventory_daily_metrics
          GROUP BY warehouse_id, product_id, movement_date
          HAVING COUNT(*) > 1
        ) x"""),

    ("duplicate_stg_inventory_snapshot",
     """SELECT COUNT(*) FROM (
          SELECT inventory_id
          FROM analytics.stg_inventory_snapshot
          GROUP BY inventory_id
          HAVING COUNT(*) > 1
        ) x"""),

    ("duplicate_fct_supplier_performance",
     """SELECT COUNT(*) FROM (
          SELECT supplier_id
          FROM analytics.fct_supplier_performance
          GROUP BY supplier_id
          HAVING COUNT(*) > 1
        ) x"""),

    ("duplicate_fct_order_delivery_performance_daily",
     """SELECT COUNT(*) FROM (
          SELECT *
          FROM analytics.fct_order_delivery_performance_daily
        ) x"""),

    ("null_movement_id",
     "SELECT COUNT(*) FROM analytics.stg_inventory_movements WHERE movement_id IS NULL"),

    ("null_daily_keys",
     """SELECT COUNT(*) FROM analytics.stg_inventory_daily_metrics
        WHERE warehouse_id IS NULL
           OR product_id IS NULL
           OR movement_date IS NULL"""),

    ("null_snapshot_inventory_id",
     "SELECT COUNT(*) FROM analytics.stg_inventory_snapshot WHERE inventory_id IS NULL"),

    ("null_supplier_id",
     "SELECT COUNT(*) FROM analytics.fct_supplier_performance WHERE supplier_id IS NULL"),

    ("stockout_rate_out_of_range",
     """SELECT COUNT(*) FROM analytics.fct_inventory_stockout_daily
        WHERE stockout_rate < 0 OR stockout_rate > 1 OR stockout_rate IS NULL"""),

    ("signed_net_reconciliation_difference",
     """SELECT
          (SELECT COALESCE(SUM(signed_quantity),0)
           FROM analytics.stg_inventory_movements)
          -
          (SELECT COALESCE(SUM(net_quantity),0)
           FROM analytics.stg_inventory_daily_metrics)"""),
]

print()
print("=== ANALYTICS INTEGRITY CHECKS ===")
for name, sql in checks:
    cur.execute(sql)
    print(f"{name}: {cur.fetchone()[0]}")

print()
print("=== NON-EMPTY CHECKS ===")
for name, sql in relations:
    cur.execute(sql)
    count = cur.fetchone()[0]
    print(f"{name}: {'PASS' if count > 0 else 'FAIL'}")

cur.close()
conn.close()
