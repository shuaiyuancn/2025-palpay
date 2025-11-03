from fastapi.testclient import TestClient
from src.main import app, db
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_firestore():
    # Clear the 'users' collection before each test
    for doc in db.collection("users").stream():
        doc.reference.delete()
    # Clear the 'activities' collection before each test
    for doc in db.collection("activities").stream():
        doc.reference.delete()
    # Clear the 'expenses' collection before each test
    for doc in db.collection("expenses").stream():
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