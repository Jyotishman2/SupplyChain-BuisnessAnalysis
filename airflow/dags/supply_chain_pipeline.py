import logging
import os
import shlex
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.exceptions import AirflowException
from airflow.utils.timezone import utc


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(os.getenv("SUPPLY_CHAIN_PROJECT_ROOT", "/opt/airflow/project"))


@task(task_id="check_source_database", retries=2, retry_delay=timedelta(minutes=5), execution_timeout=timedelta(minutes=10))
def check_source_database():
    from src.pipeline.source_validation import validate_source_database

    return validate_source_database()


@task(task_id="validate_source_data", retries=1, retry_delay=timedelta(minutes=2), execution_timeout=timedelta(minutes=15))
def validate_source_data():
    from src.pipeline.data_quality import validate_source_data_quality

    validate_source_data_quality()


@task(task_id="run_spark_processing", retries=1, retry_delay=timedelta(minutes=5), execution_timeout=timedelta(hours=1))
def run_spark_processing():
    job_path = os.getenv("SPARK_JOB_PATH", "spark/jobs/inventory_processing.py")
    job_file = PROJECT_ROOT / job_path
    if not job_file.is_file():
        raise AirflowException(f"Spark job does not exist: {job_file}")

    submit_command = os.getenv(
        "SPARK_SUBMIT_COMMAND",
        "spark-submit --packages org.postgresql:postgresql:42.7.4",
    )
    command = shlex.split(submit_command) + [str(job_file)]
    LOGGER.info("[INFO] Running Spark job: %s", " ".join(command))
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


@task(task_id="load_spark_outputs", retries=1, retry_delay=timedelta(minutes=5), execution_timeout=timedelta(hours=1))
def load_spark_outputs():
    job_path = os.getenv(
        "SPARK_LOAD_JOB_PATH",
        "spark/jobs/load_inventory_outputs.py",
    )
    job_file = PROJECT_ROOT / job_path
    if not job_file.is_file():
        raise AirflowException(f"Spark output loader does not exist: {job_file}")

    submit_command = os.getenv(
        "SPARK_LOAD_SUBMIT_COMMAND",
        "spark-submit --packages org.postgresql:postgresql:42.7.4",
    )
    command = shlex.split(submit_command) + [str(job_file)]
    LOGGER.info("[INFO] Loading Spark outputs: %s", " ".join(command))
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


@task(task_id="run_dbt", retries=1, retry_delay=timedelta(minutes=5), execution_timeout=timedelta(hours=1))
def run_dbt():
    project_dir = os.getenv("DBT_PROJECT_DIR")
    if not project_dir:
        raise AirflowException(
            "dbt is not configured. Set DBT_PROJECT_DIR to an initialized dbt "
            "project before enabling run_dbt."
        )

    project_path = Path(project_dir)
    if not (project_path / "dbt_project.yml").is_file():
        raise AirflowException(f"dbt project does not exist: {project_path}")

    command_prefix = shlex.split(os.getenv("DBT_COMMAND", "dbt"))
    command = command_prefix + ["build", "--project-dir", str(project_path)]
    LOGGER.info("[INFO] Running dbt build for project: %s", project_path)
    subprocess.run(command, cwd=project_path, check=True)


@task(task_id="validate_analytics", retries=1, retry_delay=timedelta(minutes=2), execution_timeout=timedelta(minutes=15))
def validate_analytics():
    output_schema = os.getenv("ANALYTICAL_OUTPUT_SCHEMA", "analytics").strip()
    output_tables = [
        table.strip()
        for table in os.getenv("ANALYTICAL_OUTPUT_TABLES", "").split(",")
        if table.strip()
    ]
    if not output_tables:
        raise AirflowException(
            "Analytical outputs are not configured. Set ANALYTICAL_OUTPUT_TABLES "
            "after Spark and dbt models are implemented."
        )
    if not output_schema.replace("_", "").isalnum():
        raise AirflowException(f"Invalid analytical schema name: {output_schema}")

    from src.utils.database import get_connection

    connection = get_connection()
    cursor = connection.cursor()
    try:
        for table_name in output_tables:
            if not table_name.replace("_", "").isalnum():
                raise AirflowException(f"Invalid analytical table name: {table_name}")
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                );
                """,
                (output_schema, table_name),
            )
            if not cursor.fetchone()[0]:
                raise AirflowException(
                    f"Analytical output relation is missing: {output_schema}.{table_name}"
                )
            cursor.execute(f"SELECT COUNT(*) FROM {output_schema}.{table_name};")
            row_count = cursor.fetchone()[0]
            LOGGER.info("[INFO] %s.%s row count: %s", output_schema, table_name, row_count)
            if row_count == 0:
                raise AirflowException(
                    f"Analytical output relation is empty: {output_schema}.{table_name}"
                )
    finally:
        cursor.close()
        connection.close()


@dag(
    dag_id="supply_chain_pipeline",
    schedule="@daily",
    start_date=datetime(2026, 9, 15, tzinfo=utc),
    catchup=False,
    dagrun_timeout=timedelta(hours=3),
    default_args={"owner": "supply-chain", "depends_on_past": False},
    tags=["supply-chain", "supabase", "spark", "dbt"],
    description="Validate source data, then run Spark, dbt, and analytical checks.",
)
def supply_chain_pipeline():
    source_check = check_source_database()
    quality_check = validate_source_data()
    spark_processing = run_spark_processing()
    spark_load = load_spark_outputs()
    dbt_build = run_dbt()
    analytics_check = validate_analytics()

    source_check >> quality_check >> spark_processing >> spark_load >> dbt_build >> analytics_check


supply_chain_pipeline()
