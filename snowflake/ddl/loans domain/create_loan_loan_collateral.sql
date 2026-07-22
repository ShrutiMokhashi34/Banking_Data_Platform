CREATE OR REPLACE TABLE ABC_BANK.STG.LOAN_LOAN_COLLATERAL
(
    COLLATERAL_ID           VARCHAR(20)        NOT NULL,

    LOAN_ID                 VARCHAR(20)        NOT NULL,

    ASSET_TYPE              VARCHAR(30)        NOT NULL,

    ASSET_VALUE             NUMBER(15,2)       NOT NULL,

    VALUATION_DATE          DATE               NOT NULL,

    CREATED_AT              TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ,
    SOURCE_SYSTEM           VARCHAR(50)        DEFAULT 'Loan Management System',
    BATCH_ID                VARCHAR(50),

    CONSTRAINT PK_LOAN_COLLATERAL
        PRIMARY KEY (COLLATERAL_ID),

    CONSTRAINT FK_COLLATERAL_LOAN
        FOREIGN KEY (LOAN_ID)
        REFERENCES LOAN_LOANS(LOAN_ID),

    CONSTRAINT CHK_ASSET_TYPE
        CHECK (UPPER(ASSET_TYPE) IN
        (
            'PROPERTY',
            'VEHICLE',
            'GOLD',
            'FIXED DEPOSIT',
            'SHARES',
            'MUTUAL FUNDS'
        )),

    CONSTRAINT CHK_ASSET_VALUE
        CHECK (ASSET_VALUE > 0)
);