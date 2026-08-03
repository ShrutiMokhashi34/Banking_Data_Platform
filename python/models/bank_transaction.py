from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(slots=True)
class Transaction:

    transaction_id: str

    account_id: str

    merchant_id: str | None

    card_id: str | None

    transaction_timestamp: datetime

    transaction_type: str

    transaction_channel: str

    transaction_status: str

    amount: float

    currency: str

    reference_number: str

    narration: str

    location_city: str

    location_state: str

    is_international: str

    created_at: datetime

    updated_at: datetime | None

    source_system: str

    def to_dict(self):

        return asdict(self)