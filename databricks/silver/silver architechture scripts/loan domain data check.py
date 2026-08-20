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
loan_applications_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_applications
    WHERE APPLICATION_ID IS NULL OR CUSTOMER_ID IS NULL OR APPLICATION_DATE IS NULL
       OR REQUESTED_AMOUNT IS NULL OR APPROVAL_STATUS IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

loan_collateral_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_collateral
    WHERE COLLATERAL_ID IS NULL OR LOAN_ID IS NULL OR ASSET_TYPE IS NULL
       OR ASSET_VALUE IS NULL OR VALUATION_DATE IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

loan_repayments_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_repayments
    WHERE REPAYMENT_ID IS NULL OR LOAN_ID IS NULL OR PAYMENT_DATE IS NULL
       OR AMOUNT_PAID IS NULL OR PAYMENT_MODE IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

loan_loans_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loans
    WHERE LOAN_ID IS NULL OR LOAN_APPLICATION_ID IS NULL OR CUSTOMER_ID IS NULL
       OR LOAN_TYPE IS NULL OR PRINCIPAL_AMOUNT IS NULL OR INTEREST_RATE IS NULL
       OR TENURE_MONTHS IS NULL OR EMI_AMOUNT IS NULL OR LOAN_STATUS IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

# COMMAND ----------

# DBTITLE 1,Duplicate Check
loan_applications_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY APPLICATION_ID, CUSTOMER_ID, APPLICATION_DATE,
                         REQUESTED_AMOUNT, APPROVAL_STATUS,
                         BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY APPLICATION_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_applications
    ) WHERE rn > 1
""")

loan_collateral_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY COLLATERAL_ID, LOAN_ID, ASSET_TYPE,
                         ASSET_VALUE, VALUATION_DATE,
                         BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY COLLATERAL_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_collateral
    ) WHERE rn > 1
""")

loan_repayments_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY REPAYMENT_ID, LOAN_ID, PAYMENT_DATE,
                         AMOUNT_PAID, PAYMENT_MODE,
                         BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY REPAYMENT_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_repayments
    ) WHERE rn > 1
""")

loan_loans_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY LOAN_ID, LOAN_APPLICATION_ID, CUSTOMER_ID, LOAN_TYPE,
                         PRINCIPAL_AMOUNT, INTEREST_RATE, TENURE_MONTHS,
                         EMI_AMOUNT, LOAN_STATUS,
                         BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY LOAN_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loans
    ) WHERE rn > 1
""")

# COMMAND ----------

# DBTITLE 1,Export Results to CSV
export_dir = "/tmp/data_quality_exports/loan"
os.makedirs(export_dir, exist_ok=True)

# ── Null checks ───────────────────────────────────────────────────────────────
null_app_path  = f"{export_dir}/loan_applications_null_check.csv"
null_coll_path = f"{export_dir}/loan_collateral_null_check.csv"
null_rep_path  = f"{export_dir}/loan_repayments_null_check.csv"
null_loan_path = f"{export_dir}/loan_loans_null_check.csv"

loan_applications_null_check_df.toPandas().to_csv(null_app_path, index=False)
loan_collateral_null_check_df.toPandas().to_csv(null_coll_path, index=False)
loan_repayments_null_check_df.toPandas().to_csv(null_rep_path, index=False)
loan_loans_null_check_df.toPandas().to_csv(null_loan_path, index=False)

print(f"Null check -> applications: {loan_applications_null_check_df.count()} rows")
print(f"Null check -> collateral:   {loan_collateral_null_check_df.count()} rows")
print(f"Null check -> repayments:   {loan_repayments_null_check_df.count()} rows")
print(f"Null check -> loans:        {loan_loans_null_check_df.count()} rows")

# ── Duplicate checks ──────────────────────────────────────────────────────────
dup_app_path  = f"{export_dir}/loan_applications_duplicate_check.csv"
dup_coll_path = f"{export_dir}/loan_collateral_duplicate_check.csv"
dup_rep_path  = f"{export_dir}/loan_repayments_duplicate_check.csv"
dup_loan_path = f"{export_dir}/loan_loans_duplicate_check.csv"

loan_applications_duplicate_check_df.toPandas().to_csv(dup_app_path, index=False)
loan_collateral_duplicate_check_df.toPandas().to_csv(dup_coll_path, index=False)
loan_repayments_duplicate_check_df.toPandas().to_csv(dup_rep_path, index=False)
loan_loans_duplicate_check_df.toPandas().to_csv(dup_loan_path, index=False)

print(f"Dup check  -> applications: {loan_applications_duplicate_check_df.count()} rows")
print(f"Dup check  -> collateral:   {loan_collateral_duplicate_check_df.count()} rows")
print(f"Dup check  -> repayments:   {loan_repayments_duplicate_check_df.count()} rows")
print(f"Dup check  -> loans:        {loan_loans_duplicate_check_df.count()} rows")

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

null_app_cnt  = loan_applications_null_check_df.count()
null_coll_cnt = loan_collateral_null_check_df.count()
null_rep_cnt  = loan_repayments_null_check_df.count()
null_loan_cnt = loan_loans_null_check_df.count()
dup_app_cnt   = loan_applications_duplicate_check_df.count()
dup_coll_cnt  = loan_collateral_duplicate_check_df.count()
dup_rep_cnt   = loan_repayments_duplicate_check_df.count()
dup_loan_cnt  = loan_loans_duplicate_check_df.count()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Loan Domain Data Quality Check Results"

body = f"""Hi,

Please find attached the data quality check results for the loan domain staging tables.

Null Check Summary:
  - loan_loan_applications: {null_app_cnt} row(s) with nulls
  - loan_loan_collateral:   {null_coll_cnt} row(s) with nulls
  - loan_loan_repayments:   {null_rep_cnt} row(s) with nulls
  - loan_loans:             {null_loan_cnt} row(s) with nulls

Duplicate Check Summary:
  - loan_loan_applications: {dup_app_cnt} duplicate row(s)
  - loan_loan_collateral:   {dup_coll_cnt} duplicate row(s)
  - loan_loan_repayments:   {dup_rep_cnt} duplicate row(s)
  - loan_loans:             {dup_loan_cnt} duplicate row(s)

Regards,
Databricks Data Quality Job
"""
msg.attach(MIMEText(body, "plain"))

_csv_paths = [null_app_path, null_coll_path, null_rep_path, null_loan_path,
              dup_app_path,  dup_coll_path,  dup_rep_path,  dup_loan_path]
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
# ── loan_loans: SCD2 — expire changed records ─────────────────────────────────────
merge_loan_loans = spark.sql("""
MERGE INTO banking_data_processing.silver.loan_loans AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY LOAN_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loans
    ) WHERE rn = 1
) AS source
ON target.LOAN_ID = source.LOAN_ID AND target.IS_CURRENT = TRUE
WHEN MATCHED AND (
       target.LOAN_STATUS  <> source.LOAN_STATUS
    OR COALESCE(target.INTEREST_RATE, 0) <> COALESCE(source.INTEREST_RATE, 0)
    OR COALESCE(target.EMI_AMOUNT, 0)        <> COALESCE(source.EMI_AMOUNT, 0)
    OR target.LOAN_APPLICATION_ID            <> source.LOAN_APPLICATION_ID
    OR target.LOAN_TYPE                      <> source.LOAN_TYPE
    OR COALESCE(target.PRINCIPAL_AMOUNT, 0)  <> COALESCE(source.PRINCIPAL_AMOUNT, 0)
    OR COALESCE(target.TENURE_MONTHS, 0)     <> COALESCE(source.TENURE_MONTHS, 0)
)
THEN UPDATE SET
    target.UPDATED_AT = CURRENT_TIMESTAMP(),
    target.IS_CURRENT = FALSE
""")

# ── loan_loan_applications: SCD Type 1 — expire changed records ───────────────────────
merge_loan_applications = spark.sql("""
MERGE INTO banking_data_processing.silver.loan_loan_applications AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY APPLICATION_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_applications
    ) WHERE rn = 1
) AS source
ON target.APPLICATION_ID = source.APPLICATION_ID
WHEN MATCHED AND (
       target.APPROVAL_STATUS  <> source.APPROVAL_STATUS
    OR target.APPLICATION_DATE <> source.APPLICATION_DATE
    OR COALESCE(target.REQUESTED_AMOUNT, 0) <> COALESCE(source.REQUESTED_AMOUNT, 0)
)
THEN UPDATE SET
    target.APPLICATION_DATE = source.APPLICATION_DATE,
    target.REQUESTED_AMOUNT = source.REQUESTED_AMOUNT,
    target.APPROVAL_STATUS  = source.APPROVAL_STATUS,
    target.UPDATED_AT       = CURRENT_TIMESTAMP(),
    target.BATCH_DATE       = source.BATCH_DATE,
    target.PIPELINE_RUN_ID  = source.PIPELINE_RUN_ID,
    target.DATA_SOURCE      = source.DATA_SOURCE
WHEN NOT MATCHED THEN INSERT (
    APPLICATION_ID, CUSTOMER_ID, APPLICATION_DATE, REQUESTED_AMOUNT, APPROVAL_STATUS,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
) VALUES (
    source.APPLICATION_ID, source.CUSTOMER_ID, source.APPLICATION_DATE,
    source.REQUESTED_AMOUNT, source.APPROVAL_STATUS,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE,
    source.PIPELINE_RUN_ID, source.DATA_SOURCE,
    TRUE, CURRENT_TIMESTAMP(), NULL, CURRENT_TIMESTAMP()
)
""")

# ── loan_loan_collateral: SCD2 — expire changed records ────────────────────────
merge_loan_collateral = spark.sql("""
MERGE INTO banking_data_processing.silver.loan_loan_collateral AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY COLLATERAL_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_collateral
    ) WHERE rn = 1
) AS source
ON target.COLLATERAL_ID = source.COLLATERAL_ID AND target.IS_CURRENT = TRUE
WHEN MATCHED AND (
       COALESCE(target.ASSET_VALUE, 0) <> COALESCE(source.ASSET_VALUE, 0)
    OR target.VALUATION_DATE <> source.VALUATION_DATE
    OR target.ASSET_TYPE     <> source.ASSET_TYPE
)
THEN UPDATE SET
    target.UPDATED_AT = CURRENT_TIMESTAMP(),
    target.IS_CURRENT = FALSE
""")

# ── loan_loan_repayments: fact table — insert new records only ────────────────────
merge_loan_repayments = spark.sql("""
MERGE INTO banking_data_processing.silver.loan_loan_repayments AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY REPAYMENT_ID ORDER BY BATCH_DATE DESC, PIPELINE_RUN_ID DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_repayments
    ) WHERE rn = 1
) AS source
ON target.REPAYMENT_ID = source.REPAYMENT_ID
WHEN NOT MATCHED THEN INSERT (
    REPAYMENT_ID, LOAN_ID, PAYMENT_DATE, AMOUNT_PAID, PAYMENT_MODE,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
) VALUES (
    source.REPAYMENT_ID, source.LOAN_ID, source.PAYMENT_DATE, source.AMOUNT_PAID, source.PAYMENT_MODE,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID,
    source.DATA_SOURCE, TRUE, CURRENT_TIMESTAMP(), NULL, CURRENT_TIMESTAMP()
)
""")

# COMMAND ----------

# DBTITLE 1,Insert Data into Silver Schema Tables
# ── loan_loans: insert new / updated records (SCD2) ────────────────────────────
insert_loan_loans_silver = spark.sql("""
INSERT INTO banking_data_processing.silver.loan_loans
(
    LOAN_ID, LOAN_APPLICATION_ID, CUSTOMER_ID, LOAN_TYPE,
    PRINCIPAL_AMOUNT, INTEREST_RATE, TENURE_MONTHS, EMI_AMOUNT, LOAN_STATUS,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
)
SELECT
    source.LOAN_ID, source.LOAN_APPLICATION_ID, source.CUSTOMER_ID, source.LOAN_TYPE,
    source.PRINCIPAL_AMOUNT, source.INTEREST_RATE, source.TENURE_MONTHS, source.EMI_AMOUNT, source.LOAN_STATUS,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID,
    source.DATA_SOURCE, TRUE AS IS_CURRENT,
    CURRENT_TIMESTAMP() AS EFFECTIVE_FROM, NULL AS EFFECTIVE_TO,
    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY LOAN_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
    ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loans
) AS source
LEFT JOIN banking_data_processing.silver.loan_loans AS target
    ON source.LOAN_ID = target.LOAN_ID AND target.IS_CURRENT = TRUE
WHERE source.rn = 1 AND target.LOAN_ID IS NULL
""")


# ── loan_loan_collateral: insert new / updated records (SCD2) ────────────────────
insert_loan_collateral_silver = spark.sql("""
INSERT INTO banking_data_processing.silver.loan_loan_collateral
(
    COLLATERAL_ID, LOAN_ID, ASSET_TYPE, ASSET_VALUE, VALUATION_DATE,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
)
SELECT
    source.COLLATERAL_ID, source.LOAN_ID, source.ASSET_TYPE, source.ASSET_VALUE, source.VALUATION_DATE,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID,
    source.DATA_SOURCE, TRUE AS IS_CURRENT,
    CURRENT_TIMESTAMP() AS EFFECTIVE_FROM, NULL AS EFFECTIVE_TO,
    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY COLLATERAL_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
    ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.loan_loan_collateral
) AS source
LEFT JOIN banking_data_processing.silver.loan_loan_collateral AS target
    ON source.COLLATERAL_ID = target.COLLATERAL_ID AND target.IS_CURRENT = TRUE
WHERE source.rn = 1 AND target.COLLATERAL_ID IS NULL
""")

# COMMAND ----------

# DBTITLE 1,Send Email of Ingestion Status of Loan Domain
merge_loans_m   = merge_loan_loans.collect()[0].asDict()
merge_app_m     = merge_loan_applications.collect()[0].asDict()
merge_coll_m    = merge_loan_collateral.collect()[0].asDict()
merge_rep_m     = merge_loan_repayments.collect()[0].asDict()
insert_loans_m  = insert_loan_loans_silver.collect()[0].asDict()
insert_coll_m   = insert_loan_collateral_silver.collect()[0].asDict()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Loan Domain Ingestion Status"

body = f"""Hi,

The loan domain ingestion pipeline has completed successfully.

Ingestion Summary:

  loan_loans (silver):
    - Records updated (MERGE):  {merge_loans_m.get('num_updated_rows', 'N/A')}
    - Records inserted:         {insert_loans_m.get('num_affected_rows', 'N/A')}

  loan_loan_applications (silver):
    - Records updated (MERGE):  {merge_app_m.get('num_updated_rows', 'N/A')}
    - Records inserted (MERGE): {merge_app_m.get('num_inserted_rows', 'N/A')}

  loan_loan_collateral (silver):
    - Records updated (MERGE):  {merge_coll_m.get('num_updated_rows', 'N/A')}
    - Records inserted:         {insert_coll_m.get('num_affected_rows', 'N/A')}

  loan_loan_repayments (silver):
    - Records inserted (MERGE): {merge_rep_m.get('num_inserted_rows', 'N/A')}

Regards,
Databricks Ingestion Pipeline
"""
msg.attach(MIMEText(body, "plain"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print(f"Ingestion status email sent to {RECIPIENT_EMAIL}")
print(f"  loans        -> updated: {merge_loans_m.get('num_updated_rows','N/A')}, inserted: {insert_loans_m.get('num_affected_rows','N/A')}")
print(f"  applications -> updated: {merge_app_m.get('num_updated_rows','N/A')},  inserted: {merge_app_m.get('num_inserted_rows','N/A')}")
print(f"  collateral   -> updated: {merge_coll_m.get('num_updated_rows','N/A')}, inserted: {insert_coll_m.get('num_affected_rows','N/A')}")
print(f"  repayments   -> inserted: {merge_rep_m.get('num_inserted_rows','N/A')}")