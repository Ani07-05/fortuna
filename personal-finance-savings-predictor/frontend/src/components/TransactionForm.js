import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function TransactionForm({ userId }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    category: '',
    amount: '',
    description: '',
    date: new Date().toISOString().split('T')[0] // Today's date in YYYY-MM-DD format
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [quickInput, setQuickInput] = useState('');

  const apiURL = 'http://localhost:5000/api';

  // Predefined expense categories
  const categories = [
    'Groceries', 
    'Transport', 
    'Eating_Out', 
    'Entertainment', 
    'Utilities', 
    'Healthcare', 
    'Education', 
    'Miscellaneous'
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name === 'amount' ? parseFloat(value) || '' : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Validate form data
      if (!formData.category || !formData.amount || !formData.description) {
        throw new Error('Please fill in all required fields');
      }

      // Submit transaction to the API
      await axios.post(`${apiURL}/transactions`, {
        user_id: userId,
        category: formData.category,
        amount: formData.amount,
        description: formData.description,
        date: formData.date
      });

      setSuccess(true);
      setFormData({
        category: '',
        amount: '',
        description: '',
        date: new Date().toISOString().split('T')[0]
      });
      setQuickInput('');

      // Redirect to dashboard after short delay
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to add transaction. Please try again.');
      console.error('Error adding transaction:', err);
    } finally {
      setLoading(false);
    }
  };

  // Function to parse transaction from text input
  const parseTransactionText = async () => {
    if (!quickInput.trim()) return;
    
    try {
      const response = await axios.post(`${apiURL}/parse-transaction`, {
        text: quickInput
      });
      
      const { description, amount, category } = response.data;
      
      setFormData({
        ...formData,
        description,
        amount,
        category
      });
    } catch (err) {
      setError('Could not parse transaction. Please use format: "Item amount category"');
      console.error('Error parsing transaction:', err);
    }
  };

  const handleQuickInputChange = (e) => {
    setQuickInput(e.target.value);
  };

  const handleQuickInputSubmit = (e) => {
    e.preventDefault();
    parseTransactionText();
  };

  return (
    <div className="transaction-form-container">
      <h1>Add New Transaction</h1>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">Transaction added successfully!</div>}
      
      <div className="quick-input">
        <h3>Quick Input</h3>
        <p>Enter transaction in format: "Item amount category"</p>
        <p>Example: "Samosa 30rs food" or "Doctor fees 200rs medical"</p>
        <form onSubmit={handleQuickInputSubmit}>
          <input
            type="text"
            placeholder="Enter transaction details"
            className="text-input"
            value={quickInput}
            onChange={handleQuickInputChange}
          />
          <button type="submit" className="btn">Parse</button>
        </form>
      </div>
      
      <form onSubmit={handleSubmit} className="transaction-form">
        <div className="form-group">
          <label htmlFor="category">Category:</label>
          <select
            id="category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            required
          >
            <option value="">Select a category</option>
            {categories.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="amount">Amount (₹):</label>
          <input
            type="number"
            id="amount"
            name="amount"
            value={formData.amount}
            onChange={handleChange}
            placeholder="Enter amount"
            min="0"
            step="0.01"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="description">Description:</label>
          <input
            type="text"
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="What did you spend on?"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="date">Date:</label>
          <input
            type="date"
            id="date"
            name="date"
            value={formData.date}
            onChange={handleChange}
            required
          />
        </div>
        
        <button 
          type="submit" 
          className="submit-btn" 
          disabled={loading}
        >
          {loading ? 'Adding...' : 'Add Transaction'}
        </button>
      </form>
    </div>
  );
}

export default TransactionForm;