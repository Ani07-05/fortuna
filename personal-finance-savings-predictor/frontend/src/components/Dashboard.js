import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Pie } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

function Dashboard({ userId }) {
  const [transactions, setTransactions] = useState([]);
  // Removing unused trendData state variable
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summaryData, setSummaryData] = useState({
    byCategory: {},
    recentTrends: []
  });

  const API_URL = 'http://localhost:5000/api';

  useEffect(() => {
    // Fetch user transactions
    const fetchTransactions = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/transactions/${userId}`);
        setTransactions(response.data);
        
        // Process data for charts
        processTransactionData(response.data);
        
        // Also fetch spending trends
        const trendResponse = await axios.get(`${API_URL}/spending-trends/${userId}`);
        // Use the trend data directly in the processTransactionData function
        // or remove if not needed
        
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch data. Please try again later.');
        setLoading(false);
        console.error('Error fetching data:', err);
      }
    };

    fetchTransactions();
  }, [userId, API_URL]);

  const processTransactionData = (transactionsData) => {
    // Group by category
    const byCategory = transactionsData.reduce((acc, transaction) => {
      const { category, amount } = transaction;
      if (!acc[category]) {
        acc[category] = 0;
      }
      acc[category] += amount;
      return acc;
    }, {});

    // Create recent trends (last 7 days)
    const today = new Date();
    const last7Days = new Array(7).fill(0).map((_, i) => {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      return date.toISOString().slice(0, 10); // Format as YYYY-MM-DD
    }).reverse();

    const recentTrends = last7Days.map(date => {
      const dayTotal = transactionsData
        .filter(t => t.date === date)
        .reduce((sum, t) => sum + t.amount, 0);
      
      return { date, amount: dayTotal };
    });

    setSummaryData({ byCategory, recentTrends });
  };

  // Prepare chart data
  const categoryChartData = {
    labels: Object.keys(summaryData.byCategory),
    datasets: [
      {
        label: 'Spending by Category',
        backgroundColor: [
          '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
          '#9966FF', '#FF9F40', '#8AC249', '#EA5545'
        ],
        data: Object.values(summaryData.byCategory)
      }
    ]
  };

  const trendChartData = {
    labels: summaryData.recentTrends.map(item => item.date),
    datasets: [
      {
        label: 'Daily Spending',
        borderColor: '#36A2EB',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        data: summaryData.recentTrends.map(item => item.amount),
        fill: true
      }
    ]
  };

  if (loading) return <div className="loading">Loading dashboard data...</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <div className="dashboard">
      <h1>Financial Dashboard</h1>
      
      <div className="dashboard-summary">
        <div className="summary-card">
          <h3>Total Transactions</h3>
          <p className="summary-value">{transactions.length}</p>
        </div>
        <div className="summary-card">
          <h3>Total Spending</h3>
          <p className="summary-value">
            ₹{transactions.reduce((sum, t) => sum + t.amount, 0).toFixed(2)}
          </p>
        </div>
        <div className="summary-card">
          <h3>Average Transaction</h3>
          <p className="summary-value">
            ₹{(transactions.reduce((sum, t) => sum + t.amount, 0) / 
              (transactions.length || 1)).toFixed(2)}
          </p>
        </div>
        <div className="summary-card">
          <h3>Categories</h3>
          <p className="summary-value">{Object.keys(summaryData.byCategory).length}</p>
        </div>
      </div>

      <div className="dashboard-charts">
        <div className="chart-container">
          <h2>Spending by Category</h2>
          <div className="chart-wrapper">
            {Object.keys(summaryData.byCategory).length > 0 ? (
              <Pie data={categoryChartData} />
            ) : (
              <p>No category data available</p>
            )}
          </div>
        </div>
        
        <div className="chart-container">
          <h2>Recent Spending Trends</h2>
          <div className="chart-wrapper">
            {summaryData.recentTrends.length > 0 ? (
              <Line data={trendChartData} />
            ) : (
              <p>No trend data available</p>
            )}
          </div>
        </div>
      </div>

      <div className="recent-transactions">
        <h2>Recent Transactions</h2>
        {transactions.length > 0 ? (
          <div className="transactions-list">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Category</th>
                  <th>Description</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 10).map((transaction) => (
                  <tr key={transaction.id}>
                    <td>{transaction.date}</td>
                    <td>{transaction.category}</td>
                    <td>{transaction.description}</td>
                    <td>₹{transaction.amount.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>No transactions found. <Link to="/transactions/new">Add a transaction</Link> to get started.</p>
        )}
      </div>

      <div className="dashboard-actions">
        <Link to="/transactions/new" className="btn btn-primary">Add Transaction</Link>
        <Link to="/predict" className="btn btn-secondary">Get Savings Prediction</Link>
      </div>
    </div>
  );
}

export default Dashboard;