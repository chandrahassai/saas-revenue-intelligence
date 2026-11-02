"""Schedule the existing analytics build, checks, and documentation."""

from datetime import timedelta

import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator


DBT_EXECUTABLE = "/opt/airflow/venvs/dbt/bin/dbt"

DBT_ARGUMENTS = (
    "--project-dir /opt/project "
    "--profiles-dir /opt/dbt-profiles "
    "--target-path /opt/airflow/artifacts/target"
)

DBT_LOG_ARGUMENT = "--log-path /opt/airflow/state/dbt-logs"


with DAG(
    dag_id="saas_analytics_workflow",
    description=(
        "Build and test SaaS analytics, check dashboard pages, "
        "and generate dbt documentation."
    ),
    start_date=pendulum.datetime(
        2026,
        11,
        1,
        tz="America/Los_Angeles",
    ),
    schedule="0 8 * * *",
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=30),
    default_args={
        "owner": "sai",
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
        "execution_timeout": timedelta(minutes=10),
    },
    tags=["saas", "analytics", "dbt"],
) as dag:
    build_dbt = BashOperator(
        task_id="build_and_test_dbt",
        bash_command=(
            f"{DBT_EXECUTABLE} {DBT_LOG_ARGUMENT} "
            f"build {DBT_ARGUMENTS}"
        ),
        cwd="/opt/project",
        skip_on_exit_code=None,
        do_xcom_push=False,
    )

    check_dashboard = BashOperator(
        task_id="test_dashboard_pages",
        bash_command=(
            "/opt/airflow/venvs/dashboard/bin/python "
            "-m unittest discover "
            "-s /opt/project/dashboard/tests -v"
        ),
        cwd="/opt/project",
        skip_on_exit_code=None,
        do_xcom_push=False,
    )

    generate_docs = BashOperator(
        task_id="generate_dbt_documentation",
        bash_command=(
            f"{DBT_EXECUTABLE} {DBT_LOG_ARGUMENT} "
            f"docs generate {DBT_ARGUMENTS}"
        ),
        cwd="/opt/project",
        skip_on_exit_code=None,
        do_xcom_push=False,
    )

    build_dbt >> check_dashboard >> generate_docs