import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // Adjust this if your backend is on a different host
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // User endpoints
  getUsers: () => apiClient.get('/users/'),
  createUser: (userData) => apiClient.post('/users/', userData),
  // ... other user endpoints

  // Activity endpoints
  getActivities: () => apiClient.get('/activities/'),
  createActivity: (activityData) => apiClient.post('/activities/', activityData),
  // ... other activity endpoints

  // Expense endpoints
  getExpenses: () => apiClient.get('/expenses/'),
  createExpense: (expenseData) => apiClient.post('/expenses/', expenseData),
  // ... other expense endpoints

  // Payment endpoints
  getPayments: () => apiClient.get('/payments/'),
  createPayment: (paymentData) => apiClient.post('/payments/', paymentData),
  // ... other payment endpoints

  // Balance endpoint
  getBalances: () => apiClient.get('/balances/'),
};
