"""
===============================================================================
Fraud Alert Data Model
===============================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(slots=True)
class FraudAlert:

    alert_id: str

    transaction_id: str

    fraud_score: int

    alert_reason: str

    alert_status: str

    alert_timestamp: datetime

    assigned_to: str | None

    assignee_emp_id: str | None

    resolution_date: date | None

    created_at: datetime

    updated_at: datetime | None

    source_system: str

    def to_dict(self):

        return asdict(self)
