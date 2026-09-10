import csv
import re
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
from google.cloud import bigquery


# ============================================================
# Configuration
# ============================================================

PROJECT_ID = "bankingdataplatform"
DATASET = "ABC_BANK"

CUSTOMER_TABLE = f"{PROJECT_ID}.{DATASET}.DIM_CUSTOMER"
EMPLOYEE_TABLE = f"{PROJECT_ID}.{DATASET}.DIM_EMPLOYEES"
AUTH_TABLE = f"{PROJECT_ID}.{DATASET}.AUTH_USERS"

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "datasets" / "auth"
CREDENTIALS_FILE = OUTPUT_DIR / "mock_credentials.csv"

client = bigquery.Client(project=PROJECT_ID)


# ============================================================
# Helper functions
# ============================================================

def generate_customer_password(customer_id: str) -> str:
    """
    Generate a deterministic demo password for a customer.

    Example:
        CUST00005001 -> Cust@5001x
    """

    match = re.search(r"(\d+)$", customer_id)

    if not match:
        raise ValueError(
            f"Unable to generate password for customer ID: {customer_id}"
        )

    numeric_id = int(match.group(1))

    return f"Cust@{numeric_id}x"


def generate_employee_password(employee_id: str) -> str:
    """
    Generate a deterministic demo password for an employee.

    Example:
        EMP00000350 -> Emp@350x
    """

    match = re.search(r"(\d+)$", employee_id)

    if not match:
        raise ValueError(
            f"Unable to generate password for employee ID: {employee_id}"
        )

    numeric_id = int(match.group(1))

    return f"Emp@{numeric_id}x"


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """

    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


# ============================================================
# Create AUTH_USERS table
# ============================================================

def create_auth_table():
    """
    Create AUTH_USERS if it does not already exist.
    """

    sql = f"""
    CREATE TABLE IF NOT EXISTS `{AUTH_TABLE}`
    (
        AUTH_USER_ID STRING NOT NULL,
        USER_TYPE STRING NOT NULL,
        USER_ID STRING NOT NULL,
        PASSWORD_HASH STRING NOT NULL,
        ACCOUNT_STATUS STRING NOT NULL,
        CREATED_AT TIMESTAMP NOT NULL,
        UPDATED_AT TIMESTAMP NOT NULL
    )
    """

    print("Creating AUTH_USERS table if it does not exist...")

    client.query(sql).result()

    print(f"AUTH_USERS table ready: {AUTH_TABLE}")


# ============================================================
# Read customers
# ============================================================

def get_customers():
    """
    Retrieve customer IDs from DIM_CUSTOMER.

    CUSTOMER_NAME is intentionally not inserted into AUTH_USERS.
    It will be retrieved from DIM_CUSTOMER during authentication.
    """

    sql = f"""
    SELECT DISTINCT
        CUSTOMER_ID
    FROM `{CUSTOMER_TABLE}`
    WHERE CUSTOMER_ID IS NOT NULL
    ORDER BY CUSTOMER_ID
    """

    print("Reading customers...")

    results = client.query(sql).result()

    customers = []

    for row in results:
        customers.append(row.CUSTOMER_ID)

    print(f"Customers found: {len(customers)}")

    return customers


# ============================================================
# Read employees
# ============================================================

def get_employees():
    """
    Retrieve employee IDs from DIM_EMPLOYEES.

    Employee name, designation and branch are intentionally
    not inserted into AUTH_USERS.
    """

    sql = f"""
    SELECT DISTINCT
        EMPLOYEE_ID
    FROM `{EMPLOYEE_TABLE}`
    WHERE EMPLOYEE_ID IS NOT NULL
    ORDER BY EMPLOYEE_ID
    """

    print("Reading employees...")

    results = client.query(sql).result()

    employees = []

    for row in results:
        employees.append(row.EMPLOYEE_ID)

    print(f"Employees found: {len(employees)}")

    return employees


# ============================================================
# Build authentication records
# ============================================================

def build_auth_records(customers, employees):
    """
    Build AUTH_USERS records and demo credentials.

    Progress is printed during bcrypt hashing because bcrypt
    intentionally takes time to compute each password hash.
    """

    now = datetime.now(timezone.utc).isoformat()

    auth_records = []
    demo_credentials = []

    # --------------------------------------------------------
    # Customers
    # --------------------------------------------------------

    total_customers = len(customers)

    print()
    print("=" * 60)
    print("GENERATING CUSTOMER PASSWORD HASHES")
    print("=" * 60)

    for index, customer_id in enumerate(customers, start=1):

        password = generate_customer_password(customer_id)
        password_hash = hash_password(password)

        auth_records.append(
            {
                "AUTH_USER_ID": f"AUTH_{customer_id}",
                "USER_TYPE": "CUSTOMER",
                "USER_ID": customer_id,
                "PASSWORD_HASH": password_hash,
                "ACCOUNT_STATUS": "ACTIVE",
                "CREATED_AT": now,
                "UPDATED_AT": now,
            }
        )

        demo_credentials.append(
            {
                "USER_TYPE": "CUSTOMER",
                "USER_ID": customer_id,
                "MOCK_PASSWORD": password,
            }
        )

        # Print progress every 100 users
        if index % 100 == 0 or index == total_customers:
            percentage = (index / total_customers) * 100

            print(
                f"Customers: {index:,}/{total_customers:,} "
                f"({percentage:.1f}%)",
                flush=True
            )

    # --------------------------------------------------------
    # Employees
    # --------------------------------------------------------

    total_employees = len(employees)

    print()
    print("=" * 60)
    print("GENERATING EMPLOYEE PASSWORD HASHES")
    print("=" * 60)

    for index, employee_id in enumerate(employees, start=1):

        password = generate_employee_password(employee_id)
        password_hash = hash_password(password)

        auth_records.append(
            {
                "AUTH_USER_ID": f"AUTH_{employee_id}",
                "USER_TYPE": "EMPLOYEE",
                "USER_ID": employee_id,
                "PASSWORD_HASH": password_hash,
                "ACCOUNT_STATUS": "ACTIVE",
                "CREATED_AT": now,
                "UPDATED_AT": now,
            }
        )

        demo_credentials.append(
            {
                "USER_TYPE": "EMPLOYEE",
                "USER_ID": employee_id,
                "MOCK_PASSWORD": password,
            }
        )

        # Print progress every 25 employees
        if index % 25 == 0 or index == total_employees:
            percentage = (index / total_employees) * 100

            print(
                f"Employees: {index:,}/{total_employees:,} "
                f"({percentage:.1f}%)",
                flush=True
            )

    return auth_records, demo_credentials


# ============================================================
# Insert AUTH_USERS
# ============================================================

def insert_auth_records(auth_records):
    """
    Insert authentication records into AUTH_USERS.

    Existing records with the same USER_TYPE + USER_ID
    are replaced using a staging table + MERGE.
    """

    if not auth_records:
        print("No authentication records to insert.")
        return

    staging_table = f"{AUTH_TABLE}_STAGING"

    schema = [
        bigquery.SchemaField("AUTH_USER_ID", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("USER_TYPE", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("USER_ID", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("PASSWORD_HASH", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("ACCOUNT_STATUS", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("CREATED_AT", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("UPDATED_AT", "TIMESTAMP", mode="REQUIRED"),
    ]

    print(f"Loading {len(auth_records)} records into staging...")

    staging_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_json(
        auth_records,
        staging_table,
        job_config=staging_config,
    )

    load_job.result()

    print("Staging load completed.")

    merge_sql = f"""
    MERGE `{AUTH_TABLE}` AS target
    USING `{staging_table}` AS source
    ON target.USER_TYPE = source.USER_TYPE
       AND target.USER_ID = source.USER_ID

    WHEN MATCHED THEN
        UPDATE SET
            PASSWORD_HASH = source.PASSWORD_HASH,
            ACCOUNT_STATUS = source.ACCOUNT_STATUS,
            UPDATED_AT = source.UPDATED_AT

    WHEN NOT MATCHED THEN
        INSERT
        (
            AUTH_USER_ID,
            USER_TYPE,
            USER_ID,
            PASSWORD_HASH,
            ACCOUNT_STATUS,
            CREATED_AT,
            UPDATED_AT
        )
        VALUES
        (
            source.AUTH_USER_ID,
            source.USER_TYPE,
            source.USER_ID,
            source.PASSWORD_HASH,
            source.ACCOUNT_STATUS,
            source.CREATED_AT,
            source.UPDATED_AT
        )
    """

    print("Merging authentication records...")

    client.query(merge_sql).result()

    print("AUTH_USERS merge completed.")

    # Remove staging table
    client.delete_table(staging_table, not_found_ok=True)

    print("Staging table removed.")


# ============================================================
# Write demo credentials
# ============================================================

def write_demo_credentials(demo_credentials):
    """
    Write plaintext synthetic credentials to a local CSV.

    This file is ONLY for the portfolio/demo environment.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(
        CREDENTIALS_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "USER_TYPE",
                "USER_ID",
                "MOCK_PASSWORD",
            ],
        )

        writer.writeheader()
        writer.writerows(demo_credentials)

    print(f"Demo credentials written to: {CREDENTIALS_FILE}")


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print("BANKING DATA PLATFORM - MOCK AUTH USER GENERATOR")
    print("=" * 60)

    create_auth_table()

    customers = get_customers()
    employees = get_employees()

    auth_records, demo_credentials = build_auth_records(
        customers,
        employees,
    )

    print(f"Total authentication users: {len(auth_records)}")

    insert_auth_records(auth_records)

    write_demo_credentials(demo_credentials)

    print()
    print("=" * 60)
    print("AUTHENTICATION DATA GENERATION COMPLETE")
    print("=" * 60)
    print(f"Customers : {len(customers)}")
    print(f"Employees : {len(employees)}")
    print(f"Total     : {len(auth_records)}")
    print()
    print(f"Credentials file:")
    print(CREDENTIALS_FILE)


if __name__ == "__main__":
    main()