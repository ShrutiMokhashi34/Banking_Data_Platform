"""
Authentication services for the Banking Data Platform.

Responsibilities:
    - Verify credentials
    - Retrieve customer/employee identity
    - Reject inactive employees
    - Create JWT access tokens
    - Decode JWT access tokens

Passwords and password hashes must never be passed to the LLM.
"""

from datetime import datetime, timedelta, timezone

import os
from pathlib import Path

from dotenv import load_dotenv

import bcrypt
import jwt
from google.cloud import bigquery

# Load .env from the application root
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_FILE)

# ============================================================
# Configuration
# ============================================================

PROJECT_ID = "bankingdataplatform"
DATASET = "ABC_BANK"

AUTH_TABLE = (
    f"{PROJECT_ID}.{DATASET}.AUTH_USERS"
)

CUSTOMER_TABLE = (
    f"{PROJECT_ID}.{DATASET}.DIM_CUSTOMER"
)

EMPLOYEE_TABLE = (
    f"{PROJECT_ID}.{DATASET}.DIM_EMPLOYEES"
)


JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

JWT_EXPIRATION_MINUTES = int(
    os.getenv(
        "JWT_EXPIRATION_MINUTES",
        "60",
    )
)


client = bigquery.Client(
    project=PROJECT_ID
)


# ============================================================
# Password verification
# ============================================================

def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Plaintext passwords are never stored or sent to the LLM.
    """

    try:

        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    except Exception:

        return False


# ============================================================
# Retrieve authentication record
# ============================================================

def get_auth_user(
    user_type: str,
    user_id: str,
):
    """
    Retrieve authentication information from AUTH_USERS.
    """

    sql = f"""
        SELECT
            AUTH_USER_ID,
            USER_TYPE,
            USER_ID,
            PASSWORD_HASH,
            ACCOUNT_STATUS,
            CREATED_AT,
            UPDATED_AT
        FROM `{AUTH_TABLE}`
        WHERE UPPER(USER_TYPE) = @user_type
          AND UPPER(USER_ID) = @user_id
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "user_type",
                "STRING",
                user_type.strip().upper(),
            ),
            bigquery.ScalarQueryParameter(
                "user_id",
                "STRING",
                user_id.strip().upper(),
            ),
        ]
    )

    try:

        results = client.query(
            sql,
            job_config=job_config,
        ).result()

        for row in results:
            return row

        return None

    except Exception:

        return None


# ============================================================
# Retrieve customer identity
# ============================================================

def get_customer_identity(
    customer_id: str,
):
    """
    Retrieve the trusted customer identity from DIM_CUSTOMER.
    """

    sql = f"""
        SELECT
            CUSTOMER_ID,
            CUSTOMER_NAME,
            CUSTOMER_STATUS
        FROM `{CUSTOMER_TABLE}`
        WHERE UPPER(CUSTOMER_ID) = @customer_id
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "customer_id",
                "STRING",
                customer_id.strip().upper(),
            )
        ]
    )

    try:

        results = client.query(
            sql,
            job_config=job_config,
        ).result()

        for row in results:

            return {
                "user_type": "CUSTOMER",
                "user_id": row.CUSTOMER_ID,
                "display_name": row.CUSTOMER_NAME,
                "customer_id": row.CUSTOMER_ID,
                "customer_status": row.CUSTOMER_STATUS,
            }

        return None

    except Exception:

        return None


# ============================================================
# Retrieve employee identity
# ============================================================

def get_employee_identity(
    employee_id: str,
):
    """
    Retrieve the trusted employee identity from DIM_EMPLOYEES.

    Employee status is included because authorization depends
    on the employee being active.
    """

    sql = f"""
        SELECT
            EMPLOYEE_ID,
            EMPLOYEE_NAME,
            EMPLOYEE_DESIGNATION,
            EMPLOYEE_STATUS,
            BRANCH_ID,
            BRANCH_NAME
        FROM `{EMPLOYEE_TABLE}`
        WHERE UPPER(EMPLOYEE_ID) = @employee_id
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "employee_id",
                "STRING",
                employee_id.strip().upper(),
            )
        ]
    )

    try:

        results = client.query(
            sql,
            job_config=job_config,
        ).result()

        for row in results:

            return {
                "user_type": "EMPLOYEE",
                "user_id": row.EMPLOYEE_ID,
                "display_name": row.EMPLOYEE_NAME,
                "role": row.EMPLOYEE_DESIGNATION,
                "employee_status": row.EMPLOYEE_STATUS,
                "branch_id": row.BRANCH_ID,
                "branch_name": row.BRANCH_NAME,
            }

        return None

    except Exception:

        return None


# ============================================================
# Authentication
# ============================================================

def authenticate_user(
    user_type: str,
    user_id: str,
    password: str,
):
    """
    Authenticate a customer or employee.

    Returns:
        Trusted identity dictionary on success.

    Returns:
        None on authentication failure.

    Important:
        Resigned, terminated, and retired employees are
        rejected before a JWT is created.
    """

    normalized_user_type = (
        user_type.strip().upper()
    )

    normalized_user_id = (
        user_id.strip().upper()
    )

    # --------------------------------------------------------
    # Validate user type
    # --------------------------------------------------------

    if normalized_user_type not in {
        "CUSTOMER",
        "EMPLOYEE",
    }:

        return None

    # --------------------------------------------------------
    # Retrieve authentication record
    # --------------------------------------------------------

    auth_user = get_auth_user(
        user_type=normalized_user_type,
        user_id=normalized_user_id,
    )

    if auth_user is None:
        return None

    # --------------------------------------------------------
    # Check account status
    # --------------------------------------------------------

    account_status = (
        str(auth_user.ACCOUNT_STATUS or "")
        .strip()
        .lower()
    )

    if account_status != "active":
        return None

    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    if not verify_password(
        password,
        auth_user.PASSWORD_HASH,
    ):

        return None

    # --------------------------------------------------------
    # Customer
    # --------------------------------------------------------

    if normalized_user_type == "CUSTOMER":

        identity = get_customer_identity(
            normalized_user_id
        )

        if identity is None:
            return None

        return identity

    # --------------------------------------------------------
    # Employee
    # --------------------------------------------------------

    identity = get_employee_identity(
        normalized_user_id
    )

    if identity is None:
        return None

    # --------------------------------------------------------
    # Reject inactive employees
    # --------------------------------------------------------

    employee_status = (
        str(
            identity.get(
                "employee_status",
                "",
            )
        )
        .strip()
        .lower()
    )

    if employee_status in {
        "resigned",
        "terminated",
        "retired",
    }:

        return None

    # Fail closed for unknown/missing status.
    if employee_status != "active":
        return None

    return identity


# ============================================================
# Create JWT
# ============================================================

def create_access_token(
    identity: dict,
) -> str:
    """
    Create a JWT containing trusted identity information.

    Never include:
        - password
        - password hash
        - secrets
        - API keys
        - access tokens
    """

    now = datetime.now(
        timezone.utc
    )

    expiration = (
        now
        + timedelta(
            minutes=JWT_EXPIRATION_MINUTES
        )
    )

    payload = {
        "user_type": identity["user_type"],
        "user_id": identity["user_id"],
        "display_name": identity["display_name"],
        "iat": now,
        "exp": expiration,
    }

    # --------------------------------------------------------
    # Employee-specific identity
    # --------------------------------------------------------

    if identity["user_type"] == "EMPLOYEE":

        payload.update(
            {
                "role": identity.get("role"),
                "employee_status": identity.get(
                    "employee_status"
                ),
                "branch_id": identity.get(
                    "branch_id"
                ),
                "branch_name": identity.get(
                    "branch_name"
                ),
            }
        )

    # --------------------------------------------------------
    # Customer-specific identity
    # --------------------------------------------------------

    elif identity["user_type"] == "CUSTOMER":

        payload["customer_id"] = identity.get(
            "customer_id"
        )

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


# ============================================================
# Decode JWT
# ============================================================

def decode_access_token(
    token: str,
) -> dict:
    """
    Decode and validate a JWT.

    Raises an exception if the token is invalid or expired.
    """

    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[
            JWT_ALGORITHM
        ],
    )