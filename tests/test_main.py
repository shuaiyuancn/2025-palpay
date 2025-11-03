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
    activity_data = {"name": "Weekend Trip", "participants": ["user1_id", "user2_id"]}
    response = client.post("/activities/", json=activity_data)
    assert response.status_code == 200
    created_activity = response.json()
    assert created_activity["name"] == "Weekend Trip"
    assert created_activity["participants"] == ["user1_id", "user2_id"]
    assert "id" in created_activity

def test_get_activity():
    # First, create an activity
    activity_data = {"name": "Dinner", "participants": ["user3_id"]}
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
    client.post("/activities/", json={"name": "Concert", "participants": ["user4_id"]})
    client.post("/activities/", json={"name": "Movie", "participants": ["user5_id", "user6_id"]})

    response = client.get("/activities/")
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 2
    activity_names = [activity["name"] for activity in activities]
    assert "Concert" in activity_names
    assert "Movie" in activity_names
