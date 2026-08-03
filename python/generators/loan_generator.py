"""
Loan Domain Data Generator

Generates synthetic data for:

    1. Loans
    2. Loan Applications
    3. Loan Repayments
    4. Loan Collateral
"""

from __future__ import annotations

# =====================================================================
# Standard Library
# =====================================================================

import random
from dateutil.relativedelta import relativedelta
from datetime import date, datetime

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
    NUM_LOANS,
    NUM_LOAN_APPLICATIONS,
    NUM_LOAN_REPAYMENTS,
    NUM_LOAN_COLLATERALS,
    CUSTOMERS_FILE,
    LOANS_FILE,
    LOAN_APPLICATIONS_FILE,
    LOAN_REPAYMENTS_FILE,
    LOAN_COLLATERALS_FILE,
    LOAN_SOURCE_SYSTEM,
)

from config.constants import (
    LOAN_TYPES,
    LOAN_STATUS,
    APPROVAL_STATUS,
    PAYMENT_MODES,
    ASSET_TYPES,
    MIN_INTEREST_RATE,
    MAX_INTEREST_RATE,
)

# =====================================================================
# Models
# =====================================================================

from models.loan import Loan
from models.loan_application import LoanApplication
from models.loan_repayment import LoanRepayment
from models.loan_collateral import LoanCollateral

# =====================================================================
# Utilities
# =====================================================================

from generators.id_generator import (
    loan_id,
    application_id,
    repayment_id,
    collateral_id,
)

# =====================================================================
# Logging
# =====================================================================

from config.logging_config import setup_logger

# =====================================================================
# Business Reference Data
# =====================================================================

# Principal amount ranges by loan type (min, max)
LOAN_AMOUNT_RANGES = {

    "Home Loan": (500000, 10000000),

    "Personal Loan": (50000, 1500000),

    "Car Loan": (200000, 3000000),

    "Education Loan": (100000, 4000000),

    "Business Loan": (500000, 20000000),

    "Gold Loan": (25000, 2500000),

}

# Tenure ranges (months) by loan type (min, max)
LOAN_TENURE_RANGES = {

    "Home Loan": (60, 360),

    "Personal Loan": (12, 60),

    "Car Loan": (12, 84),

    "Education Loan": (36, 180),

    "Business Loan": (12, 120),

    "Gold Loan": (3, 36),

}

# Loan types that are typically secured with collateral
SECURED_LOAN_TYPES = {

    "Home Loan",

    "Car Loan",

    "Business Loan",

    "Gold Loan",

}

# Collateral asset type mapping by loan type
COLLATERAL_ASSET_MAP = {

    "Home Loan": "Property",

    "Car Loan": "Vehicle",

    "Gold Loan": "Gold",

    "Business Loan": "Property",

}


# =====================================================================
# Loan Generator
# =====================================================================

class LoanGenerator:
    """
    Loan Domain Generator.

    Generates:

        • Loans

        • Loan Applications

        • Loan Repayments

        • Loan Collateral
    """

    def __init__(self) -> None:

        self.logger = setup_logger(__name__)

        self.fake = Faker("en_IN")

        random.seed(RANDOM_SEED)

        self.fake.seed_instance(RANDOM_SEED)

        # ==============================================================
        # Load Parent Datasets
        # ==============================================================

        self.logger.info(
            "Loading Customer dataset..."
        )

        self.customer_master = pd.read_csv(
            CUSTOMERS_FILE
        )

        self.logger.info(
            f"Loaded {len(self.customer_master)} customers."
        )

        # ==============================================================
        # Generated Objects
        # ==============================================================

        self.loans: list[Loan] = []

        self.loan_applications: list[LoanApplication] = []

        self.loan_repayments: list[LoanRepayment] = []

        self.loan_collaterals: list[LoanCollateral] = []

        self.logger.info(
            "Loan Generator initialized successfully."
        )

    def _get_customer(self) -> pd.Series:
        """
        Return a random customer.
        """

        return self.customer_master.sample(
            n=1,
        ).iloc[0]

    # =====================================================================
    # DataFrames
    # =====================================================================

    def loans_df(self) -> pd.DataFrame:
        """
        Return Loans dataframe.
        """

        return pd.DataFrame(
            [loan.to_dict() for loan in self.loans]
        )

    def loan_applications_df(self) -> pd.DataFrame:
        """
        Return Loan Applications dataframe.
        """

        return pd.DataFrame(
            [application.to_dict() for application in self.loan_applications]
        )

    def loan_repayments_df(self) -> pd.DataFrame:
        """
        Return Loan Repayments dataframe.
        """

        return pd.DataFrame(
            [repayment.to_dict() for repayment in self.loan_repayments]
        )

    def loan_collaterals_df(self) -> pd.DataFrame:
        """
        Return Loan Collateral dataframe.
        """

        return pd.DataFrame(
            [collateral.to_dict() for collateral in self.loan_collaterals]
        )

    # =====================================================================
    # Loan Helper Methods
    # =====================================================================

    def _generate_loan_type(self) -> str:
        """
        Generate loan type.
        """

        return random.choices(

            LOAN_TYPES,

            weights=[
                25,     # Home Loan
                25,     # Personal Loan
                20,     # Car Loan
                10,     # Education Loan
                12,     # Business Loan
                8,      # Gold Loan
            ],

            k=1,

        )[0]

    def _generate_loan_status(self) -> str:
        """
        Generate loan status.
        """

        return random.choices(

            LOAN_STATUS,

            weights=[
                55,     # Active
                30,     # Closed
                5,      # Defaulted
                5,      # Pending
                5,      # Written Off
            ],

            k=1,

        )[0]

    def _generate_principal_amount(
        self,
        loan_type: str,
    ) -> float:
        """
        Generate principal amount based on loan type.
        """

        minimum, maximum = LOAN_AMOUNT_RANGES[loan_type]

        return round(
            random.uniform(
                minimum,
                maximum,
            ),
            2,
        )

    def _generate_interest_rate(self) -> float:
        """
        Generate annual interest rate.
        """

        return round(
            random.uniform(
                MIN_INTEREST_RATE,
                MAX_INTEREST_RATE,
            ),
            2,
        )

    def _generate_tenure_months(
        self,
        loan_type: str,
    ) -> int:
        """
        Generate loan tenure in months.
        """

        minimum, maximum = LOAN_TENURE_RANGES[loan_type]

        return random.randint(
            minimum,
            maximum,
        )

    def _generate_emi_amount(
        self,
        principal_amount: float,
        interest_rate: float,
        tenure_months: int,
    ) -> float:
        """
        Compute the monthly EMI using the standard reducing-balance formula.

            EMI = P * r * (1+r)^n / ((1+r)^n - 1)

        where r is the monthly interest rate.
        """

        monthly_rate = (interest_rate / 12) / 100

        if monthly_rate == 0:

            return round(
                principal_amount / tenure_months,
                2,
            )

        factor = (1 + monthly_rate) ** tenure_months

        emi = principal_amount * monthly_rate * factor / (factor - 1)

        return round(emi, 2)

    def _generate_disbursement_date(self) -> date:
        """
        Generate loan disbursement date.
        """

        return self.fake.date_between(
            start_date="-15y",
            end_date="-30d",
        )

    # =====================================================================
    # Generate Loans
    # =====================================================================

    def generate_loans(self) -> None:
        """
        Generate Loan data.
        """

        self.logger.info(
            "Generating Loans..."
        )

        for _ in range(NUM_LOANS):

            customer = self._get_customer()

            loan_type = self._generate_loan_type()

            principal_amount = self._generate_principal_amount(
                loan_type
            )

            interest_rate = self._generate_interest_rate()

            tenure_months = self._generate_tenure_months(
                loan_type
            )

            loan = Loan(

                loan_id=loan_id(),

                customer_id=customer["customer_id"],

                loan_type=loan_type,

                principal_amount=principal_amount,

                interest_rate=interest_rate,

                tenure_months=tenure_months,

                emi_amount=self._generate_emi_amount(
                    principal_amount,
                    interest_rate,
                    tenure_months,
                ),

                loan_status=self._generate_loan_status(),

                disbursement_date=self._generate_disbursement_date(),

                created_at=datetime.now(),

                updated_at=None,

                source_system=LOAN_SOURCE_SYSTEM,

            )

            self.loans.append(loan)

        self.logger.info(
            f"{len(self.loans)} Loans generated successfully."
        )

    # =====================================================================
    # Validate Loans
    # =====================================================================

    def validate_loans(self) -> bool:
        """
        Validate Loans dataset.
        """

        self.logger.info(
            "Validating Loans..."
        )

        df = self.loans_df()

        if df.empty:

            self.logger.error(
                "Loans dataframe is empty."
            )

            return False

        if df["loan_id"].duplicated().any():

            self.logger.error(
                "Duplicate Loan IDs detected."
            )

            return False

        valid_customers = set(
            self.customer_master["customer_id"]
        )

        if (~df["customer_id"].isin(valid_customers)).any():

            self.logger.error(
                "Invalid Customer IDs detected."
            )

            return False

        if (df["principal_amount"] <= 0).any():

            self.logger.error(
                "Invalid principal amounts detected."
            )

            return False

        mandatory_columns = [

            "loan_id",

            "customer_id",

            "loan_type",

            "principal_amount",

            "interest_rate",

            "tenure_months",

            "emi_amount",

            "loan_status",

        ]

        for column in mandatory_columns:

            if df[column].isnull().any():

                self.logger.error(
                    f"Null values found in {column}."
                )

                return False

        self.logger.info(
            "Loan validation completed successfully."
        )

        return True

    # =====================================================================
    # Export Loans
    # =====================================================================

    def export_loans(self) -> None:
        """
        Export Loans dataset.
        """

        self.logger.info(
            "Exporting Loans..."
        )

        self.loans_df().to_csv(

            LOANS_FILE,

            index=False,

        )

        self.logger.info(
            f"Loans exported successfully to {LOANS_FILE}"
        )

    # =====================================================================
    # Loan Application Helper Methods
    # =====================================================================

    def _generate_application_date(
        self,
        loan: Loan | None,
    ) -> date:
        """
        Generate an application date that precedes disbursement
        (when the application maps to an approved loan).
        """

        if loan is not None:

            return self.fake.date_between(
                start_date=loan.disbursement_date - relativedelta(months=2),
                end_date=loan.disbursement_date,
            )

        return self.fake.date_between(
            start_date="-15y",
            end_date="today",
        )

    def _generate_approval_status(self) -> str:
        """
        Generate approval status.
        """

        return random.choices(

            APPROVAL_STATUS,

            weights=[
                8,      # Pending
                65,     # Approved
                22,     # Rejected
                5,      # Cancelled
            ],

            k=1,

        )[0]

    def _generate_requested_amount(
        self,
        approved_amount: float | None,
    ) -> float:
        """
        Generate requested loan amount.

        Business Rules
        --------------
        • For approved applications, the requested amount is close
          to (but not always exactly) the disbursed principal.
        • For other applications, a plausible amount is generated.
        """

        if approved_amount is not None:

            variance = random.uniform(0.9, 1.15)

            return round(approved_amount * variance, 2)

        loan_type = random.choice(LOAN_TYPES)

        minimum, maximum = LOAN_AMOUNT_RANGES[loan_type]

        return round(
            random.uniform(minimum, maximum),
            2,
        )

    # =====================================================================
    # Generate Loan Applications
    # =====================================================================

    def generate_loan_applications(self) -> None:
        """
        Generate Loan Application data.

        Business Rules
        --------------
        • Approved applications are linked back to a generated Loan
          (one loan may originate from at most one application).
        • Pending / Rejected / Cancelled applications have no linked loan.
        """

        self.logger.info(
            "Generating Loan Applications..."
        )

        unlinked_loans = list(self.loans)

        random.shuffle(unlinked_loans)

        loan_pointer = 0

        for _ in range(NUM_LOAN_APPLICATIONS):

            approval_status = self._generate_approval_status()

            linked_loan = None

            if (
                approval_status == "Approved"
                and loan_pointer < len(unlinked_loans)
            ):

                linked_loan = unlinked_loans[loan_pointer]

                loan_pointer += 1

                customer_id_value = linked_loan.customer_id

            else:

                customer_id_value = self._get_customer()["customer_id"]

            application = LoanApplication(

                application_id=application_id(),

                customer_id=customer_id_value,

                loan_id=(
                    linked_loan.loan_id
                    if linked_loan is not None
                    else None
                ),

                application_date=self._generate_application_date(
                    linked_loan
                ),

                requested_amount=self._generate_requested_amount(
                    linked_loan.principal_amount
                    if linked_loan is not None
                    else None
                ),

                approval_status=approval_status,

                created_at=datetime.now(),

                updated_at=None,

                source_system=LOAN_SOURCE_SYSTEM,

            )

            self.loan_applications.append(application)

        self.logger.info(
            f"{len(self.loan_applications)} Loan Applications generated successfully."
        )

    # =====================================================================
    # Validate Loan Applications
    # =====================================================================

    def validate_loan_applications(self) -> bool:
        """
        Validate Loan Applications dataset.
        """

        self.logger.info(
            "Validating Loan Applications..."
        )

        df = self.loan_applications_df()

        if df.empty:

            self.logger.error(
                "Loan Applications dataframe is empty."
            )

            return False

        if df["application_id"].duplicated().any():

            self.logger.error(
                "Duplicate Application IDs detected."
            )

            return False

        valid_customers = set(
            self.customer_master["customer_id"]
        )

        if (~df["customer_id"].isin(valid_customers)).any():

            self.logger.error(
                "Invalid Customer IDs detected."
            )

            return False

        valid_loans = set(
            self.loans_df()["loan_id"]
        )

        loan_mask = df["loan_id"].notna()

        if (~df.loc[loan_mask, "loan_id"].isin(valid_loans)).any():

            self.logger.error(
                "Invalid linked Loan IDs detected."
            )

            return False

        mandatory_columns = [

            "application_id",

            "customer_id",

            "application_date",

            "requested_amount",

            "approval_status",

        ]

        for column in mandatory_columns:

            if df[column].isnull().any():

                self.logger.error(
                    f"Null values found in {column}."
                )

                return False

        self.logger.info(
            "Loan Application validation completed successfully."
        )

        return True

    # =====================================================================
    # Export Loan Applications
    # =====================================================================

    def export_loan_applications(self) -> None:
        """
        Export Loan Applications dataset.
        """

        self.logger.info(
            "Exporting Loan Applications..."
        )

        self.loan_applications_df().to_csv(

            LOAN_APPLICATIONS_FILE,

            index=False,

        )

        self.logger.info(
            f"Loan Applications exported successfully to {LOAN_APPLICATIONS_FILE}"
        )

    # =====================================================================
    # Loan Repayment Helper Methods
    # =====================================================================

    def _generate_payment_mode(self) -> str:
        """
        Generate repayment mode.
        """

        return random.choice(PAYMENT_MODES)

    def _generate_amount_paid(
        self,
        emi_amount: float,
    ) -> float:
        """
        Generate the amount paid for a repayment installment.

        Business Rules
        --------------
        • Most repayments match the EMI exactly.
        • A small share are partial or include a late-payment surcharge.
        """

        outcome = random.random()

        if outcome < 0.85:

            return emi_amount

        if outcome < 0.95:

            # Partial payment
            return round(emi_amount * random.uniform(0.5, 0.95), 2)

        # Late payment with surcharge
        return round(emi_amount * random.uniform(1.01, 1.05), 2)

    # =====================================================================
    # Generate Loan Repayments
    # =====================================================================

    def generate_loan_repayments(self) -> None:
        """
        Generate Loan Repayment data.

        Business Rules
        --------------
        • Repayments are generated as a monthly EMI schedule starting
          from each loan's disbursement date, up to today.
        • Generation stops once NUM_LOAN_REPAYMENTS records exist.
        """

        self.logger.info(
            "Generating Loan Repayments..."
        )

        loans = list(self.loans)

        random.shuffle(loans)

        repayment_count = 0

        today = date.today()

        for loan in loans:

            if repayment_count >= NUM_LOAN_REPAYMENTS:
                break

            months_elapsed = min(
                loan.tenure_months,
                max(
                    0,
                    (today.year - loan.disbursement_date.year) * 12
                    + (today.month - loan.disbursement_date.month),
                ),
            )

            for installment in range(1, months_elapsed + 1):

                if repayment_count >= NUM_LOAN_REPAYMENTS:
                    break

                payment_date = (
                    loan.disbursement_date
                    + relativedelta(months=installment)
                )

                if payment_date > today:
                    break

                repayment = LoanRepayment(

                    repayment_id=repayment_id(),

                    loan_id=loan.loan_id,

                    payment_date=payment_date,

                    amount_paid=self._generate_amount_paid(
                        loan.emi_amount
                    ),

                    payment_mode=self._generate_payment_mode(),

                    created_at=datetime.now(),

                    updated_at=None,

                    source_system=LOAN_SOURCE_SYSTEM,

                )

                self.loan_repayments.append(repayment)

                repayment_count += 1

        self.logger.info(
            f"{len(self.loan_repayments)} Loan Repayments generated successfully."
        )

    # =====================================================================
    # Validate Loan Repayments
    # =====================================================================

    def validate_loan_repayments(self) -> bool:
        """
        Validate Loan Repayments dataset.
        """

        self.logger.info(
            "Validating Loan Repayments..."
        )

        df = self.loan_repayments_df()

        if df.empty:

            self.logger.error(
                "Loan Repayments dataframe is empty."
            )

            return False

        if df["repayment_id"].duplicated().any():

            self.logger.error(
                "Duplicate Repayment IDs detected."
            )

            return False

        valid_loans = set(
            self.loans_df()["loan_id"]
        )

        if (~df["loan_id"].isin(valid_loans)).any():

            self.logger.error(
                "Invalid Loan IDs detected."
            )

            return False

        if (df["amount_paid"] <= 0).any():

            self.logger.error(
                "Invalid repayment amounts detected."
            )

            return False

        self.logger.info(
            "Loan Repayment validation completed successfully."
        )

        return True

    # =====================================================================
    # Export Loan Repayments
    # =====================================================================

    def export_loan_repayments(self) -> None:
        """
        Export Loan Repayments dataset.
        """

        self.logger.info(
            "Exporting Loan Repayments..."
        )

        self.loan_repayments_df().to_csv(

            LOAN_REPAYMENTS_FILE,

            index=False,

        )

        self.logger.info(
            f"Loan Repayments exported successfully to {LOAN_REPAYMENTS_FILE}"
        )

    # =====================================================================
    # Loan Collateral Helper Methods
    # =====================================================================

    def _generate_asset_value(
        self,
        principal_amount: float,
    ) -> float:
        """
        Generate collateral asset value.

        Business Rule
        -------------
        Collateral is typically valued at 100%-150% of the loan
        principal (loan-to-value margin).
        """

        return round(
            principal_amount * random.uniform(1.0, 1.5),
            2,
        )

    def _generate_valuation_date(
        self,
        disbursement_date: date,
    ) -> date:
        """
        Generate the asset valuation date, shortly before disbursement.
        """

        return self.fake.date_between(
            start_date=disbursement_date - relativedelta(months=1),
            end_date=disbursement_date,
        )

    # =====================================================================
    # Generate Loan Collateral
    # =====================================================================

    def generate_loan_collateral(self) -> None:
        """
        Generate Loan Collateral data.

        Business Rule
        -------------
        Only secured loan types (Home, Car, Business, Gold) carry
        collateral records.
        """

        self.logger.info(
            "Generating Loan Collateral..."
        )

        secured_loans = [
            loan
            for loan in self.loans
            if loan.loan_type in SECURED_LOAN_TYPES
        ]

        random.shuffle(secured_loans)

        for loan in secured_loans[:NUM_LOAN_COLLATERALS]:

            asset_type = COLLATERAL_ASSET_MAP.get(
                loan.loan_type,
                random.choice(ASSET_TYPES),
            )

            collateral = LoanCollateral(

                collateral_id=collateral_id(),

                loan_id=loan.loan_id,

                asset_type=asset_type,

                asset_value=self._generate_asset_value(
                    loan.principal_amount
                ),

                valuation_date=self._generate_valuation_date(
                    loan.disbursement_date
                ),

                created_at=datetime.now(),

                updated_at=None,

                source_system=LOAN_SOURCE_SYSTEM,

            )

            self.loan_collaterals.append(collateral)

        self.logger.info(
            f"{len(self.loan_collaterals)} Loan Collateral records generated successfully."
        )

    # =====================================================================
    # Validate Loan Collateral
    # =====================================================================

    def validate_loan_collateral(self) -> bool:
        """
        Validate Loan Collateral dataset.
        """

        self.logger.info(
            "Validating Loan Collateral..."
        )

        df = self.loan_collaterals_df()

        if df.empty:

            self.logger.error(
                "Loan Collateral dataframe is empty."
            )

            return False

        if df["collateral_id"].duplicated().any():

            self.logger.error(
                "Duplicate Collateral IDs detected."
            )

            return False

        valid_loans = set(
            self.loans_df()["loan_id"]
        )

        if (~df["loan_id"].isin(valid_loans)).any():

            self.logger.error(
                "Invalid Loan IDs detected."
            )

            return False

        if (df["asset_value"] <= 0).any():

            self.logger.error(
                "Invalid asset values detected."
            )

            return False

        self.logger.info(
            "Loan Collateral validation completed successfully."
        )

        return True

    # =====================================================================
    # Export Loan Collateral
    # =====================================================================

    def export_loan_collateral(self) -> None:
        """
        Export Loan Collateral dataset.
        """

        self.logger.info(
            "Exporting Loan Collateral..."
        )

        self.loan_collaterals_df().to_csv(

            LOAN_COLLATERALS_FILE,

            index=False,

        )

        self.logger.info(
            f"Loan Collateral exported successfully to {LOAN_COLLATERALS_FILE}"
        )

    # =====================================================================
    # Validate All
    # =====================================================================

    def validate_all(self) -> bool:
        """
        Validate all generated Loan datasets.
        """

        self.logger.info(
            "Running Validation..."
        )

        validations = [

            self.validate_loans(),

            self.validate_loan_applications(),

            self.validate_loan_repayments(),

            self.validate_loan_collateral(),

        ]

        if all(validations):

            self.logger.info(
                "Validation Successful."
            )

            return True

        self.logger.error(
            "Validation Failed."
        )

        return False

    # =====================================================================
    # Export All
    # =====================================================================

    def export_all(self) -> None:
        """
        Export all Loan datasets.
        """

        self.logger.info(
            "Exporting datasets..."
        )

        self.export_loans()

        self.export_loan_applications()

        self.export_loan_repayments()

        self.export_loan_collateral()

        self.logger.info(
            "Export completed successfully."
        )

    # =====================================================================
    # Summary
    # =====================================================================

    def summary(self) -> None:
        """
        Display Loan Generation Summary.
        """

        self.logger.info("=" * 70)

        self.logger.info(
            "Loan Generation Summary"
        )

        self.logger.info(
            f"Loans Generated              : {len(self.loans)}"
        )

        self.logger.info(
            f"Loan Applications Generated  : {len(self.loan_applications)}"
        )

        self.logger.info(
            f"Loan Repayments Generated    : {len(self.loan_repayments)}"
        )

        self.logger.info(
            f"Loan Collateral Generated    : {len(self.loan_collaterals)}"
        )

        self.logger.info("=" * 70)

    # =====================================================================
    # Pipeline Execution
    # =====================================================================

    def run(self) -> None:
        """
        Execute Loan Generator.
        """

        try:

            self.logger.info("=" * 80)

            self.logger.info(
                "Starting Loan Generator..."
            )

            self.generate_loans()

            self.generate_loan_applications()

            self.generate_loan_repayments()

            self.generate_loan_collateral()

            self.summary()

            if not self.validate_all():

                raise ValueError(
                    "Validation Failed."
                )

            self.export_all()

            self.logger.info(
                "Loan Generator completed successfully."
            )

            self.logger.info("=" * 80)

        except Exception as ex:

            self.logger.exception(ex)

            raise


# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":
    print("Starting Loan Generator...")

    generator = LoanGenerator()

    print("Generator created.")

    generator.run()

    print("Pipeline finished.")
