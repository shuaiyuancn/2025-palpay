from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class User(BaseModel):
    id: str
    name: str
    email: str
    payment_details: Optional[str] = None

class Activity(BaseModel):
    id: str
    name: str
    participants: List[User]

class Expense(BaseModel):
    id: str
    activity_id: str
    paid_by_user_id: str
    amount: float
    participants: List[User]
    description: Optional[str] = None

class Payment(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    amount: float
    timestamp: datetime = datetime.now()

class Balance(BaseModel):
    debtor: User
    creditor: User
    amount: float

class AuditLog(BaseModel):
    id: Optional[str] = None
    timestamp: datetime
    action: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    details: Optional[Dict] = None