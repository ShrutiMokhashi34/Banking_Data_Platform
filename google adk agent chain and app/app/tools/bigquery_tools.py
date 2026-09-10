from google.cloud import bigquery
import re


PROJECT_ID = "bankingdataplatform"
DATASET = "ABC_BANK"

client = bigquery.Client(project=PROJECT_ID)


def _validate_identifier(value: str) -> bool:
    """
    Validate BigQuery table/column identifiers.
    """
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value))


def execute_bigquery(sql: str) -> str:
    """
    Execute a read-only SELECT query against BigQuery.
    """

    sql_clean = sql.strip().lower()

    forbidden_keywords = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "truncate ",
        "merge ",
        "create ",
    ]

    if any(keyword in sql_clean for keyword in forbidden_keywords):
        return "Only read-only SELECT queries are allowed."

    if not sql_clean.startswith("select"):
        return "Only SELECT queries are allowed."

    try:
        query_job = client.query(sql)
        results = query_job.result()

        rows = []

        for row in results:
            rows.append(dict(row.items()))

        if not rows:
            return "The query returned no results."

        return str(rows)

    except Exception as e:
        return f"BigQuery query failed: {str(e)}"


def check_nulls(table_name: str, column_name: str) -> str:
    """
    Check the number and percentage of NULL values in a column.

    Parameters:
        table_name: BigQuery table name without project or dataset.
        column_name: Column to check.
    """

    if not _validate_identifier(table_name):
        return "Invalid table name."

    if not _validate_identifier(column_name):
        return "Invalid column name."

    query = f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNTIF(`{column_name}` IS NULL) AS null_count,
            ROUND(
                SAFE_DIVIDE(
                    COUNTIF(`{column_name}` IS NULL) * 100,
                    COUNT(*)
                ),
                2
            ) AS null_percentage
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
    """

    return execute_bigquery(query)


def check_duplicates(table_name: str, column_name: str) -> str:
    """
    Check for duplicate records based on a specified column.

    Parameters:
        table_name: BigQuery table name without project or dataset.
        column_name: Column used as the business/key identifier.
    """

    if not _validate_identifier(table_name):
        return "Invalid table name."

    if not _validate_identifier(column_name):
        return "Invalid column name."

    query = f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT `{column_name}`) AS distinct_values,
            COUNT(*) - COUNT(DISTINCT `{column_name}`) AS duplicate_count
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
        WHERE `{column_name}` IS NOT NULL
    """

    return execute_bigquery(query)


def check_row_count(table_name: str) -> str:
    """
    Return the total number of records in a BigQuery table.

    Parameters:
        table_name: BigQuery table name without project or dataset.
    """

    if not _validate_identifier(table_name):
        return "Invalid table name."

    query = f"""
        SELECT
            COUNT(*) AS row_count
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
    """

    return execute_bigquery(query)


def check_freshness(
    table_name: str,
    timestamp_column: str
) -> str:
    """
    Check the most recent timestamp in a table.

    Parameters:
        table_name: BigQuery table name without project or dataset.
        timestamp_column: Timestamp/date column used for freshness.
    """

    if not _validate_identifier(table_name):
        return "Invalid table name."

    if not _validate_identifier(timestamp_column):
        return "Invalid timestamp column."

    query = f"""
        SELECT
            MAX(`{timestamp_column}`) AS latest_timestamp,
            TIMESTAMP_DIFF(
                CURRENT_TIMESTAMP(),
                MAX(`{timestamp_column}`),
                HOUR
            ) AS hours_since_latest_record
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
    """

    return execute_bigquery(query)


def check_invalid_values(
    table_name: str,
    column_name: str,
    invalid_value: str
) -> str:
    """
    Check how many records contain a specified invalid value.

    Parameters:
        table_name: BigQuery table name without project or dataset.
        column_name: Column to inspect.
        invalid_value: Value considered invalid.
    """

    if not _validate_identifier(table_name):
        return "Invalid table name."

    if not _validate_identifier(column_name):
        return "Invalid column name."

    query = f"""
        SELECT
            COUNT(*) AS invalid_value_count
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
        WHERE CAST(`{column_name}` AS STRING) = @invalid_value
    """

    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "invalid_value",
                    "STRING",
                    invalid_value
                )
            ]
        )

        query_job = client.query(
            query,
            job_config=job_config
        )

        results = query_job.result()

        rows = [
            dict(row.items())
            for row in results
        ]

        return str(rows)

    except Exception as e:
        return f"BigQuery query failed: {str(e)}"