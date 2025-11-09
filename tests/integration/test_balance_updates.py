import pytest
from src.main import PalPay
from src.models import User, Activity, Expense, Payment

# Test data based on docs/test-cases.md

@pytest.fixture
def u1():
    return User(id="1", name="User1", email="user1@example.com")

@pytest.fixture
def u2():
    return User(id="2", name="User2", email="user2@example.com")

@pytest.fixture
def u3():
    return User(id="3", name="User3", email="user3@example.com")

@pytest.fixture
def u4():
    return User(id="4", name="User4", email="user4@example.com")

@pytest.fixture
def u5():
    return User(id="5", name="User5", email="user5@example.com")

@pytest.fixture
def activity1(u1, u2):
    return Activity(id="1", name="Activity 1", participants=[u1, u2])

@pytest.fixture
def activity2(u1, u2, u3):
    return Activity(id="2", name="Activity 2", participants=[u1, u2, u3])

@pytest.fixture
def activity3(u1, u2, u3, u4, u5):
    return Activity(id="3", name="Activity 3", participants=[u1, u2, u3, u4, u5])


def test_simple_expense_creation(u1, u2, activity1):
    """
    Case 1: Simple Expense Creation
    - Scenario: User U1 and User U2 participate in an activity. U1 pays 100.
    - Expected Outcome: A balance record is created showing U2 owes U1 50.
    """
    palpay = PalPay()
    palpay.add_user(u1)
    palpay.add_user(u2)
    palpay.add_activity(activity1)
    expense = Expense(id="1", activity_id="1", paid_by_user_id="1", amount=100, participants=[u1, u2])
    palpay.add_expense(expense)
    
    balances = palpay.get_balances()
    assert len(balances) == 1
    balance = balances[0]
    assert balance.debtor.id == "2"
    assert balance.creditor.id == "1"
    assert balance.amount == 50

def test_multiple_participants(u1, u2, u3, activity2):
    """
    Case 2: Multiple Participants
    - Scenario: User U1, U2, and U3 participate in an activity. U1 pays 90.
    - Expected Outcome:
      - A balance record is created showing U2 owes U1 30.
      - A balance record is created showing U3 owes U1 30.
    """
    palpay = PalPay()
    palpay.add_user(u1)
    palpay.add_user(u2)
    palpay.add_user(u3)
    palpay.add_activity(activity2)
    expense = Expense(id="1", activity_id="2", paid_by_user_id="1", amount=90, participants=[u1, u2, u3])
    palpay.add_expense(expense)

    balances = palpay.get_balances()
    assert len(balances) == 2
    
    balance1 = next(b for b in balances if b.debtor.id == "2")
    assert balance1.creditor.id == "1"
    assert balance1.amount == 30

    balance2 = next(b for b in balances if b.debtor.id == "3")
    assert balance2.creditor.id == "1"
    assert balance2.amount == 30


def test_existing_balance_update(u1, u2, activity1):
    """
    Case 3: Existing Balance Update
    - Scenario:
      - U1 and U2 are in an activity. U1 pays 50 (U2 owes U1 25).
      - U1 pays another 50 in the same activity.
    - Expected Outcome: The existing balance is updated to show U2 owes U1 50.
    """
    palpay = PalPay()
    palpay.add_user(u1)
    palpay.add_user(u2)
    palpay.add_activity(activity1)
    
    expense1 = Expense(id="1", activity_id="1", paid_by_user_id="1", amount=50, participants=[u1, u2])
    palpay.add_expense(expense1)
    
    expense2 = Expense(id="2", activity_id="1", paid_by_user_id="1", amount=50, participants=[u1, u2])
    palpay.add_expense(expense2)

    balances = palpay.get_balances()
    assert len(balances) == 1
    balance = balances[0]
    assert balance.debtor.id == "2"
    assert balance.creditor.id == "1"
    assert balance.amount == 50


def test_balance_reversal(u1, u2, activity1):
    """
    Case 4: Balance Reversal
    - Scenario:
      - U1 and U2 are in an activity. U1 pays 20 (U2 owes U1 10).
      - U2 pays U1 20.
    - Expected Outcome: The balance is reversed to show U1 owes U2 10.
    """
    palpay = PalPay()
    palpay.add_user(u1)
    palpay.add_user(u2)
    palpay.add_activity(activity1)

    expense1 = Expense(id="1", activity_id="1", paid_by_user_id="1", amount=20, participants=[u1, u2])
    palpay.add_expense(expense1)

    payment = Payment(id="1", from_user_id="2", to_user_id="1", amount=20)
    palpay.add_payment(payment)
    
    balances = palpay.get_balances()
    assert len(balances) == 1
    balance = balances[0]
    assert balance.debtor.id == "1"
    assert balance.creditor.id == "2"
    assert balance.amount == 10


def test_zero_balance_deletion(u1, u2, activity1):
    """
    Case 5: Zero Balance Deletion
    - Scenario:
      - U1 and U2 are in an activity. U1 pays 30 (U2 owes U1 15).
      - U2 pays U1 15
    - Expected Outcome: The balance between U1 and U2 is zero.
    """
    palpay = PalPay()
    palpay.add_user(u1)
    palpay.add_user(u2)
    palpay.add_activity(activity1)

    expense = Expense(id="1", activity_id="1", paid_by_user_id="1", amount=30, participants=[u1, u2])
    palpay.add_expense(expense)

    payment = Payment(id="1", from_user_id="2", to_user_id="1", amount=15)
    palpay.add_payment(payment)

    balances = palpay.get_balances()
    assert len(balances) == 0


def test_complex_scenario(u1, u2, u3, u4, u5):
    """
    Case 6: Complex Scenario with Simplified Settlement
    - Scenario:
      - 5 Users: U1, U2, U3, U4, U5
      - Activity A1 (all 5 users):
        - U1 pays 100.
        - U2 pays 50.
        - At this point, U3, U4 and U5 owe U1 23.33; they owe U2 6.67; U2 owes U1 nothing.
      - Activity A2 (U1, U2, U3):
        - U3 pays 60.
        - At this point, U3 owes U1 3.33, U3 owes U2 nothing, U2 owes U3 13.33, U4 and U5 owe U1 23.33, U4 and U5 owe U2 6.67
      - U4 pays U1 30
        - At this point, U1 owes U4 6.67
        - Note although U4 also owes U2 6.67, we don't simplified it as U1 owes U2 6.67, U1 owes U4 nothing, U4 owes U2 nothing
    """
    palpay = PalPay()
    users = [u1, u2, u3, u4, u5]
    for user in users:
        palpay.add_user(user)
    
    activity_A1 = Activity(id="1", name="A1", participants=users)
    palpay.add_activity(activity_A1)

    expense1_A1 = Expense(id="1", activity_id="1", paid_by_user_id="1", amount=100, participants=users)
    palpay.add_expense(expense1_A1)
    
    expense2_A1 = Expense(id="2", activity_id="1", paid_by_user_id="2", amount=50, participants=users)
    palpay.add_expense(expense2_A1)

    activity_A2 = Activity(id="2", name="A2", participants=[u1, u2, u3])
    palpay.add_activity(activity_A2)

    expense1_A2 = Expense(id="3", activity_id="2", paid_by_user_id="3", amount=60, participants=[u1, u2, u3])
    palpay.add_expense(expense1_A2)

    payment = Payment(id="1", from_user_id="4", to_user_id="1", amount=30)
    palpay.add_payment(payment)

    balances = palpay.get_balances()
    
    # Expected balances based on the final simplified state in the markdown
    expected_balances = {
        ("3", "1"): 3.33,
        ("2", "3"): 13.33,
        ("4", "2"): 6.67,
        ("5", "1"): 23.33,
        ("5", "2"): 6.67,
        ("1", "4"): 6.67,
    }

    actual_balances = {(b.debtor.id, b.creditor.id): b.amount for b in balances}
    
    assert len(actual_balances) == len(expected_balances)
    
    for key, amount in expected_balances.items():
        assert key in actual_balances
        assert round(actual_balances[key], 2) == amount
