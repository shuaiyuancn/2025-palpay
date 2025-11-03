from typing import List, Dict
from collections import defaultdict

from src.models import Expense, Activity, Payment, User

def calculate_settlements(
    users: List[User],
    activities: List[Activity],
    expenses: List[Expense],
    payments: List[Payment],
) -> Dict[str, Dict[str, float]]:
    balances = defaultdict(float)

    # Initialize balances for all users
    for user in users:
        balances[user.id] = 0.0

    # Calculate total amount each user should have paid
    for activity in activities:
        total_activity_amount = sum(e.amount for e in expenses if e.activity_id == activity.id)
        num_participants = len(activity.participants)
        if num_participants == 0:
            continue
        fair_share = total_activity_amount / num_participants
        for user_id in activity.participants:
            balances[user_id] -= fair_share

    # Add the amount each user has paid
    for expense in expenses:
        balances[expense.payer_id] += expense.amount

    # Adjust balances for payments
    for payment in payments:
        balances[payment.payer_id] += payment.amount
        balances[payment.payee_id] -= payment.amount

    # Separate creditors and debtors
    creditors = {user_id: balance for user_id, balance in balances.items() if balance > 0}
    debtors = {user_id: -balance for user_id, balance in balances.items() if balance < 0}

    # Settle debts
    settlements = defaultdict(lambda: defaultdict(float))
    debtors_list = sorted(debtors.items(), key=lambda x: x[1])
    creditors_list = sorted(creditors.items(), key=lambda x: x[1], reverse=True)

    debtor_idx = 0
    creditor_idx = 0

    while debtor_idx < len(debtors_list) and creditor_idx < len(creditors_list):
        debtor_id, debt_amount = debtors_list[debtor_idx]
        creditor_id, credit_amount = creditors_list[creditor_idx]

        settle_amount = min(debt_amount, credit_amount)

        if settle_amount > 1e-9:
            settlements[debtor_id][creditor_id] = settle_amount

        debtors_list[debtor_idx] = (debtor_id, debt_amount - settle_amount)
        creditors_list[creditor_idx] = (creditor_id, credit_amount - settle_amount)

        if debtors_list[debtor_idx][1] < 1e-9:
            debtor_idx += 1
        if creditors_list[creditor_idx][1] < 1e-9:
            creditor_idx += 1

    return {debtor: dict(owes) for debtor, owes in settlements.items() if owes}