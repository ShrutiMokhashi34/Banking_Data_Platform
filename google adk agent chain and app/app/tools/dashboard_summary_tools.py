from google.cloud import bigquery

from app.auth.authorization import (
    has_full_employee_access,
    has_valid_employee_role,
    is_active_employee,
    is_employee,
    is_customer,
)


PROJECT_ID = "bankingdataplatform"
DATASET = "ABC_BANK"

client = bigquery.Client(project=PROJECT_ID)


def _serialize_value(value):
    """
    Convert BigQuery values into JSON-serializable values.
    """

    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def _rows_to_dicts(results):
    """
    Convert BigQuery rows to JSON-serializable dictionaries.
    """

    rows = []

    for row in results:
        rows.append(
            {
                key: _serialize_value(value)
                for key, value in row.items()
            }
        )

    return rows


def get_dashboard_summary(user_context: dict) -> dict:
    """
    Return the data required by the static dashboard sidebar.

    Employee:
        - Active customers
        - Open accounts
        - Total transactions
        - Branches
        - Transactions for the current financial quarter

    Customer:
        - Active customers
        - Open accounts
        - Branches
        - Recent fraud alerts belonging only to the
          authenticated customer

    Authorization is enforced here, server-side.
    """

    if not user_context:
        return {
            "error": "Authenticated user context is unavailable."
        }

    # ========================================================
    # CUSTOMER DASHBOARD
    # ========================================================

    if is_customer(user_context):

        customer_id = (
            user_context.get("customer_id")
            or user_context.get("user_id")
        )

        if not customer_id:
            return {
                "error": "Authenticated customer ID is unavailable."
            }

        # ----------------------------------------------------
        # General banking KPIs
        # ----------------------------------------------------

        kpi_query = f"""
            SELECT
                (
                    SELECT COUNT(DISTINCT CUSTOMER_ID)
                    FROM `{PROJECT_ID}.{DATASET}.DIM_CUSTOMER`
                    WHERE UPPER(CUSTOMER_STATUS) = 'ACTIVE'
                ) AS active_customers,

                (
                    SELECT COUNT(DISTINCT ACCOUNT_ID)
                    FROM `{PROJECT_ID}.{DATASET}.DIM_ACCOUNT`
                    WHERE UPPER(ACCOUNT_STATUS) = 'ACTIVE'
                ) AS open_accounts,

                (
                    SELECT COUNT(DISTINCT BRANCH_ID)
                    FROM `{PROJECT_ID}.{DATASET}.DIM_EMPLOYEES`
                    WHERE BRANCH_ID IS NOT NULL
                ) AS branches
        """

        # ----------------------------------------------------
        # Customer-specific fraud alerts
        #
        # FACT_FRAUD_ALERTS -> FACT_TRANSACTIONS
        #                    -> DIM_ACCOUNT
        #                    -> CUSTOMER_ID
        #
        # This guarantees that the customer only sees
        # alerts associated with their own accounts.
        # ----------------------------------------------------

        alerts_query = f"""
            SELECT
                fa.ALERT_ID,
                fa.ALERT_REASON,
                fa.ALERT_STATUS,
                fa.ALERT_TIMESTAMP
            FROM `{PROJECT_ID}.{DATASET}.FACT_FRAUD_ALERTS` fa
            INNER JOIN `{PROJECT_ID}.{DATASET}.FACT_TRANSACTIONS` ft
                ON fa.TRANSACTION_ID = ft.TRANSACTION_ID
            INNER JOIN `{PROJECT_ID}.{DATASET}.DIM_ACCOUNT` da
                ON ft.ACCOUNT_ID = da.ACCOUNT_ID
            WHERE da.CUSTOMER_ID = @customer_id
            ORDER BY fa.ALERT_TIMESTAMP DESC
            LIMIT 5
        """

        try:

            kpi_results = client.query(
                kpi_query
            ).result()

            kpi_rows = _rows_to_dicts(
                kpi_results
            )

            alerts_job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "customer_id",
                        "STRING",
                        customer_id,
                    )
                ]
            )

            alerts_results = client.query(
                alerts_query,
                job_config=alerts_job_config,
            ).result()

            alerts_rows = _rows_to_dicts(
                alerts_results
            )

            return {
                "role": "customer",

                "kpis": (
                    kpi_rows[0]
                    if kpi_rows
                    else {
                        "active_customers": 0,
                        "open_accounts": 0,
                        "branches": 0,
                    }
                ),

                "recent_alerts": alerts_rows,
            }

        except Exception as e:

            return {
                "error": f"Unable to load customer dashboard: {str(e)}"
            }

    # ========================================================
    # EMPLOYEE DASHBOARD
    # ========================================================

    if is_employee(user_context):

        if not is_active_employee(user_context):
            return {
                "error": "Inactive employees cannot access dashboard data."
            }

        if not has_valid_employee_role(user_context):
            return {
                "error": "Employee role is not authorized."
            }

        # ----------------------------------------------------
        # Employee dashboard requires an authorized employee.
        #
        # Total transactions and financial-quarter
        # transactions are intentionally available only here.
        # ----------------------------------------------------

        total_query = f"""
            SELECT
                (
                    SELECT COUNT(DISTINCT CUSTOMER_ID)
                    FROM `{PROJECT_ID}.{DATASET}.DIM_CUSTOMER`
                    WHERE UPPER(CUSTOMER_STATUS) = 'ACTIVE'
                ) AS active_customers,

                (
                    SELECT COUNT(DISTINCT ACCOUNT_ID)
                    FROM `{PROJECT_ID}.{DATASET}.DIM_ACCOUNT`
                    WHERE UPPER(ACCOUNT_STATUS) = 'ACTIVE'
                ) AS open_accounts,

                (
                    SELECT COUNT(DISTINCT TRANSACTION_ID)
                    FROM `{PROJECT_ID}.{DATASET}.FACT_TRANSACTIONS`
                ) AS total_transactions,

                (
                    SELECT COUNT(DISTINCT BRANCH_ID)
                    FROM `{PROJECT_ID}.{DATASET}.DIM_EMPLOYEES`
                    WHERE BRANCH_ID IS NOT NULL
                ) AS branches
        """

        # ----------------------------------------------------
        # Current financial quarter transaction activity
        #
        # Financial year:
        #   Q1 = April - June
        #   Q2 = July - September
        #   Q3 = October - December
        #   Q4 = January - March
        # ----------------------------------------------------

        quarter_query = f"""
            WITH quarter_dates AS (
                SELECT
                    CASE
                        WHEN EXTRACT(MONTH FROM CURRENT_DATE())
                             BETWEEN 4 AND 6
                            THEN DATE(
                                EXTRACT(YEAR FROM CURRENT_DATE()),
                                4,
                                1
                            )

                        WHEN EXTRACT(MONTH FROM CURRENT_DATE())
                             BETWEEN 7 AND 9
                            THEN DATE(
                                EXTRACT(YEAR FROM CURRENT_DATE()),
                                7,
                                1
                            )

                        WHEN EXTRACT(MONTH FROM CURRENT_DATE())
                             BETWEEN 10 AND 12
                            THEN DATE(
                                EXTRACT(YEAR FROM CURRENT_DATE()),
                                10,
                                1
                            )

                        ELSE DATE(
                            EXTRACT(YEAR FROM CURRENT_DATE()),
                            1,
                            1
                        )
                    END AS quarter_start
            )

            SELECT
                FORMAT_DATE(
                    '%b %d',
                    DATE(t.TRANSACTION_TIMESTAMP)
                ) AS day,

                DATE(t.TRANSACTION_TIMESTAMP) AS transaction_date,

                COUNT(DISTINCT t.TRANSACTION_ID) AS volume,

                SUM(t.TRANSACTION_AMOUNT) AS total_amount

            FROM `{PROJECT_ID}.{DATASET}.FACT_TRANSACTIONS` t

            CROSS JOIN quarter_dates q

            WHERE DATE(t.TRANSACTION_TIMESTAMP)
                  >= q.quarter_start

              AND DATE(t.TRANSACTION_TIMESTAMP)
                  <= CURRENT_DATE()

            GROUP BY
                day,
                transaction_date

            ORDER BY
                transaction_date
        """

        try:

            total_results = client.query(
                total_query
            ).result()

            total_rows = _rows_to_dicts(
                total_results
            )

            quarter_results = client.query(
                quarter_query
            ).result()

            quarter_rows = _rows_to_dicts(
                quarter_results
            )

            return {
                "role": "employee",

                "kpis": (
                    total_rows[0]
                    if total_rows
                    else {
                        "active_customers": 0,
                        "open_accounts": 0,
                        "total_transactions": 0,
                        "branches": 0,
                    }
                ),

                "quarter_transactions": quarter_rows,
            }

        except Exception as e:

            return {
                "error": f"Unable to load employee dashboard: {str(e)}"
            }

    # ========================================================
    # Unknown user type
    # ========================================================

    return {
        "error": "Unsupported user type."
    }