from fastapi import FastAPI, HTTPException
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
from typing import List

from src.models import User, Activity, Expense

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate(os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH"))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully!")
except Exception as e:
    print(f"Error initializing Firebase: {e}")

@app.get("/")
def read_root():
    return {"Hello": "PalPay"}

# User Endpoints
@app.post("/users/", response_model=User)
async def create_user(user: User):
    user_ref = db.collection("users").document()
    user.id = user_ref.id
    user_ref.set(user.model_dump())
    return user

@app.get("/users/", response_model=List[User])
async def get_all_users():
    users = []
    for doc in db.collection("users").stream():
        users.append(User(**doc.to_dict()))
    return users

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user_doc.to_dict())

# Activity Endpoints
@app.post("/activities/", response_model=Activity)
async def create_activity(activity: Activity):
    activity_ref = db.collection("activities").document()
    activity.id = activity_ref.id
    activity_ref.set(activity.model_dump())
    return activity

@app.get("/activities/", response_model=List[Activity])
async def get_all_activities():
    activities = []
    for doc in db.collection("activities").stream():
        activities.append(Activity(**doc.to_dict()))
    return activities

@app.get("/activities/{activity_id}", response_model=Activity)
async def get_activity(activity_id: str):
    activity_doc = db.collection("activities").document(activity_id).get()
    if not activity_doc.exists:
        raise HTTPException(status_code=404, detail="Activity not found")
    return Activity(**activity_doc.to_dict())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
