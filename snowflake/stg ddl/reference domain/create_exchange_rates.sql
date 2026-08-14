CREATE OR REPLACE TABLE ABC_BANK.STG.EXCHANGE_RATES
(
    RATE_DATE               DATE                NOT NULL,

    CURRENCY                VARCHAR(15)          NOT NULL,

    CURRENCY_SYMBOL         VARCHAR(10)         NOT NULL,

    RATE_TO_INR             NUMBER(18,6)        NOT NULL,

    SOURCE                  VARCHAR(100)        NOT NULL,
	
	BASE_CURRENCY           VARCHAR(3)          DEFAULT 'INR',

    CREATED_AT              TIMESTAMP_NTZ       DEFAULT CURRENT_TIMESTAMP(),

    UPDATED_AT              TIMESTAMP_NTZ,

    SOURCE_SYSTEM           VARCHAR(50)         DEFAULT 'Exchange Rate API',

    BATCH_ID                TIMESTAMP_NTZ,
	BATCH_DATE         		DATE,
	PIPELINE_RUN_ID			VARCHAR(100),
	DATA_SOURCE				VARCHAR(50)
);