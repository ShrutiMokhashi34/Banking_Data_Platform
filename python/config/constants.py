"""
===============================================================================
Banking Data Platform
constants.py

Centralized business constants used across the synthetic data generation
framework.

Author : Shruti Mokhashi
===============================================================================
"""

# =============================================================================
# GLOBAL SETTINGS
# =============================================================================

SEED = 56

COUNTRY = "India"

SOURCE_SYSTEM = "Enterprise System"

CURRENCY = "INR"

BASE_CURRENCY = "INR"

# =============================================================================
# CUSTOMER DOMAIN
# =============================================================================

GENDERS = [
    "Male",
    "Female",
    "Non-Binary",
    "Prefer Not to Say"
]

CUSTOMER_STATUS = [
    "Active",
    "Dormant",
    "Blocked",
    "Closed"
]

RISK_RATINGS = [
    "Low",
    "Medium",
    "High"
]

ADDRESS_TYPES = [
    "Home",
    "Office",
    "Permanent",
    "Mailing"
]

KYC_STATUS = [
    "Pending",
    "Verified",
    "Rejected"
]

# =============================================================================
# BANKING DOMAIN
# =============================================================================

ACCOUNT_TYPES = [
    "Savings",
    "Current",
    "Salary",
    "Fixed Deposit",
    "Recurring Deposit",
    "NRE",
    "NRO"
]

ACCOUNT_STATUS = [
    "Active",
    "Dormant",
    "Frozen",
    "Closed"
]

CARD_TYPES = [
    "Debit",
    "Credit",
    "Prepaid",
    "Charge"
]

CARD_NETWORKS = [
    "Visa",
    "Mastercard",
    "RuPay",
    "American Express"
]

CARD_STATUS = [
    "Active",
    "Blocked",
    "Expired",
    "Closed",
    "Lost",
    "Stolen"
]

TRANSACTION_TYPES = [
    "Credit",
    "Debit",
    "Transfer",
    "Withdrawal",
    "Deposit",
    "POS Purchase",
    "Online Payment",
    "Bill Payment"
]

TRANSACTION_CHANNELS = [
    "UPI",
    "ATM",
    "POS",
    "Online Banking",
    "Mobile Banking",
    "Branch",
    "NEFT",
    "RTGS",
    "IMPS",
    "ECS",
    "Cheque",
    "Auto Debit"
]

TRANSACTION_STATUS = [
    "Success",
    "Pending",
    "Failed",
    "Reversed",
    "Completed"
]

# =============================================================================
# LOAN DOMAIN
# =============================================================================

LOAN_TYPES = [
    "Home Loan",
    "Personal Loan",
    "Car Loan",
    "Education Loan",
    "Business Loan",
    "Gold Loan"
]

LOAN_STATUS = [
    "Active",
    "Closed",
    "Defaulted",
    "Pending",
    "Written Off"
]

APPROVAL_STATUS = [
    "Pending",
    "Approved",
    "Rejected",
    "Cancelled"
]

PAYMENT_MODES = [
    "UPI",
    "NEFT",
    "RTGS",
    "IMPS",
    "CASH",
    "CHEQUE",
    "AUTO DEBIT",
    "NET BANKING",
    "MOBILE BANKING"
]

ASSET_TYPES = [
    "Property",
    "Vehicle",
    "Gold",
    "Fixed Deposit",
    "Shares",
    "Mutual Funds"
]

# =============================================================================
# ORGANIZATION DOMAIN
# =============================================================================

EMPLOYEE_STATUS = [
    "Active",
    "On Leave",
    "Suspended",
    "Resigned",
    "Retired",
    "Terminated"
]

DEPARTMENTS = [
    "Retail Banking",
    "Corporate Banking",
    "Operations",
    "Risk",
    "Compliance",
    "Finance",
    "Human Resources",
    "Technology",
    "Customer Service"
]

DESIGNATIONS = [
    "Relationship Manager",
    "Branch Manager",
    "Operations Executive",
    "Software Engineer",
    "Data Engineer",
    "Data Analyst",
    "Risk Analyst",
    "HR Executive",
    "Customer Support Executive"
]

# =============================================================================
# MERCHANT DOMAIN
# =============================================================================

MERCHANT_CATEGORIES = [
    "Retail",
    "Grocery",
    "Fuel",
    "Healthcare",
    "Restaurant",
    "Travel",
    "Entertainment",
    "Education",
    "Utilities",
    "E-Commerce",
    "Government",
    "Telecom",
    "Other"
]

MERCHANT_STATUS = [
    "Active",
    "Inactive",
    "Suspended",
    "Closed"
]

ALERT_STATUS = [
    "Open",
    "Under Investigation",
    "Resolved",
    "False Positive",
    "Closed"
]

ALERT_REASONS = [
    "High Transaction Amount",
    "Multiple Failed Attempts",
    "Location Mismatch",
    "Velocity Check Failed",
    "Blacklisted Merchant",
    "Unusual Spending Pattern",
    "Card Not Present"
]

# =============================================================================
# REFERENCE DOMAIN
# =============================================================================

SUPPORTED_CURRENCIES = [
    "INR",
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "AUD",
    "CAD",
    "CHF",
    "SGD",
    "AED",
    "CNY",
    "HKD",
    "NZD"
]

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "AUD": "A$",
    "CAD": "C$",
    "CHF": "CHF",
    "SGD": "S$",
    "AED": "د.إ",
    "CNY": "¥",
    "HKD": "HK$",
    "NZD": "NZ$"
}

HOLIDAY_TYPES = [
    "National",
    "State",
    "Bank",
    "Religious",
    "Optional"
]

# =============================================================================
# DATA GENERATION PARAMETERS
# =============================================================================

MIN_CUSTOMER_AGE = 18
MAX_CUSTOMER_AGE = 80

MIN_INCOME = 250000
MAX_INCOME = 5000000

MIN_INTEREST_RATE = 6.5
MAX_INTEREST_RATE = 18.0

MIN_TRANSACTION_AMOUNT = 10
MAX_TRANSACTION_AMOUNT = 100000

MIN_FRAUD_SCORE = 0
MAX_FRAUD_SCORE = 100

# =============================================================================
# DEFAULT VALUES
# =============================================================================

DEFAULT_COUNTRY = "India"

DEFAULT_SOURCE_SYSTEM = "Enterprise System"

DEFAULT_BATCH_PREFIX = "BATCH"

DATE_FORMAT = "%Y-%m-%d"

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"