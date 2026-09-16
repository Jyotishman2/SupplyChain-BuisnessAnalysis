# dbt analytics layer

This project reads the Spark-published `analytics_staging` relations and builds
lightweight PostgreSQL views in the `analytics` schema. Credentials are supplied
only through the existing `SUPABASE_DB_*` environment variables.

Implemented KPI interfaces:

- Stock-out rate
- Supplier delivery and receipt performance
- On-time delivery and order cycle time

Deferred pending authoritative source inputs:

- Inventory turnover: no historical average-inventory basis aligned to movement periods.
- Fill rate: no fulfilled or shipped line-item quantity.
- Carrying cost: no carrying-cost rate or policy.
- Forecast accuracy: no forecast dataset.
