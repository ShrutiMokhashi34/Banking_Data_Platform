from google.cloud import bigquery

from app.auth.authorization import can_access_pipeline


PROJECT_ID = "bankingdataplatform"
DATASET = "ABC_BANK"
AUDIT_TABLE = (
    f"{PROJECT_ID}.{DATASET}."
    "DATABRICKS_GOLD_SNOWFLAKE_AGG_LOAD_AUDIT"
)

client = bigquery.Client(project=PROJECT_ID)


def _check_pipeline_access(user_context: dict) -> str | None:
    """
    Enforce authorization for pipeline/data-engineering information.

    Allowed roles:
        - Manager
        - Senior Manager
        - Officer

    Denied:
        - Customers
        - Associate
        - Senior Associate
        - Assistant Manager
        - Any unknown/invalid role
    """

    if not can_access_pipeline(user_context):
        return (
            "Access denied. Pipeline and data engineering information "
            "is restricted to Manager, Senior Manager, and Officer roles."
        )

    return None


def execute_pipeline_query(sql: str, user_context: dict) -> str:
    """
    Execute a read-only pipeline query after authorization.

    This function should only be called by the pipeline tools.
    """

    access_error = _check_pipeline_access(user_context)

    if access_error:
        return access_error

    sql_clean = sql.strip().lower()

    if not sql_clean.startswith("select"):
        return "Only SELECT queries are allowed."

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
        return f"Pipeline query failed: {str(e)}"


def get_latest_pipeline_load(user_context: dict) -> str:
    """
    Return the most recent pipeline load.
    """

    sql = f"""
        SELECT
            TABLE_NAME,
            SOURCE_TABLE,
            LOAD_TYPE,
            LOAD_START_TIME,
            LOAD_END_TIME,
            ROW_COUNT,
            LOAD_STATUS,
            UPDATED_FROM_DATABRICKS AS DATABRICKS_LOAD_TIMESTAMP,
            ERROR_MESSAGE,
            CREATED_AT
        FROM `{AUDIT_TABLE}`
        ORDER BY LOAD_END_TIME DESC
        LIMIT 1
    """

    return execute_pipeline_query(sql, user_context)


def get_recent_pipeline_loads(
    user_context: dict,
    limit: int = 10
) -> str:
    """
    Return recent pipeline loads.
    """

    # Keep the limit controlled by the application.
    limit = max(1, min(int(limit), 50))

    sql = f"""
        SELECT
            TABLE_NAME,
            SOURCE_TABLE,
            LOAD_TYPE,
            LOAD_START_TIME,
            LOAD_END_TIME,
            ROW_COUNT,
            LOAD_STATUS,
            UPDATED_FROM_DATABRICKS AS DATABRICKS_LOAD_TIMESTAMP,
            ERROR_MESSAGE,
            CREATED_AT
        FROM `{AUDIT_TABLE}`
        ORDER BY LOAD_END_TIME DESC
        LIMIT {limit}
    """

    return execute_pipeline_query(sql, user_context)


def get_failed_pipeline_loads(user_context: dict) -> str:
    """
    Return failed pipeline loads.
    """

    sql = f"""
        SELECT
            TABLE_NAME,
            SOURCE_TABLE,
            LOAD_TYPE,
            LOAD_START_TIME,
            LOAD_END_TIME,
            ROW_COUNT,
            LOAD_STATUS,
            UPDATED_FROM_DATABRICKS AS DATABRICKS_LOAD_TIMESTAMP,
            ERROR_MESSAGE,
            CREATED_AT
        FROM `{AUDIT_TABLE}`
        WHERE UPPER(LOAD_STATUS) = 'FAILED'
        ORDER BY LOAD_END_TIME DESC
    """

    return execute_pipeline_query(sql, user_context)


def get_pipeline_load_summary(user_context: dict) -> str:
    """
    Return an overall pipeline load summary.
    """

    sql = f"""
        SELECT
            COUNT(*) AS TOTAL_LOADS,

            COUNTIF(
                UPPER(LOAD_STATUS) = 'SUCCESS'
            ) AS SUCCESSFUL_LOADS,

            COUNTIF(
                UPPER(LOAD_STATUS) = 'FAILED'
            ) AS FAILED_LOADS,

            COUNTIF(
                UPPER(LOAD_STATUS) NOT IN ('SUCCESS', 'FAILED')
                OR LOAD_STATUS IS NULL
            ) AS OTHER_LOADS,

            SUM(ROW_COUNT) AS TOTAL_ROWS_LOADED,

            MAX(LOAD_END_TIME) AS LATEST_LOAD_END_TIME,

            MAX(UPDATED_FROM_DATABRICKS)
                AS LATEST_DATABRICKS_LOAD_TIMESTAMP

        FROM `{AUDIT_TABLE}`
    """

    return execute_pipeline_query(sql, user_context)


def get_table_load_status(
    user_context: dict,
    table_name: str
) -> str:
    """
    Return the latest pipeline status for a specific table.
    """

    sql = f"""
        SELECT
            TABLE_NAME,
            SOURCE_TABLE,
            LOAD_TYPE,
            LOAD_START_TIME,
            LOAD_END_TIME,
            ROW_COUNT,
            LOAD_STATUS,
            UPDATED_FROM_DATABRICKS AS DATABRICKS_LOAD_TIMESTAMP,
            ERROR_MESSAGE,
            CREATED_AT
        FROM `{AUDIT_TABLE}`
        WHERE UPPER(TABLE_NAME) = UPPER(@table_name)
        ORDER BY LOAD_END_TIME DESC
        LIMIT 1
    """

    access_error = _check_pipeline_access(user_context)

    if access_error:
        return access_error

    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "table_name",
                    "STRING",
                    table_name.strip(),
                )
            ]
        )

        query_job = client.query(
            sql,
            job_config=job_config,
        )

        results = query_job.result()

        rows = [
            dict(row.items())
            for row in results
        ]

        if not rows:
            return (
                f"No pipeline audit record was found for "
                f"table '{table_name}'."
            )

        return str(rows)

    except Exception as e:
        return f"Pipeline query failed: {str(e)}"