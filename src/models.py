from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class User(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    payment_details: Optional[str] = None

class Activity(BaseModel):
    id: Optional[str] = None
    name: str
    participants: List[str]  # List of user IDs

class Expense(BaseModel):
    id: Optional[str] = None
    activity_id: str
    payer_id: str
    amount: float
    description: Optional[str] = None

class Payment(BaseModel):
    id: Optional[str] = None
    payer_id: str
    payee_id: str
    amount: float
    timestamp: datetime

class AuditLog(BaseModel):
    id: Optional[str] = None
    timestamp: datetime
    action: str  # e.g., "ACTIVITY_CREATED", "EXPENSE_UPDATED"
    entity_type: str  # e.g., "Activity", "Expense"
    entity_id: str
    user_id: Optional[str] = None  # User who performed the action
    details: Optional[Dict] = None # Additional details about the change
