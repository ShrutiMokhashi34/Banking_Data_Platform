CREATE OR REPLACE TABLE ABC_BANK.STG.ORG_BRANCHES
(
    BRANCH_ID               VARCHAR(20)        NOT NULL,

    BRANCH_NAME             VARCHAR(100)       NOT NULL,

    CITY                    VARCHAR(100)       NOT NULL,

    STATE                   VARCHAR(100)       NOT NULL,

    COUNTRY                 VARCHAR(100)       NOT NULL,

    ZIP_CODE                VARCHAR(15)        NOT NULL,

    MANAGER_EMPLOYEE_ID     VARCHAR(20),

    OPENED_DATE             DATE               NOT NULL,

    CREATED_AT              TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ,
    SOURCE_SYSTEM           VARCHAR(50)        DEFAULT 'Enterprise System',
    BATCH_ID                TIMESTAMP_NTZ,
	BATCH_DATE         		DATE,
	PIPELINE_RUN_ID			VARCHAR(20),
	DATA_SOURCE				VARCHAR(50)
);
