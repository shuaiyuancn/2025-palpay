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
    for collection_name in ["users", "activities", "expenses", "payments", "settlements"]:
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

    # Calculate settlements
    client.post("/settlements/calculate")

    # Get settlements
    settlements_response = client.get(f"/settlements/")
    assert settlements_response.status_code == 200
    settlements = settlements_response.json()

    # Expected outcome: U2 owes U1 5.
    assert len(settlements) == 1
    settlement = settlements[0]
    assert settlement["debtor_id"] == user2_id
    assert settlement["creditor_id"] == user1_id
    assert settlement["amount"] == 5.0

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

    # Calculate settlements
    client.post("/settlements/calculate")

    # Get settlements
    settlements_response = client.get(f"/settlements/")
    assert settlements_response.status_code == 200
    settlements = settlements_response.json()

    expected_settlements = {
        (users["u2_id"], users["u1_id"]): 5.0,
        (users["u4_id"], users["u1_id"]): 20.0,
        (users["u5_id"], users["u1_id"]): 15.0,
        (users["u5_id"], users["u3_id"]): 10.0,
    }

    assert len(settlements) == len(expected_settlements)

    for settlement in settlements:
        key = (settlement["debtor_id"], settlement["creditor_id"])
        assert key in expected_settlements
        assert abs(settlement["amount"] - expected_settlements[key]) < 0.01
