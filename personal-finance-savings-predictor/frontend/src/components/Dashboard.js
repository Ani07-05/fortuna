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

// Base URL for API calls - direct connection to backend
const API_BASE_URL = 'http://localhost:5000/api';

function Dashboard({ userId }) {
  const [transactions, setTransactions] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summaryData, setSummaryData] = useState({
    byCategory: {},
    recentTrends: []
  });

  // Retry logic for API calls
  const fetchWithRetry = async (url, maxRetries = 3) => {
    let retries = 0;
    
    while (retries < maxRetries) {
      try {
        console.log(`Attempting to fetch from ${url}, attempt ${retries + 1} of ${maxRetries}`);
        return await axios.get(url, {
          timeout: 10000, // 10 second timeout
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
      } catch (error) {
        retries++;
        console.error(`Attempt ${retries} failed:`, error.message);
        
        if (retries === maxRetries) {
          throw error;
        }
        
        // Wait before retrying (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, 1000 * retries));
      }
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log(`Fetching transactions for user: ${userId}`);
        
        // Fetch transactions with direct URL
        let transactionsData = [];
        try {
          const response = await fetchWithRetry(`${API_BASE_URL}/transactions/${userId}`);
          console.log('Transactions response received:', response.status);
          transactionsData = response.data;
          setTransactions(transactionsData);
        } catch (txError) {
          console.error('Failed to fetch transactions:', txError);
          throw new Error(`Couldn't load transactions: Request failed with status code ${txError.response?.status || 'unknown'}`);
        }
        
        // Fetch spending trends (if this fails, we'll still show dashboard with transaction data only)
        try {
          const trendResponse = await fetchWithRetry(`${API_BASE_URL}/spending-trends/${userId}`);
          console.log('Trends response received:', trendResponse.status);
          setTrendData(trendResponse.data);
          
          // Process all data
          processTransactionData(transactionsData, trendResponse.data);
        } catch (trendError) {
          console.warn('Could not fetch trend data, using transactions for trends calculation:', trendError);
          // Still process transactions even if trends API fails
          processTransactionData(transactionsData);
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Error in data fetching:', err);
        setError(`${err.message || 'Failed to connect to the server'}. Please check if the backend is running.`);
        setLoading(false);
      }
    };

    fetchData();
  }, [userId]);

  const processTransactionData = (transactionsData, trendsData = null) => {
    if (!transactionsData || transactionsData.length === 0) {
      console.warn('No transaction data available for processing');
      return;
    }
    
    console.log(`Processing ${transactionsData.length} transactions`);
    
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
    let recentTrends = [];
    
    // If we have trend data from the API, use it
    if (trendsData && trendsData.daily_spending) {
      console.log('Using API trend data');
      recentTrends = trendsData.daily_spending;
    } else {
      console.log('Calculating trends from transaction data');
      // Calculate it from transactions
      const today = new Date();
      const last7Days = new Array(7).fill(0).map((_, i) => {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        return date.toISOString().slice(0, 10); // Format as YYYY-MM-DD
      }).reverse();

      recentTrends = last7Days.map(date => {
        const dayTotal = transactionsData
          .filter(t => t.date === date)
          .reduce((sum, t) => sum + t.amount, 0);
        
        return { date, amount: dayTotal };
      });
    }

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

  // Verify backend connection
  const checkBackendConnection = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/health`);
      if (response.data.status === 'healthy') {
        window.location.reload();
      } else {
        setError('Backend is responding but reports unhealthy status. Please check server logs.');
        setLoading(false);
      }
    } catch (err) {
      setError('Backend connection check failed. Make sure Flask is running on port 5000.');
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="loading-container">
      <div className="loading">Loading dashboard data...</div>
      <p>Connecting to backend server at {API_BASE_URL}...</p>
    </div>
  );
  
  if (error) return (
    <div className="error-container">
      <div className="error-message">{error}</div>
      <div className="error-actions">
        <button onClick={checkBackendConnection} className="btn btn-primary">Retry</button>
        <p>Make sure your Flask backend is running on port 5000</p>
        <p><small>Technical details: Connection to {API_BASE_URL} failed</small></p>
      </div>
    </div>
  );

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