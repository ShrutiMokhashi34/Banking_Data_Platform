"""
===============================================================================
Banking Data Platform
utils.py

Reusable utility functions for synthetic data generation.

Author : Shruti Mokhashi
===============================================================================
"""

from __future__ import annotations

import logging
import random
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from faker import Faker

from config.config import (
    OUTPUT_DIR,
    LOG_DIR,
    RANDOM_SEED,
    SUMMARY_FILE,
    PROJECT_ROOT,
    DATASETS_DIR
)
from config.constants import (
    MIN_INCOME,
    MAX_INCOME,
)

# =============================================================================
# INITIALIZE RANDOMNESS
# =============================================================================

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

fake = Faker("en_IN")
fake.seed_instance(RANDOM_SEED)

# =============================================================================
# DIRECTORY UTILITIES
# =============================================================================

def create_directories() -> None:
    """
    Create required project directories.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# DATA EXPORT
# =============================================================================

def export_csv(df: pd.DataFrame, file_path: Path) -> None:
    """
    Export a DataFrame to CSV.
    """
    df.to_csv(file_path, index=False)

# =============================================================================
# CONTACT DETAILS
# =============================================================================

def generate_phone_number() -> str:
    """
    Generate an Indian mobile number.
    """
    prefix = random.choice(["98", "99", "97", "96", "95", "94", "93", "92", "91", "90"])
    suffix = random.randint(10000000, 99999999)
    return f"+91{prefix}{suffix}"

def generate_email(first_name: str, last_name: str) -> str:
    """
    Generate a realistic email address.
    """
    domains = [
        "gmail.com",
        "outlook.com",
        "yahoo.com",
        "hotmail.com"
    ]

    return (
        f"{first_name.lower()}."
        f"{last_name.lower()}"
        f"{random.randint(1,999)}@"
        f"{random.choice(domains)}"
    )

# =============================================================================
# LOCATION DETAILS
# =============================================================================

class Geography:

    def __init__(self):

        file_path = (
            DATASETS_DIR
            / "reference"
            / "india_locations.csv"
        )

        self.df = pd.read_csv(file_path)

        # Remove duplicate combinations
        self.df = self.df[
            ["state", "city", "pincode"]
        ].drop_duplicates()

    def random_location(self) -> dict:
        """
        Returns a random valid state-city-pincode combination.
        """

        row = self.df.sample(1).iloc[0]

        return {
            "state": row["state"],
            "city": row["city"],
            "pincode": str(row["pincode"])
        }

    def random_city_from_state(self, state: str) -> dict:
        """
        Returns a random city and pincode for a given state.
        """

        locations = self.df[self.df["state"] == state]

        row = locations.sample(1).iloc[0]

        return {
            "state": state,
            "city": row["city"],
            "pincode": str(row["pincode"])
        }

# =============================================================================
# KYC
# =============================================================================

def generate_pan() -> str:
    """
    Generate a valid PAN format.
    Example:
        ABCDE1234F
    """
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    return (
        "".join(random.choices(letters, k=5))
        + str(random.randint(1000, 9999))
        + random.choice(letters)
    )

def generate_aadhaar() -> str:
    """
    Generate a 12-digit Aadhaar number.
    """
    return "".join(str(random.randint(0, 9)) for _ in range(12))

# =============================================================================
# INCOME
# =============================================================================

def generate_income() -> float:
    """
    Generate weighted annual income.
    """

    income = random.choices(
        population=[
            300000,
            500000,
            800000,
            1200000,
            2000000,
            3500000,
            5000000,
        ],
        weights=[
            35,
            25,
            15,
            10,
            8,
            5,
            2,
        ],
        k=1,
    )[0]

    return float(
        max(
            MIN_INCOME,
            min(MAX_INCOME, income)
        )
    )

# =============================================================================
# DATE UTILITIES
# =============================================================================

def current_timestamp() -> datetime:
    return datetime.now()

def random_date(
    start: date,
    end: date,
) -> date:
    """
    Return a random date between two dates.
    """
    return fake.date_between(
        start_date=start,
        end_date=end,
    )

# =============================================================================
# SUMMARY
# =============================================================================

def write_summary(summary: dict) -> None:
    """
    Write generation summary.
    """

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:

        f.write("=====================================\n")
        f.write("BANKING DATA PLATFORM\n")
        f.write("Generation Summary\n")
        f.write("=====================================\n\n")

        for key, value in summary.items():
            f.write(f"{key:<30}{value}\n")

# =============================================================================
# VALIDATION
# =============================================================================

def validate_unique(df: pd.DataFrame, column: str) -> bool:
    """
    Validate uniqueness.
    """
    return df[column].is_unique

def validate_not_null(df: pd.DataFrame, column: str) -> bool:
    """
    Validate null values.
    """
    return not df[column].isnull().any()

# =============================================================================
# LOGGER
# =============================================================================

def log_dataframe_info(
    logger: logging.Logger,
    table_name: str,
    dataframe: pd.DataFrame,
) -> None:
    """
    Log DataFrame statistics.
    """

    logger.info("-" * 60)
    logger.info("Table : %s", table_name)
    logger.info("Rows  : %s", len(dataframe))
    logger.info("Cols  : %s", len(dataframe.columns))
    logger.info("-" * 60)