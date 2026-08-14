CREATE OR REPLACE TABLE ABC_BANK.AGG.BANK_CARDS
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
    BATCH_ID                VARCHAR(50),

    CONSTRAINT PK_CARDS
        PRIMARY KEY (CARD_ID),

    CONSTRAINT UQ_CARD_NUMBER
        UNIQUE (CARD_NUMBER),

    CONSTRAINT FK_CARDS_ACCOUNTS
        FOREIGN KEY (ACCOUNT_ID)
        REFERENCES BANK_ACCOUNTS(ACCOUNT_ID),

    CONSTRAINT CHK_CARD_TYPE
        CHECK (UPPER(CARD_TYPE) IN
        (
            'DEBIT',
            'CREDIT',
            'PREPAID',
            'CHARGE'
        )),

    CONSTRAINT CHK_NETWORK
        CHECK (UPPER(NETWORK) IN
        (
            'VISA',
            'MASTERCARD',
            'RUPAY',
            'AMERICAN EXPRESS'
        )),

    CONSTRAINT CHK_CARD_STATUS
        CHECK (UPPER(CARD_STATUS) IN
        (
            'ACTIVE',
            'BLOCKED',
            'EXPIRED',
            'LOST',
            'STOLEN',
            'CLOSED'
        )),

    CONSTRAINT CHK_EXPIRY_DATE
        CHECK (EXPIRY_DATE > ISSUE_DATE),

    CONSTRAINT CHK_CREDIT_LIMIT
        CHECK (CREDIT_LIMIT IS NULL OR CREDIT_LIMIT >= 0)
);