from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import os
import pandas as pd
import sqlite3
from datetime import datetime
import json
import logging
from utils.data_processor import data_processor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Path to the directory containing trained models
MODEL_DIR = './models/models'  # Updated to point to the correct subdirectory

# Load all saved models
def load_models():
    models = {}
    
    try:
        if not os.path.exists(MODEL_DIR):
            logger.warning(f"Model directory {MODEL_DIR} not found. Creating directory.")
            os.makedirs(MODEL_DIR)
            return models
        
        model_files = [f for f in os.listdir(MODEL_DIR) if f.endswith('_model.pkl')]
        
        if not model_files:
            logger.warning(f"No model files found in {MODEL_DIR}. Models need to be trained first.")
            return models
        
        for filename in model_files:
            category = filename.replace('_model.pkl', '')
            file_path = os.path.join(MODEL_DIR, filename)
            
            with open(file_path, 'rb') as f:
                models[category] = pickle.load(f)
                logger.info(f"Loaded model: {filename}")
        
        return models
    
    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        return {}

# Initialize database
def init_db():
    conn = sqlite3.connect('finance.db')
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
    logger.info("Database initialized")

# Global models variable
models = {}

# Initialize app before first request
# @app.before_first_request decorator was removed in Flask 2.0+, using app_context instead
with app.app_context():
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Load models
    models = load_models()
    logger.info(f"Loaded {len(models)} models: {list(models.keys())}")
    
    if not models:
        logger.warning("No models loaded. Predictions will not be available.")

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'models_loaded': len(models),
        'timestamp': datetime.now().isoformat()
    })

# Route to add a new transaction
@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['user_id', 'category', 'amount', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Connect to database
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        # Insert transaction
        cursor.execute(
            'INSERT INTO transactions (user_id, date, category, amount, description) VALUES (?, ?, ?, ?, ?)',
            (
                data['user_id'],
                data.get('date', datetime.now().strftime('%Y-%m-%d')),
                data['category'],
                data['amount'],
                data['description']
            )
        )
        
        conn.commit()
        transaction_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"Added transaction {transaction_id} for user {data['user_id']}")
        
        return jsonify({
            'id': transaction_id, 
            'message': 'Transaction added successfully'
        }), 201
    
    except Exception as e:
        logger.error(f"Error adding transaction: {str(e)}")
        return jsonify({'error': 'Failed to add transaction. Please try again.'}), 500

# Route to get user transactions
@app.route('/api/transactions/<user_id>', methods=['GET'])
def get_transactions(user_id):
    try:
        # Get optional date filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        transactions = data_processor.get_user_transactions(user_id, start_date, end_date)
        
        return jsonify(transactions)
    
    except Exception as e:
        logger.error(f"Error getting transactions for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve transactions. Please try again.'}), 500
        
# Route to get user profile
@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        profile = data_processor.get_user_profile(user_id)
        
        if profile:
            return jsonify(profile)
        else:
            return jsonify({'error': 'Profile not found'}), 404
    
    except Exception as e:
        logger.error(f"Error getting profile for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve profile. Please try again.'}), 500

# Route to predict potential savings
@app.route('/api/predict/<user_id>', methods=['GET'])
def predict_savings(user_id):
    try:
        global models
        
        # Check if models are loaded
        if not models:
            models = load_models()
            if not models:
                return jsonify({
                    'error': 'No trained models available. Please train models first.'
                }), 503
        
        # Prepare features for prediction
        features, error = data_processor.prepare_features_for_prediction(user_id)
        if error:
            return jsonify({'error': error}), 400
        
        # Get actual expenses
        expenses = data_processor.aggregate_expenses_by_category(user_id)
        
        # Make predictions for each category
        predictions = {}
        for category, model in models.items():
            try:
                # Get the category name
                category_name = category.replace('potential_savings_', '').capitalize()
                
                # Get actual expense for this category
                actual_expense = expenses.get(category_name, 0)
                
                # Skip categories with no expenses
                if actual_expense <= 0:
                    continue
                
                # Predict potential savings
                potential_savings = float(model.predict(features)[0])
                
                # Cap potential savings at actual expense amount
                potential_savings = min(potential_savings, actual_expense)
                
                # Calculate savings percentage
                savings_percentage = (potential_savings / actual_expense * 100) if actual_expense > 0 else 0
                
                predictions[category_name] = {
                    'actual_expense': actual_expense,
                    'potential_savings': potential_savings,
                    'savings_percentage': savings_percentage
                }
            except Exception as e:
                logger.error(f"Error predicting for {category}: {str(e)}")
                # Skip this category if prediction fails
                continue
        
        # Calculate total potential savings
        total_actual = sum(pred['actual_expense'] for pred in predictions.values())
        total_potential_savings = sum(pred['potential_savings'] for pred in predictions.values())
        total_savings_percentage = (total_potential_savings / total_actual * 100) if total_actual > 0 else 0
        
        response = {
            'predictions': predictions,
            'totals': {
                'actual_expenses': total_actual,
                'potential_savings': total_potential_savings,
                'savings_percentage': total_savings_percentage
            }
        }
        
        logger.info(f"Generated savings prediction for user {user_id}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error predicting savings for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to predict savings. Please try again.'}), 500

# Route to parse transaction text
@app.route('/api/parse-transaction', methods=['POST'])
def parse_transaction():
    try:
        data = request.json
        
        if 'text' not in data:
            return jsonify({'error': 'Missing transaction text'}), 400
        
        transaction = data_processor.parse_transaction_text(data['text'])
        
        if transaction:
            return jsonify(transaction)
        else:
            return jsonify({
                'error': 'Could not parse transaction. Please use format: "Item amount category"'
            }), 400
    
    except Exception as e:
        logger.error(f"Error parsing transaction text: {str(e)}")
        return jsonify({'error': 'Failed to parse transaction text. Please try again.'}), 500

# Route to get spending trends
@app.route('/api/spending-trends/<user_id>', methods=['GET'])
def get_spending_trends(user_id):
    try:
        days = request.args.get('days', default=30, type=int)
        
        trends = data_processor.get_spending_trends(user_id, days)
        
        return jsonify(trends)
    
    except Exception as e:
        logger.error(f"Error getting spending trends for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to get spending trends. Please try again.'}), 500

if __name__ == '__main__':
    # Initialize the database and load models on startup
    init_db()
    models = load_models()
    logger.info(f"Loaded {len(models)} models: {list(models.keys())}")
    
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)

