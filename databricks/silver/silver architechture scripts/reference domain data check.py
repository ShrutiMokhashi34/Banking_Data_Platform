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
exchange_rates_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.exchange_rates
    WHERE RATE_DATE IS NULL OR CURRENCY IS NULL OR CURRENCY_SYMBOL IS NULL
       OR RATE_TO_INR IS NULL OR SOURCE IS NULL OR BASE_CURRENCY IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")


# COMMAND ----------

# DBTITLE 1,Duplicate Check
exchange_rates_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY RATE_DATE, CURRENCY, BASE_CURRENCY, RATE_TO_INR,
                         SOURCE, BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY RATE_DATE
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.exchange_rates
    ) WHERE rn > 1
""")


# COMMAND ----------

# DBTITLE 1,Export Results to CSV
export_dir = "/tmp/data_quality_exports/reference"
os.makedirs(export_dir, exist_ok=True)

null_rates_path    = f"{export_dir}/exchange_rates_null_check.csv"
dup_rates_path     = f"{export_dir}/exchange_rates_duplicate_check.csv"

exchange_rates_null_check_df.toPandas().to_csv(null_rates_path, index=False)
exchange_rates_duplicate_check_df.toPandas().to_csv(dup_rates_path, index=False)

print(f"Null check -> exchange_rates:      {exchange_rates_null_check_df.count()} rows")
print(f"Dup check  -> exchange_rates:      {exchange_rates_duplicate_check_df.count()} rows")

# COMMAND ----------

# DBTITLE 1,Send Email with CSV Attachments
SENDER_EMAIL    = dbutils.secrets.get(scope="email-scope", key="gmail-address")
SENDER_PASSWORD = dbutils.secrets.get(scope="email-scope", key="gmail-app-password").replace(" ", "")
RECIPIENT_EMAIL = "bankingdataplatform.project@gmail.com"

null_rates_cnt   = exchange_rates_null_check_df.count()
dup_rates_cnt    = exchange_rates_duplicate_check_df.count()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Reference Domain Data Quality Check Results"

body = f"""Hi,

Please find attached the data quality check results for the reference domain staging tables.

Null Check Summary:
  - exchange_rates:     {null_rates_cnt} row(s) with nulls

Duplicate Check Summary:
  - exchange_rates:     {dup_rates_cnt} duplicate row(s)

Regards,
Databricks Data Quality Job
"""
msg.attach(MIMEText(body, "plain"))

_csv_paths = [null_rates_path, dup_rates_path]
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
# ── exchange_rates: upsert by RATE_DATE + CURRENCY ────────────────────────────────
merge_exchange_rates = spark.sql("""
MERGE INTO banking_data_processing.silver.exchange_rates AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY RATE_DATE, CURRENCY
            ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.exchange_rates
    ) WHERE rn = 1
) AS source
ON target.RATE_DATE = source.RATE_DATE AND target.CURRENCY = source.CURRENCY
WHEN MATCHED AND (
    COALESCE(target.RATE_TO_INR, 0) <> COALESCE(source.RATE_TO_INR, 0)
)
THEN UPDATE SET
    target.RATE_TO_INR     = source.RATE_TO_INR,
    target.CURRENCY_SYMBOL = source.CURRENCY_SYMBOL,
    target.SOURCE          = source.SOURCE,
    target.BATCH_DATE      = source.BATCH_DATE,
    target.PIPELINE_RUN_ID = source.PIPELINE_RUN_ID,
    target.DATA_SOURCE     = source.DATA_SOURCE,
    target.LOAD_TIMESTAMP  = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (
    RATE_DATE, CURRENCY, CURRENCY_SYMBOL, RATE_TO_INR, SOURCE, BASE_CURRENCY,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
) VALUES (
    source.RATE_DATE, source.CURRENCY, source.CURRENCY_SYMBOL, source.RATE_TO_INR,
    source.SOURCE, 'INR',
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE,
    source.PIPELINE_RUN_ID, source.DATA_SOURCE,
    TRUE, CURRENT_TIMESTAMP(), NULL, CURRENT_TIMESTAMP()
)
""")


# COMMAND ----------

# DBTITLE 1,Send Email of Ingestion Status of Reference Domain
merge_rates_m   = merge_exchange_rates.collect()[0].asDict()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Reference Domain Ingestion Status"

body = f"""Hi,

The reference domain ingestion pipeline has completed successfully.

Ingestion Summary:

  exchange_rates (silver):
    - Records updated (MERGE):  {merge_rates_m.get('num_updated_rows', 'N/A')}
    - Records inserted (MERGE): {merge_rates_m.get('num_inserted_rows', 'N/A')}

Regards,
Databricks Ingestion Pipeline
"""
msg.attach(MIMEText(body, "plain"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print(f"Ingestion status email sent to {RECIPIENT_EMAIL}")
print(f"  exchange_rates      -> updated: {merge_rates_m.get('num_updated_rows','N/A')}, inserted: {merge_rates_m.get('num_inserted_rows','N/A')}")