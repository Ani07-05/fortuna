import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import TransactionForm from './components/TransactionForm';
import SavingsPrediction from './components/SavingsPrediction';
import UserProfile from './components/UserProfile';
import Navbar from './components/Navbar';
import './App.css';

function App() {
  // For demonstration, we'll hardcode a user ID
  // In a real app, this would come from authentication
  const [userId] = useState('user123');
  
  return (
    <Router>
      <div className="app">
        <Navbar userId={userId} />
        <div className="container">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={<Dashboard userId={userId} />} />
            <Route path="/transactions/new" element={<TransactionForm userId={userId} />} />
            <Route path="/predict" element={<SavingsPrediction userId={userId} />} />
            <Route path="/profile" element={<UserProfile userId={userId} />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;