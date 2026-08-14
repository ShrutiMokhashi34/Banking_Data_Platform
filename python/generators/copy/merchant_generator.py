"""
Merchant Domain Data Generator

Generates synthetic data for:

    1. Merchants

Author: Shruti Mokhashi
"""

from __future__ import annotations

# =====================================================================
# Standard Library
# =====================================================================

import random
from datetime import datetime

# =====================================================================
# Third Party Libraries
# =====================================================================

import pandas as pd
from faker import Faker

# =====================================================================
# Project Configuration
# =====================================================================

from config.config import (
    RANDOM_SEED,
    NUM_MERCHANTS,
    MERCHANTS_FILE,
)

from config.constants import (
    COUNTRY,
    SOURCE_SYSTEM,
    MERCHANT_CATEGORIES,
    MERCHANT_STATUS,
)

# =====================================================================
# Models
# =====================================================================

from models.merchant import Merchant

# =====================================================================
# Utilities
# =====================================================================

from generators.id_generator import (
    merchant_id,
)

from config.logging_config import setup_logger

from generators.utils import (
    Geography
)

# =====================================================================
# Merchant Generator
# =====================================================================


class MerchantGenerator:
    """
    Merchant Domain Generator.

    Generates:

        • Merchants
    """

    def __init__(self) -> None:

        self.logger = setup_logger(__name__)

        self.fake = Faker("en_IN")

        random.seed(RANDOM_SEED)

        self.fake.seed_instance(RANDOM_SEED)

        self.locations = Geography()

        # ==============================================================
        # Generated Objects
        # ==============================================================

        self.merchants: list[Merchant] = []

        self.logger.info(
            "Merchant Generator initialized successfully."
        )

    # ==============================================================
    # DataFrame
    # ==============================================================

    def merchants_df(self) -> pd.DataFrame:
        """
        Return Merchant dataframe.
        """

        return pd.DataFrame(

            [
                merchant.to_dict()
                for merchant in self.merchants
            ]

        )
        
    # =====================================================================
    # Merchant Helper Methods
    # =====================================================================
    
    def _generate_merchant_name(
        self,
        merchant_category: str,
    ) -> str:
        """
        Generate merchant name.
        """
    
        prefixes = [
    
            "Shree",
            "Sri",
            "New",
            "Royal",
            "National",
            "Modern",
            "Prime",
            "Sai",
            "Om",
    
        ]
    
        suffixes = {
    
            "Retail": [
                "Store",
                "Traders",
                "Fashion",
                "Outlet",
                "Mart",
            ],
    
            "Grocery": [
                "Supermarket",
                "Fresh",
                "Stores",
                "Mart",
                "Provision Store",
            ],
    
            "Fuel": [
                "Fuel Station",
                "Petrol Pump",
                "Energy",
            ],
    
            "Healthcare": [
                "Hospital",
                "Medical Centre",
                "Clinic",
            ],
    
            "Restaurant": [
                "Restaurant",
                "Cafe",
                "Kitchen",
                "Dhaba",
            ],
    
            "Travel": [
                "Travels",
                "Tours",
                "Transport",
            ],
    
            "Entertainment": [
                "Cinema",
                "Multiplex",
                "Arcade",
            ],
    
            "Education": [
                "Academy",
                "Institute",
                "Learning Centre",
            ],
    
            "Utilities": [
                "Electricity",
                "Water Supply",
                "Gas Services",
            ],
    
            "E-Commerce": [
                "Online",
                "Marketplace",
                "Digital",
            ],
    
            "Government": [
                "Corporation",
                "Municipality",
                "Authority",
            ],
    
            "Telecom": [
                "Communications",
                "Telecom",
                "Networks",
            ],
    
            "Other": [
                "Enterprise",
                "Services",
            ],
    
        }
    
        prefix = random.choice(prefixes)
    
        suffix = random.choice(
    
            suffixes.get(
    
                merchant_category,
    
                ["Enterprise"],
    
            )
    
        )
    
        return f"{prefix} {self.fake.last_name()} {suffix}"
    
    
    def _generate_merchant_category(self) -> str:
        """
        Generate Merchant Category.
        """
    
        return random.choices(
    
            MERCHANT_CATEGORIES,
    
            weights=[
    
                15,   # Retail
                12,   # Grocery
                6,    # Fuel
                7,    # Healthcare
                15,   # Restaurant
                5,    # Travel
                6,    # Entertainment
                4,    # Education
                8,    # Utilities
                12,   # E-Commerce
                5,    # Government
                3,    # Telecom
                2,    # Other
    
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_merchant_type(self) -> str:
        """
        Generate Merchant Type.
        """
    
        return random.choices(
    
            [
    
                "Local",
    
                "Regional",
    
                "National",
    
            ],
    
            weights=[
    
                70,
    
                20,
    
                10,
    
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_location(self):
    
        location = self.locations.random_location()
    
        return (
    
            location["city"],
    
            location["state"],
    
        )
    
    
    def _generate_merchant_status(self) -> str:
        """
        Generate Merchant Status.
        """
    
        return random.choices(
    
            MERCHANT_STATUS,
    
            weights=[
    
                94,    # Active
                3,     # Inactive
                2,     # Suspended
                1,     # Closed
    
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_accepts_upi(self) -> str:
        """
        Generate UPI acceptance flag.
        """
    
        return random.choices(
    
            [
    
                "Yes",
    
                "No",
    
            ],
    
            weights=[
    
                95,
    
                5,
    
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_accepts_cards(self) -> str:
        """
        Generate Card acceptance flag.
        """
    
        return random.choices(
    
            [
    
                "Yes",
    
                "No",
    
            ],
    
            weights=[
    
                82,
    
                18,
    
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_average_ticket_size(
        self,
        merchant_category: str,
    ) -> float:
        """
        Generate Average Ticket Size.
        """
    
        ranges = {
    
            "Retail": (500, 25000),
    
            "Grocery": (150, 5000),
    
            "Fuel": (500, 6000),
    
            "Healthcare": (1000, 100000),
    
            "Restaurant": (250, 5000),
    
            "Travel": (1000, 75000),
    
            "Entertainment": (300, 8000),
    
            "Education": (5000, 250000),
    
            "Utilities": (300, 15000),
    
            "E-Commerce": (300, 50000),
    
            "Government": (1000, 50000),
    
            "Telecom": (200, 5000),
    
            "Other": (500, 25000),
    
        }
    
        minimum, maximum = ranges[merchant_category]
    
        return round(
    
            random.uniform(
    
                minimum,
    
                maximum,
    
            ),
    
            2,
    
        )
    
    
    def _generate_onboarding_date(self):
        """
        Generate Merchant Onboarding Date.
        """
    
        return self.fake.date_between(
    
            start_date="-15y",
    
            end_date="-30d",
    
        )
        
    # =====================================================================
    # Generate Merchants
    # =====================================================================
    
    def generate_merchants(self) -> None:
        """
        Generate Merchant records.
        """
    
        self.logger.info(
            "Generating Merchants..."
        )
    
        for _ in range(NUM_MERCHANTS):
    
            # -------------------------------------------------------------
            # Merchant Category
            # -------------------------------------------------------------
    
            merchant_category = (
                self._generate_merchant_category()
            )
    
            # -------------------------------------------------------------
            # Merchant Location
            # -------------------------------------------------------------
    
            merchant_city, merchant_state = (
                self._generate_location()
            )
    
            # -------------------------------------------------------------
            # Merchant Object
            # -------------------------------------------------------------
    
            merchant = Merchant(
    
                merchant_id=merchant_id(),
    
                merchant_name=self._generate_merchant_name(
                    merchant_category
                ),
    
                merchant_category=merchant_category,
    
                merchant_type=self._generate_merchant_type(),
    
                merchant_city=merchant_city,
    
                merchant_state=merchant_state,
    
                merchant_country=COUNTRY,
    
                merchant_status=self._generate_merchant_status(),
    
                accepts_upi=self._generate_accepts_upi(),
    
                accepts_cards=self._generate_accepts_cards(),
    
                average_ticket_size=self._generate_average_ticket_size(
                    merchant_category
                ),
    
                onboarding_date=self._generate_onboarding_date(),
    
                created_at=datetime.now(),
    
                updated_at=None,
    
                source_system=SOURCE_SYSTEM,
    
            )
    
            self.merchants.append(
                merchant
            )
    
        self.logger.info(
            f"{len(self.merchants)} merchants generated successfully."
        )

    # =====================================================================
    # Validate Merchants
    # =====================================================================
    
    def validate_merchants(self) -> bool:
        """
        Validate Merchant dataset.
        """
    
        self.logger.info(
            "Validating Merchants..."
        )
    
        df = self.merchants_df()
    
        if df.empty:
    
            self.logger.error(
                "Merchant dataframe is empty."
            )
    
            return False
    
        # -------------------------------------------------------------
        # Primary Key
        # -------------------------------------------------------------
    
        if df["merchant_id"].duplicated().any():
    
            self.logger.error(
                "Duplicate Merchant IDs found."
            )
    
            return False
    
        # -------------------------------------------------------------
        # Mandatory Columns
        # -------------------------------------------------------------
    
        mandatory_columns = [
    
            "merchant_id",
    
            "merchant_name",
    
            "merchant_category",
    
            "merchant_type",
    
            "merchant_city",
    
            "merchant_state",
    
            "merchant_country",
    
            "merchant_status",
    
            "accepts_upi",
    
            "accepts_cards",
    
            "average_ticket_size",
    
            "onboarding_date",
    
            "source_system",
    
        ]
    
        for column in mandatory_columns:
    
            if df[column].isnull().any():
    
                self.logger.error(
                    f"Null values found in {column}."
                )
    
                return False
    
        # -------------------------------------------------------------
        # Category Validation
        # -------------------------------------------------------------
    
        invalid_categories = set(
    
            df["merchant_category"]
    
        ) - set(MERCHANT_CATEGORIES)
    
        if invalid_categories:
    
            self.logger.error(
                f"Invalid Merchant Categories: {invalid_categories}"
            )
    
            return False
    
        # -------------------------------------------------------------
        # Status Validation
        # -------------------------------------------------------------
    
        invalid_status = set(
    
            df["merchant_status"]
    
        ) - set(MERCHANT_STATUS)
    
        if invalid_status:
    
            self.logger.error(
                f"Invalid Merchant Status: {invalid_status}"
            )
    
            return False
    
        # -------------------------------------------------------------
        # Ticket Size
        # -------------------------------------------------------------
    
        if (df["average_ticket_size"] <= 0).any():
    
            self.logger.error(
                "Average Ticket Size must be positive."
            )
    
            return False
    
        self.logger.info(
            "Merchant validation completed successfully."
        )
    
        return True
    
    
    # =====================================================================
    # Validate All
    # =====================================================================
    
    def validate_all(self) -> bool:
        """
        Validate all generated datasets.
        """
    
        return all(
    
            [
    
                self.validate_merchants(),
    
            ]
    
        )
    
    
    # =====================================================================
    # Export Merchants
    # =====================================================================
    
    def export_merchants(self) -> None:
        """
        Export Merchant dataset.
        """
    
        self.logger.info(
            "Exporting Merchants..."
        )
    
        df = self.merchants_df()
    
        df.to_csv(
    
            MERCHANTS_FILE,
    
            index=False,
    
        )
    
        self.logger.info(
            f"Merchant dataset exported to {MERCHANTS_FILE}"
        )
    
    
    # =====================================================================
    # Export All
    # =====================================================================
    
    def export_all(self) -> None:
        """
        Export all Merchant datasets.
        """
    
        self.export_merchants()


    # ==============================================================
    # Summary
    # ==============================================================

    def summary(self) -> None:
        """
        Display Merchant Generation Summary.
        """

        self.logger.info("=" * 70)

        self.logger.info(
            "Merchant Generation Summary"
        )

        self.logger.info(
            f"Merchants Generated : {len(self.merchants)}"
        )

        self.logger.info("=" * 70)

    # =====================================================================
    # Run Generator
    # =====================================================================
    
    def run(self) -> None:
        """
        Execute Merchant Generator.
        """
    
        try:
    
            self.logger.info(
                "=" * 70
            )
    
            self.logger.info(
                "Merchant Generation Started"
            )
    
            self.logger.info(
                "=" * 70
            )
    
            # ---------------------------------------------------------
            # Generate
            # ---------------------------------------------------------
    
            self.generate_merchants()
    
            # ---------------------------------------------------------
            # Validate
            # ---------------------------------------------------------
    
            if not self.validate_all():
    
                raise ValueError(
                    "Merchant validation failed."
                )
    
            # ---------------------------------------------------------
            # Export
            # ---------------------------------------------------------
    
            self.export_all()
    
            # ---------------------------------------------------------
            # Summary
            # ---------------------------------------------------------
    
            self.summary()
    
            self.logger.info(
                "=" * 70
            )
    
            self.logger.info(
                "Merchant Generation Completed Successfully"
            )
    
            self.logger.info(
                "=" * 70
            )
    
        except Exception as ex:
    
            self.logger.exception(ex)
    
            raise ex


# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":
    print("Starting Merchant Generator...")
    
    generator = MerchantGenerator()
    
    print("Generator created.")
    
    generator.run()
    
    print("Pipeline finished.")
