# Technology Stack

| Technology | Purpose |
|------------|----------|
| Azure Data Lake Storage | Landing Zone |
| Azure Databricks | Data Processing and Transformation |
| Snowflake | Data Warehouse for Analytics |
| Airflow | Workflow Orchestration |
| GCP, Google ADK | Agent Chain Development and App Development |
| Data Studio | Executive On-Demand Dashboards |
| GitHub | Version Control |

| Programming Language | Purpose |
|------------|----------|
| PySpark | Data Transformations |
| SQL | Data Analytics |
| Python | Data Generation & Ingestion |

| Ingestion Timelines |
|------------|----------|
| Data for the analytics app is expected at a one day delay to account for any issues during data storage and ingestion |
| Azure to Snowflake STG Data Ingestion |  3pm IST Daily |
| Snowflake STG to Databricks Silver Layer | 5:15pm IST Daily |
| Databricks Silver to Databricks Gold Layer | 6pm IST Daily |
| Databricks Gold Layer to Snowflake AGG | 6:30PM IST Daily |
| Snowflake AGG to BigQuery | 7PM IST Daily |