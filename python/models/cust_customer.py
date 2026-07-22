"""
===============================================================================
Customer Data Model
===============================================================================
"""

from dataclasses import dataclass, asdict
from datetime import date, datetime


@dataclass(slots=True)
class Customer:

    customer_id: str

    first_name: str

    last_name: str

    dob: date

    gender: str

    email: str

    phone: str

    occupation: str

    annual_income: float

    customer_since: date

    risk_rating: str

    customer_status: str

    created_at: datetime

    updated_at: datetime

    source_system: str

    def __post_init__(self):

        if self.annual_income < 0:
            raise ValueError("Annual income cannot be negative.")

    def to_dict(self):

        return asdict(self)