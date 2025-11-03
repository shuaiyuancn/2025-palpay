from fastapi.testclient import TestClient
from src.main import app, db
import pytest
from datetime import datetime, timedelta

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_firestore():
    # Clear all collections before each test
    for collection_name in ["users", "activities", "expenses", "audit_logs"]:
        for doc in db.collection(collection_name).stream():
            doc.reference.delete()
    yield

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "PalPay"}

def test_create_user():
    user_data = {"name": "John Doe", "email": "john.doe@example.com"}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user["name"] == "John Doe"
    assert created_user["email"] == "john.doe@example.com"
    assert "id" in created_user

def test_get_user():
    # First, create a user
    user_data = {"name": "Jane Doe", "email": "jane.doe@example.com"}
    create_response = client.post("/users/", json=user_data)
    created_user_id = create_response.json()["id"]

    # Then, get the user
    get_response = client.get(f"/users/{created_user_id}")
    assert get_response.status_code == 200
    retrieved_user = get_response.json()
    assert retrieved_user["id"] == created_user_id
    assert retrieved_user["name"] == "Jane Doe"

def test_get_all_users():
    # Create a few users
    client.post("/users/", json={"name": "Alice", "email": "alice@example.com"})
    client.post("/users/", json={"name": "Bob", "email": "bob@example.com"})

    response = client.get("/users/")
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2
    user_names = [user["name"] for user in users]
    assert "Alice" in user_names
    assert "Bob" in user_names

def test_update_user():
    # First, create a user
    user_data = {"name": "Original Name", "email": "original@example.com"}
    create_response = client.post("/users/", json=user_data)
    user_id = create_response.json()["id"]

    # Update the user
    updated_user_data = {"id": user_id, "name": "Updated Name", "email": "updated@example.com"}
    update_response = client.put(f"/users/{user_id}", json=updated_user_data)
    assert update_response.status_code == 200
    updated_user = update_response.json()
    assert updated_user["name"] == "Updated Name"
    assert updated_user["email"] == "updated@example.com"

    # Verify the update by getting the user
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    retrieved_user = get_response.json()
    assert retrieved_user["name"] == "Updated Name"

def test_delete_user():
    # First, create a user
    user_data = {"name": "User to Delete", "email": "delete@example.com"}
    create_response = client.post("/users/", json=user_data)
    user_id = create_response.json()["id"]

    # Delete the user
    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 204

    # Verify deletion by trying to get the user
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 404

# Activity Tests
def test_create_activity():
    activity_data = {"name": "Weekend Trip", "participants": []}
    response = client.post("/activities/", json=activity_data)
    assert response.status_code == 200
    created_activity = response.json()
    assert created_activity["name"] == "Weekend Trip"
    assert created_activity["participants"] == []
    assert "id" in created_activity

def test_get_activity():
    # First, create an activity
    activity_data = {"name": "Dinner", "participants": []}
    create_response = client.post("/activities/", json=activity_data)
    created_activity_id = create_response.json()["id"]

    # Then, get the activity
    get_response = client.get(f"/activities/{created_activity_id}")
    assert get_response.status_code == 200
    retrieved_activity = get_response.json()
    assert retrieved_activity["id"] == created_activity_id
    assert retrieved_activity["name"] == "Dinner"

def test_get_all_activities():
    # Create a few activities
    client.post("/activities/", json={"name": "Concert", "participants": []})
    client.post("/activities/", json={"name": "Movie", "participants": []})

    response = client.get("/activities/")
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 2
    activity_names = [activity["name"] for activity in activities]
    assert "Concert" in activity_names
    assert "Movie" in activity_names

def test_update_activity():
    # First, create an activity
    activity_data = {"name": "Original Activity", "participants": ["user_a"]}
    create_response = client.post("/activities/", json=activity_data)
    activity_id = create_response.json()["id"]

    # Update the activity
    updated_activity_data = {"id": activity_id, "name": "Updated Activity", "participants": ["user_a", "user_b"]}
    update_response = client.put(f"/activities/{activity_id}", json=updated_activity_data)
    assert update_response.status_code == 200
    updated_activity = update_response.json()
    assert updated_activity["name"] == "Updated Activity"
    assert updated_activity["participants"] == ["user_a", "user_b"]

    # Verify the update by getting the activity
    get_response = client.get(f"/activities/{activity_id}")
    assert get_response.status_code == 200
    retrieved_activity = get_response.json()
    assert retrieved_activity["name"] == "Updated Activity"

def test_delete_activity():
    # First, create an activity
    activity_data = {"name": "Activity to Delete", "participants": []}
    create_response = client.post("/activities/", json=activity_data)
    activity_id = create_response.json()["id"]

    # Delete the activity
    delete_response = client.delete(f"/activities/{activity_id}")
    assert delete_response.status_code == 204

    # Verify deletion by trying to get the activity
    get_response = client.get(f"/activities/{activity_id}")
    assert get_response.status_code == 404

# Expense Tests
def test_create_expense():
    # First, create a user and an activity for the expense
    user_data = {"name": "Payer User", "email": "payer@example.com"}
    user_response = client.post("/users/", json=user_data)
    payer_id = user_response.json()["id"]

    activity_data = {"name": "Test Activity", "participants": [payer_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    expense_data = {"activity_id": activity_id, "payer_id": payer_id, "amount": 50.0, "description": "Groceries"}
    response = client.post("/expenses/", json=expense_data)
    assert response.status_code == 200
    created_expense = response.json()
    assert created_expense["activity_id"] == activity_id
    assert created_expense["payer_id"] == payer_id
    assert created_expense["amount"] == 50.0
    assert "id" in created_expense

def test_get_expense():
    # First, create a user and an activity for the expense
    user_data = {"name": "Payer User 2", "email": "payer2@example.com"}
    user_response = client.post("/users/", json=user_data)
    payer_id = user_response.json()["id"]

    activity_data = {"name": "Test Activity 2", "participants": [payer_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Create an expense
    expense_data = {"activity_id": activity_id, "payer_id": payer_id, "amount": 25.0, "description": "Dinner"}
    create_response = client.post("/expenses/", json=expense_data)
    created_expense_id = create_response.json()["id"]

    # Then, get the expense
    get_response = client.get(f"/expenses/{created_expense_id}")
    assert get_response.status_code == 200
    retrieved_expense = get_response.json()
    assert retrieved_expense["id"] == created_expense_id
    assert retrieved_expense["description"] == "Dinner"

def test_get_all_expenses():
    # Create users and activities for expenses
    user1_data = {"name": "User A", "email": "userA@example.com"}
    user1_response = client.post("/users/", json=user1_data)
    user1_id = user1_response.json()["id"]

    activity1_data = {"name": "Activity A", "participants": [user1_id]}
    activity1_response = client.post("/activities/", json=activity1_data)
    activity1_id = activity1_response.json()["id"]

    user2_data = {"name": "User B", "email": "userB@example.com"}
    user2_response = client.post("/users/", json=user2_data)
    user2_id = user2_response.json()["id"]

    activity2_data = {"name": "Activity B", "participants": [user2_id]}
    activity2_response = client.post("/activities/", json=activity2_data)
    activity2_id = activity2_response.json()["id"]

    # Create a few expenses
    client.post("/expenses/", json={"activity_id": activity1_id, "payer_id": user1_id, "amount": 10.0, "description": "Coffee"})
    client.post("/expenses/", json={"activity_id": activity2_id, "payer_id": user2_id, "amount": 20.0, "description": "Lunch"})

    response = client.get("/expenses/")
    assert response.status_code == 200
    expenses = response.json()
    assert len(expenses) == 2
    expense_descriptions = [expense["description"] for expense in expenses]
    assert "Coffee" in expense_descriptions
    assert "Lunch" in expense_descriptions

def test_update_expense():
    # First, create a user and an activity for the expense
    user_data = {"name": "Payer User 3", "email": "payer3@example.com"}
    user_response = client.post("/users/", json=user_data)
    payer_id = user_response.json()["id"]

    activity_data = {"name": "Test Activity 3", "participants": [payer_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Create an expense
    expense_data = {"activity_id": activity_id, "payer_id": payer_id, "amount": 100.0, "description": "Original Expense"}
    create_response = client.post("/expenses/", json=expense_data)
    expense_id = create_response.json()["id"]

    # Update the expense
    updated_expense_data = {"id": expense_id, "activity_id": activity_id, "payer_id": payer_id, "amount": 150.0, "description": "Updated Expense"}
    update_response = client.put(f"/expenses/{expense_id}", json=updated_expense_data)
    assert update_response.status_code == 200
    updated_expense = update_response.json()
    assert updated_expense["amount"] == 150.0
    assert updated_expense["description"] == "Updated Expense"

    # Verify the update by getting the expense
    get_response = client.get(f"/expenses/{expense_id}")
    assert get_response.status_code == 200
    retrieved_expense = get_response.json()
    assert retrieved_expense["amount"] == 150.0

def test_delete_expense():
    # First, create a user and an activity for the expense
    user_data = {"name": "Payer User 4", "email": "payer4@example.com"}
    user_response = client.post("/users/", json=user_data)
    payer_id = user_response.json()["id"]

    activity_data = {"name": "Test Activity 4", "participants": [payer_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    # Create an expense
    expense_data = {"activity_id": activity_id, "payer_id": payer_id, "amount": 75.0, "description": "Expense to Delete"}
    create_response = client.post("/expenses/", json=expense_data)
    expense_id = create_response.json()["id"]

    # Delete the expense
    delete_response = client.delete(f"/expenses/{expense_id}")
    assert delete_response.status_code == 204

    # Verify deletion by trying to get the expense
    get_response = client.get(f"/expenses/{expense_id}")
    assert get_response.status_code == 404

# Audit Log Tests
def test_log_activity_creation():
    activity_data = {"name": "Logged Activity", "participants": []}
    response = client.post("/activities/", json=activity_data)
    activity_id = response.json()["id"]

    audit_logs_response = client.get("/audit-logs/")
    audit_logs = audit_logs_response.json()
    assert any(log["action"] == "ACTIVITY_CREATED" and log["entity_id"] == activity_id for log in audit_logs)

def test_log_activity_update():
    activity_data = {"name": "Activity to Update", "participants": []}
    create_response = client.post("/activities/", json=activity_data)
    activity_id = create_response.json()["id"]

    updated_activity_data = {"id": activity_id, "name": "Updated Logged Activity", "participants": []}
    client.put(f"/activities/{activity_id}", json=updated_activity_data)

    audit_logs_response = client.get("/audit-logs/")
    audit_logs = audit_logs_response.json()
    assert any(log["action"] == "ACTIVITY_UPDATED" and log["entity_id"] == activity_id for log in audit_logs)

def test_log_activity_deletion():
    activity_data = {"name": "Activity to Delete Log", "participants": []}
    create_response = client.post("/activities/", json=activity_data)
    activity_id = create_response.json()["id"]

    client.delete(f"/activities/{activity_id}")

    audit_logs_response = client.get("/audit-logs/")
    audit_logs = audit_logs_response.json()
    assert any(log["action"] == "ACTIVITY_DELETED" and log["entity_id"] == activity_id for log in audit_logs)

def test_log_expense_creation():
    user_data = {"name": "Payer Log", "email": "payerlog@example.com"}
    user_response = client.post("/users/", json=user_data)
    payer_id = user_response.json()["id"]

    activity_data = {"name": "Activity Log", "participants": [payer_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    expense_data = {"activity_id": activity_id, "payer_id": payer_id, "amount": 10.0, "description": "Logged Expense"}
    response = client.post("/expenses/", json=expense_data)
    expense_id = response.json()["id"]

    audit_logs_response = client.get("/audit-logs/")
    audit_logs = audit_logs_response.json()
    assert any(log["action"] == "EXPENSE_CREATED" and log["entity_id"] == expense_id for log in audit_logs)

def test_log_expense_update():
    user_data = {"name": "Payer Log Update", "email": "payerlogupdate@example.com"}
    user_response = client.post("/users/", json=user_data)
    payer_id = user_response.json()["id"]

    activity_data = {"name": "Activity Log Update", "participants": [payer_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    expense_data = {"activity_id": activity_id, "payer_id": payer_id, "amount": 20.0, "description": "Original Logged Expense"}
    create_response = client.post("/expenses/", json=expense_data)
    expense_id = create_response.json()["id"]

    updated_expense_data = {"id": expense_id, "activity_id": activity_id, "payer_id": payer_id, "amount": 30.0, "description": "Updated Logged Expense"}
    client.put(f"/expenses/{expense_id}", json=updated_expense_data)

    audit_logs_response = client.get("/audit-logs/")
    audit_logs = audit_logs_response.json()
    assert any(log["action"] == "EXPENSE_UPDATED" and log["entity_id"] == expense_id for log in audit_logs)

def test_log_expense_deletion():
    user_data = {"name": "Payer Log Delete", "email": "payerlogdelete@example.com"}
    user_response = client.post("/users/", json=user_data)
    payer_id = user_response.json()["id"]

    activity_data = {"name": "Activity Log Delete", "participants": [payer_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    expense_data = {"activity_id": activity_id, "payer_id": payer_id, "amount": 40.0, "description": "Expense to Delete Log"}
    create_response = client.post("/expenses/", json=expense_data)
    expense_id = create_response.json()["id"]

    client.delete(f"/expenses/{expense_id}")

    audit_logs_response = client.get("/audit-logs/")
    audit_logs = audit_logs_response.json()
    assert any(log["action"] == "EXPENSE_DELETED" and log["entity_id"] == expense_id for log in audit_logs)

def test_get_audit_logs():
    # Create some activities and expenses to generate logs
    user_data = {"name": "Audit User", "email": "audit@example.com"}
    user_response = client.post("/users/", json=user_data)
    user_id = user_response.json()["id"]

    activity_data = {"name": "Audit Activity", "participants": [user_id]}
    activity_response = client.post("/activities/", json=activity_data)
    activity_id = activity_response.json()["id"]

    expense_data = {"activity_id": activity_id, "payer_id": user_id, "amount": 10.0, "description": "Audit Expense"}
    client.post("/expenses/", json=expense_data)

    audit_logs_response = client.get("/audit-logs/")
    assert audit_logs_response.status_code == 200
    audit_logs = audit_logs_response.json()
    assert len(audit_logs) >= 2  # At least activity created and expense created
    # Verify sorting by timestamp (most recent first)
    for i in range(len(audit_logs) - 1):
        assert datetime.fromisoformat(audit_logs[i]["timestamp"]) >= datetime.fromisoformat(audit_logs[i+1]["timestamp"])