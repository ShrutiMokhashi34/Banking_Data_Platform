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
bank_accounts_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.bank_accounts
    WHERE ACCOUNT_ID IS NULL OR CUSTOMER_ID IS NULL OR BRANCH_ID IS NULL
       OR ACCOUNT_NUMBER IS NULL OR ACCOUNT_TYPE IS NULL OR CURRENCY IS NULL
       OR OPEN_DATE IS NULL OR CURRENT_BALANCE IS NULL OR ACCOUNT_STATUS IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

bank_cards_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.bank_cards
    WHERE CARD_ID IS NULL OR ACCOUNT_ID IS NULL OR CARD_NUMBER IS NULL
       OR CARD_TYPE IS NULL OR NETWORK IS NULL OR ISSUE_DATE IS NULL
       OR EXPIRY_DATE IS NULL OR CARD_STATUS IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

bank_merchants_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.bank_merchants
    WHERE MERCHANT_ID IS NULL OR MERCHANT_NAME IS NULL OR MERCHANT_CATEGORY IS NULL
       OR MERCHANT_TYPE IS NULL OR MERCHANT_CITY IS NULL OR MERCHANT_COUNTRY IS NULL
       OR MERCHANT_STATUS IS NULL OR ONBOARDING_DATE IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

bank_transactions_null_check_df = spark.sql("""
    SELECT * FROM banking_data_platform_snowflake_stg_catalog.stg.bank_transactions
    WHERE TRANSACTION_ID IS NULL OR ACCOUNT_ID IS NULL
       OR TRANSACTION_TIMESTAMP IS NULL OR TRANSACTION_TYPE IS NULL
       OR AMOUNT IS NULL OR CURRENCY IS NULL OR TRANSACTION_CHANNEL IS NULL
       OR TRANSACTION_STATUS IS NULL OR REFERENCE_NUMBER IS NULL
       OR CREATED_AT IS NULL OR UPDATED_AT IS NULL OR SOURCE_SYSTEM IS NULL
       OR BATCH_DATE IS NULL OR PIPELINE_RUN_ID IS NULL OR DATA_SOURCE IS NULL
""")

# COMMAND ----------

# DBTITLE 1,Duplicate Check
bank_accounts_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY ACCOUNT_ID, CUSTOMER_ID, BRANCH_ID, ACCOUNT_NUMBER,
                         ACCOUNT_TYPE, CURRENCY, OPEN_DATE, CURRENT_BALANCE,
                         ACCOUNT_STATUS, BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY ACCOUNT_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_accounts
    ) WHERE rn > 1
""")

bank_cards_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY CARD_ID, ACCOUNT_ID, CARD_NUMBER, CARD_TYPE, NETWORK,
                         ISSUE_DATE, EXPIRY_DATE, CARD_STATUS,
                         BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY CARD_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_cards
    ) WHERE rn > 1
""")

bank_merchants_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY MERCHANT_ID, MERCHANT_NAME, MERCHANT_CATEGORY,
                         MERCHANT_TYPE, MERCHANT_CITY, MERCHANT_COUNTRY,
                         MERCHANT_STATUS, BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY MERCHANT_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_merchants
    ) WHERE rn > 1
""")

bank_transactions_duplicate_check_df = spark.sql("""
    SELECT * FROM (
        SELECT *, row_number() OVER (
            PARTITION BY TRANSACTION_ID, ACCOUNT_ID, TRANSACTION_TIMESTAMP,
                         TRANSACTION_TYPE, AMOUNT, CURRENCY, TRANSACTION_STATUS,
                         BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE
            ORDER BY TRANSACTION_ID
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_transactions
    ) WHERE rn > 1
""")

# COMMAND ----------

# DBTITLE 1,Export Results to CSV
export_dir = "/tmp/data_quality_exports/banking"
os.makedirs(export_dir, exist_ok=True)

# ── Null checks ───────────────────────────────────────────────────────────────
null_accounts_path     = f"{export_dir}/bank_accounts_null_check.csv"
null_cards_path        = f"{export_dir}/bank_cards_null_check.csv"
null_merchants_path    = f"{export_dir}/bank_merchants_null_check.csv"
null_transactions_path = f"{export_dir}/bank_transactions_null_check.csv"

bank_accounts_null_check_df.toPandas().to_csv(null_accounts_path, index=False)
bank_cards_null_check_df.toPandas().to_csv(null_cards_path, index=False)
bank_merchants_null_check_df.toPandas().to_csv(null_merchants_path, index=False)
bank_transactions_null_check_df.toPandas().to_csv(null_transactions_path, index=False)

print(f"Null check -> accounts:     {bank_accounts_null_check_df.count()} rows")
print(f"Null check -> cards:        {bank_cards_null_check_df.count()} rows")
print(f"Null check -> merchants:    {bank_merchants_null_check_df.count()} rows")
print(f"Null check -> transactions: {bank_transactions_null_check_df.count()} rows")

# ── Duplicate checks ──────────────────────────────────────────────────────────
dup_accounts_path     = f"{export_dir}/bank_accounts_duplicate_check.csv"
dup_cards_path        = f"{export_dir}/bank_cards_duplicate_check.csv"
dup_merchants_path    = f"{export_dir}/bank_merchants_duplicate_check.csv"
dup_transactions_path = f"{export_dir}/bank_transactions_duplicate_check.csv"

bank_accounts_duplicate_check_df.toPandas().to_csv(dup_accounts_path, index=False)
bank_cards_duplicate_check_df.toPandas().to_csv(dup_cards_path, index=False)
bank_merchants_duplicate_check_df.toPandas().to_csv(dup_merchants_path, index=False)
bank_transactions_duplicate_check_df.toPandas().to_csv(dup_transactions_path, index=False)

print(f"Dup check  -> accounts:     {bank_accounts_duplicate_check_df.count()} rows")
print(f"Dup check  -> cards:        {bank_cards_duplicate_check_df.count()} rows")
print(f"Dup check  -> merchants:    {bank_merchants_duplicate_check_df.count()} rows")
print(f"Dup check  -> transactions: {bank_transactions_duplicate_check_df.count()} rows")

# COMMAND ----------

# DBTITLE 1,Setup Email Secrets (run once)
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create scope if it doesn't exist
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
    print("Secrets stored successfully. You can now run the email cells.")
else:
    print("Secrets already configured — skipping setup.")

# COMMAND ----------

# DBTITLE 1,Send Email with CSV Attachments
# ── Config ────────────────────────────────────────────────────────────────────
SENDER_EMAIL    = dbutils.secrets.get(scope="email-scope", key="gmail-address")
SENDER_PASSWORD = dbutils.secrets.get(scope="email-scope", key="gmail-app-password").replace(" ", "")
RECIPIENT_EMAIL = "bankingdataplatform.project@gmail.com"
# ──────────────────────────────────────────────────────────────────────────────

null_acc_cnt  = bank_accounts_null_check_df.count()
null_card_cnt = bank_cards_null_check_df.count()
null_merch_cnt = bank_merchants_null_check_df.count()
null_txn_cnt  = bank_transactions_null_check_df.count()
dup_acc_cnt   = bank_accounts_duplicate_check_df.count()
dup_card_cnt  = bank_cards_duplicate_check_df.count()
dup_merch_cnt = bank_merchants_duplicate_check_df.count()
dup_txn_cnt   = bank_transactions_duplicate_check_df.count()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Banking Domain Data Quality Check Results"

body = f"""Hi,
Please find attached the data quality check results for the banking domain staging tables.
Null Check Summary:
  - bank_accounts:     {null_acc_cnt} row(s) with nulls
  - bank_cards:        {null_card_cnt} row(s) with nulls
  - bank_merchants:    {null_merch_cnt} row(s) with nulls
  - bank_transactions: {null_txn_cnt} row(s) with nulls
Duplicate Check Summary:
  - bank_accounts:     {dup_acc_cnt} duplicate row(s)
  - bank_cards:        {dup_card_cnt} duplicate row(s)
  - bank_merchants:    {dup_merch_cnt} duplicate row(s)
  - bank_transactions: {dup_txn_cnt} duplicate row(s)
"""
msg.attach(MIMEText(body, "plain"))

attachments = [
    (null_accounts_path,     null_acc_cnt),
    (null_cards_path,        null_card_cnt),
    (null_merchants_path,    null_merch_cnt),
    (null_transactions_path, null_txn_cnt),
    (dup_accounts_path,      dup_acc_cnt),
    (dup_cards_path,         dup_card_cnt),
    (dup_merchants_path,     dup_merch_cnt),
    (dup_transactions_path,  dup_txn_cnt),
]
MAX_ATTACH_BYTES = 25 * 1024 * 1024
total_attach_size = sum(os.path.getsize(fp) for fp, cnt in attachments if cnt > 0)

if total_attach_size <= MAX_ATTACH_BYTES:
    for file_path, cnt in attachments:
        if cnt > 0:
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
print(f"  Null  -> accounts: {null_acc_cnt}, cards: {null_card_cnt}, merchants: {null_merch_cnt}, transactions: {null_txn_cnt}")
print(f"  Dup   -> accounts: {dup_acc_cnt},  cards: {dup_card_cnt},  merchants: {dup_merch_cnt},  transactions: {dup_txn_cnt}")

# COMMAND ----------

# DBTITLE 1,Merge Data into Silver Schema Tables
# ── bank_accounts: SCD2 — expire changed records ─────────────────────────────────
merge_bank_accounts = spark.sql("""
MERGE INTO banking_data_processing.silver.bank_accounts AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY ACCOUNT_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_accounts
    ) WHERE rn = 1
) AS source
ON target.ACCOUNT_ID = source.ACCOUNT_ID AND target.IS_CURRENT = TRUE
WHEN MATCHED AND (
       COALESCE(target.CURRENT_BALANCE, 0)  <> COALESCE(source.CURRENT_BALANCE, 0)
    OR target.ACCOUNT_STATUS <> source.ACCOUNT_STATUS
    OR target.BRANCH_ID      <> source.BRANCH_ID
    OR target.ACCOUNT_TYPE   <> source.ACCOUNT_TYPE
    OR target.CURRENCY       <> source.CURRENCY
)
THEN UPDATE SET
    target.UPDATED_AT  = CURRENT_TIMESTAMP(),
    target.IS_CURRENT  = FALSE
""")

# ── bank_cards: SCD2 — expire changed records ──────────────────────────────────
merge_bank_cards = spark.sql("""
MERGE INTO banking_data_processing.silver.bank_cards AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY CARD_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_cards
    ) WHERE rn = 1
) AS source
ON target.CARD_ID = source.CARD_ID AND target.IS_CURRENT = TRUE
WHEN MATCHED AND (
       target.CARD_STATUS  <> source.CARD_STATUS
    OR target.EXPIRY_DATE  <> source.EXPIRY_DATE
    OR COALESCE(target.CREDIT_LIMIT, 0) <> COALESCE(source.CREDIT_LIMIT, 0)
    OR target.ACCOUNT_ID <> source.ACCOUNT_ID
    OR target.CARD_TYPE  <> source.CARD_TYPE
    OR target.NETWORK    <> source.NETWORK
)
THEN UPDATE SET
    target.UPDATED_AT = CURRENT_TIMESTAMP(),
    target.IS_CURRENT = FALSE
""")

# ── bank_merchants: SCD2 — expire changed records ───────────────────────
merge_bank_merchants = spark.sql("""
MERGE INTO banking_data_processing.silver.bank_merchants AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY MERCHANT_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_merchants
    ) WHERE rn = 1
) AS source
ON target.MERCHANT_ID = source.MERCHANT_ID AND target.IS_CURRENT = TRUE
WHEN MATCHED AND (
       target.MERCHANT_NAME     <> source.MERCHANT_NAME
    OR target.MERCHANT_CATEGORY <> source.MERCHANT_CATEGORY
    OR target.MERCHANT_TYPE     <> source.MERCHANT_TYPE
    OR COALESCE(target.CITY, '')           <> COALESCE(source.MERCHANT_CITY, '')
    OR COALESCE(target.STATE, '')           <> COALESCE(source.MERCHANT_STATE, '')
    OR COALESCE(target.COUNTRY, '')           <> COALESCE(source.MERCHANT_COUNTRY, '')
    OR target.MERCHANT_STATUS   <> source.MERCHANT_STATUS
    OR COALESCE(target.ACCEPTS_UPI, '')   <> COALESCE(source.ACCEPTS_UPI, '')
    OR COALESCE(target.ACCEPTS_CARDS, '') <> COALESCE(source.ACCEPTS_CARDS, '')
    OR COALESCE(target.AVG_TICKET_SIZE, 0) <> COALESCE(source.AVERAGE_TICKET_SIZE, 0)
)
THEN UPDATE SET
    target.UPDATED_AT = CURRENT_TIMESTAMP(),
    target.IS_CURRENT = FALSE
""")

# ── bank_transactions: fact table — insert new records only ──────────────────────
merge_bank_transactions = spark.sql("""
MERGE INTO banking_data_processing.silver.bank_transactions AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY TRANSACTION_ID ORDER BY BATCH_DATE DESC, PIPELINE_RUN_ID DESC
        ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_transactions
    ) WHERE rn = 1
) AS source
ON target.TRANSACTION_ID = source.TRANSACTION_ID
WHEN NOT MATCHED THEN INSERT (
    TRANSACTION_ID, ACCOUNT_ID, MERCHANT_ID, TRANSACTION_TIMESTAMP,
    TRANSACTION_TYPE, AMOUNT, CURRENCY, TRANSACTION_CHANNEL,
    TRANSACTION_STATUS, REFERENCE_NUMBER, CREATED_AT, UPDATED_AT,
    SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID, DATA_SOURCE,
    IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
) VALUES (
    source.TRANSACTION_ID, source.ACCOUNT_ID, source.MERCHANT_ID, source.TRANSACTION_TIMESTAMP,
    source.TRANSACTION_TYPE, source.AMOUNT, source.CURRENCY, source.TRANSACTION_CHANNEL,
    source.TRANSACTION_STATUS, source.REFERENCE_NUMBER, source.CREATED_AT, source.UPDATED_AT,
    source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID, source.DATA_SOURCE,
    TRUE, CURRENT_TIMESTAMP(), NULL, CURRENT_TIMESTAMP()
)
""")

# COMMAND ----------

# DBTITLE 1,Insert Data into Silver Schema Tables
# ── bank_accounts: insert new / updated records (SCD2) ──────────────────────────
insert_bank_accounts_silver = spark.sql("""
INSERT INTO banking_data_processing.silver.bank_accounts
(
    ACCOUNT_ID, CUSTOMER_ID, BRANCH_ID, ACCOUNT_NUMBER, ACCOUNT_TYPE,
    CURRENCY, OPEN_DATE, CURRENT_BALANCE, ACCOUNT_STATUS,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
)
SELECT
    source.ACCOUNT_ID, source.CUSTOMER_ID, source.BRANCH_ID, source.ACCOUNT_NUMBER, source.ACCOUNT_TYPE,
    source.CURRENCY, source.OPEN_DATE, source.CURRENT_BALANCE, source.ACCOUNT_STATUS,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID,
    source.DATA_SOURCE, TRUE AS IS_CURRENT,
    CURRENT_TIMESTAMP() AS EFFECTIVE_FROM, NULL AS EFFECTIVE_TO,
    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY ACCOUNT_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
    ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_accounts
) AS source
LEFT JOIN banking_data_processing.silver.bank_accounts AS target
    ON source.ACCOUNT_ID = target.ACCOUNT_ID AND target.IS_CURRENT = TRUE
WHERE source.rn = 1 AND target.ACCOUNT_ID IS NULL
""")

# ── bank_cards: insert new / updated records (SCD2) ────────────────────────────
insert_bank_cards_silver = spark.sql("""
INSERT INTO banking_data_processing.silver.bank_cards
(
    CARD_ID, ACCOUNT_ID, CARD_NUMBER, CARD_TYPE, NETWORK,
    ISSUE_DATE, EXPIRY_DATE, CREDIT_LIMIT, CARD_STATUS,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
)
SELECT
    source.CARD_ID, source.ACCOUNT_ID, source.CARD_NUMBER, source.CARD_TYPE, source.NETWORK,
    source.ISSUE_DATE, source.EXPIRY_DATE, source.CREDIT_LIMIT, source.CARD_STATUS,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID,
    source.DATA_SOURCE, TRUE AS IS_CURRENT,
    CURRENT_TIMESTAMP() AS EFFECTIVE_FROM, NULL AS EFFECTIVE_TO,
    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY CARD_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
    ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_cards
) AS source
LEFT JOIN banking_data_processing.silver.bank_cards AS target
    ON source.CARD_ID = target.CARD_ID AND target.IS_CURRENT = TRUE
WHERE source.rn = 1 AND target.CARD_ID IS NULL
""")

# ── bank_merchants: insert new / updated records (SCD2) ─────────────────────────
insert_bank_merchants_silver = spark.sql("""
INSERT INTO banking_data_processing.silver.bank_merchants
(
    MERCHANT_ID, MERCHANT_NAME, MERCHANT_CATEGORY, MERCHANT_TYPE,
    CITY, STATE, COUNTRY, MERCHANT_STATUS,
    ACCEPTS_UPI, ACCEPTS_CARDS, AVG_TICKET_SIZE, ONBOARDING_DATE,
    CREATED_AT, UPDATED_AT, SOURCE_SYSTEM, BATCH_DATE, PIPELINE_RUN_ID,
    DATA_SOURCE, IS_CURRENT, EFFECTIVE_FROM, EFFECTIVE_TO, LOAD_TIMESTAMP
)
SELECT
    source.MERCHANT_ID, source.MERCHANT_NAME, source.MERCHANT_CATEGORY, source.MERCHANT_TYPE,
    source.MERCHANT_CITY, source.MERCHANT_STATE, source.MERCHANT_COUNTRY, source.MERCHANT_STATUS,
    source.ACCEPTS_UPI, source.ACCEPTS_CARDS, source.AVERAGE_TICKET_SIZE AS AVG_TICKET_SIZE, source.ONBOARDING_DATE,
    source.CREATED_AT, source.UPDATED_AT, source.SOURCE_SYSTEM, source.BATCH_DATE, source.PIPELINE_RUN_ID,
    source.DATA_SOURCE, TRUE AS IS_CURRENT,
    CURRENT_TIMESTAMP() AS EFFECTIVE_FROM, NULL AS EFFECTIVE_TO,
    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY MERCHANT_ID ORDER BY UPDATED_AT DESC, BATCH_DATE DESC
    ) AS rn FROM banking_data_platform_snowflake_stg_catalog.stg.bank_merchants
) AS source
LEFT JOIN banking_data_processing.silver.bank_merchants AS target
    ON source.MERCHANT_ID = target.MERCHANT_ID AND target.IS_CURRENT = TRUE
WHERE source.rn = 1 AND target.MERCHANT_ID IS NULL
""")

# COMMAND ----------

# DBTITLE 1,Send Email of Ingestion Status of Banking Domain
merge_acc_m  = merge_bank_accounts.collect()[0].asDict()
merge_card_m = merge_bank_cards.collect()[0].asDict()
merge_merch_m = merge_bank_merchants.collect()[0].asDict()
merge_txn_m  = merge_bank_transactions.collect()[0].asDict()
insert_acc_m  = insert_bank_accounts_silver.collect()[0].asDict()
insert_card_m  = insert_bank_cards_silver.collect()[0].asDict()
insert_merch_m = insert_bank_merchants_silver.collect()[0].asDict()

msg = MIMEMultipart()
msg["From"]    = SENDER_EMAIL
msg["To"]      = RECIPIENT_EMAIL
msg["Subject"] = "Banking Domain Ingestion Status"

body = f"""Hi,

The banking domain ingestion pipeline has completed successfully.

Ingestion Summary:

  bank_accounts (silver):
    - Records updated (MERGE):  {merge_acc_m.get('num_updated_rows', 'N/A')}
    - Records inserted:         {insert_acc_m.get('num_affected_rows', 'N/A')}

  bank_cards (silver):
    - Records updated (MERGE):  {merge_card_m.get('num_updated_rows', 'N/A')}
    - Records inserted:         {insert_card_m.get('num_affected_rows', 'N/A')}

  bank_merchants (silver):
    - Records updated (MERGE):  {merge_merch_m.get('num_updated_rows', 'N/A')}
    - Records inserted:         {insert_merch_m.get('num_affected_rows', 'N/A')}

  bank_transactions (silver):
    - Records inserted (MERGE): {merge_txn_m.get('num_inserted_rows', 'N/A')}

Regards,
Databricks Ingestion Pipeline
"""
msg.attach(MIMEText(body, "plain"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print(f"Ingestion status email sent to {RECIPIENT_EMAIL}")
print(f"  accounts     -> updated: {merge_acc_m.get('num_updated_rows','N/A')}, inserted: {insert_acc_m.get('num_affected_rows','N/A')}")
print(f"  cards        -> updated: {merge_card_m.get('num_updated_rows','N/A')}, inserted: {insert_card_m.get('num_affected_rows','N/A')}")
print(f"  merchants    -> updated: {merge_merch_m.get('num_updated_rows','N/A')}, inserted: {insert_merch_m.get('num_affected_rows','N/A')}")
print(f"  transactions -> inserted: {merge_txn_m.get('num_inserted_rows','N/A')}")