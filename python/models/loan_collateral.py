"""
===============================================================================
Loan Collateral Data Model
===============================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(slots=True)
class LoanCollateral:

    collateral_id: str

    loan_id: str

    asset_type: str

    asset_value: float

    valuation_date: date

    created_at: datetime

    updated_at: datetime | None

    source_system: str

    def to_dict(self):

        return asdict(self)
