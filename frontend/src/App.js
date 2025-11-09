import React, { useState, useEffect } from 'react';
import api from './api';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row, Col, Form, Button, ListGroup, Card } from 'react-bootstrap';

function App() {
  const [users, setUsers] = useState([]);
  const [activities, setActivities] = useState([]);
  const [balances, setBalances] = useState([]);
  
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [activityName, setActivityName] = useState('');
  const [expenseAmount, setExpenseAmount] = useState('');
  const [expensePayer, setExpensePayer] = useState('');
  const [expenseActivity, setExpenseActivity] = useState('');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentFrom, setPaymentFrom] = useState('');
  const [paymentTo, setPaymentTo] = useState('');


  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const usersRes = await api.getUsers();
    setUsers(usersRes.data);
    const activitiesRes = await api.getActivities();
    setActivities(activitiesRes.data);
    const balancesRes = await api.getBalances();
    setBalances(balancesRes.data);
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    await api.createUser({ name: userName, email: userEmail });
    setUserName('');
    setUserEmail('');
    fetchData();
  };

  const handleCreateActivity = async (e) => {
    e.preventDefault();
    // For simplicity, all users are added to the activity
    await api.createActivity({ name: activityName, participants: users });
    setActivityName('');
    fetchData();
  };
  
  const handleCreateExpense = async (e) => {
    e.preventDefault();
    const activity = activities.find(a => a.id === expenseActivity);
    if (activity) {
      await api.createExpense({ 
        amount: parseFloat(expenseAmount), 
        paid_by_user_id: expensePayer, 
        activity_id: expenseActivity,
        participants: activity.participants
      });
      setExpenseAmount('');
      setExpensePayer('');
      setExpenseActivity('');
      fetchData();
    }
  };

  const handleCreatePayment = async (e) => {
    e.preventDefault();
    await api.createPayment({ 
      amount: parseFloat(paymentAmount), 
      from_user_id: paymentFrom, 
      to_user_id: paymentTo 
    });
    setPaymentAmount('');
    setPaymentFrom('');
    setPaymentTo('');
    fetchData();
  };


  return (
    <Container className="mt-5">
      <Row>
        <Col>
          <Card>
            <Card.Body>
              <Card.Title>Users</Card.Title>
              <ListGroup>
                {users.map(user => <ListGroup.Item key={user.id}>{user.name}</ListGroup.Item>)}
              </ListGroup>
              <Form onSubmit={handleCreateUser} className="mt-3">
                <Form.Group>
                  <Form.Control type="text" placeholder="User Name" value={userName} onChange={e => setUserName(e.target.value)} />
                  <Form.Control type="email" placeholder="User Email" value={userEmail} onChange={e => setUserEmail(e.target.value)} className="mt-2" />
                </Form.Group>
                <Button type="submit" className="mt-2">Add User</Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
        <Col>
          <Card>
            <Card.Body>
              <Card.Title>Activities</Card.Title>
              <ListGroup>
                {activities.map(activity => <ListGroup.Item key={activity.id}>{activity.name}</ListGroup.Item>)}
              </ListGroup>
              <Form onSubmit={handleCreateActivity} className="mt-3">
                <Form.Group>
                  <Form.Control type="text" placeholder="Activity Name" value={activityName} onChange={e => setActivityName(e.target.value)} />
                </Form.Group>
                <Button type="submit" className="mt-2">Add Activity</Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      <Row className="mt-4">
        <Col>
          <Card>
            <Card.Body>
              <Card.Title>Add Expense</Card.Title>
              <Form onSubmit={handleCreateExpense}>
                <Form.Group>
                  <Form.Control type="number" placeholder="Amount" value={expenseAmount} onChange={e => setExpenseAmount(e.target.value)} />
                  <Form.Control as="select" value={expensePayer} onChange={e => setExpensePayer(e.target.value)} className="mt-2">
                    <option value="">Payer</option>
                    {users.map(user => <option key={user.id} value={user.id}>{user.name}</option>)}
                  </Form.Control>
                  <Form.Control as="select" value={expenseActivity} onChange={e => setExpenseActivity(e.target.value)} className="mt-2">
                    <option value="">Activity</option>
                    {activities.map(activity => <option key={activity.id} value={activity.id}>{activity.name}</option>)}
                  </Form.Control>
                </Form.Group>
                <Button type="submit" className="mt-2">Add Expense</Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
        <Col>
          <Card>
            <Card.Body>
              <Card.Title>Add Payment</Card.Title>
              <Form onSubmit={handleCreatePayment}>
                <Form.Group>
                  <Form.Control type="number" placeholder="Amount" value={paymentAmount} onChange={e => setPaymentAmount(e.target.value)} />
                  <Form.Control as="select" value={paymentFrom} onChange={e => setPaymentFrom(e.target.value)} className="mt-2">
                    <option value="">From</option>
                    {users.map(user => <option key={user.id} value={user.id}>{user.name}</option>)}
                  </Form.Control>
                  <Form.Control as="select" value={paymentTo} onChange={e => setPaymentTo(e.target.value)} className="mt-2">
                    <option value="">To</option>
                    {users.map(user => <option key={user.id} value={user.id}>{user.name}</option>)}
                  </Form.Control>
                </Form.Group>
                <Button type="submit" className="mt-2">Add Payment</Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      <Row className="mt-4">
        <Col>
          <Card>
            <Card.Body>
              <Card.Title>Balances</Card.Title>
              <ListGroup>
                {balances.map((balance, index) => (
                  <ListGroup.Item key={index}>
                    {balance.debtor.name} owes {balance.creditor.name} ${balance.amount.toFixed(2)}
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default App;
