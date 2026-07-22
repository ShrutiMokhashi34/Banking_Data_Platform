CREATE OR REPLACE TABLE ABC_BANK.STG.BANK_MERCHANTS
(
    MERCHANT_ID                VARCHAR(20)        NOT NULL,

    MERCHANT_ACCOUNT_ID        VARCHAR(20)        NOT NULL,

    MERCHANT_NAME              VARCHAR(150)       NOT NULL,

    MERCHANT_CATEGORY          VARCHAR(50)        NOT NULL,

    MERCHANT_ADDRESS_LINE_1    VARCHAR(200)       NOT NULL,

    MERCHANT_ADDRESS_LINE_2    VARCHAR(200),

    CITY                       VARCHAR(100)       NOT NULL,

    STATE                      VARCHAR(100)       NOT NULL,

    COUNTRY                    VARCHAR(100)       NOT NULL,

    MERCHANT_ZIP_CODE          VARCHAR(15)        NOT NULL,

    MERCHANT_STATUS            VARCHAR(20)        NOT NULL,

    CREATED_AT                 TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),

    UPDATED_AT                 TIMESTAMP_NTZ,

    SOURCE_SYSTEM              VARCHAR(50)        DEFAULT 'Enterprise System',

    BATCH_ID                   VARCHAR(50),

    CONSTRAINT PK_MERCHANTS
        PRIMARY KEY (MERCHANT_ID),

    CONSTRAINT FK_MERCHANT_ACCOUNT
        FOREIGN KEY (MERCHANT_ACCOUNT_ID)
        REFERENCES ABC_BANK.STG.BANK_ACCOUNTS (ACCOUNT_ID),

    CONSTRAINT CHK_MERCHANT_STATUS
        CHECK (MERCHANT_STATUS IN
        (
            'Active',
            'Inactive',
            'Suspended',
            'Closed'
        )),

    CONSTRAINT CHK_MERCHANT_CATEGORY
        CHECK (MERCHANT_CATEGORY IN
        (
            'Retail',
            'Grocery',
            'Fuel',
            'Healthcare',
            'Restaurant',
            'Travel',
            'Entertainment',
            'Education',
            'Utilities',
            'E-Commerce',
            'Government',
            'Telecom',
            'Other'
        ))
);