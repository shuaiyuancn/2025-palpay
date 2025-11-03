from fastapi.testclient import TestClient
from src.main import app, db
import pytest
from datetime import datetime

from src.models import User, Activity, Expense
from src.settlement import calculate_settlements

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_firestore():
    # Clear all collections before each test
    for collection_name in ["users", "activities", "expenses", "payments"]:
        for doc in db.collection(collection_name).stream():
            doc.reference.delete()
    yield

def test_simple_split():
    # Scenario: User U1 and User U2 participate in Activity A1. U1 pays 10.
    # Expected Outcome: U2 owes U1 5.

    # Create users
    user1_data = {"name": "U1", "email": "u1@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    user2_data = {"name": "U2", "email": "u2@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    # Create activity
    activity_data = {"name": "A1", "participants": [user1_id, user2_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Create expense
    expense_data = {"activity_id": activity_id, "payer_id": user1_id, "amount": 10.0, "description": "Activity A1 expense"}
    client.post("/expenses/", json=expense_data)

    # Get settlements
    settlements_response = client.get(f"/settlements/{activity_id}")
    assert settlements_response.status_code == 200
    settlements = settlements_response.json()

    # Expected outcome: U2 owes U1 5.
    expected_settlements = {
        user2_id: {
            user1_id: 5.0
        }
    }
    assert settlements == expected_settlements

def test_multiple_activities_no_overlap():
    # Scenario:
    #   - Activity A1: Participants U1, U2. U1 pays 10.
    #   - Activity A2: Participants U2, U3. U2 pays 10.
    # Expected Outcome:
    #   - U2 owes U1 5.
    #   - U3 owes U2 5.

    # Create users
    user1_data = {"name": "U1", "email": "u1@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    user2_data = {"name": "U2", "email": "u2@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    user3_data = {"name": "U3", "email": "u3@example.com"}
    user3_response = client.post("/users/", json=user3_data)
    user3_id = user3_response.json()["id"]

    # Activity A1
    activity1_data = {"name": "A1", "participants": [user1_id, user2_id]}
    activity1_response = client.post("/activities/", json=activity1_data)
    activity1_id = activity1_response.json()["id"]

    expense1_data = {"activity_id": activity1_id, "payer_id": user1_id, "amount": 10.0, "description": "A1 expense"}
    client.post("/expenses/", json=expense1_data)

    # Activity A2
    activity2_data = {"name": "A2", "participants": [user2_id, user3_id]}
    activity2_response = client.post("/activities/", json=activity2_data)
    activity2_id = activity2_response.json()["id"]

    expense2_data = {"activity_id": activity2_id, "payer_id": user2_id, "amount": 10.0, "description": "A2 expense"}
    client.post("/expenses/", json=expense2_data)

    # Get settlements for A1
    settlements1_response = client.get(f"/settlements/{activity1_id}")
    assert settlements1_response.status_code == 200
    settlements1 = settlements1_response.json()
    expected_settlements1 = {
        user2_id: {
            user1_id: 5.0
        }
    }
    assert settlements1 == expected_settlements1

    # Get settlements for A2
    settlements2_response = client.get(f"/settlements/{activity2_id}")
    assert settlements2_response.status_code == 200
    settlements2 = settlements2_response.json()
    expected_settlements2 = {
        user3_id: {
            user2_id: 5.0
        }
    }
    assert settlements2 == expected_settlements2

def test_multiple_activities_with_overlap():
    # Scenario:
    #   - Activity A1: Participants U1, U2, U3. U1 pays 15.
    #   - Activity A2: Participants U2, U3. U2 pays 10.
    # Expected Outcome:
    #   - U2 owes U1 5.
    #   - U3 owes U2 5.
    #   - U3 owes U1 5.

    # Create users
    user1_data = {"name": "U1", "email": "u1@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    user2_data = {"name": "U2", "email": "u2@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    user3_data = {"name": "U3", "email": "u3@example.com"}
    user3_response = client.post("/users/", json=user3_data)
    user3_id = user3_response.json()["id"]

    # Activity A1
    activity1_data = {"name": "A1", "participants": [user1_id, user2_id, user3_id]}
    activity1_response = client.post("/activities/", json=activity1_data)
    activity1_id = activity1_response.json()["id"]

    expense1_data = {"activity_id": activity1_id, "payer_id": user1_id, "amount": 15.0, "description": "A1 expense"}
    client.post("/expenses/", json=expense1_data)

    # Activity A2
    activity2_data = {"name": "A2", "participants": [user2_id, user3_id]}
    activity2_response = client.post("/activities/", json=activity2_data)
    activity2_id = activity2_response.json()["id"]

    expense2_data = {"activity_id": activity2_id, "payer_id": user2_id, "amount": 10.0, "description": "A2 expense"}
    client.post("/expenses/", json=expense2_data)

    # Get settlements for A1
    settlements1_response = client.get(f"/settlements/{activity1_id}")
    assert settlements1_response.status_code == 200
    settlements1 = settlements1_response.json()
    expected_settlements1 = {
        user2_id: {
            user1_id: 5.0
        },
        user3_id: {
            user1_id: 5.0
        }
    }
    assert settlements1 == expected_settlements1

    # Get settlements for A2
    settlements2_response = client.get(f"/settlements/{activity2_id}")
    assert settlements2_response.status_code == 200
    settlements2 = settlements2_response.json()
    expected_settlements2 = {
        user3_id: {
            user2_id: 5.0
        }
    }
    assert settlements2 == expected_settlements2

def test_settlement_no_expenses():
    # Scenario: Activity A1 with U1, U2. No expenses.
    # Expected Outcome: No settlements.

    # Create users
    user1_data = {"name": "U1", "email": "u1@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    user2_data = {"name": "U2", "email": "u2@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    # Create activity
    activity_data = {"name": "A1", "participants": [user1_id, user2_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Get settlements
    settlements_response = client.get(f"/settlements/{activity_id}")
    assert settlements_response.status_code == 200
    settlements = settlements_response.json()

    assert settlements == {}

def test_settlement_one_expense():
    # Scenario: Activity A1 with U1, U2, U3. U1 pays 30.
    # Expected Outcome: U2 owes U1 10, U3 owes U1 10.

    # Create users
    user1_data = {"name": "U1", "email": "u1@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    user2_data = {"name": "U2", "email": "u2@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    user3_data = {"name": "U3", "email": "u3@example.com"}
    user3_response = client.post("/users/", json=user3_data)
    user3_id = user3_response.json()["id"]

    # Create activity
    activity_data = {"name": "A1", "participants": [user1_id, user2_id, user3_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Create expense
    expense_data = {"activity_id": activity_id, "payer_id": user1_id, "amount": 30.0, "description": "Expense 1"}
    client.post("/expenses/", json=expense_data)

    # Get settlements
    settlements_response = client.get(f"/settlements/{activity_id}")
    assert settlements_response.status_code == 200
    settlements = settlements_response.json()

    expected_settlements = {
        user2_id: {
            user1_id: 10.0
        },
        user3_id: {
            user1_id: 10.0
        }
    }
    assert settlements == expected_settlements

def test_settlement_multiple_expenses_different_payers():
    # Scenario: Activity A1 with U1, U2, U3. U1 pays 30, U2 pays 15.
    # Expected Outcome: U3 owes U1 10, U3 owes U2 5, U2 owes U1 5.

    # Create users
    user1_data = {"name": "U1", "email": "u1@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    user2_data = {"name": "U2", "email": "u2@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    user3_data = {"name": "U3", "email": "u3@example.com"}
    user3_response = client.post("/users/", json=user3_data)
    user3_id = user3_response.json()["id"]

    # Create activity
    activity_data = {"name": "A1", "participants": [user1_id, user2_id, user3_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Create expenses
    expense1_data = {"activity_id": activity_id, "payer_id": user1_id, "amount": 30.0, "description": "Expense 1"}
    client.post("/expenses/", json=expense1_data)

    expense2_data = {"activity_id": activity_id, "payer_id": user2_id, "amount": 15.0, "description": "Expense 2"}
    client.post("/expenses/", json=expense2_data)

    # Get settlements
    settlements_response = client.get(f"/settlements/{activity_id}")
    assert settlements_response.status_code == 200
    settlements = settlements_response.json()

    # Total amount = 30 + 15 = 45
    # Fair share per person = 45 / 3 = 15
    # U1 paid 30, owes 15, net +15
    # U2 paid 15, owes 15, net 0
    # U3 paid 0, owes 15, net -15
    # Expected: U3 owes U1 15
    expected_settlements = {
        user3_id: {
            user1_id: 15.0
        }
    }
    assert settlements == expected_settlements

def test_settlement_user_paid_and_owes():
    # Scenario: Activity A1 with U1, U2. U1 pays 20, U2 pays 10.
    # Expected Outcome: U1 owes U2 5.

    # Create users
    user1_data = {"name": "U1", "email": "u1@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    user2_data = {"name": "U2", "email": "u2@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    # Create activity
    activity_data = {"name": "A1", "participants": [user1_id, user2_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Create expenses
    expense1_data = {"activity_id": activity_id, "payer_id": user1_id, "amount": 20.0, "description": "Expense 1"}
    client.post("/expenses/", json=expense1_data)

    expense2_data = {"activity_id": activity_id, "payer_id": user2_id, "amount": 10.0, "description": "Expense 2"}
    client.post("/expenses/", json=expense2_data)

    # Get settlements
    settlements_response = client.get(f"/settlements/{activity_id}")
    assert settlements_response.status_code == 200
    settlements = settlements_response.json()

    # Total amount = 20 + 10 = 30
    # Fair share per person = 30 / 2 = 15
    # U1 paid 20, owes 15, net +5
    # U2 paid 10, owes 15, net -5
    # Expected: U2 owes U1 5
    expected_settlements = {
        user2_id: {
            user1_id: 5.0
        }
    }
    assert settlements == expected_settlements

def test_settlement_with_full_payment():
    # Scenario: Activity A1 with U1, U2. U1 pays 10. U2 pays U1 5.
    # Expected Outcome: No outstanding settlements.

    # Create users
    user1_data = {"name": "U1", "email": "u1@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    user2_data = {"name": "U2", "email": "u2@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    # Create activity
    activity_data = {"name": "A1", "participants": [user1_id, user2_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Create expense
    expense_data = {"activity_id": activity_id, "payer_id": user1_id, "amount": 10.0, "description": "Expense"}
    client.post("/expenses/", json=expense_data)

    # Create payment
    payment_data = {"payer_id": user2_id, "payee_id": user1_id, "amount": 5.0, "timestamp": datetime.now().isoformat()}
    client.post("/payments/", json=payment_data)

    # Get settlements
    settlements_response = client.get(f"/settlements/{activity_id}")
    assert settlements_response.status_code == 200
    settlements = settlements_response.json()

    assert settlements == {}

def test_settlement_with_partial_payment():
    # Scenario: Activity A1 with U1, U2. U1 pays 10. U2 pays U1 3.
    # Expected Outcome: U2 owes U1 2.

    # Create users
    user1_data = {"name": "U1", "email": "u1@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    user2_data = {"name": "U2", "email": "u2@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    # Create activity
    activity_data = {"name": "A1", "participants": [user1_id, user2_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Create expense
    expense_data = {"activity_id": activity_id, "payer_id": user1_id, "amount": 10.0, "description": "Expense"}
    client.post("/expenses/", json=expense_data)

    # Create payment
    payment_data = {"payer_id": user2_id, "payee_id": user1_id, "amount": 3.0, "timestamp": datetime.now().isoformat()}
    client.post("/payments/", json=payment_data)

    # Get settlements
    settlements_response = client.get(f"/settlements/{activity_id}")
    assert settlements_response.status_code == 200
    settlements = settlements_response.json()

    expected_settlements = {
        user2_id: {
            user1_id: 2.0
        }
    }
    assert settlements == expected_settlements

def test_complex_scenario_with_5_users():
    # Create users
    users = {}
    for i in range(1, 6):
        user_data = {"name": f"U{i}", "email": f"u{i}@example.com"}
        response = client.post("/users/", json=user_data)
        users[f"u{i}_id"] = response.json()["id"]

    # Activity A1
    activity1_data = {"name": "A1", "participants": list(users.values())}
    activity1_response = client.post("/activities/", json=activity1_data)
    activity1_id = activity1_response.json()["id"]

    expense1_data = {"activity_id": activity1_id, "payer_id": users["u1_id"], "amount": 100.0}
    client.post("/expenses/", json=expense1_data)

    expense2_data = {"activity_id": activity1_id, "payer_id": users["u2_id"], "amount": 50.0}
    client.post("/expenses/", json=expense2_data)

    # Activity A2
    activity2_data = {"name": "A2", "participants": [users["u1_id"], users["u2_id"], users["u3_id"]]}
    activity2_response = client.post("/activities/", json=activity2_data)
    activity2_id = activity2_response.json()["id"]

    expense3_data = {"activity_id": activity2_id, "payer_id": users["u3_id"], "amount": 60.0}
    client.post("/expenses/", json=expense3_data)

    # Payments
    payment1_data = {"payer_id": users["u4_id"], "payee_id": users["u1_id"], "amount": 10.0, "timestamp": datetime.now().isoformat()}
    client.post("/payments/", json=payment1_data)

    payment2_data = {"payer_id": users["u5_id"], "payee_id": users["u2_id"], "amount": 5.0, "timestamp": datetime.now().isoformat()}
    client.post("/payments/", json=payment2_data)

    # Get settlements for A1
    settlements1_response = client.get(f"/settlements/{activity1_id}")
    assert settlements1_response.status_code == 200
    settlements1 = settlements1_response.json()
    expected_settlements1 = {
        users["u3_id"]: {users["u1_id"]: 30.0},
        users["u4_id"]: {users["u1_id"]: 20.0},
        users["u5_id"]: {users["u1_id"]: 10.0, users["u2_id"]: 15.0},
    }
    assert settlements1 == expected_settlements1

    # Get settlements for A2
    settlements2_response = client.get(f"/settlements/{activity2_id}")
    assert settlements2_response.status_code == 200
    settlements2 = settlements2_response.json()
    expected_settlements2 = {
        users["u1_id"]: {users["u3_id"]: 20.0},
        users["u2_id"]: {users["u3_id"]: 20.0},
    }
    assert settlements2 == expected_settlements2