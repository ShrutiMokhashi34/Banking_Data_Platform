"""
===============================================================================
Banking Data Platform
id_generator.py

Reusable ID generator for all entities.

Author : Shruti Mokhashi
===============================================================================
"""

from itertools import count
from typing import Dict

# =============================================================================
# ID PREFIXES
# =============================================================================

ID_PREFIXES = {
    "customer": "CUST",
    "address": "ADDR",
    "loan": "LN",
    "application": "APP",
    "repayment": "RP",
    "collateral": "COL",
    "account": "ACC",
    "branch": "BR",
    "employee": "EMP",
    "card": "CD",
    "transaction": "TR",
    "merchant": "MER",
    "alert": "ALR",
    "holiday": "HOL"
}

# =============================================================================
# Internal Counters
# =============================================================================

_COUNTERS: Dict[str, count] = {
    prefix: count(1)
    for prefix in ID_PREFIXES.values()
}

# =============================================================================
# Generic ID Generator
# =============================================================================

def generate_id(prefix: str, width: int = 8) -> str:
    """
    Generate a sequential ID.

    Example:
        generate_id("CUST")
        CUST00000001
    """

    if prefix not in _COUNTERS:
        raise ValueError(f"Invalid prefix: {prefix}")

    return f"{prefix}{next(_COUNTERS[prefix]):0{width}d}"

# =============================================================================
# Convenience Functions
# =============================================================================

def customer_id():
    return generate_id(ID_PREFIXES["customer"])


def address_id():
    return generate_id(ID_PREFIXES["address"])


def loan_id():
    return generate_id(ID_PREFIXES["loan"])


def application_id():
    return generate_id(ID_PREFIXES["application"])


def repayment_id():
    return generate_id(ID_PREFIXES["repayment"])


def collateral_id():
    return generate_id(ID_PREFIXES["collateral"])


def account_id():
    return generate_id(ID_PREFIXES["account"])


def branch_id():
    return generate_id(ID_PREFIXES["branch"])

def employee_id():
    return generate_id(ID_PREFIXES["employee"])

def card_id():
    return generate_id(ID_PREFIXES["card"])


def transaction_id():
    return generate_id(ID_PREFIXES["transaction"])


def merchant_id():
    return generate_id(ID_PREFIXES["merchant"])


def alert_id():
    return generate_id(ID_PREFIXES["alert"])


def holiday_id():
    return generate_id(ID_PREFIXES["holiday"])


# =============================================================================
# Reset Counters
# =============================================================================

def reset_counters():
    """
    Reset all ID counters.
    Useful for testing or regenerating datasets.
    """
    global _COUNTERS

    _COUNTERS = {
        prefix: count(1)
        for prefix in ID_PREFIXES.values()
    }