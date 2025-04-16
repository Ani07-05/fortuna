import sqlite3
import random
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to sys.path to import the data_processor module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_processor import data_processor

# Categories that align with our trained models
CATEGORIES = [
    'Groceries', 
    'Transport', 
    'Eating_Out', 
    'Entertainment',
    'Utilities', 
    'Healthcare', 
    'Education', 
    'Miscellaneous'
]

# Sample descriptions for each category
DESCRIPTIONS = {
    'Groceries': ['Supermarket shopping', 'Weekly groceries', 'Fresh produce', 'Pantry items'],
    'Transport': ['Fuel refill', 'Metro pass', 'Train tickets', 'Bus fare', 'Cab ride'],
    'Eating_Out': ['Restaurant dinner', 'Lunch with friends', 'Coffee shop', 'Take-out food'],
    'Entertainment': ['Movie tickets', 'Concert', 'Streaming subscription', 'Game purchase'],
    'Utilities': ['Electricity bill', 'Water bill', 'Internet bill', 'Gas bill', 'Phone bill'],
    'Healthcare': ['Doctor visit', 'Medications', 'Health insurance', 'Gym membership'],
    'Education': ['Online course', 'Books', 'Tuition fee', 'School supplies'],
    'Miscellaneous': ['Gift purchase', 'Home repair', 'Donation', 'Household items']
}

# Sample user profile - UPDATED to use "Self_Employed" occupation to match model expectations
USER_PROFILE = {
    'user_id': 'user123',
    'age': 32,
    'dependents': 1,
    'occupation': 'Self_Employed'  # Changed from 'Salaried' to match what the model expects
}

# IMPORTANT: Use the exact same DB path as the data_processor to ensure consistency
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'finance.db'))
print(f"Actual DB path used by data_processor: {data_processor.db_path}")
# Override the data_processor's DB path to match our path
data_processor.db_path = DB_FILE
print(f"Updated data_processor to use DB path: {data_processor.db_path}")

def add_user_profile(user_id, age, dependents, occupation):
    """Add a user profile to the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if user profile already exists
    cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
    profile = cursor.fetchone()
    
    if profile:
        # Update existing profile
        cursor.execute(
            'UPDATE user_profiles SET age = ?, dependents = ?, occupation = ? WHERE user_id = ?',
            (age, dependents, occupation, user_id)
        )
        print(f"Updated profile for user {user_id}")
    else:
        # Insert new profile
        cursor.execute(
            'INSERT INTO user_profiles (user_id, age, dependents, occupation) VALUES (?, ?, ?, ?)',
            (user_id, age, dependents, occupation)
        )
        print(f"Added profile for user {user_id}")
    
    conn.commit()
    conn.close()

def add_sample_transactions(user_id, num_transactions=100):
    """Add sample transactions to the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get the current date
    end_date = datetime.now()
    
    # Generate transactions spread over the last 90 days
    for i in range(num_transactions):
        # Random date within the last 90 days
        days_ago = random.randint(0, 90)
        date = (end_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # Random category
        category = random.choice(CATEGORIES)
        
        # Random description for the category
        description = random.choice(DESCRIPTIONS[category])
        
        # Random amount (with some variance based on category)
        if category in ['Groceries', 'Utilities']:
            amount = random.uniform(500, 3000)  # Higher range for essential expenses
        elif category in ['Healthcare', 'Education']:
            amount = random.uniform(1000, 5000)  # Higher for these categories
        elif category in ['Entertainment', 'Eating_Out']:
            amount = random.uniform(200, 1500)  # Moderate range
        else:
            amount = random.uniform(100, 2000)  # Default range
        
        # Insert transaction
        cursor.execute(
            'INSERT INTO transactions (user_id, date, category, amount, description) VALUES (?, ?, ?, ?, ?)',
            (user_id, date, category, amount, description)
        )
    
    conn.commit()
    conn.close()
    print(f"Added {num_transactions} sample transactions for user {user_id}")

def check_transaction_counts():
    """Check the number of transactions in each category"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT category, COUNT(*) FROM transactions GROUP BY category')
    counts = cursor.fetchall()
    
    print("\nTransaction counts by category:")
    for category, count in counts:
        print(f"{category}: {count}")
    
    cursor.execute('SELECT COUNT(*) FROM transactions')
    total = cursor.fetchone()[0]
    print(f"\nTotal transactions: {total}")
    
    conn.close()

def test_prediction(user_id):
    """Test the prediction API for a user"""
    print("\nTesting prediction for user:", user_id)
    
    # Prepare features for prediction
    features, error = data_processor.prepare_features_for_prediction(user_id)
    if error:
        print(f"Error: {error}")
        return
    
    print("Features for prediction:", features)
    
    # Get actual expenses
    expenses = data_processor.aggregate_expenses_by_category(user_id)
    print("\nActual expenses by category:")
    for category, amount in expenses.items():
        print(f"{category}: ₹{amount:.2f}")
    
    print("\nNote: To see predictions, please run the Flask app and use the '/api/predict/user123' endpoint")

if __name__ == "__main__":
    print(f"Using database at: {DB_FILE}")
    
    # Initialize the database tables if they don't exist
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT
    )
    ''')
    
    # Create user profiles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY,
        age INTEGER,
        dependents INTEGER,
        occupation TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    
    # Add user profile
    add_user_profile(USER_PROFILE['user_id'], USER_PROFILE['age'], 
                    USER_PROFILE['dependents'], USER_PROFILE['occupation'])
    
    # Add sample transactions
    add_sample_transactions(USER_PROFILE['user_id'], 100)
    
    # Check transaction counts
    check_transaction_counts()
    
    # Test prediction functionality
    test_prediction(USER_PROFILE['user_id'])