CREATE OR REPLACE TABLE ABC_BANK.STG.ORG_EMPLOYEES
(
    EMPLOYEE_ID             VARCHAR(20)        NOT NULL,

    BRANCH_ID               VARCHAR(20)        NOT NULL,

    FIRST_NAME              VARCHAR(50)        NOT NULL,

    LAST_NAME               VARCHAR(50)        NOT NULL,

    DESIGNATION             VARCHAR(50)        NOT NULL,

    DEPARTMENT              VARCHAR(50)        NOT NULL,

    HIRE_DATE               DATE               NOT NULL,

    SALARY                  NUMBER(12,2)       NOT NULL,

    EMPLOYEE_STATUS         VARCHAR(20)        NOT NULL,

    CREATED_AT              TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ,
    SOURCE_SYSTEM           VARCHAR(50)        DEFAULT 'Enterprise System',
    BATCH_ID                VARCHAR(50),

    CONSTRAINT PK_EMPLOYEES
        PRIMARY KEY (EMPLOYEE_ID),

    CONSTRAINT FK_EMPLOYEE_BRANCH
        FOREIGN KEY (BRANCH_ID)
        REFERENCES ORG_BRANCHES(BRANCH_ID),

    CONSTRAINT CHK_SALARY
        CHECK (SALARY > 0),

    CONSTRAINT CHK_EMPLOYEE_STATUS
        CHECK (EMPLOYEE_STATUS IN
        (
            'Active',
            'On Leave',
            'Suspended',
            'Resigned',
            'Retired',
            'Terminated'
        ))
);