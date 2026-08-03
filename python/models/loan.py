"""
===============================================================================
Loan Data Model
===============================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(slots=True)
class Loan:

    loan_id: str

    customer_id: str

    loan_type: str

    principal_amount: float

    interest_rate: float

    tenure_months: int

    emi_amount: float

    loan_status: str

    disbursement_date: date

    created_at: datetime

    updated_at: datetime | None

    source_system: str

    def to_dict(self):

        return asdict(self)
