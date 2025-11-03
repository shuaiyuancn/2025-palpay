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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)