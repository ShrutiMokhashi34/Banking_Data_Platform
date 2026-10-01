# Enterprise Banking Data Platform

## Status

Project Complete!!

Live Application: https://bankingdataplatform.web.app

Detailed Project Documentation: [Google Doc](https://docs.google.com/document/d/1xvUdOWI-Qz5FylIGEO2BvV_nzCVMtPnNWYDW5BfER5M/edit?usp=sharing)

Check out ["ABC Bank Data Assistant: An End-to-End Banking Data Platform"](https://patchamomma-273845608377.us-central1.run.app/) by Shruti Mokhashi (Rank #58) on Google Patchamomma 2026!

---

## Project Overview

This project demonstrates the design and implementation of an enterprise-scale Banking Data Platform using modern cloud and data engineering technologies.

The platform ingests banking data from multiple source systems, processes it using a Medallion Architecture (Bronze, Silver, Gold) through Databricks, loads curated data into Snowflake, orchestrates workflows with Apache Airflow, and presents business insights through an application powered by a multi-agent chain created using Google ADK and BigQuery.

---

## Architecture

![Banking Data Platform Architecture](architecture/Banking%20Data%20Platform%20Architechture.png)

**Data flow:** Raw data lands daily in Azure Data Lake Storage (ADLS Gen2) → Snowflake staging via Airflow-orchestrated loads → Databricks Bronze / Silver / Gold (Delta Lake) → Snowflake aggregate layer → BigQuery, which serves the Data Studio dashboards and the Google ADK chatbot.

---

## Try the Live Application

The app enforces role-based access for customers and six employee designations: what you can see depends on who you log in as. Use these mock accounts to explore each role at https://bankingdataplatform.web.app.

| Role | User ID | Password | Customer / banking data | Employee data | Pipeline / data engineering info |
|---|---|---|---|---|---|
| Customer | `CUST00000001` | `Cust@1x` | Own data only | None | No access |
| Associate | `EMP00000005` | `Emp@5x` | Permitted access | Own record only | No access |
| Senior Associate | `EMP00000003` | `Emp@3x` | Permitted access | Own record only | No access |
| Assistant Manager | `EMP00000032` | `Emp@32x` | Permitted access | Employees in own branch | No access |
| Officer | `EMP00000008` | `Emp@8x` | Full permitted access | All employees, all branches | Full access |
| Manager | `EMP00000002` | `Emp@2x` | Full permitted access | All employees, all branches | Full access |
| Senior Manager | `EMP00000053` | `Emp@53x` | Full permitted access | All employees, all branches | Full access |
| Resigned employee | `EMP00000001` | `Emp@1x` | Login is rejected | Login is rejected | Login is rejected |
| Terminated employee | `EMP00000015` | `Emp@15x` | Login is rejected | Login is rejected | Login is rejected |
| Retired employee | `EMP00000019` | `Emp@19x` | Login is rejected | Login is rejected | Login is rejected |
| Missing / unknown status | — | — | Access denied (fail closed) | Access denied (fail closed) | Access denied (fail closed) |

Want to try other users? The full list of mock accounts (customers and employees, with each employee's designation and status) is in [`mock_credentials.csv`](google%20adk%20agent%20chain%20and%20app/app/datasets/auth/mock_credentials.csv).

**Customers** can see only their own profile, accounts, transactions, loans and fraud alerts. **Active employees** can access banking and customer data, with full permitted access for Officers, Managers and Senior Managers; their designation also controls employee data and pipeline access as shown above. **Resigned, terminated and retired employees** cannot log in or receive a valid JWT. If an employee's status is missing or unknown, authorization fails closed and denies access rather than assuming the employee is active.

> All credentials and data are synthetic and were generated for this project. No real customer or employee information is used.

### How access is enforced

Authorization happens server-side. The system does not rely on what the user claims in the chat, on the LLM deciding what the user may see, or on frontend restrictions:

```
Authenticated identity → Backend authorization → Authorized tool → BigQuery → Filtered data
```

The user's identity (user type, ID, role, employee status and branch) comes from the authenticated session (JWT), so a customer cannot type in another customer's ID to bypass the rules. Every generated query also passes a read-only SQL validation layer before it reaches BigQuery.

---

## Technology Stack Utilized

- Microsoft Azure
- Azure Data Lake Storage Gen2
- Azure Databricks
- Apache Spark (PySpark)
- Apache Airflow
- Snowflake
- BigQuery
- Google Cloud Platform (GCP) and Cloud Run
- Google ADK Kit
- Firebase
- React
- SQL
- Python
- Data Studio
- Git & GitHub

---
