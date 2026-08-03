from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(slots=True)
class Account:

    account_id: str

    customer_id: str

    branch_id: str

    account_opened_branch_id: str

    account_number: str

    account_type: str

    currency: str

    account_status: str

    open_date: date

    current_balance: float

    interest_rate: float

    account_created_city: str

    account_created_state: str

    created_at: datetime

    updated_at: datetime | None

    source_system: str

    def to_dict(self):

        return asdict(self)