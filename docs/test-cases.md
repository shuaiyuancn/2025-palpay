# Test Cases

This document outlines the test cases for the PalPay application, covering both unit and integration tests.

## How to Run Tests

The tests are run using `pytest`. To execute all tests, run the following command from the project's root directory:

```bash
pytest
```

## 1. Integration Test Cases

These test cases focus on the core balance update logic.

### Case 1: Simple Expense Creation

- **Scenario:** User U1 and User U2 participate in an activity. U1 pays 100.
- **Expected Outcome:** A balance record is created showing U2 owes U1 50.

### Case 2: Multiple Participants

- **Scenario:** User U1, U2, and U3 participate in an activity. U1 pays 90.
- **Expected Outcome:**
  - A balance record is created showing U2 owes U1 30.
  - A balance record is created showing U3 owes U1 30.

### Case 3: Existing Balance Update

- **Scenario:**
  - U1 and U2 are in an activity. U1 pays 50 (U2 owes U1 25).
  - U1 pays another 50 in the same activity.
- **Expected Outcome:** The existing balance is updated to show U2 owes U1 50.

### Case 4: Balance Reversal

- **Scenario:**
  - U1 and U2 are in an activity. U1 pays 20 (U2 owes U1 10).
  - U2 pays U1 20.
- **Expected Outcome:** The balance is reversed to show U1 owes U2 10.

### Case 5: Zero Balance Deletion

- **Scenario:**
  - U1 and U2 are in an activity. U1 pays 30 (U2 owes U1 15).
  - U2 pays U1 15
- **Expected Outcome:** The balance between U1 and U2 is zero.

### Case 6: Complex Scenario with Simplified Settlement

- **Scenario:**
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

## 2. Unit Test Cases

### 2.1. User Management (Admin)

- **Test:** Add a new user.
- **Test:** Update an existing user.

### 2.2. Activity Management

- **Test:** Create a new activity.
- **Test:** Update an existing activity.
- **Test:** Delete an activity.

### 2.3. Expense Management

- **Test:** Create a new expense.
- **Test:** Update an existing expense.
- **Test:** Delete an expense.

### 2.4. Payment Management

- **Test:** Create a new payment.
- **Test:** Update an existing payment.
- **Test:** Delete a payment.

## 3. Audit Log

- **Test:** Log activity creation, update, and deletion.
- **Test:** Log expense creation, update, and deletion.
- **Test:** Log payment creation, update, and deletion.
- **Test:** Verify that the audit log page displays the logs correctly.