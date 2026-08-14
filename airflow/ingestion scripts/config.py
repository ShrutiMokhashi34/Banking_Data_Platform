"""
===============================================================================
Airflow Ingestion Pipeline
config.py

Two layers of configuration, kept deliberately separate:

  1. METADATA (pipeline_config.yaml, next to this file)
     What tables exist, their primary keys, required columns, and
     foreign-key rules. This is business/structural information that
     belongs in version control next to the code. Add a table by
     editing the YAML - no code change needed.

  2. ENVIRONMENT (Airflow Variable "adls_snowflake_pipeline_env")
     Everything that differs between dev/stage/prod: connection IDs,
     database/schema/stage names, the Azure container, email
     recipients, the first batch date. Lives in the Airflow UI so it
     can change per-environment without a code deploy. Falls back to
     the defaults below if the Variable hasn't been set yet (e.g.
     running scripts locally, or the very first deploy).

Credentials themselves are NOT here at all - they live in the Airflow
Connections `snowflake_default` / `azure_blob_default` (see the module
docstring for setup instructions), never in a config file.

ONE-TIME SETUP
---------------

  1. Airflow Connections (Admin -> Connections):
       * snowflake_default   (type: Snowflake)
       * azure_blob_default  (type: Azure Blob Storage / Wasb)

  2. Airflow Variable (Admin -> Variables), key
     "adls_snowflake_pipeline_env", JSON value - see _ENV_DEFAULTS
     below for the shape. Only needed if you want to override a
     default.

  3. Run scripts/audit_schema.sql once against Snowflake.

  4. Create the Snowflake external stage + CSV file format referenced
     by SNOWFLAKE_STAGE / SNOWFLAKE_FILE_FORMAT below, e.g.:

        CREATE OR REPLACE FILE FORMAT ABC_BANK.STG.CSV_FORMAT
        TYPE = CSV
        PARSE_HEADER = TRUE
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        NULL_IF = ('NULL','','null')
        EMPTY_FIELD_AS_NULL = TRUE
        ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

import yaml

try:

    from airflow.models import Variable

    _AIRFLOW_AVAILABLE = True

except ImportError:

    _AIRFLOW_AVAILABLE = False

# =====================================================================
# Layer 1: Metadata (YAML)
# =====================================================================

_YAML_PATH = Path(__file__).parent / "pipeline_config.yaml"

with open(_YAML_PATH, "r") as fp:

    _METADATA = yaml.safe_load(fp)

TABLES: list[dict] = _METADATA["tables"]

# file_name -> table_name, preserved for the modules that only need
# the simple mapping (azure_file_check, snowflake_loader).
TABLE_FILE_MAP = {
    table["file_name"]: table["table_name"]
    for table in TABLES
}

# table_name -> full metadata dict (primary_key, required_columns,
# foreign_keys), used by the richer validation checks.
TABLE_METADATA = {
    table["table_name"]: table
    for table in TABLES
}

EXPECTED_FILE_COUNT = len(TABLE_FILE_MAP)

# =====================================================================
# Layer 2: Environment (Airflow Variable, with local-dev fallback)
# =====================================================================

_ENV_VARIABLE_NAME = "adls_snowflake_pipeline_env"

_ENV_DEFAULTS = {

    "snowflake_conn_id": "snowflake_default",

    "azure_conn_id": "azure_blob_default",

    "snowflake_database": "ABC_BANK",

    "snowflake_schema": "STG",

    "snowflake_stage": "ADLS_STAGE",

    "snowflake_file_format": "CSV_FORMAT",

    "azure_container_name": "rawdata",

    "pipeline_run_audit_table": "PIPELINE_RUN_AUDIT",

    "file_load_audit_table": "FILE_LOAD_AUDIT",

    "first_batch_date": "2026-08-01",

    "data_source_label": "Azure Data Lake",

    "email_recipients": ["bankingdataplatform.project@gmail.com"],

    "email_from_name": "ABC Bank Data Platform",

}


def _load_env_config() -> dict:
    """
    Read the environment-specific settings from the Airflow Variable,
    falling back to _ENV_DEFAULTS when Airflow / the Variable isn't
    available (local scripts, unit tests, or first-ever deploy before
    the Variable has been created).
    """

    if not _AIRFLOW_AVAILABLE:

        return dict(_ENV_DEFAULTS)

    try:

        return Variable.get(
            _ENV_VARIABLE_NAME,
            deserialize_json=True,
            default_var=_ENV_DEFAULTS,
        )

    except Exception:

        return dict(_ENV_DEFAULTS)


_ENV = _load_env_config()

SNOWFLAKE_CONN_ID = _ENV["snowflake_conn_id"]

AZURE_CONN_ID = _ENV["azure_conn_id"]

SNOWFLAKE_DATABASE = _ENV["snowflake_database"]

SNOWFLAKE_SCHEMA = _ENV["snowflake_schema"]

SNOWFLAKE_STAGE = (
    f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{_ENV['snowflake_stage']}"
)

SNOWFLAKE_FILE_FORMAT = (
    f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{_ENV['snowflake_file_format']}"
)

AZURE_CONTAINER_NAME = _ENV["azure_container_name"]

PIPELINE_RUN_AUDIT_TABLE = (
    f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{_ENV['pipeline_run_audit_table']}"
)

FILE_LOAD_AUDIT_TABLE = (
    f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{_ENV['file_load_audit_table']}"
)

FIRST_BATCH_DATE = _ENV["first_batch_date"]

DATA_SOURCE_LABEL = _ENV["data_source_label"]

EMAIL_RECIPIENTS = _ENV["email_recipients"]

EMAIL_FROM_NAME = _ENV["email_from_name"]


def qualified_table(table_name: str) -> str:
    """
    Fully-qualify a bare table name (e.g. "BANK_ACCOUNTS") with the
    configured database and schema.
    """

    return f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{table_name}"


def dated_file_name(base_file_name: str, batch_date: str) -> str:
    """
    Build the actual file name Azure uses for a given batch date.

    TABLE_FILE_MAP keys (e.g. "accounts.csv") are the canonical/base
    names used throughout this codebase, but the files landed in
    Azure carry a date suffix - e.g. "accounts_20260801.csv" for
    batch_date "2026-08-01". This is the single place that mapping
    happens, so azure_file_check.py and snowflake_loader.py can never
    drift out of sync on the naming convention.
    """

    stem, _, extension = base_file_name.rpartition(".")

    date_suffix = batch_date.replace("-", "")

    return f"{stem}_{date_suffix}.{extension}"
