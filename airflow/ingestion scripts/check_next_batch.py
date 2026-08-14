"""
===============================================================================
Airflow Ingestion Pipeline
check_next_batch.py

Step 1 + 2 of the flow:

    • Check the latest batch already loaded into Snowflake
    • Determine the next expected batch date
===============================================================================
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from scripts.config import (
    SNOWFLAKE_CONN_ID,
    PIPELINE_RUN_AUDIT_TABLE,
    FIRST_BATCH_DATE,
)


def get_latest_loaded_batch_date() -> date | None:
    """
    Return the most recent batch_date with a SUCCESS entry in the
    pipeline run audit table, or None if no batch has ever loaded
    successfully.
    """

    hook = SnowflakeHook(snowflake_conn_id=SNOWFLAKE_CONN_ID)

    query = f"""
        SELECT MAX(BATCH_DATE)
        FROM {PIPELINE_RUN_AUDIT_TABLE}
        WHERE OVERALL_STATUS = 'SUCCESS'
    """

    records = hook.get_records(query)

    if not records or records[0][0] is None:
        return None

    latest = records[0][0]

    if isinstance(latest, datetime):
        return latest.date()

    return latest


def determine_next_batch_date(latest_batch_date: date | None) -> date:
    """
    Compute the next expected batch date.

    Business Rule
    -------------
    • If no batch has ever loaded, start from FIRST_BATCH_DATE.
    • Otherwise, the next expected batch is exactly one day after
      the latest successfully loaded batch.
    """

    if latest_batch_date is None:

        return date.fromisoformat(FIRST_BATCH_DATE)

    return latest_batch_date + timedelta(days=1)


# =====================================================================
# Airflow Task Callables
# =====================================================================

def task_get_latest_batch_date(**context) -> str:
    """
    PythonOperator callable. Returns an ISO date string via XCom.
    """

    latest = get_latest_loaded_batch_date()

    return latest.isoformat() if latest is not None else ""


def task_determine_next_batch_date(**context) -> str:
    """
    PythonOperator callable. Reads the previous task's XCom value and
    returns the next expected batch date as an ISO string.
    """

    ti = context["ti"]

    latest_str = ti.xcom_pull(task_ids="get_latest_loaded_batch")

    latest = date.fromisoformat(latest_str) if latest_str else None

    next_batch_date = determine_next_batch_date(latest)

    return next_batch_date.isoformat()
