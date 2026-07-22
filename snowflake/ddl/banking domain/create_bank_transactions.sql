CREATE OR REPLACE TABLE ABC_BANK.STG.BANK_TRANSACTIONS
(
    TRANSACTION_ID              VARCHAR(20)        NOT NULL,

    ACCOUNT_ID                  VARCHAR(20)        NOT NULL,

    MERCHANT_ID                 VARCHAR(20),

    TRANSACTION_TIMESTAMP       TIMESTAMP_NTZ      NOT NULL,

    TRANSACTION_TYPE            VARCHAR(20)        NOT NULL,

    AMOUNT                      NUMBER(18,2)       NOT NULL,

    CURRENCY                    VARCHAR(3)         NOT NULL,

    CHANNEL                     VARCHAR(30)        NOT NULL,

    TRANSACTION_STATUS          VARCHAR(20)        NOT NULL,

    REFERENCE_NUMBER            VARCHAR(50)        NOT NULL,

    CREATED_AT                  TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT                  TIMESTAMP_NTZ,
    SOURCE_SYSTEM               VARCHAR(50)        DEFAULT 'Core Banking System',
    BATCH_ID                    VARCHAR(50),

    CONSTRAINT PK_TRANSACTIONS
        PRIMARY KEY (TRANSACTION_ID),

    CONSTRAINT UQ_REFERENCE_NUMBER
        UNIQUE (REFERENCE_NUMBER),

    CONSTRAINT FK_TRANSACTIONS_ACCOUNTS
        FOREIGN KEY (ACCOUNT_ID)
        REFERENCES BANK_ACCOUNTS(ACCOUNT_ID),

    CONSTRAINT FK_TRANSACTIONS_MERCHANTS
        FOREIGN KEY (MERCHANT_ID)
        REFERENCES BANK_MERCHANTS(MERCHANT_ID),

    CONSTRAINT CHK_TRANSACTION_TYPE
        CHECK (UPPER(TRANSACTION_TYPE) IN
        (
			'CREDIT',
			'DEBIT',
			'TRANSFER',
			'WITHDRAWAL',
			'DEPOSIT',
			'POS PURCHASE',
			'ONLINE PAYMENT',
			'BILL PAYMENT'
        )),

    CONSTRAINT CHK_TRANSACTION_STATUS
        CHECK (UPPER(TRANSACTION_STATUS) IN
        (
            'PENDING',
            'COMPLETED',
            'FAILED',
            'REVERSED',
            'CANCELLED'
        )),

    CONSTRAINT CHK_CHANNEL
        CHECK (UPPER(CHANNEL) IN
        (
            'UPI',
            'ATM',
            'POS',
            'ONLINE BANKING',
            'MOBILE BANKING',
            'BRANCH',
            'NEFT',
            'RTGS',
            'IMPS',
            'ECS',
            'CHEQUE',
            'AUTO DEBIT'
        )),

    CONSTRAINT CHK_AMOUNT
        CHECK (AMOUNT > 0)
);