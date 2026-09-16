import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    IntegerType,
    LongType,
    StringType,
    TimestampType,
)
from psycopg2 import sql

from src.utils.database import get_connection


LOGGER = logging.getLogger("load_inventory_outputs")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TARGET_SCHEMA = "analytics_staging"
OUTPUTS = {
    "inventory_movements_processed": {
        "path": "inventory_movements_processed",
        "keys": ("movement_id",),
        "columns": {
            "movement_id": LongType(), "movement_date": DateType(),
            "movement_timestamp": TimestampType(), "movement_year": IntegerType(),
            "movement_month": IntegerType(), "movement_week": IntegerType(),
            "movement_type": StringType(), "movement_direction": StringType(),
            "quantity": IntegerType(), "signed_quantity": IntegerType(),
            "reference_id": StringType(), "warehouse_id": LongType(),
            "warehouse_name": StringType(), "warehouse_city": StringType(),
            "warehouse_state": StringType(), "product_id": LongType(),
            "sku": StringType(), "product_name": StringType(),
            "category_id": LongType(), "category_name": StringType(),
        },
        "postgres_types": {
            "movement_id": "bigint", "movement_date": "date",
            "movement_timestamp": "timestamp without time zone",
            "movement_year": "integer", "movement_month": "integer",
            "movement_week": "integer", "movement_type": "text",
            "movement_direction": "text", "quantity": "integer",
            "signed_quantity": "integer", "reference_id": "text",
            "warehouse_id": "bigint", "warehouse_name": "text",
            "warehouse_city": "text", "warehouse_state": "text",
            "product_id": "bigint", "sku": "text", "product_name": "text",
            "category_id": "bigint", "category_name": "text",
        },
    },
    "inventory_daily_metrics": {
        "path": "inventory_daily_metrics",
        "keys": ("warehouse_id", "product_id", "movement_date"),
        "columns": {
            "warehouse_id": LongType(), "warehouse_name": StringType(),
            "product_id": LongType(), "sku": StringType(),
            "product_name": StringType(), "category_id": LongType(),
            "category_name": StringType(), "movement_date": DateType(),
            "movement_year": IntegerType(), "movement_month": IntegerType(),
            "inbound_quantity": LongType(), "outbound_quantity": LongType(),
            "net_quantity": LongType(), "movement_count": LongType(),
        },
        "postgres_types": {
            "warehouse_id": "bigint", "warehouse_name": "text",
            "product_id": "bigint", "sku": "text", "product_name": "text",
            "category_id": "bigint", "category_name": "text",
            "movement_date": "date", "movement_year": "integer",
            "movement_month": "integer", "inbound_quantity": "bigint",
            "outbound_quantity": "bigint", "net_quantity": "bigint",
            "movement_count": "bigint",
        },
    },
    "inventory_snapshot_enriched": {
        "path": "inventory_snapshot_enriched",
        "keys": ("inventory_id",),
        "columns": {
            "inventory_id": LongType(), "warehouse_id": LongType(),
            "product_id": LongType(), "snapshot_date": DateType(),
            "opening_stock": IntegerType(), "received_quantity": IntegerType(),
            "sold_quantity": IntegerType(), "returned_quantity": IntegerType(),
            "adjustment_quantity": IntegerType(), "closing_stock": IntegerType(),
            "reserved_quantity": IntegerType(), "sku": StringType(),
            "product_name": StringType(), "category_id": LongType(),
            "reorder_point": IntegerType(), "category_name": StringType(),
            "warehouse_name": StringType(), "warehouse_city": StringType(),
            "warehouse_state": StringType(), "snapshot_year": IntegerType(),
            "snapshot_month": IntegerType(), "available_stock": IntegerType(),
            "stock_status": StringType(),
        },
        "postgres_types": {
            "inventory_id": "bigint", "warehouse_id": "bigint",
            "product_id": "bigint", "snapshot_date": "date",
            "opening_stock": "integer", "received_quantity": "integer",
            "sold_quantity": "integer", "returned_quantity": "integer",
            "adjustment_quantity": "integer", "closing_stock": "integer",
            "reserved_quantity": "integer", "sku": "text",
            "product_name": "text", "category_id": "bigint",
            "reorder_point": "integer", "category_name": "text",
            "warehouse_name": "text", "warehouse_city": "text",
            "warehouse_state": "text", "snapshot_year": "integer",
            "snapshot_month": "integer", "available_stock": "integer",
            "stock_status": "text",
        },
    },
}

CONSTRAINTS = {
    "inventory_movements_processed": ("PRIMARY KEY", ("movement_id",)),
    "inventory_daily_metrics": (
        "PRIMARY KEY",
        ("warehouse_id", "product_id", "movement_date"),
    ),
    "inventory_snapshot_enriched": ("PRIMARY KEY", ("inventory_id",)),
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


def output_root():
    root = Path(os.getenv("SPARK_OUTPUT_PATH", "data/processed"))
    return root if root.is_absolute() else Path.cwd() / root


def validate_dataframe(name, dataframe, specification):
    expected_columns = specification["columns"]
    actual_columns = set(dataframe.columns)
    if actual_columns != set(expected_columns):
        missing = sorted(set(expected_columns) - actual_columns)
        extra = sorted(actual_columns - set(expected_columns))
        raise RuntimeError(f"{name} schema mismatch; missing={missing}, extra={extra}")

    actual_types = {field.name: field.dataType for field in dataframe.schema.fields}
    type_mismatches = {
        column: f"expected {expected.simpleString()}, got {actual_types[column].simpleString()}"
        for column, expected in expected_columns.items()
        if actual_types[column] != expected
    }
    if type_mismatches:
        raise RuntimeError(f"{name} data type mismatch: {type_mismatches}")

    row_count = dataframe.count()
    if row_count == 0:
        raise RuntimeError(f"{name} Parquet output is empty")
    key_columns = specification["keys"]
    null_key_condition = None
    for key_column in key_columns:
        condition = F.col(key_column).isNull()
        null_key_condition = (
            condition
            if null_key_condition is None
            else null_key_condition | condition
        )
    if dataframe.filter(null_key_condition).limit(1).count():
        key_label = ", ".join(key_columns)
        raise RuntimeError(f"{name} contains NULL key values for ({key_label})")

    duplicate_keys = dataframe.groupBy(*key_columns).count()
    if duplicate_keys.filter("count > 1").limit(1).count():
        key_label = ", ".join(specification["keys"])
        raise RuntimeError(f"{name} contains duplicate key values for ({key_label})")
    LOGGER.info("Validated %s Parquet rows: %s", name, row_count)
    return row_count


def create_schema():
    connection = get_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = 0")
                cursor.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}")
                    .format(sql.Identifier(TARGET_SCHEMA))
                )
    finally:
        connection.close()


def table_identifier(schema_name, table_name):
    return sql.Identifier(schema_name, table_name)


def validate_postgres_table(cursor, target_name, specification):
    cursor.execute(
        """
        SELECT column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
        """,
        (TARGET_SCHEMA, target_name),
    )
    rows = cursor.fetchall()
    actual_columns = {row[0] for row in rows}
    expected_columns = set(specification["postgres_types"])
    if actual_columns != expected_columns:
        raise RuntimeError(
            f"{TARGET_SCHEMA}.{target_name} PostgreSQL schema mismatch: "
            f"missing={sorted(expected_columns - actual_columns)}, "
            f"extra={sorted(actual_columns - expected_columns)}"
        )

    actual_types = {row[0]: (row[1], row[2]) for row in rows}
    for column, expected_type in specification["postgres_types"].items():
        data_type, udt_name = actual_types[column]
        if expected_type == "text":
            valid = data_type in ("text", "character varying")
        elif expected_type == "timestamp without time zone":
            valid = data_type == expected_type
        else:
            valid = data_type == expected_type
        if not valid:
            raise RuntimeError(
                f"{TARGET_SCHEMA}.{target_name}.{column} has type "
                f"{data_type}/{udt_name}, expected {expected_type}"
            )

    cursor.execute(
        sql.SQL("SELECT COUNT(*) FROM {}")
        .format(table_identifier(TARGET_SCHEMA, target_name))
    )
    row_count = cursor.fetchone()[0]
    if row_count == 0:
        raise RuntimeError(f"{TARGET_SCHEMA}.{target_name} is empty")

    key_columns = specification["keys"]
    null_key_predicate = sql.SQL(" OR ").join(
        sql.SQL("{} IS NULL").format(sql.Identifier(column))
        for column in key_columns
    )
    cursor.execute(
        sql.SQL("SELECT 1 FROM {} WHERE {} LIMIT 1").format(
            table_identifier(TARGET_SCHEMA, target_name),
            null_key_predicate,
        )
    )
    if cursor.fetchone() is not None:
        raise RuntimeError(f"{TARGET_SCHEMA}.{target_name} contains NULL key values")

    cursor.execute(
        sql.SQL("SELECT 1 FROM {} GROUP BY {} HAVING COUNT(*) > 1 LIMIT 1")
        .format(
            table_identifier(TARGET_SCHEMA, target_name),
            sql.SQL(", ").join(sql.Identifier(column) for column in key_columns),
        )
    )
    if cursor.fetchone() is not None:
        raise RuntimeError(f"{TARGET_SCHEMA}.{target_name} contains duplicate keys")

    constraint_kind, constraint_columns = CONSTRAINTS[target_name]
    cursor.execute(
        """
        SELECT constraint_type,
               array_agg(attribute.attname ORDER BY key_column.ordinality)
        FROM pg_constraint constraint_definition
        JOIN unnest(constraint_definition.conkey)
             WITH ORDINALITY AS key_column(attnum, ordinality) ON TRUE
        JOIN pg_attribute attribute
          ON attribute.attrelid = constraint_definition.conrelid
         AND attribute.attnum = key_column.attnum
        JOIN information_schema.table_constraints constraint_metadata
          ON constraint_metadata.constraint_name = constraint_definition.conname
         AND constraint_metadata.table_schema = %s
         AND constraint_metadata.table_name = %s
        WHERE constraint_definition.conrelid = %s::regclass
          AND constraint_definition.conname = %s
        GROUP BY constraint_type;
        """,
        (
            TARGET_SCHEMA,
            target_name,
            f"{TARGET_SCHEMA}.{target_name}",
            f"{target_name}_key",
        ),
    )
    constraint_row = cursor.fetchone()
    expected_constraint_type = "PRIMARY KEY" if constraint_kind == "PRIMARY KEY" else "UNIQUE"
    if constraint_row != (expected_constraint_type, list(constraint_columns)):
        raise RuntimeError(
            f"{TARGET_SCHEMA}.{target_name} key constraint does not match "
            f"{expected_constraint_type} ({', '.join(constraint_columns)})"
        )

    cursor.execute(
        sql.SQL("SELECT * FROM {} LIMIT 1")
        .format(table_identifier(TARGET_SCHEMA, target_name))
    )
    if cursor.fetchone() is None:
        raise RuntimeError(f"{TARGET_SCHEMA}.{target_name} representative query returned no row")
    LOGGER.info("Validated PostgreSQL target %s.%s rows: %s", TARGET_SCHEMA, target_name, row_count)


def cleanup_tables(table_names):
    connection = get_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = 0")
                for table_name in table_names:
                    cursor.execute(
                        sql.SQL("DROP TABLE IF EXISTS {}")
                        .format(table_identifier(TARGET_SCHEMA, table_name))
                    )
    except Exception:
        LOGGER.exception("Failed to clean up temporary Spark load tables")
    finally:
        connection.close()


def main():
    load_dotenv()
    jdbc_url, properties = jdbc_config()
    create_schema()
    run_id = uuid.uuid4().hex[:12]
    temporary_names = {
        target_name: f"_load_{target_name}_{run_id}"
        for target_name in OUTPUTS
    }
    spark = (
        SparkSession.builder
        .appName("LoadSupplyChainInventoryOutputs")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(os.getenv("SPARK_LOG_LEVEL", "WARN"))

    try:
        root = output_root()
        dataframes = {}
        for target_name, specification in OUTPUTS.items():
            parquet_path = root / specification["path"]
            if not parquet_path.is_dir():
                raise RuntimeError(f"Required Parquet output does not exist: {parquet_path}")
            LOGGER.info("Reading Parquet output: %s", parquet_path)
            dataframe = spark.read.parquet(str(parquet_path))
            validate_dataframe(target_name, dataframe, specification)
            dataframes[target_name] = dataframe

        LOGGER.info("Writing validated outputs to temporary PostgreSQL tables")
        for target_name, dataframe in dataframes.items():
            temporary_table = temporary_names[target_name]
            dataframe.write.mode("overwrite").option("batchsize", "10000").jdbc(
                url=jdbc_url,
                table=f"{TARGET_SCHEMA}.{temporary_table}",
                properties=properties,
            )

        connection = get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL statement_timeout = 0")
                    cursor.execute("SET LOCAL lock_timeout = '30s'")
                    for target_name, specification in OUTPUTS.items():
                        temporary_table = temporary_names[target_name]
                        cursor.execute(
                            sql.SQL("DROP TABLE IF EXISTS {}")
                            .format(table_identifier(TARGET_SCHEMA, target_name))
                        )
                        cursor.execute(
                            sql.SQL("ALTER TABLE {} RENAME TO {}")
                            .format(
                                table_identifier(TARGET_SCHEMA, temporary_table),
                                sql.Identifier(target_name),
                            )
                        )
                        constraint_kind, constraint_columns = CONSTRAINTS[target_name]
                        constraint_name = f"{target_name}_key"
                        cursor.execute(
                            sql.SQL("ALTER TABLE {} ADD CONSTRAINT {} {} ({})")
                            .format(
                                table_identifier(TARGET_SCHEMA, target_name),
                                sql.Identifier(constraint_name),
                                sql.SQL(constraint_kind),
                                sql.SQL(", ").join(
                                    sql.Identifier(column)
                                    for column in constraint_columns
                                ),
                            )
                        )
                    for target_name, specification in OUTPUTS.items():
                        validate_postgres_table(cursor, target_name, specification)
        finally:
            connection.close()

        LOGGER.info("Spark output load completed successfully")
    except Exception:
        cleanup_tables(temporary_names.values())
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
