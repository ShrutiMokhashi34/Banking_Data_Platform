CREATE OR REPLACE TABLE ABC_BANK.STG.RISK_FRAUD_ALERTS
(
    ALERT_ID                  VARCHAR(20)       NOT NULL,

    TRANSACTION_ID            VARCHAR(20)       NOT NULL,

    FRAUD_SCORE               NUMBER(5,2)       NOT NULL,

    ALERT_REASON              VARCHAR(255)      NOT NULL,

    ALERT_STATUS              VARCHAR(20)       NOT NULL,

    ALERT_TIMESTAMP           TIMESTAMP_NTZ     NOT NULL,

    ASSIGNED_TO               VARCHAR(100),

    ASSIGNEE_EMP_ID           VARCHAR(20),

    RESOLUTION_DATE           DATE,

    CREATED_AT                TIMESTAMP_NTZ     DEFAULT CURRENT_TIMESTAMP(),

    UPDATED_AT                TIMESTAMP_NTZ,

    SOURCE_SYSTEM             VARCHAR(50)       DEFAULT 'Fraud Detection System',

    BATCH_ID                  TIMESTAMP_NTZ,
	BATCH_DATE          	  DATE,
	PIPELINE_RUN_ID			  VARCHAR(20),
	DATA_SOURCE				  VARCHAR(50)
);