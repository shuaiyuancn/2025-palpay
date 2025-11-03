from pydantic import BaseModel
from typing import List, Optional

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
