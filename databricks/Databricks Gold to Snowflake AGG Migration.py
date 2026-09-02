# Databricks notebook source
# DBTITLE 1,Databricks Gold to Snowflake AGG Data Migration
# ============================================================
# STEP 1 — Import required libraries and Spark functions
# ============================================================

from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import TimestampNTZType
from datetime import datetime
import uuid


# ============================================================
# STEP 2 — Databricks → Snowflake table mapping
# ============================================================

gold_table_mapping = {
    "DIM_CUSTOMER": "dim_customer",
    "DIM_ACCOUNT": "dim_account",
    "FACT_TRANSACTIONS": "fact_transactions",
    "DIM_LOAN": "dim_loan",
    "FACT_LOAN_REPAYMENTS": "fact_loan_repayments",
    "DIM_EMPLOYEES": "dim_employees",
    "FACT_FRAUD_ALERTS": "fact_fraud_alerts",
    "DIM_EXCHANGE_RATES": "dim_exchange_rates"
}


# ============================================================
# STEP 3 — Configure Snowflake connection
# ============================================================

sf_options = {
    "sfaccount": "fqoahwq-ll82867",
    "host": "fqoahwq-ll82867.snowflakecomputing.com",
    "sfDatabase": "ABC_BANK",
    "sfSchema": "AGG",
    "sfWarehouse": "COMPUTE_WH",
    "sfUser": dbutils.secrets.get(
        scope="snowflake-creds",
        key="snowflake-user"
    ),
    "sfPassword": dbutils.secrets.get(
        scope="snowflake-creds",
        key="snowflake-password"
    )
}

dbr_options = {
    "dbrDatabase": "banking_data_processing",
    "dbrSchema": "gold"
}


# ============================================================
# STEP 4 — Track overall publication status
# ============================================================

failed_tables = []

audit_table = "DATABRICKS_GOLD_SNOWFLAKE_AGG_LOAD_AUDIT"


# ============================================================
# STEP 5 — Process each Gold table
# ============================================================

for snowflake_table, databricks_table in gold_table_mapping.items():

    # --------------------------------------------------------
    # Capture the start time for this individual table load
    # --------------------------------------------------------

    load_start = datetime.now()

    # --------------------------------------------------------
    # Build fully qualified target name for logging
    # --------------------------------------------------------

    target_table = (
        f"{sf_options['sfDatabase']}."
        f"{sf_options['sfSchema']}."
        f"{snowflake_table}"
    )

    source_table = (
        f"{dbr_options['dbrDatabase']}."
        f"{dbr_options['dbrSchema']}."
        f"{databricks_table}"
    )

    # ========================================================
    # STEP 5.1 — Print processing information
    # ========================================================

    print("=" * 70)
    print(f"Processing: {source_table}")
    print(f"Target:     {target_table}")
    print("=" * 70)

    try:

        # ====================================================
        # STEP 5.2 — Read the Databricks Gold table
        # ====================================================

        gold_df = spark.table(source_table)

        # Get schema once to avoid repeated Analyze RPC calls
        gold_schema = gold_df.schema


        # ====================================================
        # STEP 5.3 — Convert TimestampNTZType columns
        # ====================================================

        for field in gold_schema.fields:

            if isinstance(field.dataType, TimestampNTZType):

                gold_df = gold_df.withColumn(
                    field.name,
                    gold_df[field.name].cast("timestamp")
                )

                print(
                    f"Converted {field.name}: "
                    f"TimestampNTZType → TimestampType"
                )


        # ====================================================
        # STEP 5.4 — Add Databricks publication timestamp
        # ====================================================

        gold_df = gold_df.withColumn(
            "UPDATED_FROM_DATABRICKS",
            current_timestamp()
        )


        # ====================================================
        # STEP 5.5 — Count records before publishing
        # ====================================================

        row_count = gold_df.count()

        print(f"Records to publish: {row_count}")


        # ====================================================
        # STEP 5.6 — Publish Gold table to Snowflake
        # ====================================================

        gold_df.write \
            .format("snowflake") \
            .options(**sf_options) \
            .option(
                "dbtable",
                snowflake_table
            ) \
            .mode("overwrite") \
            .save()


        # ====================================================
        # STEP 5.7 — Capture successful completion time
        # ====================================================

        load_end = datetime.now()


        # ====================================================
        # STEP 5.8 — Print successful publication message
        # ====================================================

        print(
            f"SUCCESS: {row_count} records published "
            f"to {target_table}"
        )


        # ====================================================
        # STEP 5.9 — Create SUCCESS audit record
        # ====================================================

        audit_data = [
            (
                str(uuid.uuid4()),
                snowflake_table,
                source_table,
                "FULL_REFRESH",
                load_start,
                load_end,
                row_count,
                "SUCCESS",
                load_end,
                "NA",
                datetime.now()
            )
        ]


        # ====================================================
        # STEP 5.10 — Create audit DataFrame
        # ====================================================

        audit_df = spark.createDataFrame(
            audit_data,
            [
                "AUDIT_ID",
                "TABLE_NAME",
                "SOURCE_TABLE",
                "LOAD_TYPE",
                "LOAD_START_TIME",
                "LOAD_END_TIME",
                "ROW_COUNT",
                "LOAD_STATUS",
                "UPDATED_FROM_DATABRICKS",
                "ERROR_MESSAGE",
                "CREATED_AT"
            ]
        )


        # ====================================================
        # STEP 5.11 — Append audit record to Snowflake
        # ====================================================

        audit_df.write \
            .format("snowflake") \
            .options(**sf_options) \
            .option(
                "dbtable",
                audit_table
            ) \
            .mode("append") \
            .save()


        # ====================================================
        # STEP 5.12 — Print separator
        # ====================================================

        print("=" * 70)


    except Exception as e:

        # ====================================================
        # STEP 6 — Handle publication failure
        # ====================================================

        load_end = datetime.now()

        error_message = str(e)[:5000]

        failed_tables.append(snowflake_table)


        # ----------------------------------------------------
        # Print failure information
        # ----------------------------------------------------

        print(
            f"FAILED: Could not publish {target_table}"
        )

        print(
            f"Error: {error_message}"
        )

        print("=" * 70)


        # ====================================================
        # STEP 6.1 — Create FAILED audit record
        # ====================================================

        audit_data = [
            (
                str(uuid.uuid4()),
                snowflake_table,
                source_table,
                "FULL_REFRESH",
                load_start,
                load_end,
                0,
                "FAILED",
                None,
                error_message,
                datetime.now()
            )
        ]


        # ====================================================
        # STEP 6.2 — Create audit DataFrame
        # ====================================================

        audit_df = spark.createDataFrame(
            audit_data,
            [
                "AUDIT_ID",
                "TABLE_NAME",
                "SOURCE_TABLE",
                "LOAD_TYPE",
                "LOAD_START_TIME",
                "LOAD_END_TIME",
                "ROW_COUNT",
                "LOAD_STATUS",
                "UPDATED_FROM_DATABRICKS",
                "ERROR_MESSAGE",
                "CREATED_AT"
            ]
        )


        # ====================================================
        # STEP 6.3 — Write FAILED record to audit table
        # ====================================================

        audit_df.write \
            .format("snowflake") \
            .options(**sf_options) \
            .option(
                "dbtable",
                audit_table
            ) \
            .mode("append") \
            .save()


# ============================================================
# STEP 7 — Overall publication status
# ============================================================
#
# IMPORTANT:
# This is OUTSIDE the for loop.
#
# It runs only AFTER all Gold tables have been attempted.
# ============================================================

if len(failed_tables) == 0:

    print("=" * 70)
    print("ALL GOLD TABLES SUCCESSFULLY PUBLISHED TO SNOWFLAKE")
    print("=" * 70)

else:

    print("=" * 70)
    print("GOLD TABLE PUBLICATION COMPLETED WITH ERRORS")
    print("=" * 70)

    print("Failed tables:")

    for table in failed_tables:
        print(f"  - {table}")

    print("=" * 70)

    # Raise an exception so that the Databricks job is marked
    # as FAILED and an upstream orchestrator such as Airflow
    # can detect the failure.

    raise Exception(
        f"Gold publication failed for: {', '.join(failed_tables)}"
    )

# COMMAND ----------

# DBTITLE 1,Email Notification
# ============================================================
# STEP 8 — Email notification with table-wise load summary
# ============================================================

import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ============================================================
# STEP 8.1 — Email configuration
# ============================================================
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

SENDER_EMAIL    = dbutils.secrets.get(scope="email-scope", key="gmail-address")
SENDER_PASSWORD = dbutils.secrets.get(scope="email-scope", key="gmail-app-password").replace(" ", "")
RECIPIENT_EMAIL = "bankingdataplatform.project@gmail.com"   # ← replace with the target Gmail address

# ============================================================
# STEP 8.2 — Read latest audit status for each published table
# ============================================================

table_list_sql = ", ".join(
    f"'{table_name}'"
    for table_name in gold_table_mapping.keys()
)

audit_query = f"""
WITH ranked_audit AS (
    SELECT
        TABLE_NAME,
        SOURCE_TABLE,
        ROW_COUNT,
        LOAD_STATUS,
        LOAD_START_TIME,
        LOAD_END_TIME,
        ERROR_MESSAGE,
        CREATED_AT,
        ROW_NUMBER() OVER (
            PARTITION BY TABLE_NAME
            ORDER BY LOAD_END_TIME DESC, CREATED_AT DESC
        ) AS rn
    FROM {audit_table}
    WHERE TABLE_NAME IN ({table_list_sql})
)
SELECT
    TABLE_NAME,
    SOURCE_TABLE,
    ROW_COUNT,
    LOAD_STATUS,
    LOAD_START_TIME,
    LOAD_END_TIME,
    ERROR_MESSAGE
FROM ranked_audit
WHERE rn = 1
ORDER BY TABLE_NAME
"""

audit_summary_df = (
    spark.read
    .format("snowflake")
    .options(**sf_options)
    .option("query", audit_query)
    .load()
)

audit_rows = audit_summary_df.collect()

if not audit_rows:
    raise ValueError(
        "No audit rows were found for the configured Gold tables."
    )


# ============================================================
# STEP 8.3 — Build email summary
# ============================================================

success_count = sum(
    1
    for row in audit_rows
    if row["LOAD_STATUS"] == "SUCCESS"
)

failed_count = sum(
    1
    for row in audit_rows
    if row["LOAD_STATUS"] != "SUCCESS"
)

overall_status = "SUCCESS" if failed_count == 0 else "FAILED"

total_rows_loaded = sum(
    int(row["ROW_COUNT"] or 0)
    for row in audit_rows
)

html_rows = []

for row in audit_rows:
    load_status = row["LOAD_STATUS"]
    status_color = "#1b5e20" if load_status == "SUCCESS" else "#b71c1c"
    error_message = row["ERROR_MESSAGE"] or "NA"

    html_rows.append(
        f"""
        <tr>
            <td>{html.escape(str(row['TABLE_NAME']))}</td>
            <td>{html.escape(str(row['SOURCE_TABLE']))}</td>
            <td style=\"text-align:right;\">{int(row['ROW_COUNT'] or 0):,}</td>
            <td style=\"color:{status_color};font-weight:bold;\">{html.escape(str(load_status))}</td>
            <td>{html.escape(str(row['LOAD_START_TIME']))}</td>
            <td>{html.escape(str(row['LOAD_END_TIME']))}</td>
            <td>{html.escape(str(error_message))}</td>
        </tr>
        """
    )

html_body = f"""
<html>
  <body style=\"font-family:Arial,sans-serif;\">
    <h2>Databricks Gold to Snowflake AGG Migration Status</h2>
    <p><strong>Overall Status:</strong> {overall_status}</p>
    <p><strong>Total Tables:</strong> {len(audit_rows)}</p>
    <p><strong>Successful Tables:</strong> {success_count}</p>
    <p><strong>Failed Tables:</strong> {failed_count}</p>
    <p><strong>Total Rows Loaded:</strong> {total_rows_loaded:,}</p>

    <table border=\"1\" cellpadding=\"6\" cellspacing=\"0\" style=\"border-collapse:collapse;\">
      <thead style=\"background-color:#f2f2f2;\">
        <tr>
          <th>Snowflake Table</th>
          <th>Databricks Source Table</th>
          <th>Row Count</th>
          <th>Load Status</th>
          <th>Load Start Time</th>
          <th>Load End Time</th>
          <th>Error Message</th>
        </tr>
      </thead>
      <tbody>
        {''.join(html_rows)}
      </tbody>
    </table>
  </body>
</html>
"""

plain_text_lines = [
    "Databricks Gold to Snowflake AGG Migration Status",
    f"Overall Status: {overall_status}",
    f"Total Tables: {len(audit_rows)}",
    f"Successful Tables: {success_count}",
    f"Failed Tables: {failed_count}",
    f"Total Rows Loaded: {total_rows_loaded:,}",
    "",
    "Table Details:"
]

for row in audit_rows:
    plain_text_lines.extend([
        f"- Snowflake Table: {row['TABLE_NAME']}",
        f"  Databricks Source Table: {row['SOURCE_TABLE']}",
        f"  Row Count: {int(row['ROW_COUNT'] or 0):,}",
        f"  Load Status: {row['LOAD_STATUS']}",
        f"  Load Start Time: {row['LOAD_START_TIME']}",
        f"  Load End Time: {row['LOAD_END_TIME']}",
        f"  Error Message: {row['ERROR_MESSAGE'] or 'NA'}",
        ""
    ])

plain_text_body = "\n".join(plain_text_lines)


# ============================================================
# STEP 8.4 — Send the email
# ============================================================

message = MIMEMultipart("alternative")
message["Subject"] = (
    f"[{overall_status}] Databricks Gold to Snowflake AGG Migration"
)
message["From"] = SENDER_EMAIL
message["To"] = RECIPIENT_EMAIL

message.attach(MIMEText(plain_text_body, "plain"))
message.attach(MIMEText(html_body, "html"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(
        SENDER_EMAIL,
        RECIPIENT_EMAIL,
        message.as_string()
    )

print(
    f"Email notification sent successfully to: {RECIPIENT_EMAIL}"
)

display(audit_summary_df)