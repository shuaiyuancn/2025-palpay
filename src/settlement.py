from typing import List, Dict
from collections import defaultdict

from src.models import Expense, Activity, Payment

def calculate_settlements(activity: Activity, expenses: List[Expense], payments: List[Payment]) -> Dict[str, Dict[str, float]]:
    balances = defaultdict(float)

    # Calculate individual balances based on expenses
    for expense in expenses:
        payer = expense.payer_id
        amount = expense.amount
        balances[payer] += amount

    # Calculate total amount spent in the activity
    total_amount = sum(expense.amount for expense in expenses)

    # Calculate fair share for each participant
    num_participants = len(activity.participants)
    if num_participants == 0:
        return {}
    fair_share = total_amount / num_participants

    # Determine net balances after expenses
    net_balances = {user_id: balances[user_id] - fair_share for user_id in activity.participants}

    # Adjust net balances based on payments
    for payment in payments:
        if payment.payer_id in net_balances and payment.payee_id in net_balances:
            net_balances[payment.payer_id] += payment.amount
            net_balances[payment.payee_id] -= payment.amount

    # Separate creditors (owed money) and debtors (owe money)
    creditors = {user_id: balance for user_id, balance in net_balances.items() if balance > 0}
    debtors = {user_id: -balance for user_id, balance in net_balances.items() if balance < 0}

    # Settle debts
    settlements = defaultdict(lambda: defaultdict(float))
    for debtor_id, debt_amount in debtors.items():
        for creditor_id, credit_amount in creditors.items():
            if debt_amount <= 0:  # Debtor has paid off their share
                break
            if credit_amount <= 0:  # Creditor has been fully paid
                continue

            settle_amount = min(debt_amount, credit_amount)
            settlements[debtor_id][creditor_id] += settle_amount

            debt_amount -= settle_amount
            creditors[creditor_id] -= settle_amount

    return {debtor: dict(owes) for debtor, owes in settlements.items() if owes}
