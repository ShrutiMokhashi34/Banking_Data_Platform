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
    BATCH_ID                VARCHAR(50),

    CONSTRAINT PK_LOAN_REPAYMENTS
        PRIMARY KEY (REPAYMENT_ID),

    CONSTRAINT FK_REPAYMENT_LOAN
        FOREIGN KEY (LOAN_ID)
        REFERENCES LOAN_LOANS(LOAN_ID),

    CONSTRAINT CHK_AMOUNT_PAID
        CHECK (AMOUNT_PAID > 0),

    CONSTRAINT CHK_PAYMENT_MODE
        CHECK (PAYMENT_MODE IN
        (
            'UPI',
            'NEFT',
            'RTGS',
            'IMPS',
            'Cash',
            'Cheque',
            'Auto Debit',
            'Net Banking',
            'Mobile Banking'
        ))
);