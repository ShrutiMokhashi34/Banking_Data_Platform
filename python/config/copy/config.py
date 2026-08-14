"""
===============================================================================
Banking Data Platform
config.py

Project configuration settings.

Author : Shruti Mokhashi
===============================================================================
"""

from pathlib import Path

# =============================================================================
# PROJECT PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = PROJECT_ROOT.parent / "datasets" / "raw"

LOG_DIR = PROJECT_ROOT / "logs"

DATASETS_DIR = PROJECT_ROOT.parent / "datasets"

# =============================================================================
# RANDOM SEED
# =============================================================================

RANDOM_SEED = 42

# =============================================================================
# RECORD COUNTS
# =============================================================================

NUM_CUSTOMERS = 5000

NUM_ADDRESSES = 6000

NUM_KYC = NUM_CUSTOMERS

NUM_BRANCHES = 50

NUM_EMPLOYEES = 350

NUM_ACCOUNTS = 7000

NUM_CARDS = 9000

NUM_TRANSACTIONS = 250000

NUM_LOANS = 2500

NUM_LOAN_APPLICATIONS = 4000

NUM_LOAN_REPAYMENTS = 35000

NUM_LOAN_COLLATERALS = NUM_LOANS

NUM_MERCHANTS = 1000

NUM_FRAUD_ALERTS = 3000

NUM_EXCHANGE_RATE_DAYS = 365

NUM_HOLIDAYS = 500

# =============================================================================
# OUTPUT FILES
# =============================================================================

CUSTOMERS_FILE = OUTPUT_DIR / "customers_20260801.csv"

CUSTOMER_ADDRESSES_FILE = OUTPUT_DIR / "customer_addresses_20260801.csv"

KYC_FILE = OUTPUT_DIR / "kyc_20260801.csv"

BRANCHES_FILE = OUTPUT_DIR / "branches_20260801.csv"

EMPLOYEES_FILE = OUTPUT_DIR / "employees_20260801.csv"

ACCOUNTS_FILE = OUTPUT_DIR / "accounts_20260801.csv"

CARDS_FILE = OUTPUT_DIR / "cards_20260801.csv"

TRANSACTIONS_FILE = OUTPUT_DIR / "transactions_20260801.csv"

LOANS_FILE = OUTPUT_DIR / "loans_20260801.csv"

LOAN_APPLICATIONS_FILE = OUTPUT_DIR / "loan_applications_20260801.csv"

LOAN_REPAYMENTS_FILE = OUTPUT_DIR / "loan_repayments_20260801.csv"

LOAN_COLLATERALS_FILE = OUTPUT_DIR / "loan_collateral_20260801.csv"

MERCHANTS_FILE = OUTPUT_DIR / "merchants_20260801.csv"

FRAUD_ALERTS_FILE = OUTPUT_DIR / "fraud_alerts_20260801.csv"

EXCHANGE_RATES_FILE = OUTPUT_DIR / "exchange_rates_20260801.csv"

HOLIDAY_CALENDAR_FILE = OUTPUT_DIR / "holiday_calendar.csv"

SUMMARY_FILE = OUTPUT_DIR / "generation_summary_20260801.txt"

# =============================================================================
# LOGGING
# =============================================================================

LOG_FILE = LOG_DIR / "data_generation.log"

LOG_LEVEL = "INFO"

# =============================================================================
# API CONFIGURATION
# =============================================================================

EXCHANGE_RATE_API = "https://open.er-api.com/v6/latest/INR"

HOLIDAY_API_COUNTRY = "IN"

HOLIDAY_START_YEAR = 2025

HOLIDAY_END_YEAR = 2027

# =============================================================================
# BATCH CONFIGURATION
# =============================================================================

SOURCE_SYSTEM = "Enterprise System"

CRM_SOURCE_SYSTEM = "CRM/KYC Platform"

LOAN_SOURCE_SYSTEM = "Loan Management System"

FRAUD_SOURCE_SYSTEM = "Fraud Detection System"

EXCHANGE_RATE_SOURCE = "Exchange Rate API"

HOLIDAY_SOURCE = "Holiday Calendar API"

# =============================================================================
# DATA QUALITY
# =============================================================================

ENABLE_VALIDATIONS = True

EXPORT_SUMMARY = True

OVERWRITE_EXISTING_FILES = True

# =============================================================================
# PERFORMANCE
# =============================================================================

CHUNK_SIZE = 10000

MAX_WORKERS = 4