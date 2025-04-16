import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import sqlite3
import os
import pickle

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Utility class for processing transaction data for the Personal Finance Savings Predictor app.
    Provides methods for data cleaning, aggregation, and feature extraction.
    """
    
    def __init__(self, db_path='finance.db'):
        """
        Initialize the DataProcessor with the database path.
        
        Parameters:
        -----------
        db_path : str
            Path to the SQLite database
        """
        self.db_path = db_path
        self._check_db()
    
    def _check_db(self):
        """Check if database exists and initialize it if not."""
        if not os.path.exists(self.db_path):
            logger.info(f"Database not found at {self.db_path}. Initializing new database.")
            self._init_db()
        
    def _init_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
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
        logger.info("Database initialized with required tables.")
    
    def get_user_profile(self, user_id):
        """
        Retrieve user profile data from the database.
        
        Parameters:
        -----------
        user_id : str
            The user's unique identifier
            
        Returns:
        --------
        dict or None
            User profile data or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        profile = cursor.fetchone()
        
        conn.close()
        
        if profile:
            return dict(profile)
        return None
    
    def get_user_transactions(self, user_id, start_date=None, end_date=None):
        """
        Retrieve user transactions from the database with optional date filtering.
        
        Parameters:
        -----------
        user_id : str
            The user's unique identifier
        start_date : str, optional
            Start date for filtering (format: YYYY-MM-DD)
        end_date : str, optional
            End date for filtering (format: YYYY-MM-DD)
            
        Returns:
        --------
        list
            List of transaction dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM transactions WHERE user_id = ?'
        params = [user_id]
        
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY date DESC'
        
        cursor.execute(query, params)
        transactions = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return transactions
    
    def aggregate_expenses_by_category(self, user_id, period='all'):
        """
        Aggregate user expenses by category.
        
        Parameters:
        -----------
        user_id : str
            The user's unique identifier
        period : str, optional
            Time period for aggregation ('all', 'month', 'week', 'day')
            
        Returns:
        --------
        dict
            Dictionary with category as key and total amount as value
        """
        today = datetime.now().date()
        
        if period == 'month':
            start_date = (today.replace(day=1)).strftime('%Y-%m-%d')
        elif period == 'week':
            start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        elif period == 'day':
            start_date = today.strftime('%Y-%m-%d')
        else:  # 'all'
            start_date = None
        
        transactions = self.get_user_transactions(user_id, start_date)
        
        # Aggregate by category
        expenses_by_category = {}
        for transaction in transactions:
            category = transaction['category']
            amount = transaction['amount']
            
            if category not in expenses_by_category:
                expenses_by_category[category] = 0
            
            expenses_by_category[category] += amount
        
        return expenses_by_category
    
    def prepare_features_for_prediction(self, user_id):
        """
        Prepare features for ML prediction.
        
        Parameters:
        -----------
        user_id : str
            The user's unique identifier
            
        Returns:
        --------
        tuple
            (DataFrame of features, error message or None)
        """
        # Get user profile
        profile = self.get_user_profile(user_id)
        
        if not profile:
            return None, "User profile not found. Please complete your profile first."
        
        # Get aggregated expenses by category
        expenses = self.aggregate_expenses_by_category(user_id)
        
        # Define expected expense categories in the exact order they were during training
        expected_categories = [
            'Groceries', 'Transport', 'Eating_Out', 'Entertainment', 
            'Utilities', 'Healthcare', 'Education', 'Miscellaneous'
        ]
        
        # Fill in missing categories with zeros
        for category in expected_categories:
            if category not in expenses:
                expenses[category] = 0
        
        # Load a model to get the exact feature names and order
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'models', 'models', 'groceries_model.pkl')
        try:
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                    if hasattr(model, 'feature_names_in_'):
                        logger.info(f"Model expects features in this order: {model.feature_names_in_}")
                        expected_columns = model.feature_names_in_.tolist()
                    else:
                        logger.warning("Model does not have feature_names_in_ attribute, using default order")
                        expected_columns = ['Age', 'Dependents', 'Occupation_Self_Employed', 
                                          'Occupation_Student', 'Occupation_Retired'] + expected_categories
            else:
                logger.warning(f"Model file not found at {model_path}, using default order")
                expected_columns = ['Age', 'Dependents', 'Occupation_Self_Employed', 
                                   'Occupation_Student', 'Occupation_Retired'] + expected_categories
        except Exception as e:
            logger.error(f"Error loading model to get feature names: {str(e)}")
            expected_columns = ['Age', 'Dependents', 'Occupation_Self_Employed', 
                               'Occupation_Student', 'Occupation_Retired'] + expected_categories
        
        # Create a dictionary with all expected columns (initialize with zeros)
        features = {col: 0 for col in expected_columns}
        
        # Set demographic features
        features['Age'] = profile['age']
        features['Dependents'] = profile['dependents']
        
        # Map and set occupation feature
        occupation = profile['occupation']
        occupation_mapping = {
            'Business': 'Occupation_Self_Employed',
            'Freelancer': 'Occupation_Self_Employed',
            'Self_Employed': 'Occupation_Self_Employed',
            'Student': 'Occupation_Student',
            'Retired': 'Occupation_Retired',
        }
        
        if occupation in occupation_mapping:
            occ_feature = occupation_mapping[occupation]
            if occ_feature in features:
                features[occ_feature] = 1
                logger.info(f"Set occupation feature {occ_feature} = 1 for occupation '{occupation}'")
            else:
                logger.warning(f"Mapped occupation feature {occ_feature} not in expected columns")
        else:
            logger.warning(f"Occupation '{occupation}' not found in mapping, no occupation feature set to 1")
        
        # Set expense category values
        for category in expected_categories:
            if category in features:
                features[category] = expenses[category]
            else:
                logger.warning(f"Category {category} not in expected columns")
        
        # Create DataFrame with the exact columns in the exact order
        features_df = pd.DataFrame([features])
        
        # Make sure all expected columns are present and in the correct order
        if set(features_df.columns) != set(expected_columns):
            logger.warning(f"Feature mismatch. Model expects: {expected_columns}, Got: {features_df.columns}")
        
        # Reorder columns to match expected order exactly
        features_df = features_df[expected_columns]
        
        logger.info(f"Feature preparation complete. Features: {features_df.columns.tolist()}")
        return features_df, None
    
    def parse_transaction_text(self, text):
        """
        Parse natural language transaction text.
        
        Parameters:
        -----------
        text : str
            Natural language description of a transaction
            
        Returns:
        --------
        dict or None
            Parsed transaction data or None if parsing fails
        """
        try:
            # Try different regex patterns
            # Pattern 1: "Item amount category"
            import re
            
            # Try to match different formats
            patterns = [
                r'(.+?)\s+(\d+)(?:rs|?)?\s+(.+)',  # "Samosa 30rs food"
                r'(.+?)\s+(\d+(?:\.\d+)?)(?:rs|?)?\s+(.+)',  # "Samosa 30.50rs food"
                r'(.+?)\s+(?:rs|?)?(\d+(?:\.\d+)?)\s+(.+)',  # "Samosa rs30.50 food"
            ]
            
            match = None
            for pattern in patterns:
                match = re.match(pattern, text, re.IGNORECASE)
                if match:
                    break
            
            if not match:
                return None
            
            description, amount, category = match.groups()
            
            # Map the input category to one of our predefined categories
            category_map = {
                'food': 'Eating_Out',
                'grocery': 'Groceries',
                'groceries': 'Groceries',
                'transport': 'Transport',
                'travel': 'Transport',
                'entertainment': 'Entertainment',
                'movie': 'Entertainment',
                'utility': 'Utilities',
                'utilities': 'Utilities',
                'bill': 'Utilities',
                'medical': 'Healthcare',
                'doctor': 'Healthcare',
                'health': 'Healthcare',
                'education': 'Education',
                'school': 'Education',
                'book': 'Education',
                'misc': 'Miscellaneous',
                'other': 'Miscellaneous'
            }
            
            mapped_category = 'Miscellaneous'
            lower_category = category.lower()
            
            for key, value in category_map.items():
                if key in lower_category:
                    mapped_category = value
                    break
            
            return {
                'description': description.strip(),
                'amount': float(amount),
                'category': mapped_category
            }
        
        except Exception as e:
            logger.error(f"Error parsing transaction text '{text}': {str(e)}")
            return None
    
    def get_spending_trends(self, user_id, days=30):
        """
        Get spending trends over a period of days.
        
        Parameters:
        -----------
        user_id : str
            The user's unique identifier
        days : int
            Number of days to look back
            
        Returns:
        --------
        dict
            Daily and category spending trends
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        transactions = self.get_user_transactions(
            user_id, 
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        # Create a date range
        date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days+1)]
        
        # Initialize daily spending
        daily_spending = {date: 0 for date in date_range}
        
        # Initialize category spending
        category_spending = {}
        
        # Aggregate transactions
        for transaction in transactions:
            date = transaction['date']
            amount = transaction['amount']
            category = transaction['category']
            
            # Add to daily spending
            if date in daily_spending:
                daily_spending[date] += amount
            
            # Add to category spending
            if category not in category_spending:
                category_spending[category] = 0
            category_spending[category] += amount
        
        # Convert daily spending to a list format for charts
        daily_trend = [
            {'date': date, 'amount': amount}
            for date, amount in daily_spending.items()
        ]
        
        # Convert category spending to a list format for charts
        category_trend = [
            {'category': category, 'amount': amount}
            for category, amount in category_spending.items()
        ]
        
        return {
            'daily': daily_trend,
            'category': category_trend
        }

# Instance for direct import
data_processor = DataProcessor()

# For testing
if __name__ == "__main__":
    processor = DataProcessor()
    
    # Test transaction parsing
    test_texts = [
        "Samosa 30rs food",
        "doctor fees 200rs medical",
        "Uber 150 transport",
        "Movie tickets ?350 entertainment"
    ]
    
    for text in test_texts:
        result = processor.parse_transaction_text(text)
        print(f"Input: {text}")
        print(f"Parsed: {result}")
        print()