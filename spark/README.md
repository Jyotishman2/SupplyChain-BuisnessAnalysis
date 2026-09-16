# Spark processing

`jobs/inventory_processing.py` is the first Spark processing job. It reads
`inventory`, `inventory_movements`, `products`, `warehouses`, and `categories`
from Supabase/PostgreSQL over JDBC, validates the source data, enriches
inventory movement records, and writes partitioned Parquet outputs.

Outputs are written to `data/processed/` by default:

- `inventory_movements_processed/`
- `inventory_daily_metrics/`
- `inventory_snapshot_enriched/`

## Local prerequisites

- Python 3.11
- Java 17 or a compatible Spark-supported Java runtime
- PySpark 3.5.3
- PostgreSQL JDBC driver `42.7.4`

The JDBC driver is supplied to `spark-submit` with `--packages` in the Airflow
configuration. Set the existing database environment variables before running.

```powershell
$env:SPARK_OUTPUT_PATH = 'data/processed'
spark-submit --packages org.postgresql:postgresql:42.7.4 `
  spark/jobs/inventory_processing.py
```

The job does not use `collect()` or Pandas for the main processing path.