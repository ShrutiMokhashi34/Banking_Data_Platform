from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(slots=True)
class Merchant:

    merchant_id: str

    merchant_name: str

    merchant_category: str

    merchant_type: str

    merchant_city: str

    merchant_state: str

    merchant_country: str

    merchant_status: str

    accepts_upi: str

    accepts_cards: str

    average_ticket_size: float

    onboarding_date: datetime

    created_at: datetime

    updated_at: datetime | None

    source_system: str

    def to_dict(self):

        return asdict(self)