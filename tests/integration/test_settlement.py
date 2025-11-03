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
