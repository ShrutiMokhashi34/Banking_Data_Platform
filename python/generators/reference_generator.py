"""
Reference Domain Data Generator

Generates synthetic / API-sourced reference data for:

    1. Exchange Rates
    2. Holiday Calendar

Both tables prefer real, live data from public APIs (matching the
source-system labels already defined in config.py: "Exchange Rate API"
and "Holiday Calendar API"). If the API is unreachable (e.g. no network
access, rate limiting, timeout), each falls back to a clearly-flagged
synthetic dataset so the pipeline never breaks.
"""

from __future__ import annotations

# =====================================================================
# Standard Library
# =====================================================================

import random
from datetime import date, datetime, timedelta

# =====================================================================
# Third Party Libraries
# =====================================================================

import pandas as pd
import requests

# =====================================================================
# Project Configuration
# =====================================================================

from config.config import (
    RANDOM_SEED,
    NUM_EXCHANGE_RATE_DAYS,
    NUM_HOLIDAYS,
    EXCHANGE_RATES_FILE,
    HOLIDAY_CALENDAR_FILE,
    EXCHANGE_RATE_API,
    HOLIDAY_API_COUNTRY,
    HOLIDAY_START_YEAR,
    HOLIDAY_END_YEAR,
    EXCHANGE_RATE_SOURCE,
)

from config.constants import (
    COUNTRY,
    SUPPORTED_CURRENCIES,
    CURRENCY_SYMBOLS,
    BASE_CURRENCY,
    HOLIDAY_TYPES,
)

# =====================================================================
# Models
# =====================================================================

from models.exchange_rate import ExchangeRate
from models.holiday_calendar import Holiday

# =====================================================================
# Utilities
# =====================================================================

from generators.id_generator import (
    holiday_id,
)

# =====================================================================
# Logging
# =====================================================================

from config.logging_config import setup_logger

# =====================================================================
# Business Reference Data
# =====================================================================

CURRENCY_NAMES = {

    "INR": "Indian Rupee",

    "USD": "US Dollar",

    "EUR": "Euro",

    "GBP": "British Pound",

    "JPY": "Japanese Yen",

    "AUD": "Australian Dollar",

    "CAD": "Canadian Dollar",

    "CHF": "Swiss Franc",

    "SGD": "Singapore Dollar",

    "AED": "UAE Dirham",

    "CNY": "Chinese Yuan",

    "HKD": "Hong Kong Dollar",

    "NZD": "New Zealand Dollar",

}

# Approximate fallback anchor rates (units of INR per 1 foreign unit),
# used only when the live API is unreachable.
FALLBACK_RATES_TO_INR = {

    "USD": 84.0,

    "EUR": 91.0,

    "GBP": 106.0,

    "JPY": 0.56,

    "AUD": 55.0,

    "CAD": 61.0,

    "CHF": 95.0,

    "SGD": 62.0,

    "AED": 22.9,

    "CNY": 11.6,

    "HKD": 10.8,

    "NZD": 51.0,

}

# Fallback Indian national holidays (month, day, name, type), used only
# when the live holiday API is unreachable. Dates for movable/lunar
# holidays (Holi, Diwali, Eid, etc.) are approximate.
FALLBACK_HOLIDAYS = [

    (1, 26, "Republic Day", "National"),

    (3, 14, "Holi", "Religious"),

    (4, 14, "Ambedkar Jayanti", "National"),

    (5, 1, "Labour Day", "National"),

    (8, 15, "Independence Day", "National"),

    (10, 2, "Gandhi Jayanti", "National"),

    (10, 31, "Diwali", "Religious"),

    (12, 25, "Christmas", "Religious"),

]

HOLIDAY_TYPE_MAP = {

    "Public": "National",

    "National": "National",

    "Bank": "Bank",

    "Optional": "Optional",

}


# =====================================================================
# Reference Generator
# =====================================================================

class ReferenceGenerator:
    """
    Reference Domain Generator.

    Generates:

        • Exchange Rates

        • Holiday Calendar
    """

    def __init__(self) -> None:

        self.logger = setup_logger(__name__)

        random.seed(RANDOM_SEED)

        # ==============================================================
        # Generated Objects
        # ==============================================================

        self.exchange_rates: list[ExchangeRate] = []

        self.holidays: list[Holiday] = []

        self.logger.info(
            "Reference Generator initialized successfully."
        )

    # =====================================================================
    # DataFrames
    # =====================================================================

    def exchange_rates_df(self) -> pd.DataFrame:
        """
        Return Exchange Rates dataframe.
        """

        return pd.DataFrame(
            [rate.to_dict() for rate in self.exchange_rates]
        )

    def holidays_df(self) -> pd.DataFrame:
        """
        Return Holiday Calendar dataframe.
        """

        return pd.DataFrame(
            [holiday.to_dict() for holiday in self.holidays]
        )

    # =====================================================================
    # Exchange Rate Helper Methods
    # =====================================================================

    def _fetch_live_anchor_rates(self) -> dict[str, float]:
        """
        Fetch today's live exchange rates from the configured API.

        Returns
        -------
        Mapping of currency code -> rate to INR (units of INR per
        1 unit of foreign currency). Falls back to approximate
        static rates if the API call fails.
        """

        try:

            response = requests.get(
                EXCHANGE_RATE_API,
                timeout=10,
            )

            response.raise_for_status()

            payload = response.json()

            rates_from_inr = payload["rates"]

            anchor_rates = {}

            for currency in SUPPORTED_CURRENCIES:

                if currency == BASE_CURRENCY:
                    continue

                rate_from_inr = rates_from_inr.get(currency)

                if not rate_from_inr:
                    continue

                anchor_rates[currency] = 1.0 / rate_from_inr

            if anchor_rates:

                self.logger.info(
                    f"Fetched live exchange rates for {len(anchor_rates)} currencies."
                )

                return anchor_rates

            raise ValueError("API returned no usable rates.")

        except Exception as ex:

            self.logger.warning(
                f"Live exchange rate fetch failed ({ex}). "
                "Falling back to approximate static rates."
            )

            return dict(FALLBACK_RATES_TO_INR)

    def _generate_daily_rate(
        self,
        previous_rate: float,
    ) -> float:
        """
        Generate the next day's rate as a small random walk from the
        previous day's rate (simulates realistic day-to-day FX drift).
        """

        drift = random.uniform(-0.006, 0.006)

        return round(previous_rate * (1 + drift), 4)

    # =====================================================================
    # Generate Exchange Rates
    # =====================================================================

    def generate_exchange_rates(self) -> None:
        """
        Generate Exchange Rate data.

        Business Rule
        -------------
        Builds a NUM_EXCHANGE_RATE_DAYS-day daily history for each
        supported foreign currency, anchored on today's live (or
        fallback) rate and walked backward in time.
        """

        self.logger.info(
            "Generating Exchange Rates..."
        )

        anchor_rates = self._fetch_live_anchor_rates()

        today = date.today()

        for currency, anchor_rate in anchor_rates.items():

            current_rate = anchor_rate

            for day_offset in range(NUM_EXCHANGE_RATE_DAYS):

                rate_date = today - timedelta(days=day_offset)

                exchange_rate = ExchangeRate(

                    rate_date=rate_date,

                    currency=CURRENCY_NAMES.get(currency, currency),

                    currency_symbol=CURRENCY_SYMBOLS.get(currency, ""),

                    rate_to_inr=round(current_rate, 4),

                    source=EXCHANGE_RATE_SOURCE,

                )

                self.exchange_rates.append(exchange_rate)

                # Walk backward for the next (earlier) day
                current_rate = self._generate_daily_rate(current_rate)

        self.logger.info(
            f"{len(self.exchange_rates)} Exchange Rate records generated successfully."
        )

    # =====================================================================
    # Validate Exchange Rates
    # =====================================================================

    def validate_exchange_rates(self) -> bool:
        """
        Validate Exchange Rates dataset.
        """

        self.logger.info(
            "Validating Exchange Rates..."
        )

        df = self.exchange_rates_df()

        if df.empty:

            self.logger.error(
                "Exchange Rates dataframe is empty."
            )

            return False

        if df.duplicated(subset=["rate_date", "currency"]).any():

            self.logger.error(
                "Duplicate (rate_date, currency) combinations detected."
            )

            return False

        if (df["rate_to_inr"] <= 0).any():

            self.logger.error(
                "Invalid exchange rate values detected."
            )

            return False

        self.logger.info(
            "Exchange Rate validation completed successfully."
        )

        return True

    # =====================================================================
    # Export Exchange Rates
    # =====================================================================

    def export_exchange_rates(self) -> None:
        """
        Export Exchange Rates dataset.
        """

        self.logger.info(
            "Exporting Exchange Rates..."
        )

        self.exchange_rates_df().to_csv(

            EXCHANGE_RATES_FILE,

            index=False,

        )

        self.logger.info(
            f"Exchange Rates exported successfully to {EXCHANGE_RATES_FILE}"
        )

    # =====================================================================
    # Holiday Helper Methods
    # =====================================================================

    def _fetch_live_holidays(
        self,
        year: int,
    ) -> list[dict]:
        """
        Fetch public holidays for a given year from the Nager.Date API.

        Returns an empty list if the call fails (caller falls back to
        synthetic data).
        """

        try:

            response = requests.get(
                f"https://date.nager.at/api/v3/PublicHolidays/"
                f"{year}/{HOLIDAY_API_COUNTRY}",
                timeout=10,
            )

            response.raise_for_status()

            return response.json()

        except Exception as ex:

            self.logger.warning(
                f"Live holiday fetch failed for {year} ({ex}). "
                "Falling back to synthetic holidays for this year."
            )

            return []

    def _generate_fallback_holidays_for_year(
        self,
        year: int,
    ) -> list[dict]:
        """
        Build a synthetic holiday list for a year using
        FALLBACK_HOLIDAYS as a template.
        """

        holidays = []

        for month, day, name, holiday_type in FALLBACK_HOLIDAYS:

            try:

                holiday_date = date(year, month, day)

            except ValueError:
                continue

            holidays.append(
                {
                    "date": holiday_date.isoformat(),
                    "localName": name,
                    "types": [holiday_type],
                }
            )

        return holidays

    def _map_holiday_type(
        self,
        raw_types: list[str],
    ) -> str:
        """
        Map an API/fallback holiday type to one of our HOLIDAY_TYPES.
        """

        for raw_type in raw_types:

            mapped = HOLIDAY_TYPE_MAP.get(raw_type)

            if mapped in HOLIDAY_TYPES:
                return mapped

        return "National"

    # =====================================================================
    # Generate Holiday Calendar
    # =====================================================================

    def generate_holiday_calendar(self) -> None:
        """
        Generate Holiday Calendar data for the configured year range.
        """

        self.logger.info(
            "Generating Holiday Calendar..."
        )

        for year in range(HOLIDAY_START_YEAR, HOLIDAY_END_YEAR + 1):

            if len(self.holidays) >= NUM_HOLIDAYS:
                break

            raw_holidays = self._fetch_live_holidays(year)

            if not raw_holidays:

                raw_holidays = self._generate_fallback_holidays_for_year(
                    year
                )

            for raw_holiday in raw_holidays:

                if len(self.holidays) >= NUM_HOLIDAYS:
                    break

                try:

                    holiday_date = datetime.strptime(
                        raw_holiday["date"],
                        "%Y-%m-%d",
                    ).date()

                except (KeyError, ValueError):
                    continue

                holiday = Holiday(

                    holiday_id=holiday_id(),

                    holiday_date=holiday_date,

                    country=COUNTRY,

                    state="All",

                    holiday_name=raw_holiday.get(
                        "localName",
                        raw_holiday.get("name", "Holiday"),
                    ),

                    holiday_type=self._map_holiday_type(
                        raw_holiday.get("types", [])
                    ),

                )

                self.holidays.append(holiday)

        self.logger.info(
            f"{len(self.holidays)} Holiday records generated successfully."
        )

    # =====================================================================
    # Validate Holiday Calendar
    # =====================================================================

    def validate_holiday_calendar(self) -> bool:
        """
        Validate Holiday Calendar dataset.
        """

        self.logger.info(
            "Validating Holiday Calendar..."
        )

        df = self.holidays_df()

        if df.empty:

            self.logger.error(
                "Holiday Calendar dataframe is empty."
            )

            return False

        if df["holiday_id"].duplicated().any():

            self.logger.error(
                "Duplicate Holiday IDs detected."
            )

            return False

        mandatory_columns = [

            "holiday_id",

            "holiday_date",

            "holiday_name",

            "holiday_type",

        ]

        for column in mandatory_columns:

            if df[column].isnull().any():

                self.logger.error(
                    f"Null values found in {column}."
                )

                return False

        self.logger.info(
            "Holiday Calendar validation completed successfully."
        )

        return True

    # =====================================================================
    # Export Holiday Calendar
    # =====================================================================

    def export_holiday_calendar(self) -> None:
        """
        Export Holiday Calendar dataset.
        """

        self.logger.info(
            "Exporting Holiday Calendar..."
        )

        self.holidays_df().to_csv(

            HOLIDAY_CALENDAR_FILE,

            index=False,

        )

        self.logger.info(
            f"Holiday Calendar exported successfully to {HOLIDAY_CALENDAR_FILE}"
        )

    # =====================================================================
    # Validate All
    # =====================================================================

    def validate_all(self) -> bool:
        """
        Validate all generated Reference datasets.
        """

        self.logger.info(
            "Running Validation..."
        )

        validations = [

            self.validate_exchange_rates(),

            self.validate_holiday_calendar(),

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
        Export all Reference datasets.
        """

        self.logger.info(
            "Exporting datasets..."
        )

        self.export_exchange_rates()

        self.export_holiday_calendar()

        self.logger.info(
            "Export completed successfully."
        )

    # =====================================================================
    # Summary
    # =====================================================================

    def summary(self) -> None:
        """
        Display Reference Generation Summary.
        """

        self.logger.info("=" * 70)

        self.logger.info(
            "Reference Generation Summary"
        )

        self.logger.info(
            f"Exchange Rates Generated  : {len(self.exchange_rates)}"
        )

        self.logger.info(
            f"Holidays Generated        : {len(self.holidays)}"
        )

        self.logger.info("=" * 70)

    # =====================================================================
    # Pipeline Execution
    # =====================================================================

    def run(self) -> None:
        """
        Execute Reference Generator.
        """

        try:

            self.logger.info("=" * 80)

            self.logger.info(
                "Starting Reference Generator..."
            )

            self.generate_exchange_rates()

            self.generate_holiday_calendar()

            self.summary()

            if not self.validate_all():

                raise ValueError(
                    "Validation Failed."
                )

            self.export_all()

            self.logger.info(
                "Reference Generator completed successfully."
            )

            self.logger.info("=" * 80)

        except Exception as ex:

            self.logger.exception(ex)

            raise


# =====================================================================
# Main
# =====================================================================

if __name__ == "__main__":
    print("Starting Reference Generator...")

    generator = ReferenceGenerator()

    print("Generator created.")

    generator.run()

    print("Pipeline finished.")
