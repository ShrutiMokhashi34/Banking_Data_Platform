# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Import Required Libraries
import pandas as pd
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# COMMAND ----------

# DBTITLE 1,NULL Check
org_branches_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.org_branches
    WHERE BRANCH_ID IS NULL OR BRANCH_NAME IS NULL OR CITY IS NULL
       OR STATE IS NULL OR COUNTRY IS NULL OR OPENED_DATE IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

org_employees_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.org_employees
    WHERE EMPLOYEE_ID IS NULL OR BRANCH_ID IS NULL
       OR FIRST_NAME IS NULL OR LAST_NAME IS NULL
       OR DESIGNATION IS NULL OR DEPARTMENT IS NULL OR HIRE_DATE IS NULL
       OR EMPLOYEE_STATUS IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

# COMMAND ----------

# DBTITLE 1,Duplicate Check
org_branches_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY BRANCH_ID, BRANCH_NAME, CITY, STATE, COUNTRY,
                         OPENED_DATE, BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY BRANCH_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.org_branches
    ) WHERE rn > 1
""")

org_employees_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY EMPLOYEE_ID, BRANCH_ID, FIRST_NAME, LAST_NAME,
                         DESIGNATION, DEPARTMENT, HIRE_DATE, EMPLOYEE_STATUS,
                         BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY EMPLOYEE_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.org_employees
    ) WHERE rn > 1
""")

# COMMAND ----------

# DBTITLE 1,Export Results to CSV
export_dir = "/tmp/data_quality_exports/org"
os.makedirs(export_dir, exist_ok=True)

null_branches_path  = f"{export_dir}/org_branches_null_check.csv"
null_employees_path = f"{export_dir}/org_employees_null_check.csv"
dup_branches_path   = f"{export_dir}/org_branches_duplicate_check.csv"
dup_employees_path  = f"{export_dir}/org_employees_duplicate_check.csv"

org_branches_null_check_df.toPandas().to_csv(null_branches_path, index=False)
org_employees_null_check_df.toPandas().to_csv(null_employees_path, index=False)
org_branches_duplicate_check_df.toPandas().to_csv(dup_branches_path, index=False)
org_employees_duplicate_check_df.toPandas().to_csv(dup_employees_path, index=False)

print(f"Null check -> branches:  {org_branches_null_check_df.count()} rows")
print(f"Null check -> employees: {org_employees_null_check_df.count()} rows")
print(f"Dup check  -> branches:  {org_branches_duplicate_check_df.count()} rows")
print(f"Dup check  -> employees: {org_employees_duplicate_check_df.count()} rows")

# COMMAND ----------

# DBTITLE 1,Setup Email Secrets (run once)
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

try:
    w.secrets.create_scope(scope="email-scope")
    print("Secret scope 'email-scope' created.")
except Exception as e:
    if "already exists" in str(e).lower():
        print("Secret scope 'email-scope' already exists — skipping creation.")
    else:
        raise

existing_keys = {s.key for s in w.secrets.list_secrets(scope="email-scope")}

if "gmail-address" not in existing_keys or "gmail-app-password" not in existing_keys:
    from getpass import getpass
    gmail_address  = getpass("Enter your Gmail address: ")
    gmail_app_pass = getpass("Enter your Gmail App Password: ")
    w.secrets.put_secret(scope="email-scope", key="gmail-address",      string_value=gmail_address)
    w.secrets.put_secret(scope="email-scope", key="gmail-app-password", string_value=gmail_app_pass)
    print("Secrets stored successfully. You can now run the email cells.")
else:
    print("Secrets already configured — skipping setup.")

# COMMAND ----------

# DBTITLE 1,Send Email with CSV Attachments
SENDER_EMAIL    = dbutils.secrets.get(scope="email-scope", key="gmail-address")
SENDER_PASSWORD = dbutils.secrets.get(scope="email-scope", key="gmail-app-password").replace(" ", "")
RECIPIENT_EMAIL = "bankingdataplatform.project@gmail.com"

null_br_cnt = org_branches_null_check_df.count()
null_em_cnt = org_employees_null_check_df.count()
dup_br_cnt  = org_branches_duplicate_check_df.count()
dup_em_cnt  = org_employees_duplicate_check_df.count()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Org Domain Data Quality Check Results"

body = f"""Hi,

Please find attached the data quality check results for the org domain staging tables.

Null Check Summary:
  - org_branches:  {null_br_cnt} row(s) with nulls
  - org_employees: {null_em_cnt} row(s) with nulls

Duplicate Check Summary:
  - org_branches:  {dup_br_cnt} duplicate row(s)
  - org_employees: {dup_em_cnt} duplicate row(s)

Regards,
Databricks Data Quality Job
"""
msg.attach(MIMEText(body, "plain"))

_csv_paths = [null_branches_path, null_employees_path, dup_branches_path, dup_employees_path]
MAX_ATTACH_BYTES = 25 * 1024 * 1024
total_attach_size = sum(os.path.getsize(fp) for fp in _csv_paths)

if total_attach_size <= MAX_ATTACH_BYTES:
    for file_path in _csv_paths:
        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(file_path)}"')
        msg.attach(part)
else:
    print(f"Attachments skipped — total size {total_attach_size / (1024*1024):.1f} MB exceeds Gmail's 25 MB limit.")

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print(f"Email sent to {RECIPIENT_EMAIL}")

# COMMAND ----------

# DBTITLE 1,Merge Data into Silver Schema Tables
# ── org_branches: SCD2 — expire changed records ──────────────────────────────────
merge_org_branches = spark.sql("""
MERGE INTO banking_data_processing.silver.org_branches AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY BRANCH_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.org_branches
    ) WHERE rn = 1
) AS source
ON target.BRANCH_ID = source.BRANCH_ID AND target.IS_CURRENT = TRUE
WHEN MATCHED AND (
       target.BRANCH_NAME            <> source.BRANCH_NAME
    OR COALESCE(target.MANAGER_EMPLOYEE_ID, '') <> COALESCE(source.MANAGER_EMPLOYEE_ID, '')
    OR target.CITY                   <> source.CITY
    OR target.STATE                  <> source.STATE
    OR target.COUNTRY                <> source.COUNTRY
    OR COALESCE(target.ZIP_CODE, '') <> COALESCE(source.ZIP_CODE, '')
)
THEN UPDATE SET
    target.UPDATED_AT = CURRENT_TIMESTAMP(),
    target.IS_CURRENT = FALSE
""")

# ── org_employees: SCD2 — expire changed records ───────────────────────────────
merge_org_employees = spark.sql("""
MERGE INTO banking_data_processing.silver.org_employees AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY EMPLOYEE_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.org_employees
    ) WHERE rn = 1
) AS source
ON target.EMPLOYEE_ID = source.EMPLOYEE_ID AND target.IS_CURRENT = TRUE
WHEN MATCHED AND (
       target.DESIGNATION     <> source.DESIGNATION
    OR target.DEPARTMENT      <> source.DEPARTMENT
    OR target.EMPLOYEE_STATUS <> source.EMPLOYEE_STATUS
    OR target.BRANCH_ID       <> source.BRANCH_ID
    OR COALESCE(target.SALARY, 0) <> COALESCE(source.SALARY, 0)
)
THEN UPDATE SET
    target.UPDATED_AT = CURRENT_TIMESTAMP(),
    target.IS_CURRENT = FALSE
""")

# COMMAND ----------

# DBTITLE 1,Insert Data into Silver Schema Tables
# ── org_branches: insert new / updated records (SCD2) ──────────────────────────
insert_org_branches_silver = spark.sql("""
INSERT INTO banking_data_processing.silver.org_branches
(
    BRANCH_ID, BRANCH_NAME, CITY, STATE, COUNTRY, ZIP_CODE,
    MANAGER_EMPLOYEE_ID, OPENED_DATE,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
)
SELECT
    source.BRANCH_ID, source.BRANCH_NAME, source.CITY, source.STATE, source.COUNTRY, source.ZIP_CODE,
    source.MANAGER_EMPLOYEE_ID, source.OPENED_DATE,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID,
    source.DATA_SOURCE, TRUE AS IS_CURRENT,
    CURRENT_TIMESTAMP() AS EFFECTIVE_FROM, NULL AS EFFECTIVE_TO,
    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY BRANCH_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
    ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.org_branches
) AS source
LEFT JOIN banking_data_processing.silver.org_branches AS target
    ON source.BRANCH_ID = target.BRANCH_ID AND target.IS_CURRENT = TRUE
WHERE source.rn = 1 AND target.BRANCH_ID IS NULL
""")

# ── org_employees: insert new / updated records (SCD2) ─────────────────────────
insert_org_employees_silver = spark.sql("""
INSERT INTO banking_data_processing.silver.org_employees
(
    EMPLOYEE_ID, BRANCH_ID, FIRST_NAME, LAST_NAME, DESIGNATION, DEPARTMENT,
    HIRE_DATE, SALARY, EMPLOYEE_STATUS,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
)
SELECT
    source.EMPLOYEE_ID, source.BRANCH_ID, source.FIRST_NAME, source.LAST_NAME,
    source.DESIGNATION, source.DEPARTMENT, source.HIRE_DATE, source.SALARY, source.EMPLOYEE_STATUS,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID,
    source.DATA_SOURCE, TRUE AS IS_CURRENT,
    CURRENT_TIMESTAMP() AS EFFECTIVE_FROM, NULL AS EFFECTIVE_TO,
    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY EMPLOYEE_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
    ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.org_employees
) AS source
LEFT JOIN banking_data_processing.silver.org_employees AS target
    ON source.EMPLOYEE_ID = target.EMPLOYEE_ID AND target.IS_CURRENT = TRUE
WHERE source.rn = 1 AND target.EMPLOYEE_ID IS NULL
""")

# COMMAND ----------

# DBTITLE 1,Send Email of Ingestion Status of Org Domain
merge_br_m  = merge_org_branches.collect()[0].asDict()
merge_em_m  = merge_org_employees.collect()[0].asDict()
insert_br_m = insert_org_branches_silver.collect()[0].asDict()
insert_em_m = insert_org_employees_silver.collect()[0].asDict()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Org Domain Ingestion Status"

body = f"""Hi,

The org domain ingestion pipeline has completed successfully.

Ingestion Summary:

  org_branches (silver):
    - Records updated (MERGE):  {merge_br_m.get('num_updated_rows', 'N/A')}
    - Records inserted:         {insert_br_m.get('num_affected_rows', 'N/A')}

  org_employees (silver):
    - Records updated (MERGE):  {merge_em_m.get('num_updated_rows', 'N/A')}
    - Records inserted:         {insert_em_m.get('num_affected_rows', 'N/A')}

Regards,
Databricks Ingestion Pipeline
"""
msg.attach(MIMEText(body, "plain"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print(f"Ingestion status email sent to {RECIPIENT_EMAIL}")
print(f"  branches  -> updated: {merge_br_m.get('num_updated_rows','N/A')}, inserted: {insert_br_m.get('num_affected_rows','N/A')}")
print(f"  employees -> updated: {merge_em_m.get('num_updated_rows','N/A')}, inserted: {insert_em_m.get('num_affected_rows','N/A')}")