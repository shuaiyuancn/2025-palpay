this folder contains doc and code for the website "palpay" which allows a group of friends log expense and settle split payment.

# use cases

the website has the following entities
- user (name, payment details, and email)
- activity (name, date, participants which are a list of users)
- expense (linked with user and activity, amount)

the website provides the following functions
- a user can create/update/delete an activity
- a user can create/update/delete expense
- shows amount of money that one user is owed to others
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

the website uses github. the address is git@github.com:shuaiyuancn/palpay.git

the project uses a local todo.md to track tasks and progress.

during the development, do frequent commit with concise message.

set up unit tests and integration tests. do test-driven dev. make sure all tests pass with every commit.

# integration test cases

use these cases to make sure the calculation logic is correct.
these are basic test cases, don't limit yourself to just these.

## case 1

user u1 and u2 joined activity a1. u1 paid 10. in the end u2 owe u1 5.

## case 2

user u1 and u2 joined activity a1. u1 paid 10.
u2 and u3 joined activity a2. u2 paid 10.
in the end u2 owe u1 5. u3 owe u2 5.

## case 3

user u1, u2, and u3 joined activity a1. u1 paid 15.
u2 and u3 joined activity a2. u2 paid 10.
in the end u2 owe u1 5. u3 owe u2 5. u3 owe u1 5.

