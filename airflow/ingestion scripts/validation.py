"""
===============================================================================
Airflow Ingestion Pipeline
validation.py

Step 5 of the flow: validate load counts - and more.

Beyond trusting COPY INTO's own report, each table (per its metadata
in pipeline_config.yaml) gets:

    1. Row-count reconciliation - actual COUNT(*) for the batch in the
       target table vs. what COPY INTO said it loaded.
    2. Duplicate primary-key check - across the table's primary_key
       (or composite key) columns, scoped to this batch.
    3. Required-column null check - any configured required_columns
       that are NULL for this batch's rows.
    4. Foreign-key existence check - any configured foreign_keys
       pointing to a value that doesn't exist in the referenced table.

A table fails if COPY INTO reported errors, 0 rows loaded, a missing
file, OR any of the four checks above find a problem. The full set of
findings is written back to FILE_LOAD_AUDIT per table, and the overall
outcome is recorded as one row in PIPELINE_RUN_AUDIT - which is what
the next run's `get_latest_loaded_batch_date()` reads.
"""

from __future__ import annotations

from datetime import datetime

from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from scripts.config import (
    SNOWFLAKE_CONN_ID,
    PIPELINE_RUN_AUDIT_TABLE,
    FILE_LOAD_AUDIT_TABLE,
    TABLE_FILE_MAP,
    TABLE_METADATA,
    qualified_table,
)


def _check_row_count(
    hook: SnowflakeHook,
    table_name: str,
    batch_date: str,
    copy_rows_loaded: int,
) -> tuple[int, list[str]]:
    """
    Compare COPY INTO's reported rows_loaded against an independent
    COUNT(*) against the actual table, for this batch.
    """

    query = f"""
        SELECT COUNT(*)
        FROM {qualified_table(table_name)}
        WHERE BATCH_DATE = '{batch_date}'
    """

    actual_count = hook.get_first(query)[0]

    issues = []

    if actual_count != copy_rows_loaded:

        issues.append(
            f"Row count mismatch: COPY INTO reported {copy_rows_loaded} "
            f"but the table shows {actual_count} rows for this batch."
        )

    return (actual_count, issues)


def _check_duplicate_keys(
    hook: SnowflakeHook,
    table_name: str,
    batch_date: str,
    key_columns: list[str],
) -> list[str]:
    """
    Check for duplicate primary/composite key values within this
    batch's rows.
    """

    key_expr = ", ".join(key_columns)

    query = f"""
        SELECT COUNT(*) FROM (
            SELECT {key_expr}
            FROM {qualified_table(table_name)}
            WHERE BATCH_DATE = '{batch_date}'
            GROUP BY {key_expr}
            HAVING COUNT(*) > 1
        )
    """

    duplicate_group_count = hook.get_first(query)[0]

    if duplicate_group_count:

        return [
            f"{duplicate_group_count} duplicate value(s) found for "
            f"key ({key_expr})."
        ]

    return []


def _check_required_columns(
    hook: SnowflakeHook,
    table_name: str,
    batch_date: str,
    required_columns: list[str],
) -> list[str]:
    """
    Check that none of the configured required_columns are NULL for
    this batch's rows.
    """

    issues = []

    for column in required_columns:

        query = f"""
            SELECT COUNT(*)
            FROM {qualified_table(table_name)}
            WHERE BATCH_DATE = '{batch_date}'
              AND {column} IS NULL
        """

        null_count = hook.get_first(query)[0]

        if null_count:

            issues.append(
                f"{null_count} row(s) have a NULL {column}."
            )

    return issues


def _check_foreign_keys(
    hook: SnowflakeHook,
    table_name: str,
    batch_date: str,
    foreign_keys: list[dict],
) -> list[str]:
    """
    Check that every non-null foreign-key value in this batch exists
    in the referenced table.
    """

    issues = []

    for foreign_key in foreign_keys:

        column = foreign_key["column"]

        ref_table = qualified_table(foreign_key["ref_table"])

        ref_column = foreign_key["ref_column"]

        query = f"""
            SELECT COUNT(*)
            FROM {qualified_table(table_name)} t
            WHERE t.BATCH_DATE = '{batch_date}'
              AND t.{column} IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM {ref_table} r
                  WHERE r.{ref_column} = t.{column}
              )
        """

        orphan_count = hook.get_first(query)[0]

        if orphan_count:

            issues.append(
                f"{orphan_count} row(s) have a {column} not found in "
                f"{foreign_key['ref_table']}.{ref_column}."
            )

    return issues


def validate_table(
    hook: SnowflakeHook,
    table_name: str,
    batch_date: str,
    copy_result: dict,
) -> tuple[bool, list[str]]:
    """
    Run every applicable check for a single table and return
    (is_valid, issues).
    """

    issues = []

    # COPY INTO's own signal comes first - if the file was never
    # matched or nothing loaded, there's no point querying the table.
    if copy_result["status"] == "NO_FILE_MATCHED":

        return (False, ["Expected file was not found in the stage."])

    if copy_result["errors_seen"] > 0:

        issues.append(
            f"{copy_result['errors_seen']} row(s) rejected during COPY INTO."
        )

    if copy_result["rows_loaded"] == 0:

        issues.append("0 rows loaded.")

        # Nothing landed - skip the data-quality queries below, they'd
        # just report "0 rows" redundantly.
        return (False, issues)

    metadata = TABLE_METADATA.get(table_name, {})

    _, row_count_issues = _check_row_count(
        hook, table_name, batch_date, copy_result["rows_loaded"]
    )

    issues.extend(row_count_issues)

    primary_key = metadata.get("primary_key")

    if primary_key:

        issues.extend(
            _check_duplicate_keys(hook, table_name, batch_date, primary_key)
        )

    required_columns = metadata.get("required_columns")

    if required_columns:

        issues.extend(
            _check_required_columns(hook, table_name, batch_date, required_columns)
        )

    foreign_keys = metadata.get("foreign_keys")

    if foreign_keys:

        issues.extend(
            _check_foreign_keys(hook, table_name, batch_date, foreign_keys)
        )

    return (len(issues) == 0, issues)


def _update_file_load_audit_validation(
    hook: SnowflakeHook,
    pipeline_run_id: str,
    table_name: str,
    is_valid: bool,
    issues: list[str],
) -> None:
    """
    Backfill the VALIDATION_STATUS / VALIDATION_DETAILS columns on the
    FILE_LOAD_AUDIT row this run already inserted for this table.
    """

    details = "; ".join(issues) if issues else "All checks passed."

    safe_details = details.replace("'", "''")[:4000]

    update_sql = f"""
        UPDATE {FILE_LOAD_AUDIT_TABLE}
        SET VALIDATION_STATUS = '{"PASSED" if is_valid else "FAILED"}',
            VALIDATION_DETAILS = '{safe_details}'
        WHERE PIPELINE_RUN_ID = '{pipeline_run_id}'
          AND TABLE_NAME = '{table_name}'
    """

    hook.run(update_sql)


def record_pipeline_run(
    pipeline_run_id: str,
    dag_run_id: str,
    batch_date: str,
    started_at: datetime,
    overall_status: str,
    load_results: dict,
    details: str,
) -> None:
    """
    Insert the single summary row for this run into PIPELINE_RUN_AUDIT.

    This is what tomorrow's `get_latest_loaded_batch_date()` reads, so
    an OVERALL_STATUS of SUCCESS here is what lets the pipeline move
    on to the next batch date.
    """

    hook = SnowflakeHook(snowflake_conn_id=SNOWFLAKE_CONN_ID)

    total_files_loaded = sum(
        1 for result in load_results.values()
        if result["status"] != "NO_FILE_MATCHED"
    )

    total_rows_loaded = sum(
        result["rows_loaded"] for result in load_results.values()
    )

    safe_details = details.replace("'", "''")[:8000]

    insert_sql = f"""
        INSERT INTO {PIPELINE_RUN_AUDIT_TABLE}
            (PIPELINE_RUN_ID, DAG_RUN_ID, BATCH_DATE, STARTED_AT, ENDED_AT,
             OVERALL_STATUS, TOTAL_FILES_EXPECTED, TOTAL_FILES_LOADED,
             TOTAL_ROWS_LOADED, DETAILS)
        VALUES
            ('{pipeline_run_id}', '{dag_run_id}', '{batch_date}',
             '{started_at.isoformat()}', '{datetime.utcnow().isoformat()}',
             '{overall_status}', {len(TABLE_FILE_MAP)}, {total_files_loaded},
             {total_rows_loaded}, '{safe_details}')
    """

    hook.run(insert_sql)


def validate_load_results(
    load_results: dict,
    batch_date: str,
    pipeline_run_id: str,
) -> tuple[bool, str]:
    """
    Validate every table's load result and write the findings back to
    FILE_LOAD_AUDIT.

    Returns
    -------
    (is_success, details) - details is a human-readable summary used
    in both success and failure emails.
    """

    hook = SnowflakeHook(snowflake_conn_id=SNOWFLAKE_CONN_ID)

    summary_lines = []

    problem_lines = []

    is_batch_success = True

    for file_name, table_name in TABLE_FILE_MAP.items():

        copy_result = load_results.get(table_name)

        if copy_result is None:

            problem_lines.append(
                f"{table_name}: no load result recorded."
            )

            is_batch_success = False

            continue

        is_table_valid, issues = validate_table(
            hook, table_name, batch_date, copy_result
        )

        summary_lines.append(
            f"{table_name}: {copy_result['rows_loaded']} rows loaded "
            f"({'OK' if is_table_valid else 'FAILED'})"
        )

        if not is_table_valid:

            is_batch_success = False

            for issue in issues:

                problem_lines.append(f"{table_name}: {issue}")

        _update_file_load_audit_validation(
            hook, pipeline_run_id, table_name, is_table_valid, issues,
        )

    details = "\n".join(summary_lines)

    if problem_lines:

        details += "\n\nISSUES FOUND:\n" + "\n".join(problem_lines)

    return (is_batch_success, details)


# =====================================================================
# Airflow Task Callable
# =====================================================================

def task_validate_load_counts(**context) -> str:
    """
    BranchPythonOperator callable.

    Returns the task_id to run next: "send_success_email" or
    "send_failure_email". Records the run in PIPELINE_RUN_AUDIT either
    way, and pushes validation details to XCom for the notification
    step.
    """

    ti = context["ti"]

    batch_date = ti.xcom_pull(task_ids="determine_next_batch_date")

    load_results = ti.xcom_pull(task_ids="load_to_staging")

    pipeline_run_id = context["run_id"]

    is_success, details = validate_load_results(
        load_results, batch_date, pipeline_run_id,
    )

    ti.xcom_push(key="validation_details", value=details)

    record_pipeline_run(
        pipeline_run_id=pipeline_run_id,
        dag_run_id=context["dag_run"].run_id,
        batch_date=batch_date,
        started_at=context["dag_run"].start_date,
        overall_status="SUCCESS" if is_success else "FAILURE",
        load_results=load_results,
        details=details,
    )

    return "send_success_email" if is_success else "send_failure_email"
