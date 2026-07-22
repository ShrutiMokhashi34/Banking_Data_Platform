"""
Model for Employee entity.
"""

from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Optional


@dataclass(slots=True)
class Employee:
    """
    Represents a bank employee.
    """

    employee_id: str

    branch_id: str

    first_name: str

    last_name: str

    designation: str

    department: str

    hire_date: date

    salary: float

    employee_status: str

    created_at: datetime

    updated_at: Optional[datetime]

    source_system: str

    def to_dict(self) -> dict:
        """
        Convert Employee object to dictionary.
        """
        return asdict(self)