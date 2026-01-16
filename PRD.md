# Product Requirements Document: PalPay

## 1. Overview
PalPay is a lightweight, friction-free web application for logging group activity costs and calculating payments among users. It removes authentication barriers to allow for quick entry and management of shared expenses, relying on audit logs and merge tools to manage data integrity.

## 2. Core Principles
- **No Authentication:** Open access for immediate usage. No login required.
- **Global Context:** Users and Events are shared across the deployment.
- **Auditability:** Every action is logged with IP and context to prevent/trace abuse.
- **Resilience:** Built-in tools to merge duplicate data (Users/Events) resulting from unauthenticated, distributed input.

## 3. Data Entities & Schema

### 3.1 User
*   **Name:** String.
*   *Note:* Acts as the identity for debts and credits.

### 3.2 Event
*   **Name:** String.
*   **Date:** Date (Defaults to Today).
*   **Participants:** List of Users involved in this event.
*   **Costs:** List of expenses associated with the event.

### 3.3 Cost (Expense Item)
*   **Amount:** Decimal/Currency.
*   **Comment:** String (Description).
*   **Payer:** User (Required: The specific user who paid).
*   **Beneficiaries:** All Users participating in the Event (Logic: Always split equally among all event participants). Don't store again because it can be inferred from Event.Participants.

### 3.4 Payment (Settlement)
*   **From User:** User paying the debt.
*   **To User:** User receiving the money.
*   **Amount:** Decimal/Currency.
*   **Timestamp:** DateTime (Defaults to Now).

### 3.5 Balance Sheet
*   **Structure:** A persisted database table/entity showing the net financial position.
*   **Update Strategy:** Must be explicitly updated (re-calculated and saved) whenever a Cost or Payment is created, modified, or deleted. Do not calculate on-the-fly for views.

### 3.6 System Log (Audit)
*   **Timestamp:** DateTime.
*   **IP Address:** String.
*   **Action:** String (e.g., "Create Event", "Add Cost").
*   **Context:** JSON/Text details of the change.

## 4. Functional Requirements

### 4.1 Event & Cost Management
*   **Create Event:** Input name, date, and select/create participating Users.
*   **Add Cost:** Select an Event, input amount, comment, and assign to a specific Payer.
*   **View Events:** List all events and their details.

### 4.2 Settlement & Finance
*   **View Balance Sheet:** Display a matrix or list of "Who owes Whom". Can be filtered by user.
*   **Log Payment:** Record a direct transfer between two users to settle a balance.
*   **Auto-Update:** The Balance Sheet must update automatically/trigger an update whenever a Cost or Payment is modified.

### 4.3 Data Hygiene (Merge Tools)
*   **User Merge:** Interface to select multiple User entities (e.g., "Dave", "David") and merge them into a single identity, reassigning all associated Costs and Payments.
*   **Event Merge:** Interface to combine multiple Events into one, aggregating their participants and costs.

### 4.4 System Logging
*   **Capture:** Log every write operation (Create, Update, Merge) with the client's IP address.
*   **Viewer:** A dedicated page to view these logs with pagination support.

## 5. User Journeys

### Journey 1: Activity Setup
1.  User opens app.
2.  Creates a new Activity (Event).
3.  Selects existing Users from the global list or adds new ones.
4.  Adds initial Costs to the Activity.
5.  *Implicit:* System updates the global Balance Sheet.

### Journey 2: Adding Expenses
1.  User opens app and selects an existing Activity.
2.  Adds a new Cost (Amount + Comment).
3.  *Implicit:* System updates the global Balance Sheet.

### Journey 3: Settlement
1.  User views the Balance Sheet to see debts.
2.  User logs a Payment ("Alice paid Bob £50").
3.  System updates the Balance Sheet to reflect the reduced debt.
