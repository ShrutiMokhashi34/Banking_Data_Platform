"""
Organization Domain Data Generator

Generates synthetic data for:

    1. Branches
    2. Employees

"""

from __future__ import annotations

# =====================================================================
# Standard Library
# =====================================================================

import random
from datetime import datetime

# =====================================================================
# Third Party Libraries
# =====================================================================

import pandas as pd
from faker import Faker

# =====================================================================
# Project Configuration
# =====================================================================

from config.config import (
    RANDOM_SEED,
    NUM_BRANCHES,
    NUM_EMPLOYEES,
    BRANCHES_FILE,
    EMPLOYEES_FILE,
)

from config.constants import (
    COUNTRY,
    SOURCE_SYSTEM,
    DEPARTMENTS,
    DESIGNATIONS,
    EMPLOYEE_STATUS,
    DESIGNATIONS,
)

# =====================================================================
# Models
# =====================================================================

from models.org_branch import Branch
from models.org_employees import Employee

# =====================================================================
# Utilities
# =====================================================================

from generators.id_generator import (
    branch_id,
    employee_id,
)

from generators.utils import (
    Geography
)

# =====================================================================
# Logging
# =====================================================================

from config.logging_config import setup_logger

# =====================================================================
# Organization Generator
# =====================================================================

class OrganizationGenerator:
    """
    Synthetic Organization Data Generator.
    """

    def __init__(self) -> None:

        self.logger = setup_logger(__name__)

        self.geo = Geography()
        
        self.fake = Faker("en_IN")

        random.seed(RANDOM_SEED)

        self.fake.seed_instance(RANDOM_SEED)

        # ==============================================================
        # Generated Objects
        # ==============================================================

        self.branches: list[Branch] = []

        self.employees: list[Employee] = []

        self.logger.info(
            "Organization Generator initialized successfully."
        )
        
    def branches_df(self) -> pd.DataFrame:
        """
        Return Branches dataframe.
        """

        return pd.DataFrame(
            [branch.to_dict() for branch in self.branches]
        )
        
# =====================================================================
# Branch Helper Methods
# =====================================================================

    def _generate_branch_name(
        self,
        city: str,
        existing_names: set[str],
    ) -> str:
        """
        Generate a unique branch name.
        """
    
        suffix = random.choice(
            [
                "Main Branch",
                "City Branch",
                "Retail Branch",
                "Corporate Branch",
                "Commercial Branch",
                "Business Centre",
                "Regional Office",
                "Financial Centre",
            ]
        )
    
        branch_name = f"{city} {suffix}"
    
        while branch_name in existing_names:
    
            branch_name = (
                f"{city} {suffix} "
                f"{random.randint(100,999)}"
            )
    
        existing_names.add(branch_name)
    
        return branch_name
    
    
    def _generate_opened_date(self):
        """
        Generate branch opening date.
        """
    
        return self.fake.date_between(
            start_date="-30y",
            end_date="-1y",
        )
    
    
    def _generate_branch_location(self) -> dict:
        """
        Generate a valid branch location.
        """
    
        return self.geo.random_location()
            
    def employees_df(self) -> pd.DataFrame:
        """
        Return Employees dataframe.
        """
    
        return pd.DataFrame(
            [employee.to_dict() for employee in self.employees]
        )
            
# =====================================================================
# Generate Branches
# =====================================================================

    def generate_branches(self) -> None:
        """
        Generate Branch data.
        """
    
        self.logger.info(
            "Generating Branches..."
        )
    
        existing_branch_names = set()
    
        for _ in range(NUM_BRANCHES):
    
            location = self._generate_branch_location()
    
            branch = Branch(
    
                branch_id=branch_id(),
    
                branch_name=self._generate_branch_name(
                    location["city"],
                    existing_branch_names,
                ),
    
                city=location["city"],
    
                state=location["state"],
    
                country=COUNTRY,
    
                zip_code=str(location["pincode"]),
    
                manager_employee_id=None,
    
                opened_date=self._generate_opened_date(),
    
                created_at=datetime.now(),
    
                updated_at=None,
    
                source_system=SOURCE_SYSTEM,
    
            )
    
            self.branches.append(branch)
    
        self.logger.info(
            f"{len(self.branches)} branches generated successfully."
        )
        
# =====================================================================
# Validate Branches
# =====================================================================

    def validate_branches(self) -> bool:
        """
        Validate Branch dataset.
        """
    
        self.logger.info(
            "Validating Branches..."
        )
    
        df = self.branches_df()
    
        if df.empty:
    
            self.logger.error(
                "Branch dataframe is empty."
            )
    
            return False
    
        if df["branch_id"].duplicated().any():
    
            self.logger.error(
                "Duplicate Branch IDs detected."
            )
    
            return False
    
        if df["branch_name"].duplicated().any():
    
            self.logger.error(
                "Duplicate Branch Names detected."
            )
    
            return False
    
        mandatory_columns = [
    
            "branch_id",
    
            "branch_name",
    
            "city",
    
            "state",
    
            "country",
    
            "zip_code",
    
            "opened_date",
    
        ]
    
        for column in mandatory_columns:
    
            if df[column].isnull().any():
    
                self.logger.error(
                    f"Null values found in {column}."
                )
    
                return False
    
        self.logger.info(
            "Branch validation completed successfully."
        )
    
        return True
        
# =====================================================================
# Export Branches
# =====================================================================

    def export_branches(self) -> None:
        """
        Export Branch dataset.
        """
    
        self.logger.info(
            "Exporting Branches..."
        )
    
        self.branches_df().to_csv(
    
            BRANCHES_FILE,
    
            index=False,
    
        )
    
        self.logger.info(
            f"Branches exported successfully to {BRANCHES_FILE}"
        )

# =====================================================================
# Employee Helper Methods
# =====================================================================

    def _generate_designation(self) -> str:
        """
        Generate employee designation.
        """
    
        designation_weights = {
    
            "Associate": 35,
    
            "Senior Associate": 25,
    
            "Officer": 15,
    
            "Assistant Manager": 12,
    
            "Manager": 8,
    
            "Senior Manager": 5,
    
        }
    
        return random.choices(
    
            list(designation_weights.keys()),
    
            weights=list(designation_weights.values()),
    
            k=1,
    
        )[0]
    
    
    def _generate_department(self) -> str:
        """
        Generate employee department.
        """
    
        return random.choice(DEPARTMENTS)
    
    
    def _generate_employee_status(self) -> str:
        """
        Generate employee status.
        """
    
        return random.choices(
    
            EMPLOYEE_STATUS,
    
            weights=[90, 5, 5, 5, 5, 5],
    
            k=1,
    
        )[0]
    
    
    def _generate_salary(
        self,
        designation: str,
    ) -> float:
        """
        Generate salary based on designation.
        """
    
        salary_ranges = {
    
            "Associate": (350000, 600000),
    
            "Senior Associate": (600000, 900000),
    
            "Officer": (700000, 1000000),
    
            "Assistant Manager": (900000, 1400000),
    
            "Manager": (1400000, 2000000),
    
            "Senior Manager": (2000000, 3500000),
    
        }
    
        minimum, maximum = salary_ranges[designation]
    
        return round(
            random.uniform(minimum, maximum),
            2,
        )
    
    
    def _generate_hire_date(self):
        """
        Generate employee hire date.
        """
    
        return self.fake.date_between(
    
            start_date="-20y",
    
            end_date="-30d",
    
        )
        
# =====================================================================
# Generate Employees
# =====================================================================

    def generate_employees(self) -> None:
        """
        Generate Employee data.
        """
    
        self.logger.info(
            "Generating Employees..."
        )
    
        if not self.branches:
    
            raise ValueError(
                "Branches must be generated before employees."
            )

    # -----------------------------------------------------------------
    # Ensure every branch has at least one employee
    # -----------------------------------------------------------------

        branch_pool = self.branches.copy()
    
        while len(branch_pool) < NUM_EMPLOYEES:
    
            branch_pool.extend(self.branches)
    
        random.shuffle(branch_pool)
    
        branch_pool = branch_pool[:NUM_EMPLOYEES]

    # -----------------------------------------------------------------
    # Generate Employees
    # -----------------------------------------------------------------

        for branch in branch_pool:
    
            designation = self._generate_designation()
    
            employee = Employee(
    
                employee_id=employee_id(),
    
                branch_id=branch.branch_id,
    
                first_name=self.fake.first_name(),
    
                last_name=self.fake.last_name(),
    
                designation=designation,
    
                department=self._generate_department(),
    
                hire_date=self._generate_hire_date(),
    
                salary=self._generate_salary(
                    designation
                ),
    
                employee_status=self._generate_employee_status(),
    
                created_at=datetime.now(),
    
                updated_at=None,
    
                source_system=SOURCE_SYSTEM,
    
            )
    
            self.employees.append(employee)
    
        self.logger.info(
            f"{len(self.employees)} employees generated successfully."
        )
        
# =====================================================================
# Validate Employees
# =====================================================================

    def validate_employees(self) -> bool:
        """
        Validate Employee dataset.
        """
    
        self.logger.info(
            "Validating Employees..."
        )
    
        df = self.employees_df()
    
        if df.empty:
    
            self.logger.error(
                "Employee dataframe is empty."
            )
    
            return False
    
        if df["employee_id"].duplicated().any():
    
            self.logger.error(
                "Duplicate Employee IDs detected."
            )
    
            return False
    
        valid_branch_ids = {
    
            branch.branch_id
    
            for branch in self.branches
    
        }
    
        if (~df["branch_id"].isin(valid_branch_ids)).any():
    
            self.logger.error(
                "Invalid Branch IDs detected."
            )
    
            return False
    
        if (df["salary"] <= 0).any():
    
            self.logger.error(
                "Invalid salary values detected."
            )
    
            return False
    
        mandatory_columns = [
    
            "employee_id",
    
            "branch_id",
    
            "first_name",
    
            "last_name",
    
            "designation",
    
            "department",
    
            "hire_date",
    
            "salary",
    
            "employee_status",
    
        ]
    
        for column in mandatory_columns:
    
            if df[column].isnull().any():
    
                self.logger.error(
                    f"Null values found in {column}."
                )
    
                return False
    
        self.logger.info(
            "Employee validation completed successfully."
        )
    
        return True
        
# =====================================================================
# Export Employees
# =====================================================================

    def export_employees(self) -> None:
        """
        Export Employee dataset.
        """
    
        self.logger.info(
            "Exporting Employees..."
        )
    
        self.employees_df().to_csv(
    
            EMPLOYEES_FILE,
    
            index=False,
    
        )
    
        self.logger.info(
            f"Employees exported successfully to {EMPLOYEES_FILE}"
        )
        
# =====================================================================
# Branch Manager Assignment
# =====================================================================

    def assign_branch_managers(self) -> None:
        """
        Assign a manager to each branch.
        """
    
        self.logger.info(
            "Assigning Branch Managers..."
        )
    
        for branch in self.branches:
    
            eligible_employees = [
    
                employee
    
                for employee in self.employees
    
                if (
                    employee.branch_id == branch.branch_id
                    and employee.employee_status == "ACTIVE"
                    and employee.designation in [
                        "Manager",
                        "Senior Manager",
                    ]
                )
    
            ]
    
            # If no managers exist, promote one active employee
    
            if not eligible_employees:
    
                eligible_employees = [
    
                    employee
    
                    for employee in self.employees
    
                    if (
                        employee.branch_id == branch.branch_id
                        and employee.employee_status == "ACTIVE"
                    )
    
                ]
    
                if not eligible_employees:
    
                    continue
    
                manager = random.choice(
                    eligible_employees
                )
    
                manager.designation = "Manager"
    
            else:
    
                manager = random.choice(
                    eligible_employees
                )
    
            branch.manager_employee_id = manager.employee_id
    
        self.logger.info(
            "Branch Managers assigned successfully."
        )
        
# =====================================================================
# Validate All
# =====================================================================

    def validate_all(self) -> bool:
        """
        Validate all generated datasets.
        """
    
        self.logger.info(
            "Running Validation..."
        )
    
        validations = [
    
            self.validate_branches(),
    
            self.validate_employees(),
    
        ]
    
        if all(validations):
    
            self.logger.info(
                "Validation Successful."
            )
    
            return True
    
        self.logger.error(
            "Validation Failed."
        )
    
        return False
        
# =====================================================================
# Export All
# =====================================================================

    def export_all(self) -> None:
        """
        Export all Organization datasets.
        """
    
        self.logger.info(
            "Exporting datasets..."
        )
    
        self.export_branches()
    
        self.export_employees()
    
        self.logger.info(
            "Export completed successfully."
        )
        
    def summary(self) -> None:
        """
        Display Organization generation summary.
        """

        self.logger.info("=" * 60)

        self.logger.info("Organization Generation Summary")

        self.logger.info(
            f"Branches Generated  : {len(self.branches)}"
        )

        self.logger.info(
            f"Employees Generated : {len(self.employees)}"
        )

        self.logger.info("=" * 60)
        
# =====================================================================
# Ppeline Execution
# =====================================================================

    def run(self) -> None:
        """
        Execute Organization Generator.
        """
    
        try:
    
            self.logger.info("=" * 80)
    
            self.logger.info(
                "Starting Organization Generator..."
            )
    
            self.generate_branches()
    
            self.generate_employees()
    
            self.assign_branch_managers()
    
            self.summary()
    
            if not self.validate_all():
    
                raise ValueError(
                    "Validation Failed."
                )
    
            self.export_all()
    
            self.logger.info(
                "Organization Generator completed successfully."
            )
    
            self.logger.info("=" * 80)
    
        except Exception as ex:
    
            self.logger.exception(ex)
    
            raise
            
if __name__ == "__main__":
    print("Starting Org Generator...")
    
    generator = OrganizationGenerator()
    
    print("Generator created.")
    
    generator.run()
    
    print("Pipeline finished.")