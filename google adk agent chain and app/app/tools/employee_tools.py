from google.cloud import bigquery
from google.adk.tools import ToolContext

PROJECT_ID = "bankingdataplatform"
DATASET = "ABC_BANK"

client = bigquery.Client(project=PROJECT_ID)


VALID_EMPLOYEE_ROLES = {
    "associate",
    "assistant manager",
    "senior associate",
    "officer",
    "senior manager",
    "manager",
}

FULL_ACCESS_ROLES = {
    "manager",
    "senior manager",
    "officer",
}

BRANCH_ACCESS_ROLE = "assistant manager"

INACTIVE_STATUSES = {
    "resigned",
    "terminated",
    "retired",
}


def _get_user_context(tool_context: ToolContext) -> dict:
    """Get trusted authenticated identity from ADK session state."""

    user_context = tool_context.state.get("user_context")

    if not user_context:
        return {}

    return user_context


def _normalize(value: str | None) -> str:
    if not value:
        return ""

    return value.strip().lower()


def _is_active_employee(user: dict) -> bool:
    if _normalize(user.get("user_type")) != "employee":
        return False

    status = _normalize(user.get("employee_status"))

    if not status:
        return False

    if status in INACTIVE_STATUSES:
        return False

    return status == "active"


def _has_valid_role(user: dict) -> bool:
    role = _normalize(user.get("role"))

    return role in VALID_EMPLOYEE_ROLES


def _has_full_access(user: dict) -> bool:
    if not _is_active_employee(user):
        return False

    if not _has_valid_role(user):
        return False

    return _normalize(user.get("role")) in FULL_ACCESS_ROLES


def get_my_employee_profile(
    tool_context: ToolContext,
) -> dict:
    """
    Return the authenticated employee's own employee profile.

    The employee ID comes exclusively from trusted backend
    authentication context.
    """

    user = _get_user_context(tool_context)

    if not _is_active_employee(user):
        return {
            "authorized": False,
            "error": "Employee is not authorized to access employee data."
        }

    if not _has_valid_role(user):
        return {
            "authorized": False,
            "error": "Employee role is not authorized."
        }

    employee_id = user.get("user_id")

    if not employee_id:
        return {
            "authorized": False,
            "error": "Authenticated employee ID is unavailable."
        }

    query = f"""
        SELECT
            EMPLOYEE_ID,
            EMPLOYEE_NAME,
            EMPLOYEE_DESIGNATION,
            EMPLOYEE_STATUS,
            BRANCH_ID,
            BRANCH_NAME
        FROM `{PROJECT_ID}.{DATASET}.DIM_EMPLOYEES`
        WHERE EMPLOYEE_ID = @employee_id
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "employee_id",
                "STRING",
                employee_id,
            )
        ]
    )

    try:
        results = client.query(
            query,
            job_config=job_config,
        ).result()

        rows = [dict(row.items()) for row in results]

        if not rows:
            return {
                "authorized": False,
                "error": "Employee profile not found."
            }

        return {
            "authorized": True,
            "employee": rows[0],
        }

    except Exception as e:
        return {
            "authorized": False,
            "error": f"Unable to retrieve employee profile: {str(e)}"
        }


def get_employee_data(
    tool_context: ToolContext,
    target_employee_id: str | None = None,
) -> dict:
    """
    Retrieve employee data according to the authenticated employee's
    role and branch authorization.

    Rules:

    Manager/Senior Manager/Officer:
        Can view all employees.

    Assistant Manager:
        Can view employees in their own branch.

    Associate/Senior Associate:
        Can view only their own employee record.

    Customers:
        Cannot use this tool.

    Inactive employees:
        Cannot use this tool.
    """

    user = _get_user_context(tool_context)

    if not _is_active_employee(user):
        return {
            "authorized": False,
            "error": "Employee is not authorized to access employee data."
        }

    if not _has_valid_role(user):
        return {
            "authorized": False,
            "error": "Employee role is not authorized."
        }

    requester_id = user.get("user_id")

    if not requester_id:
        return {
            "authorized": False,
            "error": "Authenticated employee ID is unavailable."
        }

    role = _normalize(user.get("role"))

    # --------------------------------------------------------
    # Full-access employees
    # --------------------------------------------------------

    if role in FULL_ACCESS_ROLES:

        query = f"""
            SELECT
                EMPLOYEE_ID,
                EMPLOYEE_NAME,
                EMPLOYEE_DESIGNATION,
                EMPLOYEE_STATUS,
                BRANCH_ID,
                BRANCH_NAME
            FROM `{PROJECT_ID}.{DATASET}.DIM_EMPLOYEES`
        """

        params = []

    # --------------------------------------------------------
    # Assistant Manager
    # --------------------------------------------------------

    elif role == BRANCH_ACCESS_ROLE:

        branch_id = user.get("branch_id")

        if not branch_id:
            return {
                "authorized": False,
                "error": "Authenticated employee branch is unavailable."
            }

        query = f"""
            SELECT
                EMPLOYEE_ID,
                EMPLOYEE_NAME,
                EMPLOYEE_DESIGNATION,
                EMPLOYEE_STATUS,
                BRANCH_ID,
                BRANCH_NAME
            FROM `{PROJECT_ID}.{DATASET}.DIM_EMPLOYEES`
            WHERE BRANCH_ID = @branch_id
        """

        params = [
            bigquery.ScalarQueryParameter(
                "branch_id",
                "STRING",
                branch_id,
            )
        ]

        # If a specific employee was requested, make sure they
        # belong to the Assistant Manager's branch.
        if target_employee_id:

            query += """
                AND EMPLOYEE_ID = @target_employee_id
            """

            params.append(
                bigquery.ScalarQueryParameter(
                    "target_employee_id",
                    "STRING",
                    target_employee_id,
                )
            )

    # --------------------------------------------------------
    # Associate / Senior Associate
    # --------------------------------------------------------

    else:

        # These employees can only access their own record.
        if target_employee_id:
            if target_employee_id.strip().upper() != requester_id.strip().upper():
                return {
                    "authorized": False,
                    "error": "You are not authorized to access this employee's data."
                }

        query = f"""
            SELECT
                EMPLOYEE_ID,
                EMPLOYEE_NAME,
                EMPLOYEE_DESIGNATION,
                EMPLOYEE_STATUS,
                BRANCH_ID,
                BRANCH_NAME
            FROM `{PROJECT_ID}.{DATASET}.DIM_EMPLOYEES`
            WHERE EMPLOYEE_ID = @employee_id
        """

        params = [
            bigquery.ScalarQueryParameter(
                "employee_id",
                "STRING",
                requester_id,
            )
        ]

    try:

        job_config = bigquery.QueryJobConfig(
            query_parameters=params
        )

        results = client.query(
            query,
            job_config=job_config,
        ).result()

        rows = [dict(row.items()) for row in results]

        if not rows:
            return {
                "authorized": True,
                "employees": [],
                "message": "No employee records found."
            }

        return {
            "authorized": True,
            "employees": rows,
        }

    except Exception as e:

        return {
            "authorized": False,
            "error": f"Unable to retrieve employee data: {str(e)}"
        }
