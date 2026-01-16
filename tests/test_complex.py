import sys
import os
sys.path.append(os.getcwd())
from main import db, users, events, event_participants, costs, payments, balances, audit_logs, recalculate_balances, User, Event, EventParticipant, Cost, Payment
from decimal import Decimal
from datetime import date, datetime

def setup_module():
    # Clear DB
    audit_logs.delete_where()
    balances.delete_where()
    payments.delete_where()
    costs.delete_where()
    event_participants.delete_where()
    events.delete_where()
    users.delete_where()

def test_complex_case_1():
    # 1. Create Users
    alice = users.insert(User(name="Alice"))
    bob = users.insert(User(name="Bob"))
    charlie = users.insert(User(name="Charlie"))

    # 2. Create Event
    e1 = events.insert(Event(name="Party", date=date.today()))
    event_participants.insert(EventParticipant(event_id=e1.id, user_id=alice.id))
    event_participants.insert(EventParticipant(event_id=e1.id, user_id=bob.id))
    event_participants.insert(EventParticipant(event_id=e1.id, user_id=charlie.id))

    # 3. Add Costs
    # Alice pays 90 for Pizza
    costs.insert(Cost(event_id=e1.id, payer_id=alice.id, amount=Decimal(90), comment="Pizza", timestamp=datetime.now()))
    
    # Bob pays 120 for Wine
    costs.insert(Cost(event_id=e1.id, payer_id=bob.id, amount=Decimal(120), comment="Wine", timestamp=datetime.now()))
    
    # 4. Recalc
    recalculate_balances()
    
    # 5. Verify Balances
    bals = balances()
    
    # Expected:
    # Charlie -> Alice: 20
    # Charlie -> Bob: 50
    
    # Helper to find debt
    def get_debt(debtor, creditor):
        for b in bals:
            if b.debtor_id == debtor.id and b.creditor_id == creditor.id:
                return b.amount
        return Decimal(0)

    # Check Charlie's Debts
    c_to_a = get_debt(charlie, alice)
    c_to_b = get_debt(charlie, bob)
    
    # There should be no other debts
    # Bob owes Alice?
    # Alice Net: +20. Bob Net: +50. Charlie Net: -70.
    # The logic simplifies pairwise.
    # Initially from Pizza: B->A 30, C->A 30.
    # From Wine: A->B 40, C->B 40.
    # Net Pairwise:
    # A vs B: B owes A 30, A owes B 40 -> A owes B 10.
    # A vs C: C owes A 30.
    # B vs C: C owes B 40.
    
    # So raw pairwise consolidation:
    # A->B: 10
    # C->A: 30
    # C->B: 40
    
    # Wait, let's trace the implementation logic.
    # My implementation sums up debts pairwise.
    # Alice -> Bob: -30 (from Pizza split where Bob owed Alice) + 40 (Wine split where Alice owes Bob) = +10. (Alice owes Bob 10).
    # Alice -> Charlie: -30 (from Pizza C->A) + 0 = -30. (Charlie owes Alice 30).
    # Bob -> Charlie: 0 + -40 (from Wine C->B) = -40. (Charlie owes Bob 40).
    
    # Final Result of pairwise logic:
    # Alice owes Bob 10.
    # Charlie owes Alice 30.
    # Charlie owes Bob 40.
    
    # Total Position check:
    # Alice: -10 (to Bob) + 30 (from Charlie) = +20. Correct.
    # Bob: +10 (from Alice) + 40 (from Charlie) = +50. Correct.
    # Charlie: -30 (to Alice) - 40 (to Bob) = -70. Correct.
    
    # THE USER TEST CASE SAYS:
    # - charlie owes alice 20
    # - charlie owes bob 50
    
    # My logic produces:
    # - Alice owes Bob 10
    # - Charlie owes Alice 30
    # - Charlie owes Bob 40
    
    # Both result in the same Net Position, but the EDGES (who pays whom) are different.
    # The user's case implies a specific graph optimization (simplification of debts).
    # My current implementation is "Pairwise Net". It consolidates A->B and B->A.
    # It does NOT do transitive simplification (A->B->C => A->C).
    
    # Updated Assertions for Optimized Logic
    assert get_debt(charlie, alice) == Decimal(20)
    assert get_debt(charlie, bob) == Decimal(50)
    assert get_debt(alice, bob) == Decimal(0)
    assert get_debt(bob, alice) == Decimal(0)
