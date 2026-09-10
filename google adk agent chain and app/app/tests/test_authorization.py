from app.auth.authorization import (
    can_access_branch_employee_data,
    can_access_customer,
    can_access_pipeline,
    can_view_employee,
)


# ============================================================
# Test users
# ============================================================

customer = {
    "user_type": "CUSTOMER",
    "user_id": "CUST00005001",
    "customer_id": "CUST00005001",
    "display_name": "Test Customer",
}


relationship_manager = {
    "user_type": "EMPLOYEE",
    "user_id": "EMP00000100",
    "display_name": "Test RM",
    "role": "Relationship Manager",
    "branch_id": "BR00001",
}


assistant_manager = {
    "user_type": "EMPLOYEE",
    "user_id": "EMP00000200",
    "display_name": "Test Assistant Manager",
    "role": "Assistant Manager",
    "branch_id": "BR00001",
}


manager = {
    "user_type": "EMPLOYEE",
    "user_id": "EMP00000300",
    "display_name": "Test Manager",
    "role": "Manager",
    "branch_id": "BR00002",
}


# ============================================================
# Customer tests
# ============================================================

def test_customer_can_access_own_data():

    assert can_access_customer(
        customer,
        "CUST00005001"
    )


def test_customer_cannot_access_other_customer():

    assert not can_access_customer(
        customer,
        "CUST00005002"
    )


def test_customer_cannot_access_pipeline():

    assert not can_access_pipeline(customer)


# ============================================================
# Employee tests
# ============================================================

def test_relationship_manager_cannot_access_pipeline():

    assert not can_access_pipeline(
        relationship_manager
    )


def test_assistant_manager_cannot_access_pipeline():

    assert not can_access_pipeline(
        assistant_manager
    )


def test_manager_can_access_pipeline():

    assert can_access_pipeline(
        manager
    )


def test_relationship_manager_can_view_own_employee():

    assert can_view_employee(
        relationship_manager,
        "EMP00000100"
    )


def test_relationship_manager_cannot_view_other_employee():

    assert not can_view_employee(
        relationship_manager,
        "EMP00000200"
    )


def test_manager_can_view_any_employee():

    assert can_view_employee(
        manager,
        "EMP00000200"
    )


# ============================================================
# Branch tests
# ============================================================

def test_assistant_manager_can_access_own_branch():

    assert can_access_branch_employee_data(
        assistant_manager,
        "BR00001"
    )


def test_assistant_manager_cannot_access_other_branch():

    assert not can_access_branch_employee_data(
        assistant_manager,
        "BR00002"
    )


def test_manager_can_access_any_branch():

    assert can_access_branch_employee_data(
        manager,
        "BR00099"
    )