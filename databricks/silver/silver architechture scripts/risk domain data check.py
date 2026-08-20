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
# ASSIGNED_TO, ASSIGNEE_EMP_ID, RESOLUTION_DATE are nullable (alert may not be resolved yet)
risk_fraud_alerts_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.risk_fraud_alerts
    WHERE ALERT_ID IS NULL OR TRANSACTION_ID IS NULL
       OR FRAUD_SCORE IS NULL OR ALERT_REASON IS NULL OR ALERT_STATUS IS NULL
       OR ALERT_TIMESTAMP IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

# COMMAND ----------

# DBTITLE 1,Duplicate Check
risk_fraud_alerts_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY ALERT_ID, TRANSACTION_ID, FRAUD_SCORE, ALERT_REASON,
                         ALERT_STATUS, ALERT_TIMESTAMP,
                         BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY ALERT_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.risk_fraud_alerts
    ) WHERE rn > 1
""")

# COMMAND ----------

# DBTITLE 1,Export Results to CSV
export_dir = "/tmp/data_quality_exports/risk"
os.makedirs(export_dir, exist_ok=True)

null_alerts_path = f"{export_dir}/risk_fraud_alerts_null_check.csv"
dup_alerts_path  = f"{export_dir}/risk_fraud_alerts_duplicate_check.csv"

risk_fraud_alerts_null_check_df.toPandas().to_csv(null_alerts_path, index=False)
risk_fraud_alerts_duplicate_check_df.toPandas().to_csv(dup_alerts_path, index=False)

print(f"Null check -> fraud_alerts: {risk_fraud_alerts_null_check_df.count()} rows")
print(f"Dup check  -> fraud_alerts: {risk_fraud_alerts_duplicate_check_df.count()} rows")

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

null_alert_cnt = risk_fraud_alerts_null_check_df.count()
dup_alert_cnt  = risk_fraud_alerts_duplicate_check_df.count()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Risk Domain Data Quality Check Results"

body = f"""Hi,

Please find attached the data quality check results for the risk domain staging tables.

Null Check Summary:
  - risk_fraud_alerts: {null_alert_cnt} row(s) with nulls

Duplicate Check Summary:
  - risk_fraud_alerts: {dup_alert_cnt} duplicate row(s)

Regards,
Databricks Data Quality Job
"""
msg.attach(MIMEText(body, "plain"))

_csv_paths = [null_alerts_path, dup_alerts_path]
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
# ── risk_fraud_alerts: upsert — alert status and assignment can change ───────────────
merge_risk_fraud_alerts = spark.sql("""
MERGE INTO banking_data_processing.silver.risk_fraud_alerts AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY ALERT_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.risk_fraud_alerts
    ) WHERE rn = 1
) AS source
ON target.ALERT_ID = source.ALERT_ID
WHEN MATCHED AND (
       target.ALERT_STATUS   <> source.ALERT_STATUS
    OR COALESCE(target.ASSIGNED_TO, '')      <> COALESCE(source.ASSIGNED_TO, '')
    OR COALESCE(target.ASSIGNEE_EMP_ID, '')  <> COALESCE(source.ASSIGNEE_EMP_ID, '')
    OR COALESCE(CAST(target.RESOLUTION_DATE AS STRING), '')
       <> COALESCE(CAST(source.RESOLUTION_DATE AS STRING), '')
    OR COALESCE(target.FRAUD_SCORE, 0) <> COALESCE(source.FRAUD_SCORE, 0)
)
THEN UPDATE SET
    target.ALERT_STATUS    = source.ALERT_STATUS,
    target.ASSIGNED_TO     = source.ASSIGNED_TO,
    target.ASSIGNEE_EMP_ID = source.ASSIGNEE_EMP_ID,
    target.RESOLUTION_DATE = source.RESOLUTION_DATE,
    target.FRAUD_SCORE     = source.FRAUD_SCORE,
    target.BATCH_DATE      = source.BATCH_DATE,
    target.PIPELINE_RUN_ID = source.PIPELINE_RUN_ID,
    target.DATA_SOURCE     = source.DATA_SOURCE,
    target.UPDATED_AT      = CURRENT_TIMESTAMP(),
    target.LOAD_TIMESTAMP  = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (
    ALERT_ID, TRANSACTION_ID, FRAUD_SCORE, ALERT_REASON, ALERT_STATUS,
    ALERT_TIMESTAMP, ASSIGNED_TO, ASSIGNEE_EMP_ID, RESOLUTION_DATE,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
) VALUES (
    source.ALERT_ID, source.TRANSACTION_ID, source.FRAUD_SCORE, source.ALERT_REASON, source.ALERT_STATUS,
    source.ALERT_TIMESTAMP, source.ASSIGNED_TO, source.ASSIGNEE_EMP_ID, source.RESOLUTION_DATE,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID,
    source.DATA_SOURCE, TRUE, CURRENT_TIMESTAMP(), NULL, CURRENT_TIMESTAMP()
)
""")

# COMMAND ----------

# DBTITLE 1,Send Email of Ingestion Status of Risk Domain
merge_alert_m = merge_risk_fraud_alerts.collect()[0].asDict()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Risk Domain Ingestion Status"

body = f"""Hi,

The risk domain ingestion pipeline has completed successfully.

Ingestion Summary:

  risk_fraud_alerts (silver):
    - Records updated (MERGE):  {merge_alert_m.get('num_updated_rows', 'N/A')}
    - Records inserted (MERGE): {merge_alert_m.get('num_inserted_rows', 'N/A')}

Regards,
Databricks Ingestion Pipeline
"""
msg.attach(MIMEText(body, "plain"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print(f"Ingestion status email sent to {RECIPIENT_EMAIL}")
print(f"  fraud_alerts -> updated: {merge_alert_m.get('num_updated_rows','N/A')}, inserted: {merge_alert_m.get('num_inserted_rows','N/A')}")