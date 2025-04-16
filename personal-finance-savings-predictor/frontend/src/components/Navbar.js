import React from 'react';
import { Link } from 'react-router-dom';

function Navbar({ userId }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">Personal Finance Optimizer</div>
      <div className="navbar-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/transactions/new">Add Transaction</Link>
        <Link to="/predict">Savings Prediction</Link>
        <Link to="/profile">Profile</Link>
      </div>
      <div className="navbar-user">
        User: {userId}
      </div>
    </nav>
  );
}

export default Navbar;