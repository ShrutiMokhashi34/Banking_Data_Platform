CREATE OR REPLACE TABLE ABC_BANK.AGG.HOLIDAY_CALENDAR
(
    HOLIDAY_ID              VARCHAR(20)         NOT NULL,

    HOLIDAY_DATE            DATE                NOT NULL,

    COUNTRY                 VARCHAR(100)        NOT NULL,

    STATE                   VARCHAR(100),

    HOLIDAY_NAME            VARCHAR(100)        NOT NULL,

    HOLIDAY_TYPE            VARCHAR(30)         NOT NULL,

    IS_BANK_HOLIDAY         BOOLEAN             DEFAULT TRUE,

    CREATED_AT              TIMESTAMP_NTZ       DEFAULT CURRENT_TIMESTAMP(),

    UPDATED_AT              TIMESTAMP_NTZ,

    SOURCE_SYSTEM           VARCHAR(50)         DEFAULT 'Holiday Calendar API',

    BATCH_ID                VARCHAR(50),

    CONSTRAINT PK_HOLIDAY_CALENDAR
        PRIMARY KEY (HOLIDAY_ID),

    CONSTRAINT UQ_HOLIDAY
        UNIQUE
        (
            HOLIDAY_DATE,
            COUNTRY,
            STATE,
            HOLIDAY_NAME
        ),

    CONSTRAINT CHK_HOLIDAY_TYPE
        CHECK
        (
            UPPER(HOLIDAY_TYPE) IN
            (
                'NATIONAL',
                'STATE',
                'BANK',
                'RELIGIOUS',
                'OPTIONAL'
            )
        )
);