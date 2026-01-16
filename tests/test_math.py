import pytest
from datetime import date, datetime
from decimal import Decimal
import sys
import os

# Add root to path to import main
sys.path.append(os.getcwd())

from main import db, users, events, event_participants, costs, payments, balances, audit_logs, recalculate_balances, User, Event, EventParticipant, Cost, Payment

def setup_module():
    # Clear DB
    audit_logs.delete_where()
    balances.delete_where()
    payments.delete_where()
    costs.delete_where()
    event_participants.delete_where()
    events.delete_where()
    users.delete_where()

def test_split_logic():
    # 1. Create Users
    u1 = users.insert(User(name="Alice"))
    u2 = users.insert(User(name="Bob"))
    u3 = users.insert(User(name="Charlie"))

    # 2. Create Event
    e1 = events.insert(Event(name="Dinner", date=date.today()))
    event_participants.insert(EventParticipant(event_id=e1.id, user_id=u1.id))
    event_participants.insert(EventParticipant(event_id=e1.id, user_id=u2.id))
    event_participants.insert(EventParticipant(event_id=e1.id, user_id=u3.id))

    # 3. Add Cost: Alice pays £90
    costs.insert(Cost(event_id=e1.id, payer_id=u1.id, amount=Decimal(90), comment="Pizza", timestamp=datetime.now()))
    
    # 4. Recalc
    recalculate_balances()
    
    # 5. Verify
    # Split is 90 / 3 = 30.
    # Alice is +60 (Paid 90, consumed 30).
    # Bob is -30.
    # Charlie is -30.
    # Balances should show: Bob->Alice 30, Charlie->Alice 30.
    
    bals = balances()
    assert len(bals) == 2
    
    # Check Bob->Alice
    b_ba = next((b for b in bals if b.debtor_id == u2.id and b.creditor_id == u1.id), None)
    assert b_ba is not None
    assert b_ba.amount == Decimal(30)
    
    # Check Charlie->Alice
    b_ca = next((b for b in bals if b.debtor_id == u3.id and b.creditor_id == u1.id), None)
    assert b_ca is not None
    assert b_ca.amount == Decimal(30)

def test_payment_logic():
    # Setup from previous test state implicitly or query clean? 
    # Let's trust the sequence or re-fetch.
    u1 = users(where="name='Alice'")[0].id
    u2 = users(where="name='Bob'")[0].id
    
    # Bob pays Alice £30
    payments.insert(Payment(from_user_id=u2, to_user_id=u1, amount=Decimal(30), timestamp=datetime.now()))
    
    recalculate_balances()
    
    # Verify Bob is clear
    bals = balances()
    # Should only have Charlie->Alice 30 left
    assert len(bals) == 1
    assert bals[0].debtor_id != u2
