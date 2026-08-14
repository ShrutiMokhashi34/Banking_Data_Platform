"""
===============================================================================
Airflow Ingestion Pipeline
azure_file_check.py

Step 3 of the flow: check Azure Storage for the expected batch folder.
===============================================================================
"""

from __future__ import annotations

from airflow.providers.microsoft.azure.hooks.wasb import WasbHook

from scripts.config import (
    AZURE_CONN_ID,
    AZURE_CONTAINER_NAME,
    TABLE_FILE_MAP,
    dated_file_name,
)


def _blob_name(blob) -> str:
    """
    Normalize a single item from WasbHook.get_blobs_list() to its
    plain blob name string.

    Different versions of the underlying Azure SDK / provider package
    return either a plain string (blob name) or a BlobProperties-style
    object with a .name attribute. Handle both so this doesn't break
    again on a provider upgrade/downgrade.
    """

    return blob.name if hasattr(blob, "name") else blob


def list_batch_files(batch_date: str) -> list[str]:
    """
    Return the blob names found under rawdata/{batch_date}/.
    """

    hook = WasbHook(wasb_conn_id=AZURE_CONN_ID)

    prefix = f"{batch_date}/"

    blobs = hook.get_blobs_list(
        container_name=AZURE_CONTAINER_NAME,
        prefix=prefix,
    )

    return [_blob_name(blob).split("/")[-1] for blob in blobs]


def batch_folder_is_complete(batch_date: str) -> tuple[bool, list[str]]:
    """
    Check whether every expected CSV file is present for a batch date.

    Files in Azure carry a date suffix (e.g. "accounts_20260801.csv"
    for batch_date "2026-08-01"), not the bare base name - see
    config.dated_file_name() for the naming convention.

    Returns
    -------
    (is_complete, missing_files) - missing_files are reported using
    the base names (e.g. "accounts.csv") for readability in emails/logs.
    """

    found_files = set(list_batch_files(batch_date))

    expected_by_base_name = {
        base_name: dated_file_name(base_name, batch_date)
        for base_name in TABLE_FILE_MAP
    }

    missing_files = sorted(
        base_name
        for base_name, dated_name in expected_by_base_name.items()
        if dated_name not in found_files
    )

    return (len(missing_files) == 0, missing_files)


# =====================================================================
# Airflow Task Callable
# =====================================================================

def task_check_azure_folder(**context) -> str:
    """
    BranchPythonOperator callable.

    Returns the task_id to run next: "load_to_staging" if the batch
    folder is complete, otherwise "send_missing_folder_email".
    """

    ti = context["ti"]

    batch_date = ti.xcom_pull(task_ids="determine_next_batch_date")

    is_complete, missing_files = batch_folder_is_complete(batch_date)

    if not is_complete:

        ti.xcom_push(key="missing_files", value=missing_files)

        return "send_missing_folder_email"

    return "load_to_staging"
