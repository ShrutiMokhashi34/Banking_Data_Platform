"""
===============================================================================
Customer Address Data Model
===============================================================================
"""

from dataclasses import dataclass, asdict
from datetime import date


@dataclass(slots=True)
class Address:

    address_id: str

    customer_id: str

    address_type: str

    address_line1: str

    address_line2: str

    city: str

    state: str

    postal_code: str

    country: str

    is_current: bool

    effective_date: date

    expiry_date: date | None

    def to_dict(self):

        return asdict(self)