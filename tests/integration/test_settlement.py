from fastapi.testclient import TestClient
from src.main import app, db
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_firestore():
    # Clear all collections before each test
    for collection_name in ["users", "activities", "expenses"]:
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