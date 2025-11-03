from fastapi import FastAPI, HTTPException, Request
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
from typing import List, Dict

from src.models import User, Activity, Expense, AuditLog
from src.settlement import calculate_settlements
from src.audit_log import log_audit_event

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

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: User):
    user_ref = db.collection("users").document(user_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")
    user.id = user_id  # Ensure the ID in the payload matches the path ID
    user_ref.set(user.model_dump())
    return user

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: str):
    user_ref = db.collection("users").document(user_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.delete()
    return

# Activity Endpoints
@app.post("/activities/", response_model=Activity)
async def create_activity(activity: Activity):
    activity_ref = db.collection("activities").document()
    activity.id = activity_ref.id
    activity_ref.set(activity.model_dump())
    log_audit_event("ACTIVITY_CREATED", "Activity", activity.id, details=activity.model_dump())
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

@app.put("/activities/{activity_id}", response_model=Activity)
async def update_activity(activity_id: str, activity: Activity):
    activity_ref = db.collection("activities").document(activity_id)
    if not activity_ref.get().exists:
        raise HTTPException(status_code=404, detail="Activity not found")
    activity.id = activity_id
    log_audit_event("ACTIVITY_UPDATED", "Activity", activity.id, details=activity.model_dump())
    activity_ref.set(activity.model_dump())
    return activity

@app.delete("/activities/{activity_id}", status_code=204)
async def delete_activity(activity_id: str):
    activity_ref = db.collection("activities").document(activity_id)
    if not activity_ref.get().exists:
        raise HTTPException(status_code=404, detail="Activity not found")
    log_audit_event("ACTIVITY_DELETED", "Activity", activity_id)
    activity_ref.delete()
    return

# Expense Endpoints
@app.post("/expenses/", response_model=Expense)
async def create_expense(expense: Expense):
    expense_ref = db.collection("expenses").document()
    expense.id = expense_ref.id
    expense_ref.set(expense.model_dump())
    log_audit_event("EXPENSE_CREATED", "Expense", expense.id, details=expense.model_dump())
    return expense

@app.get("/expenses/", response_model=List[Expense])
async def get_all_expenses():
    expenses = []
    for doc in db.collection("expenses").stream():
        expenses.append(Expense(**doc.to_dict()))
    return expenses

@app.get("/expenses/{expense_id}", response_model=Expense)
async def get_expense(expense_id: str):
    expense_doc = db.collection("expenses").document(expense_id).get()
    if not expense_doc.exists:
        raise HTTPException(status_code=404, detail="Expense not found")
    return Expense(**expense_doc.to_dict())

@app.put("/expenses/{expense_id}", response_model=Expense)
async def update_expense(expense_id: str, expense: Expense):
    expense_ref = db.collection("expenses").document(expense_id)
    if not expense_ref.get().exists:
        raise HTTPException(status_code=404, detail="Expense not found")
    expense.id = expense_id
    log_audit_event("EXPENSE_UPDATED", "Expense", expense.id, details=expense.model_dump())
    expense_ref.set(expense.model_dump())
    return expense

@app.delete("/expenses/{expense_id}", status_code=204)
async def delete_expense(expense_id: str):
    expense_ref = db.collection("expenses").document(expense_id)
    if not expense_ref.get().exists:
        raise HTTPException(status_code=404, detail="Expense not found")
    log_audit_event("EXPENSE_DELETED", "Expense", expense_id)
    expense_ref.delete()
    return

# Settlement Endpoints
@app.get("/settlements/{activity_id}", response_model=Dict[str, Dict[str, float]])
async def get_settlements(activity_id: str):
    activity_doc = db.collection("activities").document(activity_id).get()
    if not activity_doc.exists:
        raise HTTPException(status_code=404, detail="Activity not found")
    activity = Activity(**activity_doc.to_dict())

    expenses = []
    for doc in db.collection("expenses").where("activity_id", "==", activity_id).stream():
        expenses.append(Expense(**doc.to_dict()))

    settlements = calculate_settlements(activity, expenses)
    return settlements

# Audit Log Endpoints
@app.get("/audit-logs/", response_model=List[AuditLog])
async def get_audit_logs():
    audit_logs = []
    for doc in db.collection("audit_logs").order_by("timestamp", direction=firestore.Query.DESCENDING).stream():
        audit_logs.append(AuditLog(**doc.to_dict()))
    return audit_logs


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)