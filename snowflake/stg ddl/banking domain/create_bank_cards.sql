CREATE OR REPLACE TABLE ABC_BANK.STG.BANK_CARDS
(
    CARD_ID                 VARCHAR(20)        NOT NULL,

    ACCOUNT_ID              VARCHAR(20)        NOT NULL,

    CARD_NUMBER             VARCHAR(19)        NOT NULL,

    CARD_TYPE               VARCHAR(20)        NOT NULL,

    NETWORK                 VARCHAR(20)        NOT NULL,

    ISSUE_DATE              DATE               NOT NULL,

    EXPIRY_DATE             DATE               NOT NULL,

    CREDIT_LIMIT            NUMBER(15,2),

    CARD_STATUS             VARCHAR(20)        NOT NULL,

    CREATED_AT              TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ,
    SOURCE_SYSTEM           VARCHAR(50)        DEFAULT 'Card Management System',
	BATCH_DATE          DATE,
	PIPELINE_RUN_ID		VARCHAR(20),
	DATA_SOURCE			VARCHAR(50)
);