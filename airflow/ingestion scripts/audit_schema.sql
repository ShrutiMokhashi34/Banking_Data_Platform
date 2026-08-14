-- =============================================================================
-- Audit Schema - run once, manually, before first use.
--
-- Replaces the earlier single BATCH_LOAD_LOG table with two tables:
--
--   PIPELINE_RUN_AUDIT  - one row per DAG run (the overall outcome)
--   FILE_LOAD_AUDIT      - one row per file processed within a run
--
-- check_next_batch.py reads PIPELINE_RUN_AUDIT.OVERALL_STATUS to find the
-- latest successfully loaded batch date.
-- =============================================================================

CREATE TABLE IF NOT EXISTS ABC_BANK.STG.PIPELINE_RUN_AUDIT (

    PIPELINE_RUN_ID         VARCHAR(250)    NOT NULL,

    DAG_RUN_ID              VARCHAR(250),

    BATCH_DATE              DATE            NOT NULL,

    STARTED_AT              TIMESTAMP_NTZ   NOT NULL,

    ENDED_AT                TIMESTAMP_NTZ,

    OVERALL_STATUS          VARCHAR(20)     NOT NULL,     -- SUCCESS | FAILURE

    TOTAL_FILES_EXPECTED    NUMBER(5,0),

    TOTAL_FILES_LOADED      NUMBER(5,0),

    TOTAL_ROWS_LOADED       NUMBER(18,0),

    DETAILS                 VARCHAR(8000),

    CREATED_AT              TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()

);

CREATE TABLE IF NOT EXISTS ABC_BANK.STG.FILE_LOAD_AUDIT (

    PIPELINE_RUN_ID         VARCHAR(250)    NOT NULL,

    BATCH_DATE              DATE            NOT NULL,

    FILE_NAME               VARCHAR(200)    NOT NULL,

    TABLE_NAME               VARCHAR(200)    NOT NULL,

    ROWS_PARSED             NUMBER(18,0),

    ROWS_LOADED             NUMBER(18,0),

    ERRORS_SEEN             NUMBER(18,0),

    COPY_STATUS              VARCHAR(30),     -- LOADED | PARTIALLY_LOADED_OR_FAILED | NO_FILE_MATCHED

    VALIDATION_STATUS        VARCHAR(20),     -- PASSED | FAILED

    VALIDATION_DETAILS       VARCHAR(4000),

    LOAD_STARTED_AT          TIMESTAMP_NTZ,

    LOAD_ENDED_AT             TIMESTAMP_NTZ,

    CREATED_AT               TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()

);
