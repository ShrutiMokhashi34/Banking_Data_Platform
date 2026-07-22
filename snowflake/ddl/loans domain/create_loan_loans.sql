CREATE OR REPLACE TABLE ABC_BANK.STG.LOAN_LOANS
(
    LOAN_ID                 VARCHAR(20)        NOT NULL,
	LOAN_APPLICATION_ID 	VARCHAR(20)		   NOT NULL,
    CUSTOMER_ID             VARCHAR(20)        NOT NULL,

    LOAN_TYPE               VARCHAR(30)        NOT NULL,

    PRINCIPAL_AMOUNT        NUMBER(15,2)       NOT NULL,

    INTEREST_RATE           NUMBER(5,2)        NOT NULL,

    TENURE_MONTHS           NUMBER(4,0)        NOT NULL,

    EMI_AMOUNT              NUMBER(15,2)       NOT NULL,

    LOAN_STATUS             VARCHAR(20)        NOT NULL,

    CREATED_AT              TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ,
    SOURCE_SYSTEM           VARCHAR(50)        DEFAULT 'Loan Management System',
    BATCH_ID                VARCHAR(50),

    CONSTRAINT PK_LOANS
        PRIMARY KEY (LOAN_ID),

	CONSTRAINT FK_LOANS_APPLICATION
		FOREIGN KEY (LOAN_APPLICATION_ID)
		REFERENCES LOAN_LOAN_APPLICATIONS(APPLICATION_ID),

    CONSTRAINT FK_LOANS_CUSTOMERS
        FOREIGN KEY (CUSTOMER_ID)
        REFERENCES CUST_CUSTOMERS(CUSTOMER_ID),

    CONSTRAINT CHK_LOAN_TYPE
        CHECK (LOAN_TYPE IN
        (
            'Home Loan',
            'Personal Loan',
            'Auto Loan',
            'Education Loan',
            'Business Loan',
            'Gold Loan'
        )),

    CONSTRAINT CHK_PRINCIPAL_AMOUNT
        CHECK (PRINCIPAL_AMOUNT > 0),

    CONSTRAINT CHK_INTEREST_RATE
        CHECK (INTEREST_RATE BETWEEN 0 AND 100),

    CONSTRAINT CHK_TENURE
        CHECK (TENURE_MONTHS > 0),

    CONSTRAINT CHK_EMI
        CHECK (EMI_AMOUNT > 0),

    CONSTRAINT CHK_LOAN_STATUS
        CHECK (LOAN_STATUS IN
        (
            'Pending',
            'Active',
            'Closed',
            'Defaulted',
            'Written Off'
        ))
);