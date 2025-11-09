from collections import defaultdict
from .models import Balance, User

class BalanceCalculator:
    def __init__(self, users, activities, expenses, payments):
        self.users = {u.id: u for u in users}
        self.activities = {a.id: a for a in activities}
        self.expenses = expenses
        self.payments = payments
        self.balances = defaultdict(float)

    def calculate(self):
        self._calculate_expenses()
        self._apply_payments()
        
        # Final simplification step
        final_balances = []
        processed_pairs = set()

        for (user1_id, user2_id), amount in self.balances.items():
            if (user1_id, user2_id) in processed_pairs or (user2_id, user1_id) in processed_pairs:
                continue

            reverse_amount = self.balances.get((user2_id, user1_id), 0)
            net_amount = amount - reverse_amount

            if round(net_amount, 2) > 0:
                final_balances.append(Balance(debtor=self.users[user1_id], creditor=self.users[user2_id], amount=round(net_amount, 2)))
            elif round(net_amount, 2) < 0:
                final_balances.append(Balance(debtor=self.users[user2_id], creditor=self.users[user1_id], amount=round(-net_amount, 2)))
            
            processed_pairs.add((user1_id, user2_id))

        return final_balances

    def _calculate_expenses(self):
        # Group expenses by activity
        activity_expenses = defaultdict(list)
        for expense in self.expenses:
            activity_expenses[expense.activity_id].append(expense)

        for activity_id, expenses_in_activity in activity_expenses.items():
            # Find the activity to get the full list of participants
            activity = self.activities.get(activity_id)
            if not activity:
                continue # Or raise an error if an expense has an invalid activity_id

            participants = activity.participants
            num_participants = len(participants)
            if num_participants == 0:
                continue

            # Calculate total paid per user and total expense for the activity
            paid_by = defaultdict(float)
            total_activity_expense = 0
            for expense in expenses_in_activity:
                paid_by[expense.paid_by_user_id] += expense.amount
                total_activity_expense += expense.amount

            # Calculate share per person
            share = total_activity_expense / num_participants

            # Calculate personal balance for each participant in the activity
            personal_balances = {}
            for participant in participants:
                personal_balances[participant.id] = paid_by[participant.id] - share

            # Separate into debtors and creditors
            debtors = {uid: -bal for uid, bal in personal_balances.items() if bal < 0}
            creditors = {uid: bal for uid, bal in personal_balances.items() if bal > 0}

            total_credit = sum(creditors.values())
            if total_credit == 0:
                continue

            # Distribute debts proportionally
            for debtor_id, debt_amount in debtors.items():
                for creditor_id, credit_amount in creditors.items():
                    proportion = credit_amount / total_credit
                    amount_owed = debt_amount * proportion
                    self.balances[(debtor_id, creditor_id)] += amount_owed

    def _apply_payments(self):
        for payment in self.payments:
            # A payment from user A to user B reduces A's debt to B
            self.balances[(payment.from_user_id, payment.to_user_id)] -= payment.amount
            
    def _simplify_balances(self):
        # This method is now integrated into calculate()
        pass
