import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

// Base URL for API calls - direct connection to backend
const API_BASE_URL = 'http://localhost:5000/api';

function SavingsPrediction({ userId }) {
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasProfile, setHasProfile] = useState(true);
  const [hasTransactions, setHasTransactions] = useState(true);

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
    // Check if user has a profile
    const checkUserProfile = async () => {
      try {
        console.log(`Checking profile for user: ${userId}`);
        await fetchWithRetry(`${API_BASE_URL}/profile/${userId}`);
        setHasProfile(true);
        return true;
      } catch (err) {
        console.error('Profile check failed:', err.message);
        if (err.response && err.response.status === 404) {
          setHasProfile(false);
          setLoading(false);
          return false;
        }
        throw err;
      }
    };

    // Check if user has transactions
    const checkUserTransactions = async () => {
      try {
        console.log(`Checking transactions for user: ${userId}`);
        const response = await fetchWithRetry(`${API_BASE_URL}/transactions/${userId}`);
        const hasData = response.data && response.data.length > 0;
        setHasTransactions(hasData);
        return hasData;
      } catch (err) {
        console.error('Transactions check failed:', err.message);
        setHasTransactions(false);
        setLoading(false);
        return false;
      }
    };

    // Fetch predictions if profile and transactions exist
    const fetchPredictions = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const profileExists = await checkUserProfile();
        if (!profileExists) return;
        
        const transactionsExist = await checkUserTransactions();
        if (!transactionsExist) return;
        
        console.log(`Fetching predictions for user: ${userId}`);
        const response = await fetchWithRetry(`${API_BASE_URL}/predict/${userId}`);
        console.log('Predictions response received:', response.status);
        setPredictions(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching predictions:', err);
        setError(`Failed to fetch predictions: ${err.message || 'Unknown error'}`);
        setLoading(false);
      }
    };

    fetchPredictions();
  }, [userId]);

  // Prepare chart data if predictions exist
  const prepareChartData = () => {
    if (!predictions || !predictions.predictions) return null;

    const categories = Object.keys(predictions.predictions);
    const actualExpenses = categories.map(cat => predictions.predictions[cat].actual_expense);
    const potentialSavings = categories.map(cat => predictions.predictions[cat].potential_savings);

    // Comparison bar chart
    const comparisonData = {
      labels: categories,
      datasets: [
        {
          label: 'Actual Expenses',
          backgroundColor: 'rgba(255, 99, 132, 0.7)',
          data: actualExpenses
        },
        {
          label: 'Potential Savings',
          backgroundColor: 'rgba(54, 162, 235, 0.7)',
          data: potentialSavings
        }
      ]
    };

    // Savings percentage doughnut chart
    const savingsPercentageData = {
      labels: categories,
      datasets: [{
        label: 'Savings Percentage',
        backgroundColor: [
          '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
          '#9966FF', '#FF9F40', '#8AC249', '#EA5545'
        ],
        data: categories.map(cat => predictions.predictions[cat].savings_percentage)
      }]
    };

    return { comparisonData, savingsPercentageData };
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

  if (!hasProfile) {
    return (
      <div className="prediction-error">
        <h1>Profile Missing</h1>
        <p>Please complete your profile before requesting savings predictions.</p>
        <Link to="/profile" className="btn btn-primary">Create Profile</Link>
      </div>
    );
  }

  if (!hasTransactions) {
    return (
      <div className="prediction-error">
        <h1>No Transactions Found</h1>
        <p>Please add some transactions before requesting savings predictions.</p>
        <Link to="/transactions/new" className="btn btn-primary">Add Transactions</Link>
      </div>
    );
  }

  if (loading) return (
    <div className="loading-container">
      <div className="loading">Loading predictions...</div>
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

  const chartData = prepareChartData();

  return (
    <div className="savings-prediction">
      <h1>Potential Savings Prediction</h1>
      
      {predictions && predictions.totals && (
        <div className="prediction-summary">
          <div className="summary-card">
            <h3>Total Expenses</h3>
            <p className="summary-value">₹{predictions.totals.actual_expenses.toFixed(2)}</p>
          </div>
          <div className="summary-card highlight">
            <h3>Total Potential Savings</h3>
            <p className="summary-value">₹{predictions.totals.potential_savings.toFixed(2)}</p>
          </div>
          <div className="summary-card">
            <h3>Overall Savings %</h3>
            <p className="summary-value">{predictions.totals.savings_percentage.toFixed(2)}%</p>
          </div>
        </div>
      )}
      
      {chartData && (
        <div className="prediction-charts">
          <div className="chart-container">
            <h2>Expense vs. Potential Savings Comparison</h2>
            <div className="chart-wrapper">
              <Bar 
                data={chartData.comparisonData}
                options={{
                  scales: {
                    y: {
                      beginAtZero: true,
                      title: {
                        display: true,
                        text: 'Amount (₹)'
                      }
                    },
                    x: {
                      title: {
                        display: true,
                        text: 'Categories'
                      }
                    }
                  }
                }}
              />
            </div>
          </div>
          
          <div className="chart-container">
            <h2>Savings Percentage by Category</h2>
            <div className="chart-wrapper">
              <Doughnut 
                data={chartData.savingsPercentageData}
                options={{
                  plugins: {
                    tooltip: {
                      callbacks: {
                        label: function(context) {
                          return `${context.label}: ${context.raw.toFixed(2)}%`;
                        }
                      }
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}
      
      {predictions && predictions.predictions && (
        <div className="detailed-predictions">
          <h2>Detailed Savings Breakdown</h2>
          <table className="predictions-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Current Expenses</th>
                <th>Potential Savings</th>
                <th>Savings %</th>
                <th>Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(predictions.predictions).map(([category, data]) => (
                <tr key={category}>
                  <td>{category}</td>
                  <td>₹{data.actual_expense.toFixed(2)}</td>
                  <td>₹{data.potential_savings.toFixed(2)}</td>
                  <td>{data.savings_percentage.toFixed(2)}%</td>
                  <td>
                    {data.savings_percentage > 20 
                      ? "High potential for savings!" 
                      : data.savings_percentage > 10 
                        ? "Moderate savings possible" 
                        : "Good job! You're already efficient"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      <div className="savings-tips">
        <h2>Savings Tips</h2>
        <div className="tips-container">
          <div className="tip-card">
            <h3>Groceries</h3>
            <p>Plan meals, buy in bulk, and use loyalty programs to save on groceries.</p>
          </div>
          <div className="tip-card">
            <h3>Transport</h3>
            <p>Consider carpooling, public transport, or cycling for regular commutes.</p>
          </div>
          <div className="tip-card">
            <h3>Eating Out</h3>
            <p>Set a budget for dining out and look for deals and happy hours.</p>
          </div>
          <div className="tip-card">
            <h3>Entertainment</h3>
            <p>Look for free local events and use subscription services efficiently.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SavingsPrediction;