"""
===============================================================================
Exchange Rate Data Model
===============================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date


@dataclass(slots=True)
class ExchangeRate:

    rate_date: date

    currency: str

    currency_symbol: str

    rate_to_inr: float

    source: str

    def to_dict(self):

        return asdict(self)
