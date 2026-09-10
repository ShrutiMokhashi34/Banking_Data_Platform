"""
Authorization rules for the Banking Data Platform.

Authorization is enforced server-side and must not depend on
instructions given to the LLM or claims made by the user.
"""


# ============================================================
# Valid employee roles
# ============================================================

VALID_EMPLOYEE_ROLES = {
    "associate",
    "assistant manager",
    "senior associate",
    "officer",
    "senior manager",
    "manager",
}


# ============================================================
# Roles with full access
# ============================================================

FULL_ACCESS_ROLES = {
    "manager",
    "senior manager",
    "officer",
}


# ============================================================
# Branch-level employee access
# ============================================================

BRANCH_EMPLOYEE_ACCESS_ROLE = "assistant manager"


# ============================================================
# Employee statuses that have NO data access
# ============================================================

INACTIVE_EMPLOYEE_STATUSES = {
    "resigned",
    "terminated",
    "retired",
}


# ============================================================
# Normalization helpers
# ============================================================

def normalize_role(role: str | None) -> str:
    """
    Normalize an employee designation.

    Handles:
    - None
    - leading/trailing spaces
    - capitalization differences
    """

    if not role:
        return ""

    return role.strip().lower()


def normalize_status(status: str | None) -> str:
    """
    Normalize employee/customer status.
    """

    if not status:
        return ""

    return status.strip().lower()


# ============================================================
# User-type checks
# ============================================================

def is_customer(user: dict) -> bool:
    """
    Return True if the authenticated user is a customer.
    """

    return (
        user.get("user_type", "").strip().upper()
        == "CUSTOMER"
    )


def is_employee(user: dict) -> bool:
    """
    Return True if the authenticated user is an employee.
    """

    return (
        user.get("user_type", "").strip().upper()
        == "EMPLOYEE"
    )


# ============================================================
# Employee status
# ============================================================

def is_active_employee(user: dict) -> bool:
    """
    Return True only if the employee is active.

    Employees with the following statuses have no data access:

        Resigned
        Terminated
        Retired

    The check is intentionally fail-closed for employee records
    with an unknown or missing status.
    """

    if not is_employee(user):
        return False

    status = normalize_status(
        user.get("employee_status")
    )

    # Explicitly deny known inactive statuses.
    if status in INACTIVE_EMPLOYEE_STATUSES:
        return False

    # Fail closed if the employee status is missing/unknown.
    if not status:
        return False

    # Only "active" employees are considered active.
    return status == "active"


# ============================================================
# Employee role validation
# ============================================================

def has_valid_employee_role(user: dict) -> bool:
    """
    Return True if the employee has a recognized designation.
    """

    if not is_employee(user):
        return False

    role = normalize_role(
        user.get("role")
    )

    return role in VALID_EMPLOYEE_ROLES


# ============================================================
# Full employee access
# ============================================================

def has_full_employee_access(user: dict) -> bool:
    """
    Manager, Senior Manager and Officer have full employee
    and permitted domain access.

    The employee must also:
        - be active
        - have a valid designation
    """

    if not is_active_employee(user):
        return False

    if not has_valid_employee_role(user):
        return False

    role = normalize_role(
        user.get("role")
    )

    return role in FULL_ACCESS_ROLES


# ============================================================
# Pipeline / Data Engineering access
# ============================================================

def can_access_pipeline(user: dict) -> bool:
    """
    Determine whether the employee can access pipeline /
    data engineering information.

    Allowed:
        - Manager
        - Senior Manager
        - Officer

    Denied:
        - Customer
        - Associate
        - Senior Associate
        - Assistant Manager
        - Resigned employees
        - Terminated employees
        - Retired employees
        - Unknown/invalid roles
    """

    if not is_active_employee(user):
        return False

    return has_full_employee_access(user)


# ============================================================
# Employee data access
# ============================================================

def can_view_employee(
    requesting_user: dict,
    target_employee_id: str,
) -> bool:
    """
    Determine whether the requesting user can view
    the specified employee's data.

    Rules:

        Manager / Senior Manager / Officer
            -> all employee data

        Assistant Manager
            -> branch-level employee access
               (target branch must be checked by the
                data-access tool)

        Associate / Senior Associate
            -> own employee record only

        Customer
            -> no employee data

        Resigned / Terminated / Retired
            -> no employee data
    """

    if not is_active_employee(requesting_user):
        return False

    if not has_valid_employee_role(requesting_user):
        return False

    requester_id = (
        requesting_user
        .get("user_id", "")
        .strip()
        .upper()
    )

    target_id = (
        target_employee_id
        .strip()
        .upper()
    )

    # Manager / Senior Manager / Officer
    # can view all employee data.
    if has_full_employee_access(requesting_user):
        return True

    role = normalize_role(
        requesting_user.get("role")
    )

    # Assistant Manager is permitted to request
    # employee data, but the actual tool must verify
    # that the target employee belongs to the same branch.
    if role == BRANCH_EMPLOYEE_ACCESS_ROLE:
        return True

    # Associate / Senior Associate:
    # own employee record only.
    return requester_id == target_id


# ============================================================
# Customer data access
# ============================================================

def can_access_customer(
    requesting_user: dict,
    target_customer_id: str,
) -> bool:
    """
    Determine whether the requesting user can access
    the specified customer's data.

    Rules:

        Customer
            -> own customer data only

        Active Manager / Senior Manager / Officer
            -> customer data allowed

        Other active employees
            -> customer/business-domain access allowed
               according to application/tool rules

        Resigned / Terminated / Retired employee
            -> no data access

        Unknown user type
            -> denied
    """

    target_id = (
        target_customer_id
        .strip()
        .upper()
    )

    # --------------------------------------------------------
    # Customer
    # --------------------------------------------------------

    if is_customer(requesting_user):

        requester_id = (
            requesting_user
            .get(
                "customer_id",
                requesting_user.get("user_id", ""),
            )
            .strip()
            .upper()
        )

        # Customer can only access their own data.
        return requester_id == target_id

    # --------------------------------------------------------
    # Employee
    # --------------------------------------------------------

    if is_employee(requesting_user):

        # Resigned / terminated / retired employees
        # cannot access any data.
        if not is_active_employee(requesting_user):
            return False

        # Unknown/invalid employee roles are denied.
        if not has_valid_employee_role(requesting_user):
            return False

        return True

    # --------------------------------------------------------
    # Unknown user type
    # --------------------------------------------------------

    return False


# ============================================================
# Branch employee data access
# ============================================================

def can_access_branch_employee_data(
    requesting_user: dict,
    target_branch_id: str,
) -> bool:
    """
    Determine whether the requesting user can access
    employee data for a branch.

    Rules:

        Manager / Senior Manager / Officer
            -> all branches

        Assistant Manager
            -> own branch only

        Associate / Senior Associate
            -> denied through branch-level access

        Customer
            -> denied

        Resigned / Terminated / Retired
            -> denied
    """

    if not is_active_employee(requesting_user):
        return False

    if not has_valid_employee_role(requesting_user):
        return False

    # Full-access roles can access all branches.
    if has_full_employee_access(requesting_user):
        return True

    role = normalize_role(
        requesting_user.get("role")
    )

    if role == BRANCH_EMPLOYEE_ACCESS_ROLE:

        requester_branch = (
            requesting_user
            .get("branch_id", "")
            .strip()
            .upper()
        )

        target_branch = (
            target_branch_id
            .strip()
            .upper()
        )

        # Assistant Manager can only access
        # their own branch.
        return requester_branch == target_branch

    return False