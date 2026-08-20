CREATE OR REPLACE TABLE banking_data_processing.silver.CUST_CUSTOMERS
(
    CUSTOMER_ID         VARCHAR(20)        NOT NULL,
    FIRST_NAME          VARCHAR(50)        NOT NULL,
    LAST_NAME           VARCHAR(50)        NOT NULL,
    DOB                 DATE               NOT NULL,
    GENDER              VARCHAR(20)        NOT NULL,
    EMAIL               VARCHAR(100),
    PHONE               VARCHAR(20),
    OCCUPATION          VARCHAR(100),
    ANNUAL_INCOME       DECIMAL(15,2),
    CUSTOMER_SINCE      DATE               NOT NULL,
    RISK_RATING         VARCHAR(10)        NOT NULL,
    CUSTOMER_STATUS     VARCHAR(20)        NOT NULL,
    CREATED_AT          TIMESTAMP_NTZ,
    UPDATED_AT          TIMESTAMP_NTZ,
    SOURCE_SYSTEM       VARCHAR(50)        NOT NULL,
	BATCH_DATE          DATE,
	PIPELINE_RUN_ID		VARCHAR(100),
	DATA_SOURCE			VARCHAR(50),
	IS_CURRENT			VARCHAR(5),

    CONSTRAINT PK_CUSTOMERS
        PRIMARY KEY (CUSTOMER_ID)
);