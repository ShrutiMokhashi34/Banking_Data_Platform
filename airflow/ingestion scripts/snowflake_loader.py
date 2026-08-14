"""
===============================================================================
Airflow Ingestion Pipeline
snowflake_loader.py

Step 4 of the flow: load each CSV for the batch into its Snowflake
staging table.

Loading strategy
-----------------
COPY INTO is run with MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE, so each
source CSV column is matched to the target table column with the same
name (via the CSV's header row). This is more resilient than a plain
positional COPY INTO:

    * Extra source columns not present in the target are ignored.
    * Extra target columns not present in the source are left NULL.

It does NOT fix columns that are simply named differently on each side
(e.g. TRANSACTION_CHANNEL vs CHANNEL) - see the note left in the DAG /
README for the specific mismatches found in the current DDLs.

Because MATCH_BY_COLUMN_NAME reads columns straight off the file, the
audit columns (BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE) that don't
exist in the source CSVs can't be injected in the same COPY INTO
statement. They're backfilled with a follow-up UPDATE, scoped to the
rows this run just inserted (identified by BATCH_DATE IS NULL).

Every file load attempt - regardless of outcome - is also recorded as
its own row in FILE_LOAD_AUDIT (comprehensive per-file audit trail).
The validation step (validation.py) later updates that same row with
its data-quality findings.
"""

from __future__ import annotations

from datetime import datetime

from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from scripts.config import (
    SNOWFLAKE_CONN_ID,
    SNOWFLAKE_STAGE,
    SNOWFLAKE_FILE_FORMAT,
    TABLE_FILE_MAP,
    DATA_SOURCE_LABEL,
    FILE_LOAD_AUDIT_TABLE,
    qualified_table,
    dated_file_name,
)

# Column names in COPY INTO's result set (order is fixed by Snowflake).
_COPY_RESULT_COLUMNS = [
    "file",
    "status",
    "rows_parsed",
    "rows_loaded",
    "error_limit",
    "errors_seen",
    "first_error",
    "first_error_line",
    "first_error_character",
    "first_error_column_name",
]


def _record_file_load_audit(
    hook: SnowflakeHook,
    pipeline_run_id: str,
    batch_date: str,
    file_name: str,
    table_name: str,
    result: dict,
    load_started_at: datetime,
    load_ended_at: datetime,
) -> None:
    """
    Insert one row into FILE_LOAD_AUDIT for this file's load attempt.

    VALIDATION_STATUS / VALIDATION_DETAILS are left NULL here - the
    validation step (validation.py) updates this same row once it has
    run the richer data-quality checks.
    """

    insert_sql = f"""
        INSERT INTO {FILE_LOAD_AUDIT_TABLE}
            (PIPELINE_RUN_ID, BATCH_DATE, FILE_NAME, TABLE_NAME,
             ROWS_PARSED, ROWS_LOADED, ERRORS_SEEN, COPY_STATUS,
             LOAD_STARTED_AT, LOAD_ENDED_AT)
        VALUES
            ('{pipeline_run_id}', '{batch_date}', '{file_name}', '{table_name}',
             {result['rows_parsed']}, {result['rows_loaded']}, {result['errors_seen']},
             '{result['status']}',
             '{load_started_at.isoformat()}', '{load_ended_at.isoformat()}')
    """

    hook.run(insert_sql)


def _copy_into_table(
    hook: SnowflakeHook,
    file_name: str,
    table_name: str,
    batch_date: str,
    pipeline_run_id: str,
) -> dict:
    """
    Run COPY INTO for a single file/table pair, record the attempt in
    FILE_LOAD_AUDIT, and return a parsed result summary.
    """

    target_table = qualified_table(table_name)

    actual_file_name = dated_file_name(file_name, batch_date)

    load_started_at = datetime.utcnow()

    copy_sql = f"""
        COPY INTO {target_table}
        FROM @{SNOWFLAKE_STAGE}/{batch_date}/
        FILES = ('{actual_file_name}')
        FILE_FORMAT = (FORMAT_NAME = '{SNOWFLAKE_FILE_FORMAT}')
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
        ON_ERROR = 'CONTINUE'
    """

    rows = hook.get_records(copy_sql)

    if not rows:

        result = {
            "table": table_name,
            "file": file_name,
            "rows_loaded": 0,
            "rows_parsed": 0,
            "errors_seen": 0,
            "status": "NO_FILE_MATCHED",
        }

        _record_file_load_audit(
            hook, pipeline_run_id, batch_date, actual_file_name, table_name,
            result, load_started_at, datetime.utcnow(),
        )

        return result

    # A file can be split into multiple parts by Snowflake; sum across
    # all result rows for this file.
    total_rows_loaded = 0

    total_rows_parsed = 0

    total_errors_seen = 0

    statuses = []

    for row in rows:

        record = dict(zip(_COPY_RESULT_COLUMNS, row))

        total_rows_loaded += record.get("rows_loaded") or 0

        total_rows_parsed += record.get("rows_parsed") or 0

        total_errors_seen += record.get("errors_seen") or 0

        statuses.append(record.get("status"))

    overall_status = (
        "LOADED"
        if all(status == "LOADED" for status in statuses)
        else "PARTIALLY_LOADED_OR_FAILED"
    )

    # Backfill audit columns on the business table for the rows this
    # COPY just inserted.
    if total_rows_loaded > 0:

        update_sql = f"""
            UPDATE {target_table}
            SET BATCH_DATE = '{batch_date}',
                PIPELINE_RUN_ID = '{pipeline_run_id}',
                DATA_SOURCE = '{DATA_SOURCE_LABEL}'
            WHERE BATCH_DATE IS NULL
        """

        hook.run(update_sql)

    result = {
        "table": table_name,
        "file": file_name,
        "rows_loaded": total_rows_loaded,
        "rows_parsed": total_rows_parsed,
        "errors_seen": total_errors_seen,
        "status": overall_status,
    }

    _record_file_load_audit(
        hook, pipeline_run_id, batch_date, actual_file_name, table_name,
        result, load_started_at, datetime.utcnow(),
    )

    return result


def load_batch_to_staging(
    batch_date: str,
    pipeline_run_id: str,
) -> dict:
    """
    Load every file for the given batch date into its staging table.

    Returns
    -------
    Dict keyed by table name -> load result summary (see
    `_copy_into_table`).
    """

    hook = SnowflakeHook(snowflake_conn_id=SNOWFLAKE_CONN_ID)

    # Diagnostic: log exactly what Airflow authenticated as, right
    # before the loads that have been failing on integration
    # authorization. Temporary - safe to remove once the mismatch is
    # found (search for "DIAGNOSTIC" to find/remove this block).
    identity = hook.get_first(
        "SELECT CURRENT_ROLE(), CURRENT_ACCOUNT(), CURRENT_WAREHOUSE(), "
        "CURRENT_DATABASE(), CURRENT_SCHEMA()"
    )

    hook.log.info(
        "DIAGNOSTIC - connected as role=%s account=%s warehouse=%s "
        "database=%s schema=%s",
        *identity,
    )

    load_results = {}

    for file_name, table_name in TABLE_FILE_MAP.items():

        result = _copy_into_table(
            hook,
            file_name,
            table_name,
            batch_date,
            pipeline_run_id,
        )

        load_results[table_name] = result

    return load_results


# =====================================================================
# Airflow Task Callable
# =====================================================================

def task_load_to_staging(**context) -> dict:
    """
    PythonOperator callable. Loads the batch and returns per-table
    results via XCom for the validation step.
    """

    ti = context["ti"]

    batch_date = ti.xcom_pull(task_ids="determine_next_batch_date")

    return load_batch_to_staging(
        batch_date,
        pipeline_run_id=context["run_id"],
    )