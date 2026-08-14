"""
===============================================================================
Airflow Ingestion Pipeline
daily_ingestion_dag.py

Flow
-----

    Scheduler (3:00 PM IST)
            |
            v
    Check latest batch loaded in Snowflake
            |
            v
    Determine expected next batch date
            |
            v
    Check Azure Storage for expected folder
        +---------+---------+
        |                   |
        v                   v
     Exists              Not Found
        |                   |
        v                   v
    Load into STG       Send Missing-Folder Email
        |
        v
    Validate Load Counts
        |
    +---+----+
    |        |
    v        v
 Success   Failure
    |        |
    v        v
 Success   Failure
  Email     Email

Configuration
--------------
Table list and validation rules are metadata-driven
(scripts/pipeline_config.yaml) - add/remove a table there, not in
code. Environment-specific settings (connection IDs, stage/database
names, email recipients) come from the Airflow Variable
"adls_snowflake_pipeline_env", not from a config file. See
scripts/config.py for full setup instructions.

Audit trail
-----------
Every run writes to two Snowflake tables (DDL in
scripts/audit_schema.sql):

    * PIPELINE_RUN_AUDIT - one row per DAG run (overall outcome)
    * FILE_LOAD_AUDIT     - one row per file, every run (COPY result
                            + data-quality validation result)

`check_next_batch.py` reads PIPELINE_RUN_AUDIT.OVERALL_STATUS to find
the latest successfully loaded batch date.

KNOWN DATA ISSUES (fix before relying on this in production - see the
chat writeup for full detail):

    • create_cust_customer_addresses.sql has a missing comma and will
      fail to even create the table as currently written.
    • LOAN_LOANS.LOAN_APPLICATION_ID is NOT NULL but is never produced
      by the generator - every row will be rejected.
    • BANK_MERCHANTS requires MERCHANT_ACCOUNT_ID, MERCHANT_ADDRESS_LINE_1,
      and MERCHANT_ZIP_CODE (all NOT NULL) which the generator doesn't
      produce - every row will be rejected. CITY/STATE also won't
      auto-match against the source's MERCHANT_CITY/MERCHANT_STATE.
    • BANK_TRANSACTIONS.CHANNEL is NOT NULL but the source column is
      named TRANSACTION_CHANNEL - name mismatch means every row will
      be rejected.
    • LOAN_LOAN_APPLICATIONS has no LOAN_ID column, so the
      application -> loan link is silently dropped on load.

None of these stop the DAG from running - `validation.py` will simply
report 0 rows loaded / errors for the affected tables, and the batch
will be marked FAILURE with details in the email.

Holiday Calendar is intentionally excluded - it is not landed in
Azure in the current data flow.
===============================================================================
"""

from __future__ import annotations

import os
import sys
import pendulum
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator

# =====================================================================
# Make scripts/ importable as `scripts.*`
# =====================================================================

DAG_FOLDER = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.dirname(DAG_FOLDER)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from scripts.check_next_batch import (
    task_get_latest_batch_date,
    task_determine_next_batch_date,
)
from scripts.azure_file_check import task_check_azure_folder
from scripts.snowflake_loader import task_load_to_staging
from scripts.validation import task_validate_load_counts
from scripts.notification import (
    task_send_missing_folder_email,
    task_send_success_email,
    task_send_failure_email,
)

# =====================================================================
# DAG Definition
# =====================================================================

default_args = {

    "owner": "data-engineering",

    "retries": 1,

    "retry_delay": timedelta(minutes=5),

}

IST = pendulum.timezone("Asia/Kolkata")

with DAG(
    dag_id="daily_ingestion_dag",
    description="Load daily Azure rawdata CSV batches into Snowflake STG tables.",
    default_args=default_args,
    schedule="0 15 * * *",
    start_date=pendulum.datetime(2026, 8, 14, tz=IST),
    catchup=False,
    max_active_runs=1,
    tags=["snowflake", "azure", "abc-bank"],
) as dag:

    # -----------------------------------------------------------------
    # Step 1: Check latest batch loaded in Snowflake
    # -----------------------------------------------------------------

    get_latest_loaded_batch = PythonOperator(
        task_id="get_latest_loaded_batch",
        python_callable=task_get_latest_batch_date,
    )

    # -----------------------------------------------------------------
    # Step 2: Determine expected next batch date
    # -----------------------------------------------------------------

    determine_next_batch_date = PythonOperator(
        task_id="determine_next_batch_date",
        python_callable=task_determine_next_batch_date,
    )

    # -----------------------------------------------------------------
    # Step 3: Check Azure Storage for expected folder (branch)
    # -----------------------------------------------------------------

    check_azure_folder = BranchPythonOperator(
        task_id="check_azure_folder",
        python_callable=task_check_azure_folder,
    )

    # -----------------------------------------------------------------
    # Exists Branch: Load into STG -> Validate -> Success/Failure email
    # -----------------------------------------------------------------

    load_to_staging = PythonOperator(
        task_id="load_to_staging",
        python_callable=task_load_to_staging,
    )

    validate_load_counts = BranchPythonOperator(
        task_id="validate_load_counts",
        python_callable=task_validate_load_counts,
    )

    send_success_email = PythonOperator(
        task_id="send_success_email",
        python_callable=task_send_success_email,
    )

    send_failure_email = PythonOperator(
        task_id="send_failure_email",
        python_callable=task_send_failure_email,
    )

    # -----------------------------------------------------------------
    # Not Found Branch: Send Missing-Folder Email
    # -----------------------------------------------------------------

    send_missing_folder_email = PythonOperator(
        task_id="send_missing_folder_email",
        python_callable=task_send_missing_folder_email,
    )

    # -----------------------------------------------------------------
    # End marker (both branches converge here for a clean DAG graph)
    # -----------------------------------------------------------------

    end = EmptyOperator(
        task_id="end",
        trigger_rule="none_failed_min_one_success",
    )

    # -----------------------------------------------------------------
    # Wiring
    # -----------------------------------------------------------------

    get_latest_loaded_batch >> determine_next_batch_date >> check_azure_folder

    check_azure_folder >> [load_to_staging, send_missing_folder_email]

    load_to_staging >> validate_load_counts

    validate_load_counts >> [send_success_email, send_failure_email]

    [send_success_email, send_failure_email, send_missing_folder_email] >> end
