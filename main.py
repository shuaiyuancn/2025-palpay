from fasthtml.common import *
from fastsql import Database
import os
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# --- Database Setup ---
def get_db_url():
    url = os.getenv("DATABASE_URL")
    if url: 
        print("Using DATABASE_URL from env.")
        return url.replace("postgres://", "postgresql://")
    non_pooling_url = os.getenv("POSTGRES_URL_NON_POOLING")
    if non_pooling_url: 
        print("Using POSTGRES_URL_NON_POOLING from env.")
        return non_pooling_url.replace("postgres://", "postgresql://")
    pg_url = os.getenv("POSTGRES_URL")
    if pg_url: 
        print("Using POSTGRES_URL from env.")
        return pg_url.replace("postgres://", "postgresql://")
    
    print("Using Local/Docker default DB URL.")
    return "postgresql://postgres:postgres@db:5432/postgres"

db = Database(get_db_url())

# --- Models ---
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    
@dataclass
class Event:
    id: int
    name: str
    date: date

@dataclass
class EventParticipant:
    event_id: int
    user_id: int

@dataclass
class Cost:
    id: int
    event_id: int
    payer_id: int
    amount: Decimal
    comment: str
    timestamp: datetime

@dataclass
class Payment:
    id: int
    from_user_id: int
    to_user_id: int
    amount: Decimal
    timestamp: datetime

@dataclass
class Balance:
    id: int
    debtor_id: int
    creditor_id: int
    amount: Decimal

@dataclass
class AuditLog:
    id: int
    timestamp: datetime
    ip_address: str
    action: str
    context: str

# Create tables
users = db.create(User)
events = db.create(Event)
event_participants = db.create(EventParticipant)
costs = db.create(Cost)
payments = db.create(Payment)
balances = db.create(Balance)
audit_logs = db.create(AuditLog)

# --- Logic: Accounting ---

def recalculate_balances():
    """
    Full ledger rebuild.
    1. Clear Balance table.
    2. Process all Costs -> Create Debts.
    3. Process all Payments -> Reduce Debts.
    4. Save Net Debts.
    """
    balances.delete_where() # Clear all
    
    # Using a dictionary to track net debt: (debtor, creditor) -> amount
    # If amount is positive, debtor owes creditor.
    ledger = {} 

    def add_debt(debtor, creditor, amount):
        if debtor == creditor: return
        key = (debtor, creditor)
        if key not in ledger: ledger[key] = Decimal(0)
        ledger[key] += amount

    # 1. Process Costs
    all_costs = costs()
    for cost in all_costs:
        # Get participants for this event
        parts = db.q(f"SELECT user_id FROM event_participant WHERE event_id = {cost.event_id}")
        participant_ids = [p['user_id'] for p in parts]
        
        if not participant_ids: continue
        
        # Split logic: Everyone (including payer) "consumes" an equal share.
        # Payer paid full Amount.
        # Net effect: Payer is owed (Amount - Share) by the group.
        # Each other participant owes (Share) to the Payer.
        
        share = Decimal(cost.amount) / len(participant_ids)
        for uid in participant_ids:
            if uid != cost.payer_id:
                add_debt(debtor=uid, creditor=cost.payer_id, amount=share)

    # 2. Process Payments
    all_payments = payments()
    for pay in all_payments:
        # Payment reduces the debt from Payer(Debtor) to Receiver(Creditor)
        # Or, effectively, it's a "Reverse Debt"
        # Alice owes Bob £50. Alice pays Bob £50.
        # Debt(Alice->Bob) -= 50
        
        # We handle this by adding a negative debt or a reverse credit?
        # Let's subtract from the debt.
        
        # We need to handle the case where A pays B, but maybe B owed A?
        # Standardize: Debt(A->B) is the canonical key? No.
        # Let's just subtract from (from_user, to_user)
        
        key = (pay.from_user_id, pay.to_user_id)
        if key not in ledger: ledger[key] = Decimal(0)
        ledger[key] -= Decimal(pay.amount)

    # 3. Simplify and Persist (Net Position Algorithm)
    
    # Calculate Net Position for each user
    net_balances = {} # user_id -> Decimal
    
    for (u1, u2), amt in ledger.items():
        # u1 owes u2 amt
        net_balances[u1] = net_balances.get(u1, Decimal(0)) - amt
        net_balances[u2] = net_balances.get(u2, Decimal(0)) + amt
        
    # Separate into Debtors and Creditors
    debtors = []
    creditors = []
    
    for uid, amt in net_balances.items():
        if amt < -0.01: # Tolerance for float math if any, though we use Decimal
            debtors.append({'id': uid, 'amount': amt})
        elif amt > 0.01:
            creditors.append({'id': uid, 'amount': amt})
            
    # Sort for determinism (e.g. by amount descending magnitude, then ID)
    debtors.sort(key=lambda x: (x['amount'], x['id'])) # Ascending (most negative first)
    creditors.sort(key=lambda x: (-x['amount'], x['id'])) # Descending (most positive first)
    
    # Greedy Matching
    d_idx = 0
    c_idx = 0
    
    while d_idx < len(debtors) and c_idx < len(creditors):
        debtor = debtors[d_idx]
        creditor = creditors[c_idx]
        
        # Amount to settle is min(abs(debtor), creditor)
        amount = min(abs(debtor['amount']), creditor['amount'])
        
        # Record the balance
        if amount > 0:
            balances.insert(Balance(debtor_id=debtor['id'], creditor_id=creditor['id'], amount=amount))
        
        # Update remaining amounts
        debtor['amount'] += amount
        creditor['amount'] -= amount
        
        # Move indices if settled (close to 0)
        if abs(debtor['amount']) < 0.01: d_idx += 1
        if creditor['amount'] < 0.01: c_idx += 1

# --- App Setup ---
app, rt = fast_app(
    hdrs=(
        Link(rel='stylesheet', href='https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css'),
        Link(rel='stylesheet', href='https://fonts.googleapis.com/icon?family=Material+Icons'),
        Script(src='https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js'),
        Link(rel='stylesheet', href='index.css'),
    ),
    pico=False
)

# --- Views ---

@rt('/')
def get():
    recent_events = events(order_by='date desc', limit=3)
    
    return Titled("PalPay",
        Div(cls="container")(
            # Row 1: Quick Actions & Stats
            Div(cls="row")(
                Div(cls="col s12")(
                    Div(cls="card-panel center-align")(
                        A("View Balance Sheet", href="/balances", cls="btn-flat teal-text")
                    )
                )
            ),
            
            # Row 2: Events (Vertical Stack)
            Div(cls="row")(
                Div(cls="col s12")(
                    Div(cls="card")(
                        Div(cls="card-content")(
                            Span("Recent Events", cls="card-title"),
                            Ul(cls="collection")(
                                *[Li(cls="collection-item")(
                                    A(
                                        Span(e.name, cls="title"),
                                        Span(f" ({e.date})", cls="grey-text"),
                                        href=f"/events/{e.id}", cls="black-text"
                                    )
                                ) for e in recent_events]
                            ) if recent_events else P("No events yet."),
                        ),
                        Div(cls="card-action center-align")(
                            A("New Event", href="/events/new", cls="btn-flat teal-text"),
                            " ",
                            A("All Events", href="/events/all", cls="btn-flat teal-text")
                        )
                    )
                )
            ),

            # Row 3: Admin / Setup (Vertical Stack)
            Div(cls="row")(
                Div(cls="col s12")(
                    Div(cls="card")(
                        Form(
                            Div(cls="card-content")(
                                Span("Quick Add User", cls="card-title"),
                                Div(cls="input-field")(
                                    Input(name="name", id="user_name", type="text", required=True),
                                    Label("Name", **{'for': 'user_name'})
                                )
                            ),
                            Div(cls="card-action center-align", style="border-top: 0")(
                                Button("Add", type="submit", cls="btn-small waves-effect waves-light"),
                                " ",
                                A("All Users", href="/users", cls="btn-flat teal-text")
                            ),
                            action="/users", method="post"
                        )
                    )
                )
            ),
            Div(cls="row")(
                Div(cls="col s12")(
                     Div(cls="card grey lighten-4")(
                        Div(cls="card-content")(
                            Span("Admin Tools", cls="card-title"),
                            A("Merge Tools", href="/tools", cls="btn-flat teal-text"),
                            " ",
                            A("Audit Logs", href="/logs", cls="btn-flat teal-text")
                        )
                    )
                )
            )
        )
    )

@rt('/events/all')
def get():
    all_events = events(order_by='date desc')
    return Titled("All Events",
        Div(cls="container")(
            Div(cls="row")(
                Div(cls="col s12")(
                    Ul(cls="collection with-header")(
                        Li(cls="collection-header", h4="Events History"),
                        *[Li(cls="collection-item")(
                            A(f"{e.name} - {e.date}", href=f"/events/{e.id}", cls="teal-text")
                        ) for e in all_events]
                    )
                )
            ),
            Div(cls="fixed-action-btn")(
                A(I("add"), href="/events/new", cls="btn-floating btn-large red")
            ),
             P(A("Back to Dashboard", href="/", cls="btn-flat"))
        )
    )

@rt('/users')
def get():
    all_users = users(order_by="name")
    return Titled("All Users",
        Div(cls="container")(
            Ul(cls="collection with-header")(
                Li(cls="collection-header", h4="Users Directory"),
                *[Li(cls="collection-item")(u.name) for u in all_users]
            ),
            P(A("Back to Dashboard", href="/", cls="btn-flat"))
        )
    )

@rt('/users')
def post(name: str):
    users.insert(User(name=name))
    return Redirect("/")

@rt('/tools')
def get():
    all_users = users()
    all_events = events()
    return Titled("Data Merge Tools",
        Div(cls="container")(
            Div(cls="row")(
                Div(cls="col s12 m6")(
                    Div(cls="card red lighten-5")(
                        Div(cls="card-content")(
                            Span("Merge Users", cls="card-title"),
                            P("Merge 'Source' into 'Target'. Source will be deleted.", cls="grey-text"),
                            Form(
                                Div(cls="input-field")(
                                    Select(*[Option(u.name, value=u.id) for u in all_users], name="source_id"),
                                    Label("Source (Delete)")
                                ),
                                Div(cls="input-field")(
                                    Select(*[Option(u.name, value=u.id) for u in all_users], name="target_id"),
                                    Label("Target (Keep)")
                                ),
                                Button("Merge Users", type="submit", cls="btn red darken-2 waves-effect"),
                                action="/tools/merge_users", method="post"
                            )
                        )
                    )
                ),
                Div(cls="col s12 m6")(
                    Div(cls="card red lighten-5")(
                        Div(cls="card-content")(
                            Span("Merge Events", cls="card-title"),
                            P("Merge 'Source' into 'Target'. Source will be deleted.", cls="grey-text"),
                            Form(
                                Div(cls="input-field")(
                                    Select(*[Option(f"{e.name} ({e.date})", value=e.id) for e in all_events], name="source_id"),
                                    Label("Source (Delete)")
                                ),
                                Div(cls="input-field")(
                                    Select(*[Option(f"{e.name} ({e.date})", value=e.id) for e in all_events], name="target_id"),
                                    Label("Target (Keep)")
                                ),
                                Button("Merge Events", type="submit", cls="btn red darken-2 waves-effect"),
                                action="/tools/merge_events", method="post"
                            )
                        )
                    )
                )
            ),
            P(A("Back to Dashboard", href="/", cls="btn-flat")),
            Script("document.addEventListener('DOMContentLoaded', function() { var elems = document.querySelectorAll('select'); var instances = M.FormSelect.init(elems); });")
        )
    )

@rt('/tools/merge_users')
def post(source_id: int, target_id: int):
    if source_id == target_id: return Titled("Error", P("Cannot merge user into themselves."))
    
    # 1. Update Event Participants (Handle duplicates)
    source_parts = event_participants(where=f"user_id={source_id}")
    for sp in source_parts:
        exists = event_participants(where=f"event_id={sp.event_id} AND user_id={target_id}")
        if exists:
            db.q(f"DELETE FROM event_participant WHERE event_id = {sp.event_id} AND user_id = {source_id}")
        else:
            db.q(f"UPDATE event_participant SET user_id = {target_id} WHERE event_id = {sp.event_id} AND user_id = {source_id}")
            
    # 2. Update Costs (Payer)
    db.q(f"UPDATE cost SET payer_id = {target_id} WHERE payer_id = {source_id}")
    
    # 3. Update Payments
    db.q(f"UPDATE payment SET from_user_id = {target_id} WHERE from_user_id = {source_id}")
    db.q(f"UPDATE payment SET to_user_id = {target_id} WHERE to_user_id = {source_id}")
    
    
    recalculate_balances()
    
    # 4. Delete Source
    users.delete(source_id)
    
    audit_logs.insert(AuditLog(timestamp=datetime.now(), ip_address="0.0.0.0", action="Merge Users", context=f"{source_id} -> {target_id}"))
    return Redirect("/tools")

@rt('/tools/merge_events')
def post(source_id: int, target_id: int):
    if source_id == target_id: return Titled("Error", P("Cannot merge event into itself."))

    # 1. Move Participants
    source_parts = event_participants(where=f"event_id={source_id}")
    for sp in source_parts:
        exists = event_participants(where=f"event_id={target_id} AND user_id={sp.user_id}")
        if not exists:
            db.q(f"UPDATE event_participant SET event_id = {target_id} WHERE event_id = {source_id} AND user_id = {sp.user_id}")
        else:
            db.q(f"DELETE FROM event_participant WHERE event_id = {source_id} AND user_id = {sp.user_id}")

    # 2. Move Costs
    db.q(f"UPDATE cost SET event_id = {target_id} WHERE event_id = {source_id}")
    
    # 3. Delete Source Event
    events.delete(source_id)
    
    recalculate_balances()
    audit_logs.insert(AuditLog(timestamp=datetime.now(), ip_address="0.0.0.0", action="Merge Events", context=f"{source_id} -> {target_id}"))
    return Redirect("/tools")


@rt('/events/new')
def get():
    all_users = users()
    return Title("New Event"), Div(cls="container")(
            H4("Create New Event"),
            Form(
                Div(cls="input-field")(
                    Input(name="name", id="evt_name", type="text", required=True),
                    Label("Event Name", **{'for': 'evt_name'})
                ),
                Div(cls="input-field")(
                    Input(name="date", id="evt_date", type="date", value=date.today()),
                    Label("Date", **{'for': 'evt_date', 'class': 'active'})
                ),
                Div(cls="input-field")(
                    Select(
                        *[Option(u.name, value=u.id) for u in all_users],
                        name="participants", multiple=True, required=True
                    ),
                    Label("Participants")
                ),
                Button("Create Event", type="submit", cls="btn waves-effect waves-light"),
                action="/events", method="post"
            ),
            Script("document.addEventListener('DOMContentLoaded', function() { var elems = document.querySelectorAll('select'); var instances = M.FormSelect.init(elems); });")
        )

@rt('/events')
def post(name: str, date: str, participants: List[int]):
    try:
        e = events.insert(Event(name=name, date=date))
        e_id = e.id
        for uid in participants:
            event_participants.insert(EventParticipant(event_id=e_id, user_id=uid))
        
        audit_logs.insert(AuditLog(timestamp=datetime.now(), ip_address="0.0.0.0", action="Create Event", context=f"Name: {name}"))
        return Redirect(f"/events/{e_id}")
    except Exception as e:
        return Titled("Error", Div(cls="container red-text")(P(f"Failed to create event: {e}")))

@rt('/events/{id}')
def get(id: int):
    ev = events[id]
    parts = db.q(f"SELECT u.* FROM \"user\" u JOIN event_participant ep ON u.id = ep.user_id WHERE ep.event_id = {id}")
    participant_objs = [User(**p) for p in parts]
    ev_costs = costs(where=f"event_id={id}", order_by="timestamp desc")
    user_map = {u.id: u.name for u in users()}
    
    return Titled(f"Event: {ev.name}",
        Div(cls="container")(
            Div(cls="row")(
                Div(cls="col s12 m6")(
                    Div(cls="card")(
                        Div(cls="card-content")(
                            Span(f"{ev.name}", cls="card-title"),
                            P(f"Date: {ev.date}", cls="grey-text"),
                            Div(cls="section")(
                                A(I("edit"), href=f"/events/{id}/edit", cls="btn-small flat waves-effect", title="Edit", style="margin-right: 12px;"),
                                Form(
                                    Button(I("delete"), type="submit", cls="btn-small red lighten-1 waves-effect", onclick="return confirm('Are you sure?')", title="Delete"),
                                    action=f"/events/{id}/delete", method="post", style="display:inline;"
                                )
                            ),
                            H6("Participants"),
                            Ul(cls="collection")(
                                *[Li(u.name, cls="collection-item") for u in participant_objs]
                            )
                        )
                    )
                ),
                Div(cls="col s12 m6")(
                    Div(cls="card")(
                        Div(cls="card-content")(
                            Span("Add Expense", cls="card-title"),
                            Form(
                                Div(cls="input-field")(
                                    Input(name="amount", id="amt", type="number", step="0.01", required=True),
                                    Label("Amount (£)", **{'for': 'amt'})
                                ),
                                Div(cls="input-field")(
                                    Input(name="comment", id="desc", type="text", required=True),
                                    Label("Description", **{'for': 'desc'})
                                ),
                                Div(cls="input-field")(
                                    Select(*[Option(u.name, value=u.id) for u in participant_objs], name="payer_id", required=True),
                                    Label("Who Paid?")
                                ),
                                Button("Add Cost", type="submit", cls="btn waves-effect waves-light"),
                                action=f"/events/{id}/costs", method="post"
                            )
                        )
                    )
                )
            ),
            Div(cls="row")(
                Div(cls="col s12")(
                    Div(cls="card")(
                        Div(cls="card-content")(
                            Span("Expense Log", cls="card-title"),
                            Table(cls="striped highlight responsive-table")(
                                Thead(Tr(Th("Amount"), Th("Payer"), Th("Desc"))),
                                Tbody(*[
                                    Tr(
                                        Td(f"£{float(c.amount):.2f}", cls="green-text" if float(c.amount) > 0 else ""),
                                        Td(user_map.get(c.payer_id, "Unknown")),
                                        Td(c.comment)
                                    ) for c in ev_costs
                                ])
                            ) if ev_costs else P("No expenses recorded yet.")
                        )
                    )
                )
            ),
            P(A("Back to Dashboard", href="/", cls="btn-flat")),
            Script("document.addEventListener('DOMContentLoaded', function() { var elems = document.querySelectorAll('select'); var instances = M.FormSelect.init(elems); });")
        )
    )

@rt('/events/{id}/edit')
def get(id: int):
    ev = events[id]
    all_users = users()
    parts = db.q(f"SELECT user_id FROM event_participant WHERE event_id = {id}")
    current_ids = {p['user_id'] for p in parts}
    
    return Titled(f"Edit Event: {ev.name}",
        Div(cls="container")(
            H4("Edit Event"),
            Form(
                Div(cls="input-field")(
                    Input(name="name", id="evt_name", type="text", value=ev.name, required=True),
                    Label("Event Name", **{'for': 'evt_name', 'class': 'active'})
                ),
                Div(cls="input-field")(
                    Input(name="date", id="evt_date", type="date", value=ev.date),
                    Label("Date", **{'for': 'evt_date', 'class': 'active'})
                ),
                Div(cls="input-field")(
                    Select(
                        *[Option(u.name, value=u.id, selected=(u.id in current_ids)) for u in all_users],
                        name="participants", multiple=True, required=True
                    ),
                    Label("Participants")
                ),
                Button("Save Changes", type="submit", cls="btn waves-effect waves-light"),
                action=f"/events/{id}/edit", method="post"
            ),
            P(A("Cancel", href=f"/events/{id}", cls="btn-flat")),
            Script("document.addEventListener('DOMContentLoaded', function() { var elems = document.querySelectorAll('select'); var instances = M.FormSelect.init(elems); });")
        )
    )

@rt('/events/{id}/edit')
def post(id: int, name: str, date: str, participants: List[int]):
    ev = events[id]
    ev.name = name
    ev.date = date
    events.update(ev)
    
    parts = db.q(f"SELECT user_id FROM event_participant WHERE event_id = {id}")
    current_ids = {p['user_id'] for p in parts}
    new_ids = set(participants)
    
    to_remove = current_ids - new_ids
    for uid in to_remove:
        db.q(f"DELETE FROM event_participant WHERE event_id = {id} AND user_id = {uid}")
        
    to_add = new_ids - current_ids
    for uid in to_add:
        event_participants.insert(EventParticipant(event_id=id, user_id=uid))
        
    recalculate_balances()
    audit_logs.insert(AuditLog(timestamp=datetime.now(), ip_address="0.0.0.0", action="Edit Event", context=f"ID: {id}"))
    return Redirect(f"/events/{id}")

@rt('/events/{id}/delete')
def post(id: int):
    # 1. Delete Costs (Cascade logic manually because simple DB)
    db.q(f"DELETE FROM cost WHERE event_id = {id}")
    
    # 2. Delete Participants
    db.q(f"DELETE FROM event_participant WHERE event_id = {id}")
    
    # 3. Delete Event
    events.delete(id)
    
    # 4. Recalculate
    recalculate_balances()
    audit_logs.insert(AuditLog(timestamp=datetime.now(), ip_address="0.0.0.0", action="Delete Event", context=f"ID: {id}"))
    return Redirect("/")

@rt('/events/{id}/costs')
def post(id: int, amount: float, comment: str, payer_id: int):
    costs.insert(Cost(event_id=id, payer_id=payer_id, amount=Decimal(amount), comment=comment, timestamp=datetime.now()))
    recalculate_balances()
    audit_logs.insert(AuditLog(timestamp=datetime.now(), ip_address="0.0.0.0", action="Add Cost", context=f"Event {id}, Amount {amount}"))
    return Redirect(f"/events/{id}")

@rt('/balances')
def get(sort: str = 'amount'):
    all_users = users()
    user_map = {u.id: u.name for u in all_users}
    
    all_bals = balances()
    
    # Sorting logic
    if sort == 'debtor':
        all_bals.sort(key=lambda b: user_map.get(b.debtor_id, "").lower())
    elif sort == 'creditor':
        all_bals.sort(key=lambda b: user_map.get(b.creditor_id, "").lower())
    else: # amount
        all_bals.sort(key=lambda b: b.amount, reverse=True)
    
    return Titled("Balance Sheet",
        Div(cls="container")(
            Div(cls="row")(
                Div(cls="col s12")(
                    Div(cls="card")(
                        Div(cls="card-content")(
                            Span("Net Debts", cls="card-title"),
                            Table(cls="striped highlight")(
                                Thead(Tr(
                                    Th(A("Debtor (Owes)", href="?sort=debtor", cls="teal-text")), 
                                    Th(A("Creditor (Is Owed)", href="?sort=creditor", cls="teal-text")), 
                                    Th(A("Amount", href="?sort=amount", cls="teal-text"))
                                )),
                                Tbody(*[
                                    Tr(
                                        Td(user_map.get(b.debtor_id, "Unknown")),
                                        Td(user_map.get(b.creditor_id, "Unknown")),
                                        Td(f"£{float(b.amount):.2f}", cls="red-text")
                                    ) for b in all_bals
                                ])
                            ) if all_bals else P("All settled up! No debts.", cls="green-text")
                        )
                    )
                )
            ),
            Div(cls="row")(
                Div(cls="col s12")(
                    Div(cls="card")(
                        Div(cls="card-content")(
                            Span("Record Payment (Settle Up)", cls="card-title"),
                            Form(
                                Div(cls="row")(
                                    Div(cls="input-field col s12 m4")(
                                        Select(*[Option(u.name, value=u.id) for u in all_users], name="from_user_id"),
                                        Label("From (Payer)")
                                    ),
                                    Div(cls="input-field col s12 m4")(
                                        Select(*[Option(u.name, value=u.id) for u in all_users], name="to_user_id"),
                                        Label("To (Receiver)")
                                    ),
                                    Div(cls="input-field col s12 m4")(
                                        Input(name="amount", id="pay_amt", type="number", step="0.01", required=True),
                                        Label("Amount (£)", **{'for': 'pay_amt'})
                                    )
                                ),
                                Button("Record Payment", type="submit", cls="btn waves-effect waves-light"),
                                action="/payments", method="post"
                            )
                        )
                    )
                )
            ),
            P(A("Back to Dashboard", href="/", cls="btn-flat")),
            Script("document.addEventListener('DOMContentLoaded', function() { var elems = document.querySelectorAll('select'); var instances = M.FormSelect.init(elems); });")
        )
    )

@rt('/payments')
def post(from_user_id: int, to_user_id: int, amount: float):
    payments.insert(Payment(from_user_id=from_user_id, to_user_id=to_user_id, amount=Decimal(amount), timestamp=datetime.now()))
    recalculate_balances()
    audit_logs.insert(AuditLog(timestamp=datetime.now(), ip_address="0.0.0.0", action="Payment", context=f"{from_user_id}->{to_user_id}: {amount}"))
    return Redirect("/balances")



@rt('/logs')
def get(page: int = 0):
    limit = 50
    offset = page * limit
    logs = audit_logs(order_by="timestamp desc", limit=limit, offset=offset)
    
    return Titled("System Audit Logs",
        Div(cls="container")(
             Div(cls="card")(
                Div(cls="card-content")(
                    Table(cls="striped responsive-table")(
                        Thead(Tr(Th("Time"), Th("Action"), Th("Context"), Th("IP"))),
                        Tbody(*[
                            Tr(
                                Td(l.timestamp),
                                Td(l.action),
                                Td(l.context),
                                Td(l.ip_address)
                            ) for l in logs
                        ])
                    )
                ),
                Div(cls="card-action")(
                    A("Previous", href=f"/logs?page={page-1}", cls="btn-flat") if page > 0 else "",
                    A("Next", href=f"/logs?page={page+1}", cls="btn-flat") if len(logs) == limit else ""
                )
             ),
             P(A("Back to Dashboard", href="/", cls="btn-flat"))
        )
    )

if __name__ == "__main__":
    serve()