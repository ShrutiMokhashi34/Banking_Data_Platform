"""
===============================================================================
KYC Data Model
===============================================================================
"""

from dataclasses import dataclass, asdict
from datetime import date


@dataclass(slots=True)
class KYC:

    customer_id: str

    pan_number: str

    aadhaar_number: str

    pan_verified: bool

    aadhaar_verified: bool

    address_verified: bool

    kyc_status: str

    verification_date: date | None

    def to_dict(self):

        return asdict(self)