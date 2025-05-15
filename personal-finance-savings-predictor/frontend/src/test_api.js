// A simple test file to verify direct API connections
// Run with Node.js: node test_api.js

const fetch = require('node-fetch');

const API_BASE_URL = 'http://localhost:5000/api';
const USER_ID = 'user123';

// Test health endpoint
async function testHealth() {
  try {
    console.log('Testing API health endpoint...');
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();
    console.log('Health Status:', response.status, data);
    return response.ok;
  } catch (error) {
    console.error('Health check failed:', error.message);
    return false;
  }
}

// Test transactions endpoint
async function testTransactions() {
  try {
    console.log('Testing transactions endpoint...');
    const response = await fetch(`${API_BASE_URL}/transactions/${USER_ID}`);
    const data = await response.json();
    console.log('Transactions Status:', response.status);
    console.log('Number of transactions:', Array.isArray(data) ? data.length : 'Not an array');
    if (Array.isArray(data) && data.length > 0) {
      console.log('First transaction:', data[0]);
    }
    return response.ok;
  } catch (error) {
    console.error('Transactions test failed:', error.message);
    return false;
  }
}

// Test profile endpoint
async function testProfile() {
  try {
    console.log('Testing profile endpoint...');
    const response = await fetch(`${API_BASE_URL}/profile/${USER_ID}`);
    const data = await response.json();
    console.log('Profile Status:', response.status, data);
    return response.ok;
  } catch (error) {
    console.error('Profile test failed:', error.message);
    return false;
  }
}

// Run all tests
async function runTests() {
  const healthOk = await testHealth();
  console.log('-'.repeat(50));
  
  const transactionsOk = await testTransactions();
  console.log('-'.repeat(50));
  
  const profileOk = await testProfile();
  console.log('-'.repeat(50));
  
  console.log('Test Results:');
  console.log('Health:', healthOk ? '✓' : '✗');
  console.log('Transactions:', transactionsOk ? '✓' : '✗');
  console.log('Profile:', profileOk ? '✓' : '✗');
}

runTests();