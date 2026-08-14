CREATE OR REPLACE TABLE ABC_BANK.STG.HOLIDAY_CALENDAR
(
    HOLIDAY_ID              VARCHAR(20)         NOT NULL,

    HOLIDAY_DATE            DATE                NOT NULL,

    COUNTRY                 VARCHAR(100)        NOT NULL,

    STATE                   VARCHAR(100),

    HOLIDAY_NAME            VARCHAR(100)        NOT NULL,

    HOLIDAY_TYPE            VARCHAR(30)         NOT NULL,

    IS_BANK_HOLIDAY         BOOLEAN             DEFAULT 'Y',

    CREATED_AT              TIMESTAMP_NTZ       DEFAULT CURRENT_TIMESTAMP(),

    UPDATED_AT              TIMESTAMP_NTZ,

    SOURCE_SYSTEM           VARCHAR(50)         DEFAULT 'Holiday Calendar API'
);