CREATE OR REPLACE TABLE ABC_BANK.STG.LOAN_LOAN_REPAYMENTS
(
    REPAYMENT_ID            VARCHAR(20)        NOT NULL,

    LOAN_ID                 VARCHAR(20)        NOT NULL,

    PAYMENT_DATE            DATE               NOT NULL,

    AMOUNT_PAID             NUMBER(15,2)       NOT NULL,

    PAYMENT_MODE            VARCHAR(20)        NOT NULL,

    CREATED_AT              TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ,
    SOURCE_SYSTEM           VARCHAR(50)        DEFAULT 'Loan Management System',
    BATCH_ID                TIMESTAMP_NTZ,
	BATCH_DATE          	DATE,
	PIPELINE_RUN_ID			VARCHAR(100),
	DATA_SOURCE				VARCHAR(50)
);