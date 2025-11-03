# Product Requirements Document: PalPay

## 1. Introduction

PalPay is a web application designed to simplify expense tracking and settlement for groups of friends. It provides a centralized platform for logging expenses related to shared activities and calculating who owes what to whom. The application is designed to be simple and accessible, with no need for user accounts or complex permissions.

## 2. Vision

To create a frictionless way for friends to manage shared expenses, ensuring transparency and fairness without the overhead of user management.

## 3. Scope

### 3.1. In-Scope Features

- **User Management (Admin):**
  - Admins can add new users.
  - Admins can update existing user details.
- **Activity Management:**
  - Users can create, update, and delete activities.
  - An activity has a name, date, and a list of participants.
- **Expense Management:**
  - Users can create, update, and delete expenses.
  - An expense is linked to a user (who paid) and an activity.
- **Settlement Calculation:**
  - The application will calculate and display the amount of money each user owes to others.
- **Payment Logging:**
  - Users can log payments made to settle debts.
  - Payments can be for the full or partial amount owed.
- **Transparency:**
  - All activities and expenses are visible to all users.
- **Audit Log:**
  - All create, update, and delete actions on activities and expenses are logged.
  - These logs are visible to all users on a dedicated page.

### 3.2. Out-of-Scope Features

- **User Authentication:** No login, passwords, or user accounts.
- **Permissions:** No access control; all users have the same permissions.
- **Payment Processing:** The application will only calculate settlements; it will not handle actual money transfers.

## 4. User Personas

- **The Organizer:** A user who creates an activity and adds initial expenses.
- **The Participant:** A user who participates in an activity and may or may not have paid for expenses.

## 5. Functional Requirements

### 5.1. Entities

- **User:**
  - Name
  - Payment Details (a simple text field for users to provide their PayPal, bank details, etc.)
  - Email
- **Activity:**
  - Name
  - Date
  - Participants (a list of Users)
- **Expense:**
  - Payer (a User)
  - Activity (linked to an Activity)
  - Amount
- **Payment:**
  - Payer (a User)
  - Payee (a User)
  - Amount
  - Date

### 5.2. User-Facing Functionality



- **View Activities:** A list of all activities, showing their name, date, and participants.

- **View Expenses:** A detailed view of an activity, showing all associated expenses, who paid, and the amount.

- **View Settlements:** A summary page displaying a consolidated matrix view of who owes whom across all activities. If a user owes zero to another, the corresponding cell will be empty. If a row or column in the matrix is entirely empty (meaning a user neither owes nor is owed by anyone), that row or column will be omitted.

- **Create/Edit/Delete Activity:** Forms to create, update, and delete activities.

- **Create/Edit/Delete Expense:** Forms to create, update, and delete expenses within an activity.

- **Log Payment:** A form to log a payment from one user to another.

- **View Audit Log:** A dedicated page to display a user-friendly log of all CRUD actions performed on activities and expenses.

### 5.3. Admin Functionality

- **Access:** Admin functions will be accessible via a secret, non-public URL.
- **User List:** A view for admins to see all users.
- **Add/Edit User:** Forms for admins to add new users or update existing ones.

## 6. Non-Functional Requirements

- **Usability:** The application should be intuitive and easy to use for non-technical users.
- **Performance:** The application should be fast and responsive.
- **Deployment:** The application will be deployed on GCP/Firebase (Free Tier).
- **UI/UX Design:**
  - **Architecture:** Multi-page application, with each page dedicated to a single primary function.
  - **Frontend Framework:** React.

## 7. Assumptions and Constraints

- The application is for a small, trusted group of users.
- The lack of authentication and permissions is a deliberate design choice for simplicity.
- The "payment details" for a user are for informational purposes only.
