# Databricks notebook source
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
customer_null_check_df = spark.sql("""
    SELECT *
    FROM banking_data_platform_snowflake_stg_catalog.stg.cust_customers
    WHERE customer_id IS NULL OR first_name IS NULL OR last_name IS NULL OR dob IS NULL OR gender IS NULL OR email IS NULL OR phone IS NULL OR occupation IS NULL OR annual_income IS NULL OR customer_since IS NULL OR risk_rating IS NULL OR customer_status IS NULL OR created_at IS NULL OR updated_at IS NULL OR source_system IS NULL OR batch_date IS NULL OR pipeline_run_id IS NULL OR data_source IS NULL
""")

customer_addresses_null_check_df = spark.sql("""
    SELECT *
    FROM banking_data_platform_snowflake_stg_catalog.stg.cust_customer_addresses
    WHERE address_id IS NULL OR customer_id IS NULL OR address_type IS NULL OR city IS NULL OR state IS NULL OR postal_code IS NULL OR country IS NULL OR is_current IS NULL OR effective_date IS NULL OR expiry_date IS NULL OR batch_date IS NULL OR pipeline_run_id IS NULL OR data_source IS NULL
""")

customer_kyc_null_check_df = spark.sql("""
    SELECT *
    FROM banking_data_platform_snowflake_stg_catalog.stg.cust_kyc
    WHERE customer_id IS NULL OR pan_number IS NULL OR aadhaar_number IS NULL OR pan_verified IS NULL OR aadhaar_verified IS NULL OR address_verified IS NULL OR kyc_status IS NULL OR batch_date IS NULL OR pipeline_run_id IS NULL OR data_source IS NULL
""")

# COMMAND ----------

# DBTITLE 1,Duplicate Check
customers_duplicate_check_df = spark.sql("""
    SELECT *
    FROM 
    (
     SELECT *, row_number() OVER (PARTITION BY customer_id,first_name, last_name, dob, gender, email, phone, occupation, annual_income, customer_since, risk_rating, customer_status, created_at, updated_at, source_system, batch_date, pipeline_run_id, data_source 
     ORDER BY customer_id) as rn FROM banking_data_platform_snowflake_stg_catalog.stg.cust_customers
    )
    WHERE rn > 1
    
""")

customer_addresses_duplicate_check_df = spark.sql("""
    SELECT *
    FROM 
    (
     SELECT *, row_number() OVER (PARTITION BY address_id, customer_id,address_type,address_line1,city,state,postal_code,country,is_current,effective_date,expiry_date,batch_date,pipeline_run_id,data_source 
     ORDER BY address_id) as rn FROM banking_data_platform_snowflake_stg_catalog.stg.cust_customer_addresses
    )
    WHERE rn > 1
    
""")

customer_kyc_duplicate_check_df = spark.sql("""
    SELECT *
    FROM 
    (
     SELECT *, row_number() OVER (PARTITION BY customer_id, pan_number, aadhaar_number, pan_verified, aadhaar_verified, address_verified, kyc_status, batch_date, pipeline_run_id, data_source
     ORDER BY customer_id) as rn FROM banking_data_platform_snowflake_stg_catalog.stg.cust_kyc
    )
    WHERE rn > 1
    
""")

# COMMAND ----------

# DBTITLE 1,Export Results to CSV
export_dir = "/tmp/data_quality_exports"
os.makedirs(export_dir, exist_ok=True)

# ── Null checks ───────────────────────────────────────────────────────────────
null_check_path          = f"{export_dir}/customer_null_check.csv"
null_addr_check_path     = f"{export_dir}/customer_addresses_null_check.csv"
null_kyc_check_path      = f"{export_dir}/customer_kyc_null_check.csv"

customer_null_check_df.toPandas().to_csv(null_check_path, index=False)
customer_addresses_null_check_df.toPandas().to_csv(null_addr_check_path, index=False)
customer_kyc_null_check_df.toPandas().to_csv(null_kyc_check_path, index=False)

print(f"Null check  -> customers: {customer_null_check_df.count()} rows")
print(f"Null check  -> addresses: {customer_addresses_null_check_df.count()} rows")
print(f"Null check  -> kyc:       {customer_kyc_null_check_df.count()} rows")

# ── Duplicate checks ──────────────────────────────────────────────────────────
dup_check_path           = f"{export_dir}/customer_duplicate_check.csv"
dup_addr_check_path      = f"{export_dir}/customer_addresses_duplicate_check.csv"
dup_kyc_check_path       = f"{export_dir}/customer_kyc_duplicate_check.csv"

customers_duplicate_check_df.toPandas().to_csv(dup_check_path, index=False)
customer_addresses_duplicate_check_df.toPandas().to_csv(dup_addr_check_path, index=False)
customer_kyc_duplicate_check_df.toPandas().to_csv(dup_kyc_check_path, index=False)

print(f"Dup check   -> customers: {customers_duplicate_check_df.count()} rows")
print(f"Dup check   -> addresses: {customer_addresses_duplicate_check_df.count()} rows")
print(f"Dup check   -> kyc:       {customer_kyc_duplicate_check_df.count()} rows")

# COMMAND ----------

# DBTITLE 1,Setup Email Secrets (run once)
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create scope (skip if already exists)
try:
    w.secrets.create_scope(scope="email-scope")
    print("Secret scope 'email-scope' created.")
except Exception as e:
    if "already exists" in str(e).lower():
        print("Secret scope 'email-scope' already exists — skipping creation.")
    else:
        raise

# Only prompt if secrets are not already stored
existing_keys = {s.key for s in w.secrets.list_secrets(scope="email-scope")}

if "gmail-address" not in existing_keys or "gmail-app-password" not in existing_keys:
    from getpass import getpass
    gmail_address  = getpass("Enter your Gmail address: ")
    gmail_app_pass = getpass("Enter your Gmail App Password: ")
    w.secrets.put_secret(scope="email-scope", key="gmail-address",      string_value=gmail_address)
    w.secrets.put_secret(scope="email-scope", key="gmail-app-password", string_value=gmail_app_pass)
    print("Secrets stored successfully. You can now run the email cell.")
else:
    print("Secrets already configured — skipping setup.")

# COMMAND ----------

# DBTITLE 1,Send Email with CSV Attachments

# ── Config ────────────────────────────────────────────────────────────────────
# Store your Gmail address and App Password in Databricks secrets:
#   databricks secrets create-scope email-scope
#   databricks secrets put-secret email-scope gmail-address
#   databricks secrets put-secret email-scope gmail-app-password
SENDER_EMAIL    = dbutils.secrets.get(scope="email-scope", key="gmail-address")
SENDER_PASSWORD = dbutils.secrets.get(scope="email-scope", key="gmail-app-password").replace(" ", "")
RECIPIENT_EMAIL = "bankingdataplatform.project@gmail.com"   # ← replace with the target Gmail address
# ──────────────────────────────────────────────────────────────────────────────

null_count      = customer_null_check_df.count()
null_addr_count = customer_addresses_null_check_df.count()
null_kyc_count  = customer_kyc_null_check_df.count()
dup_count       = customers_duplicate_check_df.count()
dup_addr_count  = customer_addresses_duplicate_check_df.count()
dup_kyc_count   = customer_kyc_duplicate_check_df.count()

# Build email
msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Customer Domain Data Quality Check Results"

body = f"""Hi,

Please find attached the data quality check results for the customer domain staging tables.

Null Check Summary:
  - cust_customers:         {null_count} row(s) with nulls
  - cust_customer_addresses:{null_addr_count} row(s) with nulls
  - cust_kyc:               {null_kyc_count} row(s) with nulls

Duplicate Check Summary:
  - cust_customers:         {dup_count} duplicate row(s)
  - cust_customer_addresses:{dup_addr_count} duplicate row(s)
  - cust_kyc:               {dup_kyc_count} duplicate row(s)

Regards,
Databricks Data Quality Job
"""
msg.attach(MIMEText(body, "plain"))

# Attach CSVs only if collectively under Gmail's 25 MB limit
_csv_paths = [null_check_path, null_addr_check_path, null_kyc_check_path,
              dup_check_path,  dup_addr_check_path,  dup_kyc_check_path]
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

# Send via Gmail SMTP
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print(f"Email sent to {RECIPIENT_EMAIL}")
print(f"  Null check   -> customers: {null_count}, addresses: {null_addr_count}, kyc: {null_kyc_count}")
print(f"  Dup  check   -> customers: {dup_count},  addresses: {dup_addr_count},  kyc: {dup_kyc_count}")

# COMMAND ----------

# DBTITLE 1,Merge Data into Silver Schema Tables
merge_customers = spark.sql("""
MERGE INTO banking_data_processing.silver.cust_customers AS target

USING
(
    SELECT *
    FROM
    (
        SELECT
            *,
            ROW_NUMBER() OVER
            (
                PARTITION BY CUSTOMER_ID
                ORDER BY
                    UPDATED_AT DESC,
                    BATCH_DATE DESC
            ) AS rn
        FROM banking_data_platform_snowflake_stg_catalog.stg.cust_customers
    )
    WHERE rn = 1
) AS source

ON target.customer_id = source.customer_id
AND target.is_current = TRUE

WHEN MATCHED
     AND (
            target.first_name <> source.first_name
         OR target.last_name <> source.last_name
         OR COALESCE(target.email, '') <> COALESCE(source.email, '')
         OR COALESCE(target.phone, '') <> COALESCE(source.phone, '')
         OR COALESCE(target.occupation, '') <> COALESCE(source.occupation, '')
         OR COALESCE(target.annual_income, 0) <> COALESCE(source.annual_income, 0)
         OR target.risk_rating <> source.risk_rating
         OR target.customer_status <> source.customer_status
         )

THEN UPDATE SET

    target.updated_at = CURRENT_TIMESTAMP(),
    target.is_current = FALSE;
""")

merge_customer_addresses = spark.sql("""
MERGE INTO banking_data_processing.silver.cust_customer_addresses AS target

USING
(
    SELECT *
    FROM
    (
        SELECT
            *,
            ROW_NUMBER() OVER
            (
                PARTITION BY ADDRESS_ID
                ORDER BY
                    COALESCE(BATCH_DATE, EFFECTIVE_DATE) DESC,
                    PIPELINE_RUN_ID DESC
            ) AS rn

        FROM banking_data_platform_snowflake_stg_catalog.stg.cust_customer_addresses
    )
    WHERE rn = 1
) AS source

ON target.ADDRESS_ID = source.ADDRESS_ID
AND target.IS_CURRENT = TRUE

WHEN MATCHED
     AND (
            target.CUSTOMER_ID <> source.CUSTOMER_ID
         OR target.ADDRESS_TYPE <> source.ADDRESS_TYPE
         OR COALESCE(target.ADDRESS_LINE1, '')
            <> COALESCE(source.ADDRESS_LINE1, '')

         OR COALESCE(target.ADDRESS_LINE2, '')
            <> COALESCE(source.ADDRESS_LINE2, '')

         OR target.CITY <> source.CITY
         OR target.STATE <> source.STATE
         OR target.POSTAL_CODE <> source.POSTAL_CODE
         OR target.COUNTRY <> source.COUNTRY

         OR target.SOURCE_EFFECTIVE_DATE <> source.EFFECTIVE_DATE

         OR COALESCE(target.SOURCE_EXPIRY_DATE, DATE '9999-12-31')
            <> COALESCE(source.EXPIRY_DATE, DATE '9999-12-31')

         OR target.IS_CURRENT <> source.IS_CURRENT
         )

THEN UPDATE SET

    target.EFFECTIVE_TO = CURRENT_TIMESTAMP(),
    target.IS_CURRENT = FALSE
""")

merge_kyc_silver = spark.sql("""
MERGE INTO banking_data_processing.silver.cust_kyc AS target

USING
(
    SELECT *
    FROM
    (
        SELECT
            CUSTOMER_ID,
            PAN_NUMBER,
            AADHAAR_NUMBER,
            PAN_VERIFIED,
            AADHAAR_VERIFIED,
            ADDRESS_VERIFIED,
            KYC_STATUS,
            BATCH_ID,
            BATCH_DATE,
            PIPELINE_RUN_ID,
            DATA_SOURCE,

            ROW_NUMBER() OVER
            (
                PARTITION BY CUSTOMER_ID
                ORDER BY
                    COALESCE(VERIFICATION_DATE, DATE '1900-01-01') DESC,
                    BATCH_DATE DESC,
                    PIPELINE_RUN_ID DESC
            ) AS rn

        FROM banking_data_platform_snowflake_stg_catalog.stg.cust_kyc
    )
    WHERE rn = 1
) AS source

ON target.CUSTOMER_ID = source.CUSTOMER_ID


WHEN MATCHED
     AND (
            target.PAN_NUMBER <> source.PAN_NUMBER

         OR target.AADHAAR_NUMBER <> source.AADHAAR_NUMBER

         OR target.PAN_VERIFIED <> source.PAN_VERIFIED

         OR target.AADHAAR_VERIFIED <> source.AADHAAR_VERIFIED

         OR target.ADDRESS_VERIFIED <> source.ADDRESS_VERIFIED

         OR target.KYC_STATUS <> source.KYC_STATUS
         )

THEN UPDATE SET

    target.PAN_NUMBER =
        source.PAN_NUMBER,

    target.AADHAAR_NUMBER =
        source.AADHAAR_NUMBER,

    target.PAN_VERIFIED =
        source.PAN_VERIFIED,

    target.AADHAAR_VERIFIED =
        source.AADHAAR_VERIFIED,

    target.ADDRESS_VERIFIED =
        source.ADDRESS_VERIFIED,

    target.KYC_STATUS =
        source.KYC_STATUS,

    target.BATCH_DATE =
        source.BATCH_DATE,

    target.PIPELINE_RUN_ID =
        source.PIPELINE_RUN_ID,

    target.DATA_SOURCE =
        source.DATA_SOURCE,

    target.LOAD_TIMESTAMP =
        CURRENT_TIMESTAMP()


WHEN NOT MATCHED

THEN INSERT
(
    CUSTOMER_ID,

    PAN_NUMBER,
    AADHAAR_NUMBER,

    PAN_VERIFIED,
    AADHAAR_VERIFIED,
    ADDRESS_VERIFIED,

    KYC_STATUS,
	
    BATCH_DATE,
    PIPELINE_RUN_ID,
    DATA_SOURCE,

    LOAD_TIMESTAMP
)

VALUES
(
    source.CUSTOMER_ID,

    source.PAN_NUMBER,
    source.AADHAAR_NUMBER,

    source.PAN_VERIFIED,
    source.AADHAAR_VERIFIED,
    source.ADDRESS_VERIFIED,

    source.KYC_STATUS,
	
    source.BATCH_DATE,
    source.PIPELINE_RUN_ID,
    source.DATA_SOURCE,

    CURRENT_TIMESTAMP()
)
""")

# COMMAND ----------

# DBTITLE 1,Insert Data into Silver Schema Tables
insert_customers_silver = spark.sql("""
    INSERT INTO banking_data_processing.silver.cust_customers
(
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    DOB,
    GENDER,
    EMAIL,
    PHONE,
    OCCUPATION,
    ANNUAL_INCOME,
    CUSTOMER_SINCE,
    RISK_RATING,
    CUSTOMER_STATUS,
    CREATED_AT,
    UPDATED_AT,
    SOURCE_SYSTEM,
    BATCH_DATE,
    PIPELINE_RUN_ID,
    DATA_SOURCE,
    IS_CURRENT
)

SELECT
    source.CUSTOMER_ID,
    source.FIRST_NAME,
    source.LAST_NAME,
    source.DOB,
    source.GENDER,
    source.EMAIL,
    source.PHONE,
    source.OCCUPATION,
    source.ANNUAL_INCOME,
    source.CUSTOMER_SINCE,
    source.RISK_RATING,
    source.CUSTOMER_STATUS,
    source.CREATED_AT,
    source.UPDATED_AT,
    source.SOURCE_SYSTEM,
    source.BATCH_DATE,
    source.PIPELINE_RUN_ID,
    source.DATA_SOURCE,
    TRUE AS IS_CURRENT

FROM banking_data_platform_snowflake_stg_catalog.stg.cust_customers AS source

LEFT JOIN banking_data_processing.silver.cust_customers AS target

    ON source.customer_id = target.customer_id
    AND target.is_current = TRUE

WHERE target.customer_id IS NULL;
    
""")

insert_customer_addresses_silver = spark.sql("""
INSERT INTO banking_data_processing.silver.cust_customer_addresses
(
    ADDRESS_ID,
    CUSTOMER_ID,

    ADDRESS_TYPE,

    ADDRESS_LINE1,
    ADDRESS_LINE2,

    CITY,
    STATE,
    POSTAL_CODE,
    COUNTRY,

    SOURCE_IS_CURRENT,

    SOURCE_EFFECTIVE_DATE,
    SOURCE_EXPIRY_DATE,
    BATCH_DATE,
    PIPELINE_RUN_ID,
    DATA_SOURCE,

    EFFECTIVE_FROM,
    EFFECTIVE_TO,
    IS_CURRENT,

    LOAD_TIMESTAMP
)

SELECT
    source.ADDRESS_ID,
    source.CUSTOMER_ID,

    source.ADDRESS_TYPE,

    source.ADDRESS_LINE1,
    source.ADDRESS_LINE2,

    source.CITY,
    source.STATE,
    source.POSTAL_CODE,
    source.COUNTRY,

    source.IS_CURRENT,

    source.EFFECTIVE_DATE,
    source.EXPIRY_DATE,
    source.BATCH_DATE,
    source.PIPELINE_RUN_ID,
    source.DATA_SOURCE,

    CURRENT_TIMESTAMP() AS EFFECTIVE_FROM,

    NULL AS EFFECTIVE_TO,
    TRUE AS IS_CURRENT,

    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP

FROM
(
    SELECT *
    FROM
    (
        SELECT
            *,
            ROW_NUMBER() OVER
            (
                PARTITION BY ADDRESS_ID
                ORDER BY
                    COALESCE(BATCH_DATE, EFFECTIVE_DATE) DESC,
                    PIPELINE_RUN_ID DESC
            ) AS rn

        FROM banking_data_platform_snowflake_stg_catalog.stg.cust_customer_addresses
    )
    WHERE rn = 1
) AS source

LEFT JOIN banking_data_processing.silver.cust_customer_addresses AS target

    ON source.ADDRESS_ID = target.ADDRESS_ID
    AND target.IS_CURRENT = TRUE

WHERE target.ADDRESS_ID IS NULL
""")

# COMMAND ----------

# DBTITLE 1,Send Email of Ingestion Status of Customer Domain
# Collect operation metrics from Cells 6 & 7
merge_cust_m    = merge_customers.collect()[0].asDict()
merge_addr_m    = merge_customer_addresses.collect()[0].asDict()
merge_kyc_m     = merge_kyc_silver.collect()[0].asDict()
insert_cust_m   = insert_customers_silver.collect()[0].asDict()
insert_addr_m   = insert_customer_addresses_silver.collect()[0].asDict()
# KYC inserts are handled by the WHEN NOT MATCHED clause in the merge above

# Build email
msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Customer Domain Ingestion Status"

body = f"""Hi,

The customer domain ingestion pipeline has completed successfully.

Ingestion Summary:

  cust_customers (silver):
    - Records updated (MERGE):  {merge_cust_m.get('num_updated_rows', 'N/A')}
    - Records inserted:         {insert_cust_m.get('num_affected_rows', 'N/A')}

  cust_customer_addresses (silver):
    - Records updated (MERGE):  {merge_addr_m.get('num_updated_rows', 'N/A')}
    - Records inserted:         {insert_addr_m.get('num_affected_rows', 'N/A')}

  cust_kyc (silver):
    - Records updated (MERGE):  {merge_kyc_m.get('num_updated_rows', 'N/A')}
    - Records inserted (MERGE): {merge_kyc_m.get('num_inserted_rows', 'N/A')}

Regards,
Databricks Ingestion Pipeline
"""
msg.attach(MIMEText(body, "plain"))

# Send via Gmail SMTP
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print(f"Ingestion status email sent to {RECIPIENT_EMAIL}")
print(f"  cust_customers   -> updated: {merge_cust_m.get('num_updated_rows', 'N/A')}, inserted: {insert_cust_m.get('num_affected_rows', 'N/A')}")
print(f"  cust_addresses   -> updated: {merge_addr_m.get('num_updated_rows', 'N/A')}, inserted: {insert_addr_m.get('num_affected_rows', 'N/A')}")
print(f"  cust_kyc         -> updated: {merge_kyc_m.get('num_updated_rows', 'N/A')}, inserted: {merge_kyc_m.get('num_inserted_rows', 'N/A')}")