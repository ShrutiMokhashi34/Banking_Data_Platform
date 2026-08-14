"""
===============================================================================
Airflow Ingestion Pipeline
notification.py

Step 6 of the flow: send the appropriate email for each outcome.

Uses Airflow's built-in SMTP email utility, which reads the
`smtp_default` connection / [smtp] section of airflow.cfg.
===============================================================================
"""

from __future__ import annotations

from airflow.utils.email import send_email

from scripts.config import EMAIL_RECIPIENTS


def _send(subject: str, html_content: str) -> None:

    send_email(
        to=EMAIL_RECIPIENTS,
        subject=subject,
        html_content=html_content,
    )


def send_missing_folder_notification(
    batch_date: str,
    missing_files: list[str],
) -> None:
    """
    Sent when the expected Azure batch folder is absent or incomplete.
    """

    missing_list_html = "".join(
        f"<li>{file_name}</li>" for file_name in missing_files
    )

    _send(
        subject=f"[ABC Bank] Batch {batch_date} not found in Azure",
        html_content=f"""
            <p>The ingestion pipeline expected a batch folder for
            <b>{batch_date}</b> in Azure Storage, but it was missing
            or incomplete.</p>
            <p>Missing / not found files:</p>
            <ul>{missing_list_html}</ul>
            <p>No data was loaded. The pipeline will retry this same
            batch date on its next scheduled run.</p>
        """,
    )


def send_success_notification(
    batch_date: str,
    details: str,
) -> None:
    """
    Sent when a batch loads and validates successfully.
    """

    details_html = details.replace("\n", "<br>")

    _send(
        subject=f"[ABC Bank] Batch {batch_date} loaded successfully",
        html_content=f"""
            <p>Batch <b>{batch_date}</b> loaded and validated
            successfully.</p>
            <p>{details_html}</p>
        """,
    )


def send_failure_notification(
    batch_date: str,
    details: str,
) -> None:
    """
    Sent when a batch loads but fails validation.
    """

    details_html = details.replace("\n", "<br>")

    _send(
        subject=f"[ABC Bank] Batch {batch_date} FAILED validation",
        html_content=f"""
            <p>Batch <b>{batch_date}</b> was loaded but failed
            validation. Review the details below.</p>
            <p>{details_html}</p>
        """,
    )


# =====================================================================
# Airflow Task Callables
# =====================================================================

def task_send_missing_folder_email(**context) -> None:

    ti = context["ti"]

    batch_date = ti.xcom_pull(task_ids="determine_next_batch_date")

    missing_files = ti.xcom_pull(
        task_ids="check_azure_folder",
        key="missing_files",
    ) or []

    send_missing_folder_notification(batch_date, missing_files)


def task_send_success_email(**context) -> None:

    ti = context["ti"]

    batch_date = ti.xcom_pull(task_ids="determine_next_batch_date")

    details = ti.xcom_pull(
        task_ids="validate_load_counts",
        key="validation_details",
    ) or ""

    send_success_notification(batch_date, details)


def task_send_failure_email(**context) -> None:

    ti = context["ti"]

    batch_date = ti.xcom_pull(task_ids="determine_next_batch_date")

    details = ti.xcom_pull(
        task_ids="validate_load_counts",
        key="validation_details",
    ) or ""

    send_failure_notification(batch_date, details)
