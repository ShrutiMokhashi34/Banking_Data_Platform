"""
===============================================================================
Banking Data Platform
customer_generator.py

Generates synthetic data for:
    - Customers
    - Customer Addresses
    - KYC
    
===============================================================================
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import List

import pandas as pd
from faker import Faker

from config.config import (
    NUM_CUSTOMERS,
    RANDOM_SEED,
    OUTPUT_DIR,
    CUSTOMERS_FILE,
    CUSTOMER_ADDRESSES_FILE,
    KYC_FILE
)

from config.constants import (
    GENDERS,
    CUSTOMER_STATUS,
    RISK_RATINGS,
    ADDRESS_TYPES,
    KYC_STATUS,
    COUNTRY,
    SOURCE_SYSTEM
)

from config.logging_config import setup_logger

from generators.id_generator import (
    customer_id,
    address_id
)

from generators.utils import (
    generate_email,
    generate_phone_number,
    generate_income,
    generate_pan,
    generate_aadhaar,
    current_timestamp,
    Geography
)

from models.cust_customer import Customer
from models.cust_addresses import Address
from models.cust_kyc import KYC


class CustomerGenerator:
    """
    Generates Customer domain datasets.

    Tables
    ------
    1. Customers
    2. CustomerAddresses
    3. KYC
    """

    def __init__(self):

        self.logger = setup_logger(__name__)

        self.fake = Faker("en_IN")

        random.seed(RANDOM_SEED)
        self.fake.seed_instance(RANDOM_SEED)

        self.customers: List[Customer] = []
        
        self.geo = Geography()

        self.addresses: List[Address] = []

        self.kyc_records: List[KYC] = []

        self.logger.info("=" * 70)
        self.logger.info("Customer Generator Initialized")
        self.logger.info("=" * 70)

    # ==========================================================
    # Helper Methods
    # ==========================================================

    def _random_dob(self) -> date:
        """
        Generate DOB between 18 and 80 years.
        """

        return self.fake.date_of_birth(
            minimum_age=18,
            maximum_age=80
        )

    def _customer_since(self, dob: date) -> date:
        """
        Customer cannot join before turning 18.
        """

        earliest = dob + timedelta(days=18 * 365)

        if earliest > date.today():
            earliest = date.today()

        return self.fake.date_between(
            start_date=earliest,
            end_date="today"
        )

    def _risk_rating(self, income: float) -> str:
        """
        Assign customer risk based on income.

        (Can later be enhanced with occupation,
        KYC status, and transaction history.)
        """

        if income >= 2_000_000:
            return "Low"

        if income >= 800_000:
            return "Medium"

        return "High"

    def _customer_status(self) -> str:
        """
        Weighted customer status.
        """

        return random.choices(
            CUSTOMER_STATUS,
            weights=[85, 7, 5, 3],
            k=1
        )[0]

    def _kyc_status(self) -> str:
        """
        Weighted KYC status.
        """

        return random.choices(
            KYC_STATUS,
            weights=[92, 6, 2],
            k=1
        )[0]

    def _gender(self) -> str:
        """
        Random gender.
        """

        return random.choice(GENDERS)

    def _address_type(self) -> str:
        """
        Random address type.
        """

        return random.choice(ADDRESS_TYPES)

    def _occupation(self) -> str:
        """
        Generate occupation.
        """

        return self.fake.job()

    def _first_name(self) -> str:
        return self.fake.first_name()

    def _last_name(self) -> str:
        return self.fake.last_name()

    def _street(self) -> str:
        return self.fake.street_address()

    # ==========================================================
    # Statistics
    # ==========================================================

    @property
    def customer_count(self) -> int:
        return len(self.customers)

    @property
    def address_count(self) -> int:
        return len(self.addresses)

    @property
    def kyc_count(self) -> int:
        return len(self.kyc_records)

    # ==========================================================
    # DataFrame Converters
    # ==========================================================

    def customers_df(self) -> pd.DataFrame:

        return pd.DataFrame(
            [c.to_dict() for c in self.customers]
        )

    def addresses_df(self) -> pd.DataFrame:

        return pd.DataFrame(
            [a.to_dict() for a in self.addresses]
        )

    def kyc_df(self) -> pd.DataFrame:

        return pd.DataFrame(
            [k.to_dict() for k in self.kyc_records]
        )
    # ==========================================================
    # Customer Generation
    # ==========================================================

    def generate_customers(self) -> None:
        """
        Generate synthetic customer master records.

        This method populates self.customers with Customer model objects.
        """

        self.logger.info("Generating %s customers...", NUM_CUSTOMERS)

        for _ in range(NUM_CUSTOMERS):

            customer = self._build_customer()

            self.customers.append(customer)

        self.logger.info(
            "Successfully generated %s customers.",
            self.customer_count
        )

    def _build_customer(self) -> Customer:
        """
        Build a single customer record.
        """

        first_name = self._first_name()

        last_name = self._last_name()

        dob = self._random_dob()

        income = generate_income()

        customer_since = self._customer_since(dob)

        timestamp = current_timestamp()

        customer = Customer(

            customer_id=customer_id(),

            first_name=first_name,

            last_name=last_name,

            dob=dob,

            gender=self._gender(),

            email=generate_email(
                first_name,
                last_name
            ),

            phone=generate_phone_number(),

            occupation=self._occupation(),

            annual_income=income,

            customer_since=customer_since,

            risk_rating=self._risk_rating(income),

            customer_status=self._customer_status(),

            created_at=timestamp,

            updated_at=timestamp,

            source_system=SOURCE_SYSTEM

        )

        return customer


    # ==========================================================
    # Statistics
    # ==========================================================

    def customer_statistics(self) -> dict:
        """
        Return summary statistics for generated customers.
        """

        if not self.customers:

            return {}

        df = self.customers_df()

        return {

            "total_customers": len(df),

            "active_customers":
                int(
                    (df["customer_status"] == "Active").sum()
                ),

            "blocked_customers":
                int(
                    (df["customer_status"] == "Blocked").sum()
                ),

            "closed_customers":
                int(
                    (df["customer_status"] == "Closed").sum()
                ),

            "average_income":
                round(
                    df["annual_income"].mean(),
                    2
                ),

            "maximum_income":
                float(
                    df["annual_income"].max()
                ),

            "minimum_income":
                float(
                    df["annual_income"].min()
                )
        }

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_customers(self) -> bool:
        """
        Validate generated customer records.
        """

        df = self.customers_df()

        validations = {

            "Unique Customer IDs":
                df["customer_id"].is_unique,

            "No Null Customer IDs":
                not df["customer_id"].isnull().any(),

            "No Null Emails":
                not df["email"].isnull().any(),

            "No Null Phones":
                not df["phone"].isnull().any(),

            "Income Positive":
                (df["annual_income"] > 0).all()
        }

        success = True

        self.logger.info("-" * 60)

        self.logger.info("Customer Validation Results")

        self.logger.info("-" * 60)

        for check, result in validations.items():

            if result:

                self.logger.info("PASS : %s", check)

            else:

                self.logger.error("FAIL : %s", check)

                success = False

        return success
    # ==========================================================
    # Address Generation
    # ==========================================================

    def generate_addresses(self) -> None:
        """
        Generate customer addresses.

        Business Rules
        --------------
        1. Every customer has one current address.
        2. Approximately 25% of customers have one historical address.
        3. Only one address is marked as current.
        """

        self.logger.info("Generating customer addresses...")

        for customer in self.customers:

            current_address = self._build_address(
                customer=customer,
                is_current=True
            )

            self.addresses.append(current_address)

            # 25% probability of an additional historical address
            if random.random() < 0.25:

                historical_address = self._build_address(
                    customer=customer,
                    is_current=False
                )

                self.addresses.append(historical_address)

        self.logger.info(
            "Successfully generated %s addresses.",
            self.address_count
        )
  
    def _address_line2(self) -> str:
        """
        Generate an optional second address line.
        """

        values = [
            "",
            "",
            "",
            f"Apartment {random.randint(1, 500)}",
            f"Flat {random.randint(1, 300)}",
            f"Floor {random.randint(1, 20)}",
            f"Suite {random.randint(1, 50)}",
            "Near Bus Stand",
            "Near Metro Station",
            "Opposite City Mall"
        ]
    
        return random.choice(values)
        
    def _location(self) -> dict:
        """
        Returns a valid state-city-pincode combination.
        """
        return self.geo.random_location()

    # ==========================================================
    # Address Builder
    # ==========================================================

    def _build_address(
        self,
        customer: Customer,
        is_current: bool
    ) -> Address:
        """
        Build a single address record.
        """

        effective_date = self.fake.date_between(
            start_date=customer.customer_since,
            end_date="today"
        )

        expiry_date = None

        if not is_current:

            expiry_date = self.fake.date_between(
                start_date=effective_date,
                end_date="today"
            )
        
        location = self._location()
        
        address = Address(

            address_id=address_id(),

            customer_id=customer.customer_id,

            address_type=self._address_type(),

            address_line1=self.fake.building_number()
            + " "
            + self.fake.street_name(),

            address_line2=self._address_line2(),

            city=location["city"],
            
            state=location["state"],
            
            postal_code=location["pincode"],

            country=COUNTRY,

            is_current=is_current,

            effective_date=effective_date,

            expiry_date=expiry_date

        )

        return address

    # ==========================================================
    # Address Statistics
    # ==========================================================

    def address_statistics(self) -> dict:
        """
        Return summary statistics for addresses.
        """

        if not self.addresses:
            return {}

        df = self.addresses_df()

        return {

            "total_addresses":
                len(df),

            "current_addresses":
                int(df["is_current"].sum()),

            "historical_addresses":
                int((~df["is_current"]).sum()),

            "customers_with_multiple_addresses":
                int(
                    (
                        df.groupby("customer_id")
                          .size()
                          .gt(1)
                          .sum()
                    )
                )

        }

    # ==========================================================
    # Address Validation
    # ==========================================================

    def validate_addresses(self) -> bool:
        """
        Validate generated addresses.
        """

        df = self.addresses_df()

        success = True

        self.logger.info("-" * 60)
        self.logger.info("Address Validation Results")
        self.logger.info("-" * 60)

        validations = {

            "Unique Address IDs":
                df["address_id"].is_unique,

            "No Null Address IDs":
                not df["address_id"].isnull().any(),

            "No Null Customer IDs":
                not df["customer_id"].isnull().any(),

            "One Current Address Maximum":
                (
                    df[df["is_current"]]
                    .groupby("customer_id")
                    .size()
                    .max()
                    <= 1
                ),

            "Customer Exists":
                set(df["customer_id"]).issubset(
                    {
                        c.customer_id
                        for c in self.customers
                    }
                )

        }

        for rule, result in validations.items():

            if result:

                self.logger.info("PASS : %s", rule)

            else:

                self.logger.error("FAIL : %s", rule)

                success = False

        return success
    # ==========================================================
    # KYC Generation
    # ==========================================================

    def generate_kyc(self) -> None:
        """
        Generate KYC records for all customers.

        Business Rules
        --------------
        1. Every customer has exactly one KYC record.
        2. Verification flags depend on KYC status.
        3. Verification date is populated only for
           Verified or Rejected customers.
        """

        self.logger.info("Generating KYC records...")

        for customer in self.customers:

            kyc = self._build_kyc(customer)

            self.kyc_records.append(kyc)

        self.logger.info(
            "Successfully generated %s KYC records.",
            self.kyc_count
        )

    # ==========================================================
    # KYC Builder
    # ==========================================================

    def _build_kyc(
        self,
        customer: Customer
    ) -> KYC:
        """
        Build a single KYC record.
        """

        status = self._kyc_status()

        if status == "Verified":

            pan_verified = True
            aadhaar_verified = True
            address_verified = True

            verification_date = self.fake.date_between(
                start_date=customer.customer_since,
                end_date="today"
            )

        elif status == "Pending":

            pan_verified = random.choice([True, False])
            aadhaar_verified = random.choice([True, False])
            address_verified = random.choice([True, False])

            verification_date = None

        else:   # Rejected

            pan_verified = False
            aadhaar_verified = False
            address_verified = False

            verification_date = self.fake.date_between(
                start_date=customer.customer_since,
                end_date="today"
            )

        kyc = KYC(

            customer_id=customer.customer_id,

            pan_number=generate_pan(),

            aadhaar_number=generate_aadhaar(),

            pan_verified=pan_verified,

            aadhaar_verified=aadhaar_verified,

            address_verified=address_verified,

            kyc_status=status,

            verification_date=verification_date

        )

        return kyc

    # ==========================================================
    # KYC Statistics
    # ==========================================================

    def kyc_statistics(self) -> dict:
        """
        Return KYC summary statistics.
        """

        if not self.kyc_records:

            return {}

        df = self.kyc_df()

        return {

            "total_kyc_records":
                len(df),

            "verified":
                int(
                    (df["kyc_status"] == "Verified").sum()
                ),

            "pending":
                int(
                    (df["kyc_status"] == "Pending").sum()
                ),

            "rejected":
                int(
                    (df["kyc_status"] == "Rejected").sum()
                ),

            "pan_verified":
                int(df["pan_verified"].sum()),

            "aadhaar_verified":
                int(df["aadhaar_verified"].sum()),

            "address_verified":
                int(df["address_verified"].sum())
        }

    # ==========================================================
    # KYC Validation
    # ==========================================================

    def validate_kyc(self) -> bool:
        """
        Validate KYC records.
        """

        df = self.kyc_df()

        success = True

        self.logger.info("-" * 60)
        self.logger.info("KYC Validation Results")
        self.logger.info("-" * 60)

        validations = {

            "Unique Customer IDs":
                df["customer_id"].is_unique,

            "No Null PAN":
                not df["pan_number"].isnull().any(),

            "No Null Aadhaar":
                not df["aadhaar_number"].isnull().any(),

            "Customer Exists":
                set(df["customer_id"]).issubset(
                    {
                        c.customer_id
                        for c in self.customers
                    }
                ),

            "Verified Records Consistent":
                (
                    df[
                        df["kyc_status"] == "Verified"
                    ][
                        [
                            "pan_verified",
                            "aadhaar_verified",
                            "address_verified"
                        ]
                    ]
                    .all(axis=1)
                    .all()
                )
        }

        for rule, result in validations.items():

            if result:

                self.logger.info("PASS : %s", rule)

            else:

                self.logger.error("FAIL : %s", rule)

                success = False

        return success

    # ==========================================================
    # Combined Statistics
    # ==========================================================

    def summary_statistics(self) -> dict:
        """
        Return combined statistics for the Customer domain.
        """

        summary = {}

        summary.update(self.customer_statistics())
        summary.update(self.address_statistics())
        summary.update(self.kyc_statistics())

        return summary
# ==========================================================
# Export Functions
# ==========================================================

    def export_customers(self) -> None:
        """
        Export Customers table.
        """
    
        from config.config import CUSTOMERS_FILE
    
        df = self.customers_df()
        
        print(df.shape)
    
        df.to_csv(
            CUSTOMERS_FILE,
            index=False
        )
    
        self.logger.info(
            "Customers exported to %s",
            CUSTOMERS_FILE
        )
    
    
    def export_addresses(self) -> None:
        """
        Export Customer Addresses table.
        """
    
        from config.config import CUSTOMER_ADDRESSES_FILE
    
        df = self.addresses_df()
        
        print(df.shape)
    
        df.to_csv(
            CUSTOMER_ADDRESSES_FILE,
            index=False
        )
    
        self.logger.info(
            "CustomerAddresses exported to %s",
            CUSTOMER_ADDRESSES_FILE
        )
    
    
    def export_kyc(self) -> None:
        """
        Export KYC table.
        """
    
        from config.config import KYC_FILE
    
        df = self.kyc_df()
        
        print(df.shape)
    
        df.to_csv(
            KYC_FILE,
            index=False
        )
    
        self.logger.info(
            "KYC exported to %s",
            KYC_FILE
        )


# ==========================================================
# Export All
# ==========================================================

    def export_all(self) -> None:
        """
        Export all Customer Domain tables.
        """
    
        self.logger.info("=" * 70)
        self.logger.info("Exporting Customer Domain Tables")
        self.logger.info("=" * 70)
    
        self.export_customers()
    
        self.export_addresses()
    
        self.export_kyc()
    
        self.logger.info("Export completed.")


# ==========================================================
# Validation
# ==========================================================

    def validate_all(self) -> bool:
        """
        Execute all validations.
    
        Returns
        -------
        bool
            True if every validation passes.
        """
    
        self.logger.info("=" * 70)
        self.logger.info("Running Customer Domain Validations")
        self.logger.info("=" * 70)
    
        results = [
    
            self.validate_customers(),
    
            self.validate_addresses(),
    
            self.validate_kyc()
    
        ]
    
        success = all(results)
    
        if success:
    
            self.logger.info(
                "All validations passed."
            )
    
        else:
    
            self.logger.error(
                "Validation failures detected."
            )
    
        return success


# ==========================================================
# Row Counts
# ==========================================================

    def row_counts(self) -> dict:
        """
        Return record counts for each table.
        """
    
        return {
    
            "Customers":
                self.customer_count,
    
            "CustomerAddresses":
                self.address_count,
    
            "KYC":
                self.kyc_count
    
        }


# ==========================================================
# Export Summary
# ==========================================================

    def export_summary(self) -> None:
        """
        Log summary statistics.
        """
    
        stats = self.summary_statistics()
    
        self.logger.info("=" * 70)
    
        self.logger.info(
            "Customer Domain Summary"
        )
    
        self.logger.info("=" * 70)
    
        for key, value in stats.items():
    
            self.logger.info(
                "%-40s : %s",
                key,
                value
            )
    
        self.logger.info("=" * 70)


# ==========================================================
# Data Quality Report
# ==========================================================

    def data_quality_report(self) -> pd.DataFrame:
        """
        Generate a simple data quality report.
    
        Returns
        -------
        pandas.DataFrame
        """
    
        report = pd.DataFrame(
    
            [
    
                {
    
                    "Table": "Customers",
    
                    "Rows": self.customer_count,
    
                    "Unique IDs":
                        self.customers_df()["customer_id"].nunique(),
    
                    "Null Values":
                        self.customers_df().isnull().sum().sum()
    
                },
    
                {
    
                    "Table": "CustomerAddresses",
    
                    "Rows": self.address_count,
    
                    "Unique IDs":
                        self.addresses_df()["address_id"].nunique(),
    
                    "Null Values":
                        self.addresses_df().isnull().sum().sum()
    
                },
    
                {
    
                    "Table": "KYC",
    
                    "Rows": self.kyc_count,
    
                    "Unique IDs":
                        self.kyc_df()["customer_id"].nunique(),
    
                    "Null Values":
                        self.kyc_df().isnull().sum().sum()
    
                }
    
            ]
    
        )
    
        return report


# ==========================================================
# Display Summary
# ==========================================================

    def display_summary(self) -> None:
        """
        Print summary to console.
        """
    
        print()
    
        print("=" * 70)
    
        print("CUSTOMER DOMAIN SUMMARY")
    
        print("=" * 70)
    
        for table, count in self.row_counts().items():
    
            print(f"{table:<25}{count}")
    
        print("=" * 70)
    
        print()
    
        print(self.data_quality_report())
    
        print()
 # ==========================================================
# Pipeline Execution
# ==========================================================

    def run(self) -> None:
        """
        Execute the complete Customer Domain pipeline.
        """
    
        self.logger.info("=" * 80)
        self.logger.info("CUSTOMER DOMAIN PIPELINE STARTED")
        self.logger.info("=" * 80)
    
        start_time = current_timestamp()
    
        try:
    
            # ---------------------------------------
            # Generate Data
            # ---------------------------------------
            print("Step 1")
            self.generate_customers()
            
            print("Step 2")
            self.generate_addresses()
    
            print("Step 3")
            self.generate_kyc()
    
            # ---------------------------------------
            # Validate
            # ---------------------------------------
            
            print("Step 4")
            if not self.validate_all():
    
                raise ValueError(
                    "Customer domain validation failed."
                )
    
            # ---------------------------------------
            # Export
            # ---------------------------------------
            print("Step 5")
            print(OUTPUT_DIR)
            self.export_all()
    
            # ---------------------------------------
            # Summary
            # ---------------------------------------
            
            print("Step 6")
            self.export_summary()
    
            self.display_summary()
    
            end_time = current_timestamp()
    
            duration = (
                end_time - start_time
            ).total_seconds()
    
            self.logger.info("=" * 80)
            self.logger.info("CUSTOMER DOMAIN COMPLETED")
            self.logger.info("Execution Time : %.2f seconds", duration)
            self.logger.info("=" * 80)
    
        except Exception as ex:
    
            self.logger.exception(
                "Customer Domain Pipeline Failed."
            )
    
            raise ex
        
if __name__ == "__main__":
    print("Starting Customer Generator...")
    
    generator = CustomerGenerator()
    
    print("Generator created.")
    
    generator.run()
    
    print("Pipeline finished.")