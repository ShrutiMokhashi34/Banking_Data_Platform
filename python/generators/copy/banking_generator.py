"""
Banking Domain Data Generator

Generates synthetic data for:

    1. Accounts
    2. Cards
    3. Transactions
"""

from __future__ import annotations

# =====================================================================
# Standard Library
# =====================================================================

import random
from datetime import datetime, timedelta

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
    NUM_ACCOUNTS,
    NUM_CARDS,
    NUM_TRANSACTIONS,
    CUSTOMERS_FILE,
    BRANCHES_FILE,
    MERCHANTS_FILE,
    ACCOUNTS_FILE,
    CARDS_FILE,
    TRANSACTIONS_FILE,
)

from config.constants import (
    SOURCE_SYSTEM,
    ACCOUNT_TYPES,
    ACCOUNT_STATUS,
    CARD_TYPES,
    CARD_NETWORKS,
    CARD_STATUS,
    TRANSACTION_TYPES,
    TRANSACTION_CHANNELS,
    TRANSACTION_STATUS,
)

# =====================================================================
# Models
# =====================================================================

from models.bank_account import Account
from models.bank_card import Card
from models.bank_transaction import Transaction

# =====================================================================
# Utilities
# =====================================================================

from generators.id_generator import (
    account_id,
    card_id,
    transaction_id,
)

from generators.utils import (
    Geography
)

# =====================================================================
# Logging
# =====================================================================

from config.logging_config import setup_logger


# =====================================================================
# Banking Generator
# =====================================================================

class BankingGenerator:
    """
    Banking Domain Generator.

    Generates:

        • Accounts

        • Cards

        • Transactions
    """

    def __init__(self) -> None:

        self.logger = setup_logger(__name__)

        self.fake = Faker("en_IN")

        random.seed(RANDOM_SEED)

        self.fake.seed_instance(RANDOM_SEED)

        self.locations = Geography()

        self.account_numbers = set()

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

        self.logger.info(
            "Loading Branch dataset..."
        )

        self.branch_master = pd.read_csv(
            BRANCHES_FILE
        )

        self.logger.info(
            f"Loaded {len(self.branch_master)} branches."
        )
        
        self.logger.info(
            "Loading Merchants dataset..."
        )

        self.merchant_master = pd.read_csv(
            MERCHANTS_FILE
        )

        self.logger.info(
            f"Loaded {len(self.merchant_master)} merchants."
        )

        # ==============================================================
        # Generated Objects
        # ==============================================================

        self.accounts: list[Account] = []

        self.cards: list[Card] = []

        self.transactions: list[Transaction] = []

        self.logger.info(
            "Banking Generator initialized successfully."
        )

    def _get_customer(
        self,
    ) -> pd.Series:
        """
        Return a random customer.
        """
    
        return self.customer_master.sample(
            n=1,
        ).iloc[0]
    
    
    def _get_branch(
        self,
    ) -> pd.Series:
        """
        Return a random branch.
        """
    
        return self.branch_master.sample(
            n=1,
        ).iloc[0]

    # ==============================================================
    # DataFrames
    # ==============================================================

    def accounts_df(self) -> pd.DataFrame:
        """
        Return Accounts dataframe.
        """

        return pd.DataFrame(
            [account.to_dict() for account in self.accounts]
        )

    def merchants_df(self) -> pd.DataFrame:
        """
        Return the (pre-loaded) Merchants dataframe.
        """

        return self.merchant_master

        
    # =====================================================================
    # Account Helper Methods
    # =====================================================================
    
    def _generate_account_number(self) -> str:
    
        while True:
    
            account_number = "".join(
                random.choices("0123456789", k=12)
            )
    
            if account_number not in self.account_numbers:
    
                self.account_numbers.add(account_number)
    
                return account_number
    
    
    def _generate_account_type(self) -> str:
        """
        Generate account type.
        """
    
        return random.choices(
    
            ACCOUNT_TYPES,
    
            weights=[
                55,    # Savings
                10,    # Current
                15,    # Salary
                8,     # Fixed Deposit
                5,     # Recurring Deposit
                4,     # NRE
                3,     # NRO
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_account_status(self) -> str:
        """
        Generate account status.
        """
    
        return random.choices(
    
            ACCOUNT_STATUS,
    
            weights=[
                88,    # Active
                5,     # Dormant
                3,     # Frozen
                4,     # Closed
            ],
    
            k=1,
    
        )[0]


    def _generate_account_opening_branch(
        self,
        servicing_branch: pd.Series,
    ) -> pd.Series:
        """
        Generate the branch where the account was originally opened.
    
        Business Rules
        --------------
        • 85% opened at servicing branch.
        • 15% opened at another branch.
        """
    
        if random.random() < 0.85:
            return servicing_branch
    
        other_branches = self.branch_master[
            self.branch_master["branch_id"]
            != servicing_branch["branch_id"]
        ]
    
        return other_branches.sample(
            n=1
        ).iloc[0]
    
    
    def _generate_currency(
        self,
        account_type: str,
    ) -> str:
        """
        Generate account currency.
        """
    
        if account_type in ["NRE", "NRO"]:
    
            return random.choice(
                [
                    "USD",
                    "EUR",
                    "GBP",
                    "AED",
                    "INR",
                ]
            )
    
        return "INR"
    
    
    def _generate_open_date(self):
        """
        Generate account opening date.
        """
    
        return self.fake.date_between(
    
            start_date="-20y",
    
            end_date="-30d",
    
        )
    
    
    def _generate_interest_rate(
        self,
        account_type: str,
    ) -> float:
        """
        Generate interest rate.
        """
    
        interest_rates = {
    
            "Savings": (2.5, 4.5),
    
            "Current": (0.0, 0.0),
    
            "Salary": (2.5, 4.0),
    
            "Fixed Deposit": (5.5, 7.5),
    
            "Recurring Deposit": (5.0, 7.0),
    
            "NRE": (5.5, 7.0),
    
            "NRO": (3.0, 5.5),
    
        }
    
        minimum, maximum = interest_rates[account_type]
    
        return round(
    
            random.uniform(
    
                minimum,
    
                maximum,
    
            ),
    
            2,
    
        )
    
    
    def _generate_balance(
        self,
        account_type: str,
    ) -> float:
        """
        Generate current account balance.
        """
    
        balance_ranges = {
    
            "Savings": (1000, 500000),
    
            "Current": (10000, 3000000),
    
            "Salary": (0, 300000),
    
            "Fixed Deposit": (25000, 5000000),
    
            "Recurring Deposit": (5000, 1000000),
    
            "NRE": (50000, 10000000),
    
            "NRO": (10000, 3000000),
    
        }
    
        minimum, maximum = balance_ranges[account_type]
    
        return round(
    
            random.uniform(
    
                minimum,
    
                maximum,
    
            ),
    
            2,
    
        )
    
    # =====================================================================
    # Generate Accounts
    # =====================================================================
    
    def generate_accounts(self) -> None:
        """
        Generate Account data.
        """
    
        self.logger.info(
            "Generating Accounts..."
        )
    
        account_count = 0
    
        # -----------------------------------------------------------------
        # Every customer gets at least one account
        # -----------------------------------------------------------------
    
        customer_indices = list(self.customer_master.index)
    
        random.shuffle(customer_indices)
    
        for idx in customer_indices:
    
            if account_count >= NUM_ACCOUNTS:
                break
    
            customer = self.customer_master.loc[idx]
    
            # Current servicing branch
            branch = self._get_branch()
            
            # Opening branch
            opening_branch = self._generate_account_opening_branch(
                branch
            )
    
            account_type = self._generate_account_type()
    
            account = Account(

                account_id=account_id(),
            
                customer_id=customer["customer_id"],
            
                # Current servicing branch
                branch_id=branch["branch_id"],
            
                # Historical opening branch
                account_opened_branch_id=opening_branch["branch_id"],
            
                account_number=self._generate_account_number(),
            
                account_type=account_type,
            
                currency=self._generate_currency(
                    account_type
                ),
            
                account_status=self._generate_account_status(),
            
                open_date=self._generate_open_date(),
            
                current_balance=self._generate_balance(
                    account_type
                ),
            
                interest_rate=self._generate_interest_rate(
                    account_type
                ),
            
                account_created_city=opening_branch["city"],
            
                account_created_state=opening_branch["state"],
            
                created_at=datetime.now(),
            
                updated_at=None,
            
                source_system=SOURCE_SYSTEM,
        
            )   
    
            self.accounts.append(account)
    
            account_count += 1
    
        # -----------------------------------------------------------------
        # Generate additional accounts
        # -----------------------------------------------------------------
    
        while account_count < NUM_ACCOUNTS:
    
            customer = self._get_customer()
    
            customer_account_count = sum(
    
                account.customer_id == customer["customer_id"]
    
                for account in self.accounts
    
            )
    
            # Maximum 3 accounts/customer
    
            if customer_account_count >= 3:
                continue
    
            branch = self._get_branch()
    
            opening_branch = self._generate_account_opening_branch(
                branch
            )
    
            account_type = self._generate_account_type()
    
            account = Account(
    
                account_id=account_id(),
    
                customer_id=customer["customer_id"],
    
                branch_id=branch["branch_id"],
    
                account_opened_branch_id=opening_branch["branch_id"],
    
                account_number=self._generate_account_number(),
    
                account_type=account_type,
    
                currency=self._generate_currency(
                    account_type
                ),
    
                account_status=self._generate_account_status(),
    
                open_date=self._generate_open_date(),
    
                current_balance=self._generate_balance(
                    account_type
                ),
    
                interest_rate=self._generate_interest_rate(
                    account_type
                ),
    
                account_created_city=opening_branch["city"],
    
                account_created_state=opening_branch["state"],
    
                created_at=datetime.now(),
    
                updated_at=None,
    
                source_system=SOURCE_SYSTEM,
    
            )
    
            self.accounts.append(account)
    
            account_count += 1
    
        self.logger.info(
            f"{len(self.accounts)} Accounts generated successfully."
        )
        
    # =====================================================================
    # Validate Accounts
    # =====================================================================
    
    def validate_accounts(self) -> bool:
        """
        Validate Accounts dataset.
        """
    
        self.logger.info(
            "Validating Accounts..."
        )
    
        df = self.accounts_df()
    
        if df.empty:
    
            self.logger.error(
                "Accounts dataframe is empty."
            )
    
            return False
    
        if df["account_id"].duplicated().any():
    
            self.logger.error(
                "Duplicate Account IDs detected."
            )
    
            return False
    
        if df["account_number"].duplicated().any():
    
            self.logger.error(
                "Duplicate Account Numbers detected."
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
    
        valid_branches = set(
            self.branch_master["branch_id"]
        )
    
        if (~df["branch_id"].isin(valid_branches)).any():
    
            self.logger.error(
                "Invalid Branch IDs detected."
            )
    
            return False
    
        mandatory_columns = [
    
            "account_id",
    
            "customer_id",
    
            "branch_id",
    
            "account_number",
    
            "account_type",
    
            "currency",
    
            "account_status",
    
            "current_balance",
    
        ]
    
        for column in mandatory_columns:
    
            if df[column].isnull().any():
    
                self.logger.error(
                    f"Null values found in {column}."
                )
    
                return False
    
        self.logger.info(
            "Account validation completed successfully."
        )
    
        return True
        
    # =====================================================================
    # Export Accounts
    # =====================================================================
    
    def export_accounts(self) -> None:
        """
        Export Accounts dataset.
        """
    
        self.logger.info(
            "Exporting Accounts..."
        )
    
        self.accounts_df().to_csv(
    
            ACCOUNTS_FILE,
    
            index=False,
    
        )
    
        self.logger.info(
            f"Accounts exported successfully to {ACCOUNTS_FILE}"
        )

    def cards_df(self) -> pd.DataFrame:
        """
        Return Cards dataframe.
        """

        return pd.DataFrame(
            [card.to_dict() for card in self.cards]
        )
        
    # =====================================================================
    # Card Helper Methods
    # =====================================================================
    
    def _generate_card_number(self) -> str:
        """
        Generate a unique 16-digit card number.
        """
    
        while True:
    
            card_number = "".join(
                random.choices(
                    "0123456789",
                    k=16,
                )
            )
    
            if not hasattr(self, "_generated_card_numbers"):
                self._generated_card_numbers = set()
    
            if card_number not in self._generated_card_numbers:
                self._generated_card_numbers.add(card_number)
                return card_number
    
    
    def _generate_card_type(self) -> str:
        """
        Generate card type.
        """
    
        return random.choices(
    
            CARD_TYPES,
    
            weights=[
                65,    # Debit
                25,    # Credit
                7,     # Prepaid
                3,     # Charge
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_card_network(self) -> str:
        """
        Generate card network.
        """
    
        return random.choices(
    
            CARD_NETWORKS,
    
            weights=[
                35,     # Visa
                30,     # Mastercard
                30,     # RuPay
                5,      # American Express
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_card_status(self) -> str:
        """
        Generate card status.
        """
    
        return random.choices(
    
            CARD_STATUS,
    
            weights=[
                85,     # Active
                4,      # Blocked
                3,      # Expired
                3,      # Closed
                3,      # Lost
                2,      # Stolen
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_issue_date(
        self,
        account_open_date,
    ):
        """
        Generate card issue date.
        """
    
        return self.fake.date_between(
    
            start_date=account_open_date,
    
            end_date="today",
    
        )
    
    
    def _generate_expiry_date(
        self,
        issue_date,
    ):
        """
        Generate expiry date.
        """
    
        return issue_date + timedelta(days=365 * 5)
    
    
    def _generate_credit_limit(
        self,
        card_type: str,
    ) -> float:
        """
        Generate credit limit.
        """
    
        if card_type == "Debit":
            return 0.0
    
        if card_type == "Prepaid":
            return random.choice(
                [
                    10000,
                    25000,
                    50000,
                ]
            )
    
        return random.choice(
            [
                50000,
                100000,
                200000,
                500000,
                1000000,
            ]
        )

    def _generate_card_holder_name(
        self,
        account: pd.Series,
    ) -> str:
        """
        Generate card holder name.
        """
    
        customer = self.customer_master[
            self.customer_master["customer_id"]
            == account["customer_id"]
        ].iloc[0]
    
        return (
            f"{customer['first_name']} "
            f"{customer['last_name']}"
        ).upper()

    def _generate_cvv(self) -> str:
        """
        Generate CVV.
        """
    
        return f"{random.randint(100, 999)}"
        
    def _generate_pin_generation_status(self) -> str:
        """
        Generate PIN generation status.
        """
    
        return random.choices(
    
            [
    
                "Generated",
    
                "Pending",
    
            ],
    
            weights=[95, 5],
    
            k=1,

        )[0]
        
    def _generate_contactless_enabled(self) -> str:
        """
        Generate contactless flag.
        """
    
        return random.choices(
    
            [
    
                "Yes",
    
                "No",
    
            ],
    
            weights=[90, 10],
    
            k=1,
    
        )[0]
        
    def _generate_international_usage_enabled(
        self,
        card_type: str,
    ) -> str:
        """
        Generate international usage flag.
        """
    
        if card_type == "Prepaid":
    
            return "No"
    
        return random.choices(
    
            [
    
                "Yes",
    
                "No",
    
            ],
    
            weights=[25, 75],
    
            k=1,
    
        )[0]
    
    # =====================================================================
    # Generate Cards
    # =====================================================================
    
    def generate_cards(self) -> None:
        """
        Generate Cards.
        """
    
        self.logger.info(
            "Generating Cards..."
        )
    
        eligible_accounts = self.accounts_df()
    
        eligible_accounts = eligible_accounts[
    
            eligible_accounts["account_type"].isin(
    
                [
                    "Savings",
                    "Current",
                    "Salary",
                    "NRE",
                    "NRO",
                ]
    
            )
    
        ]
    
        generated_cards = 0
    
        for _, account in eligible_accounts.iterrows():
    
            if generated_cards >= NUM_CARDS:
                break
    
            cards_to_generate = random.choices(
    
                [0, 1, 2],
    
                weights=[
                    10,
                    60,
                    30,
                ],
    
                k=1,
    
            )[0]
    
            for _ in range(cards_to_generate):
    
                if generated_cards >= NUM_CARDS:
                    break
    
                card_type = self._generate_card_type()
    
                issue_date = self._generate_issue_date(
                    account["open_date"]
                )
    
                card = Card(

                    card_id=card_id(),
                
                    account_id=account["account_id"],
                
                    card_number=self._generate_card_number(),
                
                    card_type=card_type,
                
                    network=self._generate_card_network(),
                
                    issue_date=issue_date,
                
                    expiry_date=self._generate_expiry_date(
                        issue_date
                    ),
                
                    credit_limit=self._generate_credit_limit(
                        card_type
                    ),
                
                    card_status=self._generate_card_status(),
                
                    card_holder_name=self._generate_card_holder_name(
                        account
                    ),
                
                    cvv=self._generate_cvv(),
                
                    pin_generation_status=self._generate_pin_generation_status(),
                
                    contactless_enabled=self._generate_contactless_enabled(),
                
                    international_usage_enabled=self._generate_international_usage_enabled(
                        card_type
                    ),
                
                    created_at=datetime.now(),
                
                    updated_at=None,
                
                    source_system=SOURCE_SYSTEM,

                )
    
                self.cards.append(card)
    
                generated_cards += 1
    
        self.logger.info(
            f"{len(self.cards)} Cards generated successfully."
        )
    
    
    # =====================================================================
    # Validate Cards
    # =====================================================================
    
    def validate_cards(self) -> bool:
        """
        Validate Cards dataset.
        """
    
        self.logger.info(
            "Validating Cards..."
        )
    
        df = self.cards_df()
    
        if df.empty:
    
            self.logger.error(
                "Cards dataframe is empty."
            )
    
            return False
    
        if df["card_id"].duplicated().any():
    
            self.logger.error(
                "Duplicate Card IDs detected."
            )
    
            return False
    
        if df["card_number"].duplicated().any():
    
            self.logger.error(
                "Duplicate Card Numbers detected."
            )
    
            return False
    
        valid_accounts = set(
            self.accounts_df()["account_id"]
        )
    
        if (~df["account_id"].isin(valid_accounts)).any():
    
            self.logger.error(
                "Invalid Account IDs detected."
            )
    
            return False
    
        self.logger.info(
            "Card validation successful."
        )
    
        return True
    
    
    # =====================================================================
    # Export Cards
    # =====================================================================
    
    def export_cards(self) -> None:
        """
        Export Cards dataset.
        """
    
        self.logger.info(
            "Exporting Cards..."
        )
    
        self.cards_df().to_csv(
    
            CARDS_FILE,
    
            index=False,
    
        )
    
        self.logger.info(
            f"Cards exported to {CARDS_FILE}"
        )

    def transactions_df(self) -> pd.DataFrame:
        """
        Return Transactions dataframe.
        """

        return pd.DataFrame(
            [
                transaction.to_dict()
                for transaction in self.transactions
            ]
        )
        
    # =====================================================================
    # Transaction Helper Methods
    # =====================================================================
    
    def _generate_transaction_type(self) -> str:
        """
        Generate Transaction Type.
        """
    
        return random.choices(
    
            TRANSACTION_TYPES,
    
            weights=[
    
                28,     # Credit
                27,     # Debit
                10,     # Transfer
                8,      # Withdrawal
                5,      # Deposit
                12,     # POS Purchase
                7,      # Online Payment
                3,      # Bill Payment
    
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_transaction_channel(
        self,
        transaction_type: str,
    ) -> str:
        """
        Generate Transaction Channel based on transaction type.
        """
    
        channel_mapping = {
    
            "Withdrawal": [
    
                "ATM",
    
                "Branch",
    
            ],
    
            "Deposit": [
    
                "ATM",
    
                "Branch",
    
                "Cheque",
    
            ],
    
            "Transfer": [
    
                "NEFT",
    
                "RTGS",
    
                "IMPS",
    
                "Online Banking",
    
                "Mobile Banking",
    
            ],
    
            "POS Purchase": [
    
                "POS",
    
            ],
    
            "Online Payment": [
    
                "UPI",
    
                "Online Banking",
    
                "Mobile Banking",
    
            ],
    
            "Bill Payment": [
    
                "UPI",
    
                "Mobile Banking",
    
                "Online Banking",
    
                "Auto Debit",
    
            ],
    
            "Credit": [
    
                "UPI",
    
                "NEFT",
    
                "IMPS",
    
                "RTGS",
    
                "Branch",
    
            ],
    
            "Debit": [
    
                "UPI",
    
                "POS",
    
                "ATM",
    
                "Mobile Banking",
    
                "Online Banking",
    
            ],
    
        }
    
        return random.choice(
    
            channel_mapping[transaction_type]
    
        )
    
    
    def _generate_transaction_status(self) -> str:
        """
        Generate Transaction Status.
        """
    
        return random.choices(
    
            TRANSACTION_STATUS,
    
            weights=[
    
                94,     # Success
    
                2,      # Pending
    
                2,      # Failed
    
                1,      # Reversed
    
                1,      # Completed
    
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_transaction_currency(self) -> str:
        """
        Generate transaction currency.
        """
    
        return "INR"
    
    
    def _generate_transaction_amount(
        self,
        transaction_type: str,
        transaction_channel: str,
    ) -> float:
        """
        Generate transaction amount.
        """
    
        if transaction_channel == "UPI":
    
            minimum, maximum = (10, 25000)
    
        elif transaction_channel == "ATM":
    
            minimum, maximum = (100, 20000)
    
        elif transaction_channel == "POS":
    
            minimum, maximum = (50, 75000)
    
        elif transaction_channel == "NEFT":
    
            minimum, maximum = (1000, 500000)
    
        elif transaction_channel == "RTGS":
    
            minimum, maximum = (200000, 2000000)
    
        elif transaction_channel == "IMPS":
    
            minimum, maximum = (100, 500000)
    
        elif transaction_channel == "Cheque":
    
            minimum, maximum = (1000, 1000000)
    
        elif transaction_type == "Bill Payment":
    
            minimum, maximum = (100, 100000)
    
        elif transaction_type == "Deposit":
    
            minimum, maximum = (500, 500000)
    
        else:
    
            minimum, maximum = (100, 100000)
    
        return round(
    
            random.uniform(
    
                minimum,
    
                maximum,
    
            ),
    
            2,
    
        )
    
    
    def _generate_transaction_timestamp(
        self,
        account_open_date,
    ):
        """
        Generate transaction timestamp after account opening.
        """
    
        transaction_date = self.fake.date_time_between(
    
            start_date=account_open_date,
    
            end_date="now",
    
        )
    
        return transaction_date
        
    # =====================================================================
    # Transaction Selection Helper Methods
    # =====================================================================
    
    def _prepare_transaction_lookup_caches(self) -> None:
        """
        Precompute lookup structures used repeatedly while generating
        transactions.

        Without this, `_select_account`, `_select_card`, and
        `_select_merchant` each rebuilt a full DataFrame from scratch
        on every single call - fine for a one-off validation call, but
        catastrophic when called ~250,000 times in the transaction
        loop (that rebuild cost is what was driving generation past
        the 2-hour mark). Everything here is computed once, up front.
        """

        self.logger.info(
            "Preparing transaction lookup caches..."
        )

        # ------------------------------------------------------------
        # Eligible accounts (with sampling weights precomputed)
        # ------------------------------------------------------------

        accounts = self.accounts_df()

        eligible_accounts = accounts[
            accounts["account_status"].isin(
                [
                    "Active",
                    "Dormant",
                    "Frozen",
                ]
            )
        ].reset_index(drop=True)

        if eligible_accounts.empty:

            raise ValueError(
                "No eligible accounts available."
            )

        status_weights = {

            "Active": 90,

            "Dormant": 8,

            "Frozen": 2,

        }

        self._eligible_accounts_cache = eligible_accounts

        self._eligible_account_weights_cache = eligible_accounts[
            "account_status"
        ].map(
            status_weights
        ).tolist()

        # ------------------------------------------------------------
        # Active cards, grouped by account_id
        # ------------------------------------------------------------

        cards = self.cards_df()

        active_cards = cards[
            cards["card_status"] == "Active"
        ]

        self._active_cards_by_account_cache = (
            active_cards
            .groupby("account_id")["card_id"]
            .apply(list)
            .to_dict()
        )

        # ------------------------------------------------------------
        # Active merchants, plus a fast merchant_id -> location lookup
        # ------------------------------------------------------------

        merchants = self.merchants_df()

        self._active_merchants_cache = merchants[
            merchants["merchant_status"] == "Active"
        ].reset_index(drop=True)

        self._merchant_location_cache = merchants.set_index(
            "merchant_id"
        )[
            ["merchant_city", "merchant_state"]
        ].to_dict("index")

        self.logger.info(
            "Transaction lookup caches ready "
            f"({len(eligible_accounts)} eligible accounts, "
            f"{len(active_cards)} active cards, "
            f"{len(self._active_merchants_cache)} active merchants)."
        )

    def _select_account(self) -> pd.Series:
        """
        Select an account eligible for transactions.

        Business Rules
        --------------
        • Active accounts are selected most frequently.
        • Dormant accounts are selected occasionally.
        • Frozen accounts are selected rarely.
        • Closed accounts are excluded.
        """

        eligible_accounts = self._eligible_accounts_cache

        selected_position = random.choices(

            population=range(len(eligible_accounts)),

            weights=self._eligible_account_weights_cache,

            k=1,

        )[0]

        return eligible_accounts.iloc[
            selected_position
        ]


    def _select_card(
        self,
        account_id: str,
    ) -> str | None:
        """
        Select a card linked to an account.

        Returns
        -------
        Card ID if available, otherwise None.
        """

        card_ids = self._active_cards_by_account_cache.get(
            account_id
        )

        if not card_ids:

            return None

        return random.choice(card_ids)

    # =====================================================================
    # Merchant & Location Helper Methods
    # =====================================================================

    def _select_merchant(
        self,
        transaction_type: str,
    ) -> str | None:
        """
        Select a merchant for merchant-based transactions.

        Returns
        -------
        Merchant ID if applicable, otherwise None.
        """

        merchant_transactions = {

            "POS Purchase",

            "Online Payment",

            "Bill Payment",

        }

        if transaction_type not in merchant_transactions:

            return None

        active_merchants = self._active_merchants_cache

        if active_merchants.empty:

            return None

        selected_position = random.randrange(
            len(active_merchants)
        )

        return active_merchants.iloc[
            selected_position
        ]["merchant_id"]


    def _generate_transaction_location(
        self,
        merchant_id: str | None,
        account: pd.Series,
    ) -> tuple[str, str]:
        """
        Generate transaction city and state.

        Business Rules
        --------------
        • Merchant transactions usually occur at the
        merchant's location.

        • Non-merchant transactions usually occur near
        the customer's account location.

        • Around 10% of transactions occur from a
        different city/state to simulate travel.
        """

        # -------------------------------------------------------------
        # Merchant Transaction
        # -------------------------------------------------------------

        if merchant_id is not None:

            merchant_location = self._merchant_location_cache[
                merchant_id
            ]

            city = merchant_location["merchant_city"]

            state = merchant_location["merchant_state"]

        # -------------------------------------------------------------
        # Non-Merchant Transaction
        # -------------------------------------------------------------

        else:

            city = account["account_created_city"]

            state = account["account_created_state"]

        # -------------------------------------------------------------
        # Simulate Travel Transactions
        # -------------------------------------------------------------

        if random.random() < 0.10:

            location = self.locations.random_location()

            city = location["city"]

            state = location["state"]

        return (

            city,

            state,

        )
        
    # =====================================================================
    # Transaction Helper Methods (Continued)
    # =====================================================================
    
    def _generate_reference_number(self) -> str:
        """
        Generate bank transaction reference number.
    
        Example
        -------
        UTR202607240001245689
        """
    
        return (
            "TXN"
    
            + datetime.now().strftime("UTR%Y%m%d")
    
            + self.fake.numerify("##########")
    
        )
    
    
    def _generate_narration(
        self,
        transaction_type: str,
        transaction_channel: str,
        merchant_id: str | None,
    ) -> str:
        """
        Generate transaction narration.
        """
    
        # -------------------------------------------------------------
        # Merchant Transactions
        # -------------------------------------------------------------
    
        if merchant_id is not None:
    
            merchant = self.merchants_df()[
    
                self.merchants_df()["merchant_id"]
    
                == merchant_id
    
            ].iloc[0]
    
            merchant_name = merchant["merchant_name"]
    
            narration_map = {
    
                "POS Purchase":
                    f"POS Purchase at {merchant_name}",
    
                "Online Payment":
                    f"Online Payment to {merchant_name}",
    
                "Bill Payment":
                    f"Bill Payment - {merchant_name}",
    
            }
    
            return narration_map.get(
    
                transaction_type,
    
                f"{transaction_type} - {merchant_name}",
    
            )
    
        # -------------------------------------------------------------
        # Non Merchant Transactions
        # -------------------------------------------------------------
    
        narration_map = {
    
            "Credit": "Funds Credited",
    
            "Debit": "Funds Debited",
    
            "Transfer": f"{transaction_channel} Transfer",
    
            "Withdrawal": "Cash Withdrawal",
    
            "Deposit": "Cash Deposit",
    
        }
    
        return narration_map.get(
    
            transaction_type,
    
            transaction_type,
    
        )
    
    
    def _generate_is_international(
        self,
        transaction_channel: str,
    ) -> str:
        """
        Generate international transaction flag.
    
        International transactions are more likely
        for card and online channels.
        """
    
        if transaction_channel in [
    
            "POS",
    
            "Online Banking",
    
            "Mobile Banking",
    
        ]:
    
            probability = 5
    
        else:
    
            probability = 1
    
        return random.choices(
    
            [
    
                "Yes",
    
                "No",
    
            ],
    
            weights=[
    
                probability,
    
                100 - probability,
    
            ],
    
            k=1,
    
        )[0]
    
    
    def _generate_created_timestamp(self):
        """
        Generate record creation timestamp.
        """
    
        return datetime.now()
    
    
    def _generate_updated_timestamp(self):
        """
        Generate updated timestamp.
        """
    
        return None
    
    
    def _generate_source_system(self):
        """
        Generate source system.
        """
    
        return SOURCE_SYSTEM

    # =====================================================================
    # Generate Transactions
    # =====================================================================

    def generate_transactions(self) -> None:
        """
        Generate Transaction data.
        """

        self.logger.info(
            "Generating Transactions..."
        )

        self._prepare_transaction_lookup_caches()

        for _ in range(NUM_TRANSACTIONS):

            account = self._select_account()

            transaction_type = self._generate_transaction_type()

            transaction_channel = self._generate_transaction_channel(
                transaction_type
            )

            card_id_value = self._select_card(
                account["account_id"]
            )

            merchant_id_value = self._select_merchant(
                transaction_type
            )

            city, state = self._generate_transaction_location(
                merchant_id_value,
                account,
            )

            transaction = Transaction(

                transaction_id=transaction_id(),

                account_id=account["account_id"],

                merchant_id=merchant_id_value,

                card_id=card_id_value,

                transaction_timestamp=self._generate_transaction_timestamp(
                    account["open_date"]
                ),

                transaction_type=transaction_type,

                transaction_channel=transaction_channel,

                transaction_status=self._generate_transaction_status(),

                amount=self._generate_transaction_amount(
                    transaction_type,
                    transaction_channel,
                ),

                currency=self._generate_transaction_currency(),

                reference_number=self._generate_reference_number(),

                narration=self._generate_narration(
                    transaction_type,
                    transaction_channel,
                    merchant_id_value,
                ),

                location_city=city,

                location_state=state,

                is_international=self._generate_is_international(
                    transaction_channel
                ),

                created_at=self._generate_created_timestamp(),

                updated_at=self._generate_updated_timestamp(),

                source_system=self._generate_source_system(),

            )

            self.transactions.append(transaction)

        self.logger.info(
            f"{len(self.transactions)} Transactions generated successfully."
        )

    # =====================================================================
    # Validate Transactions
    # =====================================================================

    def validate_transactions(self) -> bool:
        """
        Validate Transactions dataset.
        """

        self.logger.info(
            "Validating Transactions..."
        )

        df = self.transactions_df()

        if df.empty:

            self.logger.error(
                "Transactions dataframe is empty."
            )

            return False

        if df["transaction_id"].duplicated().any():

            self.logger.error(
                "Duplicate Transaction IDs detected."
            )

            return False

        valid_accounts = set(
            self.accounts_df()["account_id"]
        )

        if (~df["account_id"].isin(valid_accounts)).any():

            self.logger.error(
                "Invalid Account IDs detected."
            )

            return False

        valid_cards = set(
            self.cards_df()["card_id"]
        )

        card_mask = df["card_id"].notna()

        if (~df.loc[card_mask, "card_id"].isin(valid_cards)).any():

            self.logger.error(
                "Invalid Card IDs detected."
            )

            return False

        valid_merchants = set(
            self.merchants_df()["merchant_id"]
        )

        merchant_mask = df["merchant_id"].notna()

        if (~df.loc[merchant_mask, "merchant_id"].isin(valid_merchants)).any():

            self.logger.error(
                "Invalid Merchant IDs detected."
            )

            return False

        mandatory_columns = [

            "transaction_id",

            "account_id",

            "transaction_type",

            "transaction_channel",

            "transaction_status",

            "amount",

            "currency",

        ]

        for column in mandatory_columns:

            if df[column].isnull().any():

                self.logger.error(
                    f"Null values found in {column}."
                )

                return False

        self.logger.info(
            "Transaction validation completed successfully."
        )

        return True

    # =====================================================================
    # Export Transactions
    # =====================================================================

    def export_transactions(self) -> None:
        """
        Export Transactions dataset.
        """

        self.logger.info(
            "Exporting Transactions..."
        )

        self.transactions_df().to_csv(

            TRANSACTIONS_FILE,

            index=False,

        )

        self.logger.info(
            f"Transactions exported successfully to {TRANSACTIONS_FILE}"
        )

    # ==============================================================
    # Validate All
    # ==============================================================

    def validate_all(self) -> bool:
        """
        Validate all generated Banking datasets.
        """

        self.logger.info(
            "Running Validation..."
        )

        validations = [

            self.validate_accounts(),

            self.validate_cards(),

            self.validate_transactions(),

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

    # ==============================================================
    # Export All
    # ==============================================================

    def export_all(self) -> None:
        """
        Export all Banking datasets.
        """

        self.logger.info(
            "Exporting datasets..."
        )

        self.export_accounts()

        self.export_cards()

        self.export_transactions()

        self.logger.info(
            "Export completed successfully."
        )

    # ==============================================================
    # Summary
    # ==============================================================

    def summary(self) -> None:
        """
        Display Banking Generation Summary.
        """

        self.logger.info("=" * 70)

        self.logger.info(
            "Banking Generation Summary"
        )

        self.logger.info(
            f"Accounts Generated      : {len(self.accounts)}"
        )

        self.logger.info(
            f"Cards Generated         : {len(self.cards)}"
        )

        self.logger.info(
            f"Transactions Generated  : {len(self.transactions)}"
        )

        self.logger.info("=" * 70)

    # =====================================================================
    # Pipeline Execution
    # =====================================================================

    def run(self) -> None:
        """
        Execute Banking Generator.
        """

        try:

            self.logger.info("=" * 80)

            self.logger.info(
                "Starting Banking Generator..."
            )

            self.generate_accounts()

            self.generate_cards()

            self.generate_transactions()

            self.summary()

            if not self.validate_all():

                raise ValueError(
                    "Validation Failed."
                )

            self.export_all()

            self.logger.info(
                "Banking Generator completed successfully."
            )

            self.logger.info("=" * 80)

        except Exception as ex:

            self.logger.exception(ex)

            raise

# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":
    print("Starting Banking Generator...")
    
    generator = BankingGenerator()
    
    print("Generator created.")
    
    generator.run()
    
    print("Pipeline finished.")