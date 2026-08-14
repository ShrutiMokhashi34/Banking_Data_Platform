CREATE OR REPLACE TABLE ABC_BANK.STG.BANK_ACCOUNTS
(
    ACCOUNT_ID              VARCHAR(20)        NOT NULL,
    CUSTOMER_ID             VARCHAR(20)        NOT NULL,
    BRANCH_ID               VARCHAR(20)        NOT NULL,

    ACCOUNT_NUMBER          VARCHAR(20)        NOT NULL,

    ACCOUNT_TYPE            VARCHAR(20),

    CURRENCY                VARCHAR(3)         NOT NULL,

    OPEN_DATE               DATE               NOT NULL,

    CURRENT_BALANCE         NUMBER(18,2)       NOT NULL,

    ACCOUNT_STATUS          VARCHAR(20)        NOT NULL,

    CREATED_AT              TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ,
    SOURCE_SYSTEM           VARCHAR(50)        DEFAULT 'Core Banking System',
    BATCH_ID                TIMESTAMP_NTZ,
	BATCH_DATE          	DATE,
	PIPELINE_RUN_ID			VARCHAR(20),
	DATA_SOURCE				VARCHAR(50)
);