# Test Cases

This document outlines the test cases for the PalPay application, covering both unit and integration tests.

## How to Run Tests

The tests are run using `pytest`. To execute all tests, run the following command from the project's root directory:

```bash
pytest
```

## 1. Integration Test Cases

These test cases focus on the core settlement calculation logic.

### Case 1: Simple Split

- **Scenario:** User U1 and User U2 participate in Activity A1. U1 pays 10.
- **Expected Outcome:** U2 owes U1 5.

### Case 2: Multiple Activities, No Overlap

- **Scenario:**
  - Activity A1: Participants U1, U2. U1 pays 10.
  - Activity A2: Participants U2, U3. U2 pays 10.
- **Expected Outcome:**
  - U2 owes U1 5.
  - U3 owes U2 5.

### Case 3: Multiple Activities, With Overlap

- **Scenario:**
  - Activity A1: Participants U1, U2, U3. U1 pays 15.
  - Activity A2: Participants U2, U3. U2 pays 10.
- **Expected Outcome:**
  - U2 owes U1 5.
  - U3 owes U2 5.
  - U3 owes U1 5.

### Case 4: Settlement with Full Payment

- **Scenario:**
  - Activity A1: Participants U1, U2. U1 pays 10.
  - U2 pays U1 5.
- **Expected Outcome:**
  - No outstanding settlements for Activity A1.

### Case 5: Settlement with Partial Payment

- **Scenario:**
  - Activity A1: Participants U1, U2. U1 pays 10.
  - U2 pays U1 3.
- **Expected Outcome:**
  - U2 owes U1 2.

### Case 6: Complex Scenario with 5 Users

- **Scenario:**
  - 5 Users: U1, U2, U3, U4, U5
  - Activity A1 (all 5 users):
    - U1 pays 100.
    - U2 pays 50.
  - Activity A2 (U1, U2, U3):
    - U3 pays 60.
  - Payments:
    - U4 pays U1 10.
    - U5 pays U2 5.
- **Expected Outcome:**
  - U2 owes U1 5.
  - U4 owes U1 20.
  - U5 owes U1 15.
  - U5 owes U3 10.

## 2. Unit Test Cases

### 2.1. User Management (Admin)

- **Test:** Add a new user.
  - **Steps:**
    1. Access the admin user creation page.
    2. Fill in the user's name, payment details, and email.
    3. Submit the form.
  - **Expected Outcome:** The new user is added to the system and appears in the user list.
- **Test:** Update an existing user.
  - **Steps:**
    1. Access the admin user edit page for a specific user.
    2. Change the user's payment details.
    3. Submit the form.
  - **Expected Outcome:** The user's details are updated.

### 2.2. Activity Management

- **Test:** Create a new activity.
- **Test:** Update an existing activity (e.g., change the name, add/remove participants).
- **Test:** Delete an activity.

### 2.3. Expense Management

- **Test:** Create a new expense for an activity.
- **Test:** Update an existing expense (e.g., change the amount or the payer).
- **Test:** Delete an expense.

### 2.4. Settlement Calculation

- **Test:** Calculate settlement with no expenses.
- **Test:** Calculate settlement with one expense.
- **Test:** Calculate settlement with multiple expenses from different payers.
- **Test:** Calculate settlement with a user who has both paid and owes money.

### 2.5. Payment Management

- **Test:** Create a new payment.
- **Test:** Update an existing payment.
- **Test:** Delete a payment.

## 3. Audit Log

- **Test:** Log activity creation.
- **Test:** Log activity update.
- **Test:** Log activity deletion.
- **Test:** Log expense creation.
- **Test:** Log expense update.
- **Test:** Log expense deletion.
- **Test:** Log payment creation.
- **Test:** Log payment update.
- **Test:** Log payment deletion.
- **Test:** Verify that the audit log page displays the logs correctly.
