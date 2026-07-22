"""
Model for Branch entity.
"""

from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Optional


@dataclass(slots=True)
class Branch:
    """
    Represents a bank branch.
    """

    branch_id: str

    branch_name: str

    city: str

    state: str

    country: str

    zip_code: str

    manager_employee_id: Optional[str]

    opened_date: date

    created_at: datetime

    updated_at: Optional[datetime]

    source_system: str

    def to_dict(self) -> dict:
        """
        Convert Branch object to dictionary.
        """
        return asdict(self)