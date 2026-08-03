"""
===============================================================================
Holiday Calendar Data Model
===============================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date


@dataclass(slots=True)
class Holiday:

    holiday_id: str

    holiday_date: date

    country: str

    state: str

    holiday_name: str

    holiday_type: str

    def to_dict(self):

        return asdict(self)
