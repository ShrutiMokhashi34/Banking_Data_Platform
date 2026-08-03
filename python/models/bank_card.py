from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(slots=True)
class Card:

    card_id: str

    account_id: str

    card_number: str

    card_type: str

    network: str

    issue_date: date

    expiry_date: date

    credit_limit: float

    card_status: str

    card_holder_name: str

    cvv: str

    pin_generation_status: str

    contactless_enabled: str

    international_usage_enabled: str

    created_at: datetime

    updated_at: datetime | None

    source_system: str

    def to_dict(self):

        return asdict(self)