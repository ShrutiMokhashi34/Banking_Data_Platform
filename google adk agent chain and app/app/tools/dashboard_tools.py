import re
from typing import Any

from google.cloud import bigquery

from app.auth.authorization import (
    has_full_employee_access,
    has_valid_employee_role,
    is_active_employee,
)

PROJECT_ID = "bankingdataplatform"
DATASET = "ABC_BANK"

client = bigquery.Client(project=PROJECT_ID)

ALLOWED_TABLES = {
    "DIM_CUSTOMER",
    "DIM_ACCOUNT",
    "DIM_EMPLOYEES",
    "DIM_EXCHANGE_RATES",
    "DIM_LOAN",
    "FACT_TRANSACTIONS",
    "FACT_LOAN_REPAYMENTS",
    "FACT_FRAUD_ALERTS",
}

# Only simple SELECT statements are accepted by the dashboard execution layer.
FORBIDDEN_SQL = {
    "insert", "update", "delete", "drop", "alter", "truncate",
    "merge", "create", "replace", "grant", "revoke", "call",
    "execute", "export", "load", "copy",
}


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def _extract_tables(sql: str) -> set[str]:
    """Extract physical table names from fully-qualified BigQuery references."""
    matches = re.findall(
        r"`(?:[\w-]+\.){1,2}([A-Za-z_][A-Za-z0-9_]*)`",
        sql,
        flags=re.IGNORECASE,
    )
    return {m.upper() for m in matches}


def _validate_sql(sql: str) -> tuple[bool, str]:
    sql = sql.strip()

    if not sql:
        return False, "Dashboard query is empty."

    if not re.match(r"^select\b", sql, flags=re.IGNORECASE):
        return False, "Dashboard queries must start with SELECT."

    # One statement only; comments are not needed for generated dashboard SQL.
    if ";" in sql or "--" in sql or "/*" in sql or "*/" in sql:
        return False, "Only a single SELECT statement is allowed."

    tokens = set(re.findall(r"\b[a-z_]+\b", sql.lower()))
    blocked = sorted(tokens.intersection(FORBIDDEN_SQL))
    if blocked:
        return False, f"Forbidden SQL operation detected: {blocked[0]}."

    tables = _extract_tables(sql)
    if not tables:
        return False, "Dashboard queries must use approved fully-qualified BigQuery tables."

    unauthorized = tables - ALLOWED_TABLES
    if unauthorized:
        return False, f"Table(s) not approved for dashboard generation: {sorted(unauthorized)}."

    return True, ""


def execute_dashboard_query(sql: str, user_context: dict) -> dict:
    """
    Execute a dashboard SELECT query after enforcing server-side authorization.

    The LLM may generate the SELECT statement, but the LLM never decides
    whether the caller is allowed to run it.
    """
    if not user_context:
        return {"error": "Authenticated user context is unavailable."}

    ok, error = _validate_sql(sql)
    if not ok:
        return {"error": error}

    user_type = _normalize(user_context.get("user_type")).upper()
    tables = _extract_tables(sql)

    query_parameters = []

    if user_type == "CUSTOMER":
        customer_id = str(
            user_context.get("customer_id") or user_context.get("user_id") or ""
        ).strip().upper()

        if not customer_id:
            return {"error": "Authenticated customer ID is unavailable."}

        # Customer dashboards must explicitly use the trusted backend parameter.
        if not re.search(r"@customer_id\b", sql, flags=re.IGNORECASE):
            return {
                "error": (
                    "Customer dashboard queries must be restricted to the "
                    "authenticated customer's customer_id."
                )
            }

        # Customers may never query employee data.
        if "DIM_EMPLOYEES" in tables:
            return {"error": "Customers are not authorized to view employee data."}

        query_parameters.append(
            bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id)
        )

    elif user_type == "EMPLOYEE":
        if not is_active_employee(user_context):
            return {"error": "Inactive employees cannot access dashboard data."}

        if not has_valid_employee_role(user_context):
            return {"error": "Employee role is not authorized."}

        # Employee-specific access is enforced when DIM_EMPLOYEES is queried.
        if "DIM_EMPLOYEES" in tables:
            role = _normalize(user_context.get("role"))

            if has_full_employee_access(user_context):
                pass

            elif role == "assistant manager":
                branch_id = str(user_context.get("branch_id") or "").strip().upper()
                if not branch_id:
                    return {"error": "Authenticated employee branch is unavailable."}

                if not re.search(r"@branch_id\b", sql, flags=re.IGNORECASE):
                    return {
                        "error": (
                            "Assistant Manager employee dashboards must be "
                            "restricted to the authenticated employee's branch."
                        )
                    }

                query_parameters.append(
                    bigquery.ScalarQueryParameter("branch_id", "STRING", branch_id)
                )

            else:
                employee_id = str(user_context.get("user_id") or "").strip().upper()
                if not employee_id:
                    return {"error": "Authenticated employee ID is unavailable."}

                if not re.search(r"@employee_id\b", sql, flags=re.IGNORECASE):
                    return {
                        "error": (
                            "This employee role may only access its own employee "
                            "record."
                        )
                    }

                query_parameters.append(
                    bigquery.ScalarQueryParameter("employee_id", "STRING", employee_id)
                )

    else:
        return {"error": "Unknown user type."}

    try:
        job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
        results = list(client.query(sql, job_config=job_config).result())

        if not results:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
            }

        columns = list(results[0].keys())
        rows = [[row[column] for column in columns] for row in results]

        # Convert BigQuery values to JSON-friendly values.
        serializable_rows = []
        for row in rows:
            serializable_rows.append([
                value.isoformat() if hasattr(value, "isoformat") else value
                for value in row
            ])

        return {
            "columns": columns,
            "rows": serializable_rows,
            "row_count": len(serializable_rows),
        }

    except Exception as exc:
        return {"error": f"Dashboard query failed: {str(exc)}"}


def get_table_schema(table_name: str, tool_context) -> dict:
    """Return the actual schema for an approved dashboard table."""
    table_name = table_name.strip().upper()

    if table_name not in ALLOWED_TABLES:
        return {"error": "Table is not available for dashboard generation."}

    user_context = tool_context.state.get("user_context")
    if not user_context:
        return {"error": "Authenticated user context is unavailable."}

    query = f"""
        SELECT column_name, data_type
        FROM `{PROJECT_ID}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = @table_name
        ORDER BY ordinal_position
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("table_name", "STRING", table_name)
        ]
    )

    try:
        results = client.query(query, job_config=job_config).result()
        columns = [
            {"column_name": row.column_name, "data_type": row.data_type}
            for row in results
        ]

        if not columns:
            return {"error": f"No schema found for {table_name}."}

        return {"table": table_name, "columns": columns}

    except Exception as exc:
        return {"error": f"Unable to retrieve schema: {str(exc)}"}
