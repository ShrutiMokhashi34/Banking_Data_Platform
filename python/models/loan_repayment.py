"""
===============================================================================
Loan Repayment Data Model
===============================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(slots=True)
class LoanRepayment:

    repayment_id: str

    loan_id: str

    payment_date: date

    amount_paid: float

    payment_mode: str

    created_at: datetime

    updated_at: datetime | None

    source_system: str

    def to_dict(self):

        return asdict(self)
