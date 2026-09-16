import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    IntegerType,
    LongType,
    StringType,
    TimestampType,
)


LOGGER = logging.getLogger("inventory_processing")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

MOVEMENT_TYPES = (
    "PURCHASE_RECEIPT",
    "SALE",
    "RETURN",
    "TRANSFER_IN",
    "TRANSFER_OUT",
    "DAMAGE",
    "ADJUSTMENT",
)
INBOUND_TYPES = ("PURCHASE_RECEIPT", "RETURN", "TRANSFER_IN")
OUTBOUND_TYPES = ("SALE", "DAMAGE", "TRANSFER_OUT")
REQUIRED_COLUMNS = {
    "inventory": {
        "inventory_id", "warehouse_id", "product_id", "snapshot_date",
        "opening_stock", "received_quantity", "sold_quantity",
        "returned_quantity", "adjustment_quantity", "closing_stock",
        "reserved_quantity",
    },
    "inventory_movements": {
        "movement_id", "warehouse_id", "product_id", "movement_type",
        "quantity", "movement_date", "reference_id",
    },
    "products": {"product_id", "product_name", "category_id", "sku", "reorder_point"},
    "warehouses": {"warehouse_id", "warehouse_name", "city", "state"},
    "categories": {"category_id", "category_name"},
}


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def jdbc_config():
    host = required_env("SUPABASE_DB_HOST")
    port = os.getenv("SUPABASE_DB_PORT", "5432")
    database = os.getenv("SUPABASE_DB_NAME", "postgres")
    user = required_env("SUPABASE_DB_USER")
    password = required_env("SUPABASE_DB_PASSWORD")

    return (
        f"jdbc:postgresql://{host}:{port}/{database}",
        {
            "user": user,
            "password": password,
            "driver": "org.postgresql.Driver",
            "fetchsize": "10000",
        },
    )


def read_table(spark, jdbc_url, properties, table_name):
    LOGGER.info("Reading source table: %s", table_name)
    return spark.read.jdbc(
        url=jdbc_url,
        table=f"public.{table_name}",
        properties=properties,
    )


def validate_schema(dataframes):
    for table_name, dataframe in dataframes.items():
        missing_columns = REQUIRED_COLUMNS[table_name] - set(dataframe.columns)
        if missing_columns:
            raise RuntimeError(
                f"{table_name} is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )


def standardize_sources(dataframes):
    inventory = dataframes["inventory"].select(
        F.col("inventory_id").cast(LongType()).alias("inventory_id"),
        F.col("warehouse_id").cast(LongType()).alias("warehouse_id"),
        F.col("product_id").cast(LongType()).alias("product_id"),
        F.col("snapshot_date").cast(DateType()).alias("snapshot_date"),
        *[
            F.col(column).cast(IntegerType()).alias(column)
            for column in (
                "opening_stock", "received_quantity", "sold_quantity",
                "returned_quantity", "adjustment_quantity", "closing_stock",
                "reserved_quantity",
            )
        ],
    )
    movements = dataframes["inventory_movements"].select(
        F.col("movement_id").cast(LongType()).alias("movement_id"),
        F.col("warehouse_id").cast(LongType()).alias("warehouse_id"),
        F.col("product_id").cast(LongType()).alias("product_id"),
        F.col("movement_type").cast(StringType()).alias("movement_type"),
        F.col("quantity").cast(IntegerType()).alias("quantity"),
        F.col("movement_date").cast(TimestampType()).alias("movement_timestamp"),
        F.col("reference_id").cast(StringType()).alias("reference_id"),
    )
    products = dataframes["products"].select(
        F.col("product_id").cast(LongType()).alias("product_id"),
        F.col("sku").cast(StringType()).alias("sku"),
        F.col("product_name").cast(StringType()).alias("product_name"),
        F.col("category_id").cast(LongType()).alias("category_id"),
        F.col("reorder_point").cast(IntegerType()).alias("reorder_point"),
    )
    warehouses = dataframes["warehouses"].select(
        F.col("warehouse_id").cast(LongType()).alias("warehouse_id"),
        F.col("warehouse_name").cast(StringType()).alias("warehouse_name"),
        F.col("city").cast(StringType()).alias("warehouse_city"),
        F.col("state").cast(StringType()).alias("warehouse_state"),
    )
    categories = dataframes["categories"].select(
        F.col("category_id").cast(LongType()).alias("category_id"),
        F.col("category_name").cast(StringType()).alias("category_name"),
    )
    return inventory, movements, products, warehouses, categories


def validate_movements(movements, products, warehouses):
    required_nulls = movements.filter(
        F.col("movement_id").isNull()
        | F.col("warehouse_id").isNull()
        | F.col("product_id").isNull()
        | F.col("movement_type").isNull()
        | F.col("quantity").isNull()
        | F.col("movement_timestamp").isNull()
    ).limit(1).count()
    if required_nulls:
        raise RuntimeError("Inventory movements contain NULL required fields")

    if movements.filter(~F.col("movement_type").isin(*MOVEMENT_TYPES)).limit(1).count():
        raise RuntimeError("Inventory movements contain invalid movement types")
    if movements.filter(F.col("quantity") <= 0).limit(1).count():
        raise RuntimeError("Inventory movements contain non-positive quantities")
    if movements.filter(F.col("movement_timestamp") > F.current_timestamp()).limit(1).count():
        raise RuntimeError("Inventory movements contain future timestamps")
    if movements.groupBy("movement_id").count().filter(F.col("count") > 1).limit(1).count():
        raise RuntimeError("Inventory movements contain duplicate movement IDs")
    if movements.join(products.select("product_id"), "product_id", "left_anti").limit(1).count():
        raise RuntimeError("Inventory movements contain invalid product IDs")
    if movements.join(warehouses.select("warehouse_id"), "warehouse_id", "left_anti").limit(1).count():
        raise RuntimeError("Inventory movements contain invalid warehouse IDs")


def build_movement_output(movements, products, warehouses, categories):
    enriched = (
        movements.join(products, "product_id", "left")
        .join(categories, "category_id", "left")
        .join(warehouses, "warehouse_id", "left")
        .withColumn("movement_date", F.to_date("movement_timestamp"))
        .withColumn("movement_year", F.year("movement_timestamp"))
        .withColumn("movement_month", F.month("movement_timestamp"))
        .withColumn("movement_week", F.weekofyear("movement_timestamp"))
        .withColumn(
            "movement_direction",
            F.when(F.col("movement_type").isin(*INBOUND_TYPES), F.lit("inbound"))
            .when(F.col("movement_type").isin(*OUTBOUND_TYPES), F.lit("outbound"))
            .otherwise(F.lit("adjustment")),
        )
        .withColumn(
            "signed_quantity",
            F.when(F.col("movement_type").isin(*INBOUND_TYPES), F.col("quantity"))
            .when(F.col("movement_type").isin(*OUTBOUND_TYPES), -F.col("quantity"))
            .otherwise(F.lit(0)),
        )
    )
    return enriched.select(
        "movement_id", "movement_date", "movement_timestamp", "movement_year",
        "movement_month", "movement_week", "movement_type", "movement_direction",
        "quantity", "signed_quantity", "reference_id", "warehouse_id",
        "warehouse_name", "warehouse_city", "warehouse_state", "product_id",
        "sku", "product_name", "category_id", "category_name",
    )


def build_daily_output(enriched_movements):
    return (
        enriched_movements.groupBy(
            "warehouse_id", "warehouse_name", "product_id", "sku",
            "product_name", "category_id", "category_name", "movement_date",
            "movement_year", "movement_month",
        )
        .agg(
            F.sum(F.when(F.col("movement_direction") == "inbound", F.col("quantity")).otherwise(0)).alias("inbound_quantity"),
            F.sum(F.when(F.col("movement_direction") == "outbound", F.col("quantity")).otherwise(0)).alias("outbound_quantity"),
            F.sum("signed_quantity").alias("net_quantity"),
            F.count("movement_id").alias("movement_count"),
        )
    )


def build_inventory_output(inventory, products, warehouses, categories):
    return (
        inventory.join(products, "product_id", "left")
        .join(categories, "category_id", "left")
        .join(warehouses, "warehouse_id", "left")
        .withColumn("snapshot_year", F.year("snapshot_date"))
        .withColumn("snapshot_month", F.month("snapshot_date"))
        .withColumn(
            "available_stock",
            F.col("closing_stock") - F.col("reserved_quantity"),
        )
        .withColumn(
            "stock_status",
            F.when(F.col("available_stock") <= 0, F.lit("STOCK_OUT"))
            .when(F.col("available_stock") <= F.col("reorder_point"), F.lit("REORDER"))
            .otherwise(F.lit("HEALTHY")),
        )
    )


def validate_output(dataframe, name, required_columns):
    missing_columns = set(required_columns) - set(dataframe.columns)
    if missing_columns:
        raise RuntimeError(
            f"{name} output is missing columns: " + ", ".join(sorted(missing_columns))
        )
    if dataframe.limit(1).count() == 0:
        raise RuntimeError(f"{name} output is unexpectedly empty")


def main():
    load_dotenv()
    output_root = Path(os.getenv("SPARK_OUTPUT_PATH", "data/processed"))
    if not output_root.is_absolute():
        output_root = Path.cwd() / output_root

    LOGGER.info("Starting inventory Spark job")
    LOGGER.info("Output root: %s", output_root)
    jdbc_url, properties = jdbc_config()
    spark = (
        SparkSession.builder
        .appName("SupplyChainInventoryProcessing")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(os.getenv("SPARK_LOG_LEVEL", "WARN"))

    try:
        table_names = ("inventory", "inventory_movements", "products", "warehouses", "categories")
        dataframes = {
            table_name: read_table(spark, jdbc_url, properties, table_name)
            for table_name in table_names
        }
        validate_schema(dataframes)
        inventory, movements, products, warehouses, categories = standardize_sources(dataframes)
        LOGGER.info("Rows read from inventory_movements: %s", movements.count())
        validate_movements(movements, products, warehouses)

        enriched_movements = build_movement_output(
            movements, products, warehouses, categories
        )
        daily_metrics = build_daily_output(enriched_movements)
        inventory_snapshot = build_inventory_output(
            inventory, products, warehouses, categories
        )
        validate_output(
            enriched_movements,
            "inventory_movements_processed",
            ("movement_id", "movement_date", "signed_quantity", "category_id"),
        )
        validate_output(
            daily_metrics,
            "inventory_daily_metrics",
            ("movement_date", "inbound_quantity", "outbound_quantity", "net_quantity"),
        )
        validate_output(
            inventory_snapshot,
            "inventory_snapshot_enriched",
            ("snapshot_date", "closing_stock", "available_stock", "stock_status"),
        )

        output_root.mkdir(parents=True, exist_ok=True)
        LOGGER.info("Writing processed inventory data")
        enriched_movements.write.mode("overwrite").partitionBy(
            "movement_year", "movement_month"
        ).parquet(str(output_root / "inventory_movements_processed"))
        daily_metrics.write.mode("overwrite").partitionBy(
            "movement_year", "movement_month"
        ).parquet(str(output_root / "inventory_daily_metrics"))
        inventory_snapshot.write.mode("overwrite").partitionBy(
            "snapshot_year", "snapshot_month"
        ).parquet(str(output_root / "inventory_snapshot_enriched"))

        LOGGER.info("Rows written: inventory movements=%s", enriched_movements.count())
        LOGGER.info("Rows written: daily metrics=%s", daily_metrics.count())
        LOGGER.info("Rows written: inventory snapshots=%s", inventory_snapshot.count())
        LOGGER.info("Validation: PASSED")
        LOGGER.info("Spark job completed successfully")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()