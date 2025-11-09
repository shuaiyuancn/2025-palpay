from fastapi import FastAPI, HTTPException
from typing import List
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

from .models import User, Activity, Expense, Payment, Balance
from .balance_calculator import BalanceCalculator

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
def create_user(user: User):
    user_ref = db.collection("users").document()
    user.id = user_ref.id
    user_ref.set(user.dict())
    return user

@app.get("/users/", response_model=List[User])
def get_all_users():
    users = []
    for doc in db.collection("users").stream():
        users.append(User(**doc.to_dict()))
    return users

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str):
    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user_doc.to_dict())

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: str, user: User):
    user_ref = db.collection("users").document(user_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")
    user.id = user_id
    user_ref.set(user.dict())
    return user

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str):
    user_ref = db.collection("users").document(user_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.delete()
    return

# Activity Endpoints
@app.post("/activities/", response_model=Activity)
def create_activity(activity: Activity):
    activity_ref = db.collection("activities").document()
    activity.id = activity_ref.id
    activity_ref.set(activity.dict())
    return activity

@app.get("/activities/", response_model=List[Activity])
def get_all_activities():
    activities = [Activity(**doc.to_dict()) for doc in db.collection("activities").stream()]
    return activities

@app.get("/activities/{activity_id}", response_model=Activity)
def get_activity(activity_id: str):
    activity_doc = db.collection("activities").document(activity_id).get()
    if not activity_doc.exists:
        raise HTTPException(status_code=404, detail="Activity not found")
    return Activity(**activity_doc.to_dict())

@app.put("/activities/{activity_id}", response_model=Activity)
def update_activity(activity_id: str, activity: Activity):
    activity_ref = db.collection("activities").document(activity_id)
    if not activity_ref.get().exists:
        raise HTTPException(status_code=404, detail="Activity not found")
    activity.id = activity_id
    activity_ref.set(activity.dict())
    return activity

@app.delete("/activities/{activity_id}", status_code=204)
def delete_activity(activity_id: str):
    activity_ref = db.collection("activities").document(activity_id)
    if not activity_ref.get().exists:
        raise HTTPException(status_code=404, detail="Activity not found")
    activity_ref.delete()
    return

# Expense Endpoints
@app.post("/expenses/", response_model=Expense)
def create_expense(expense: Expense):
    expense_ref = db.collection("expenses").document()
    expense.id = expense_ref.id
    expense_ref.set(expense.dict())
    return expense

@app.get("/expenses/", response_model=List[Expense])
def get_all_expenses():
    expenses = [Expense(**doc.to_dict()) for doc in db.collection("expenses").stream()]
    return expenses

@app.get("/expenses/{expense_id}", response_model=Expense)
def get_expense(expense_id: str):
    expense_doc = db.collection("expenses").document(expense_id).get()
    if not expense_doc.exists:
        raise HTTPException(status_code=404, detail="Expense not found")
    return Expense(**expense_doc.to_dict())

@app.put("/expenses/{expense_id}", response_model=Expense)
def update_expense(expense_id: str, expense: Expense):
    expense_ref = db.collection("expenses").document(expense_id)
    if not expense_ref.get().exists:
        raise HTTPException(status_code=404, detail="Expense not found")
    expense.id = expense_id
    expense_ref.set(expense.dict())
    return expense

@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: str):
    expense_ref = db.collection("expenses").document(expense_id)
    if not expense_ref.get().exists:
        raise HTTPException(status_code=404, detail="Expense not found")
    expense_ref.delete()
    return

# Payment Endpoints
@app.post("/payments/", response_model=Payment)
def create_payment(payment: Payment):
    payment_ref = db.collection("payments").document()
    payment.id = payment_ref.id
    payment_ref.set(payment.dict())
    return payment

@app.get("/payments/", response_model=List[Payment])
def get_all_payments():
    payments = [Payment(**doc.to_dict()) for doc in db.collection("payments").stream()]
    return payments

@app.get("/payments/{payment_id}", response_model=Payment)
def get_payment(payment_id: str):
    payment_doc = db.collection("payments").document(payment_id).get()
    if not payment_doc.exists:
        raise HTTPException(status_code=404, detail="Payment not found")
    return Payment(**payment_doc.to_dict())

@app.put("/payments/{payment_id}", response_model=Payment)
def update_payment(payment_id: str, payment: Payment):
    payment_ref = db.collection("payments").document(payment_id)
    if not payment_ref.get().exists:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment.id = payment_id
    payment_ref.set(payment.dict())
    return payment

@app.delete("/payments/{payment_id}", status_code=204)
def delete_payment(payment_id: str):
    payment_ref = db.collection("payments").document(payment_id)
    if not payment_ref.get().exists:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment_ref.delete()
    return

@app.get("/balances/", response_model=List[Balance])
def get_balances():
    users = [User(**doc.to_dict()) for doc in db.collection("users").stream()]
    activities = [Activity(**doc.to_dict()) for doc in db.collection("activities").stream()]
    expenses = [Expense(**doc.to_dict()) for doc in db.collection("expenses").stream()]
    payments = [Payment(**doc.to_dict()) for doc in db.collection("payments").stream()]
    
    calculator = BalanceCalculator(users, activities, expenses, payments)
    return calculator.calculate()

