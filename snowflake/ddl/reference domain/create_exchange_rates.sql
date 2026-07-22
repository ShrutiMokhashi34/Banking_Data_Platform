CREATE OR REPLACE TABLE ABC_BANK.STG.EXCHANGE_RATES
(
    RATE_DATE               DATE                NOT NULL,

    BASE_CURRENCY           VARCHAR(3)          NOT NULL DEFAULT 'INR',

    CURRENCY                VARCHAR(3)          NOT NULL,

    CURRENCY_SYMBOL         VARCHAR(10)         NOT NULL,

    RATE_TO_INR             NUMBER(18,6)        NOT NULL,

    SOURCE                  VARCHAR(100)        NOT NULL,

    CREATED_AT              TIMESTAMP_NTZ       DEFAULT CURRENT_TIMESTAMP(),

    UPDATED_AT              TIMESTAMP_NTZ,

    SOURCE_SYSTEM           VARCHAR(50)         DEFAULT 'Exchange Rate API',

    BATCH_ID                VARCHAR(50),

    CONSTRAINT PK_EXCHANGE_RATES
        PRIMARY KEY
        (
            RATE_DATE,
            BASE_CURRENCY,
            CURRENCY
        ),

    CONSTRAINT CHK_RATE
        CHECK (RATE_TO_INR > 0),

    CONSTRAINT CHK_BASE_CURRENCY
        CHECK
        (
            BASE_CURRENCY IN
            (
                'INR',
                'USD',
                'EUR',
                'GBP'
            )
        ),

    CONSTRAINT CHK_CURRENCY
        CHECK
        (
            CURRENCY IN
            (
                'INR',
                'USD',
                'EUR',
                'GBP',
                'JPY',
                'AUD',
                'CAD',
                'CHF',
                'SGD',
                'AED',
                'CNY',
                'HKD',
                'NZD'
            )
        )
);