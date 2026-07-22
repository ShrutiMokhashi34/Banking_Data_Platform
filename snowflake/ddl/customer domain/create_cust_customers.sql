CREATE OR REPLACE TABLE ABC_BANK.STG.CUST_CUSTOMERS
(
    CUSTOMER_ID         VARCHAR(20)        NOT NULL,
    FIRST_NAME          VARCHAR(50)        NOT NULL,
    LAST_NAME           VARCHAR(50)        NOT NULL,
    DOB                 DATE               NOT NULL,
    GENDER              VARCHAR(20)        NOT NULL,
    EMAIL               VARCHAR(100),
    PHONE               VARCHAR(20),
    OCCUPATION          VARCHAR(100),
    ANNUAL_INCOME       NUMBER(15,2),
    CUSTOMER_SINCE      DATE               NOT NULL,
    RISK_RATING         VARCHAR(10)        NOT NULL,
    CUSTOMER_STATUS     VARCHAR(20)        NOT NULL,

    CREATED_AT          TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT          TIMESTAMP_NTZ,
    SOURCE_SYSTEM       VARCHAR(50)        NOT NULL,
    BATCH_ID            VARCHAR(50)        NOT NULL,

    CONSTRAINT PK_CUSTOMERS
        PRIMARY KEY (CUSTOMER_ID),

    CONSTRAINT CHK_GENDER
        CHECK (GENDER IN ('Male','Female','Non-Binary','Prefer Not To Say')),

    CONSTRAINT CHK_RISK_RATING
        CHECK (RISK_RATING IN ('Low','Medium','High')),

    CONSTRAINT CHK_CUSTOMER_STATUS
        CHECK (CUSTOMER_STATUS IN ('Active','Dormant','Closed','Blocked')),

    CONSTRAINT CHK_ANNUAL_INCOME
        CHECK (ANNUAL_INCOME >= 0)
);