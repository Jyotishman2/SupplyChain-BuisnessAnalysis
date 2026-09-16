# Supply Chain & Inventory Intelligence Platform

## Airflow orchestration

The `supply_chain_pipeline` DAG validates the existing Supabase/PostgreSQL
source data, runs source data-quality checks, invokes the inventory Spark job,
runs the future dbt project, and validates analytical outputs.

The source datasets are already complete. The DAG does not regenerate them.

### Local startup

1. Copy `.env.example` to `.env` and fill in the Supabase connection values.
2. Keep `.env` local; it is excluded by `.gitignore`.
3. Start Airflow with Docker Desktop (the Compose services pass the database
	environment variables into Airflow):

```powershell
docker-compose up --build
```

Open `http://localhost:8080` and sign in with the local Airflow credentials
from `.env`.

Trigger `supply_chain_pipeline` from the Airflow UI or with:

```powershell
docker-compose exec airflow-webserver airflow dags trigger supply_chain_pipeline
```

### DAG stages

1. `check_source_database` checks all required public tables and logs row counts.
2. `validate_source_data` checks source relationships and inventory movement quality.
3. `run_spark_processing` runs `spark/jobs/inventory_processing.py` with `spark-submit` and the PostgreSQL JDBC driver.
4. `load_spark_outputs` runs `spark/jobs/load_inventory_outputs.py`, validates the Parquet outputs, and atomically loads them into PostgreSQL.
5. `run_dbt` requires an initialized `DBT_PROJECT_DIR` and runs `dbt deps`, `seed`, `run`, and `test`.
6. `validate_analytics` requires comma-separated `ANALYTICAL_OUTPUT_TABLES` and verifies they exist and contain rows.

Spark inventory processing is implemented. dbt remains a configuration gate
until its project is initialized; it does not report success when its required
configuration is missing.

### Spark-to-PostgreSQL bridge

The loader creates the `analytics_staging` schema when needed and publishes:

- `analytics_staging.inventory_movements_processed`
- `analytics_staging.inventory_daily_metrics`
- `analytics_staging.inventory_snapshot_enriched`

Each run reads the Parquet outputs, validates schemas and duplicate keys, bulk
writes run-scoped temporary tables through Spark JDBC, validates PostgreSQL
types and representative rows, and swaps the temporary tables into place in a
single PostgreSQL transaction. Existing `public` source tables are not changed.

### Current limitations

- Airflow is provided for local Docker development; no deployment platform is configured.
- Spark currently processes inventory and inventory movements only; order and
	broader supply-chain jobs remain future extensions.
- Analytical output table names must be configured after those stages exist.
