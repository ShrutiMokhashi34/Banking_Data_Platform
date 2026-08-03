"""
===============================================================================
Loan Application Data Model
===============================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(slots=True)
class LoanApplication:

    application_id: str

    customer_id: str

    loan_id: str | None

    application_date: date

    requested_amount: float

    approval_status: str

    created_at: datetime

    updated_at: datetime | None

    source_system: str

    def to_dict(self):

        return asdict(self)
