CREATE OR REPLACE TABLE ABC_BANK.STG.BANK_TRANSACTIONS
(
    TRANSACTION_ID              VARCHAR(20)        NOT NULL,

    ACCOUNT_ID                  VARCHAR(20)        NOT NULL,

    MERCHANT_ID                 VARCHAR(20),

    TRANSACTION_TIMESTAMP       TIMESTAMP_NTZ      NOT NULL,

    TRANSACTION_TYPE            VARCHAR(20)        NOT NULL,

    AMOUNT                      NUMBER(18,2)       NOT NULL,

    CURRENCY                    VARCHAR(3)         NOT NULL,

    TRANSACTION_CHANNEL         VARCHAR(30)        NOT NULL,

    TRANSACTION_STATUS          VARCHAR(20)        NOT NULL,

    REFERENCE_NUMBER            VARCHAR(50)        NOT NULL,

    CREATED_AT                  TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT                  TIMESTAMP_NTZ,
    SOURCE_SYSTEM               VARCHAR(50)        DEFAULT 'Core Banking System',
    BATCH_ID                    TIMESTAMP_NTZ,
	BATCH_DATE                  DATE,
	PIPELINE_RUN_ID		VARCHAR(20),
	DATA_SOURCE			VARCHAR(50)
);