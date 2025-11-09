this folder contains doc and code for the website "palpay" which allows a group of friends log expense and settle split payment.

# use cases

the website has the following entities
- user (name, email, and payment details which are simple text for information only)
- activity (name, date, participants which are a list of users)
- expense (one user pays for some cost in one activity; there could be multiple expenses in one activity, and they could be paid by different users)
- balance (one user owes some amount to another user)
- payment (one user pays another to settle the balance)

the website provides the following functions
- a user can create/update/delete an activity
- a user can create/update/delete an expense
- a user can create/update/delete a payment
- shows amount of money that one user is owed to one other
- all activities are logged and visible to all users

the website doesn't need these functions
- login or password
- permission or access control -- anyone can do anything

in the admin control, the website has the following functions
- adding new users
- update users' details

# implementation

the website is implemented using python, fastapi, and other necessary tools. python env is managed by uv.

the website is deployed in gcp using firebase free plan. the service account with admin access is configured in .env

the website uses github. the address is git@github.com:shuaiyuancn/2025-palpay.git

the project uses a local todo.md to track tasks and progress.

during the development, do frequent commit with concise message.

set up unit tests and integration tests. do test-driven dev. make sure all tests pass with every commit.
