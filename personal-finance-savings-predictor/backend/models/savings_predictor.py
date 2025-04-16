import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to load and preprocess the dataset
def preprocess_data(file_path):
    logger.info(f"Loading data from {file_path}")
    
    # Load the data
    df = pd.read_csv(file_path)
    
    logger.info(f"Dataset loaded with {df.shape[0]} rows and {df.shape[1]} columns")
    logger.info(f"Columns: {df.columns.tolist()}")
    
    # As per requirements, drop income, city tier, loan-related, income-related, and savings-related columns
    columns_to_drop = [col for col in df.columns if any(keyword in col.lower() for keyword in 
                      ['income', 'city_tier', 'loan', 'savings', 'desired'])]
    
    logger.info(f"Dropping columns: {columns_to_drop}")
    df = df.drop(columns=columns_to_drop, errors='ignore')
    
    # Define expense categories and features
    expense_categories = ['Groceries', 'Transport', 'Eating_Out', 'Entertainment', 
                         'Utilities', 'Healthcare', 'Education', 'Miscellaneous']
    
    # Columns to keep for features
    demographic_features = ['Age', 'Dependents', 'Occupation']
    feature_columns = demographic_features + expense_categories
    
    # Target columns (potential savings in each category)
    target_columns = [f'Potential_Savings_{category}' for category in expense_categories]
    
    # Check if all required columns exist
    missing_columns = [col for col in feature_columns + target_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Missing columns in dataset: {missing_columns}")
        # For demonstration, we'll create these columns if they don't exist
        for col in missing_columns:
            if col in target_columns:
                # Create dummy potential savings (30% of the corresponding expense)
                expense_cat = col.replace('Potential_Savings_', '')
                if expense_cat in df.columns:
                    logger.info(f"Creating {col} as 30% of {expense_cat}")
                    df[col] = df[expense_cat] * 0.3
                else:
                    logger.info(f"Creating random {col} values")
                    df[col] = np.random.randint(100, 1000, size=len(df))
            else:
                if col == 'Age':
                    logger.info(f"Creating random {col} values")
                    df[col] = np.random.randint(18, 65, size=len(df))
                elif col == 'Dependents':
                    logger.info(f"Creating random {col} values")
                    df[col] = np.random.randint(0, 5, size=len(df))
                elif col == 'Occupation':
                    logger.info(f"Creating random {col} values")
                    occupations = ['Salaried', 'Business', 'Freelancer', 'Student', 'Retired']
                    df[col] = np.random.choice(occupations, size=len(df))
                else:
                    logger.info(f"Creating random {col} values")
                    df[col] = np.random.randint(1000, 10000, size=len(df))
    
    # Handle categorical variables - convert Occupation to one-hot encoding
    if 'Occupation' in df.columns and df['Occupation'].dtype == 'object':
        logger.info("One-hot encoding Occupation column")
        df = pd.get_dummies(df, columns=['Occupation'], drop_first=True)
        # Update feature_columns to include new one-hot encoded columns
        occupation_columns = [col for col in df.columns if col.startswith('Occupation_')]
        feature_columns = [col for col in feature_columns if col != 'Occupation'] + occupation_columns
    
    # Check for missing values
    missing_values = df[feature_columns + target_columns].isnull().sum()
    missing_value_cols = missing_values[missing_values > 0].index.tolist()
    
    if missing_value_cols:
        logger.warning(f"Columns with missing values: {missing_value_cols}")
        logger.info("Filling missing values with column means")
        df[missing_value_cols] = df[missing_value_cols].fillna(df[missing_value_cols].mean())
    
    return df, feature_columns, target_columns

# Function to train models for each expense category
def train_savings_models(df, feature_columns, target_columns):
    logger.info("Starting model training...")
    
    models = {}
    model_performances = {}
    
    # For each expense category, train a separate model
    for target in target_columns:
        logger.info(f"Training model for {target}...")
        
        # Extract features and target
        X = df[feature_columns]
        y = df[target]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        logger.info(f"Training set size: {X_train.shape[0]}, Test set size: {X_test.shape[0]}")
        
        # Create pipeline with preprocessing and model
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', RandomForestRegressor(n_estimators=100, random_state=42))
        ])
        
        # Train the model
        pipeline.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Store model and performance metrics
        models[target] = pipeline
        model_performances[target] = {
            'mse': mse,
            'r2': r2,
            'feature_importance': pipeline.named_steps['model'].feature_importances_
        }
        
        logger.info(f"  - MSE: {mse:.2f}")
        logger.info(f"  - R²: {r2:.2f}")
    
    return models, model_performances

# Function to save trained models
def save_models(models, output_dir='./models'):
    logger.info(f"Saving models to {output_dir}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for target, model in models.items():
        model_name = target.replace('Potential_Savings_', '')
        model_path = f"{output_dir}/{model_name.lower()}_model.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
            
        logger.info(f"Saved model: {model_path}")
    
    logger.info(f"All models saved to {output_dir}")

# Function to visualize model performance and feature importance
def visualize_model_results(df, feature_columns, model_performances, output_dir='./visualizations'):
    logger.info(f"Creating model visualization outputs in {output_dir}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 1. Create a bar chart of R² scores for each model
    plt.figure(figsize=(12, 6))
    r2_scores = [perf['r2'] for perf in model_performances.values()]
    categories = [target.replace('Potential_Savings_', '') for target in model_performances.keys()]
    
    plt.bar(categories, r2_scores)
    plt.title('Model Performance (R² Score)')
    plt.ylabel('R²')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/model_performance.png')
    logger.info(f"Saved model performance visualization to {output_dir}/model_performance.png")
    
    # 2. Create a heatmap of feature importances
    plt.figure(figsize=(12, 8))
    
    # Create a DataFrame for the heatmap
    feature_imp_df = pd.DataFrame(index=feature_columns)
    
    for target, perf in model_performances.items():
        category = target.replace('Potential_Savings_', '')
        feature_imp_df[category] = perf['feature_importance']
    
    sns.heatmap(feature_imp_df, annot=True, cmap='viridis')
    plt.title('Feature Importance for Each Expense Category')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/feature_importance.png')
    logger.info(f"Saved feature importance visualization to {output_dir}/feature_importance.png")
    
    # 3. Sample distributions of actual vs potential savings
    plt.figure(figsize=(15, 10))
    
    for i, category in enumerate(categories):
        if i >= 9:  # Limit to 9 subplots
            break
            
        plt.subplot(3, 3, i+1)
        
        actual = df[category]
        potential = df[f'Potential_Savings_{category}']
        
        sns.histplot(actual, color='blue', alpha=0.5, label='Actual Expense')
        sns.histplot(potential, color='green', alpha=0.5, label='Potential Savings')
        
        plt.title(f'{category}')
        if i == 0:
            plt.legend()
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/expense_distributions.png')
    logger.info(f"Saved expense distributions visualization to {output_dir}/expense_distributions.png")

# Function to make predictions for a single user
def predict_savings(user_data, models):
    """
    Make savings predictions for a single user.
    
    Parameters:
    -----------
    user_data : dict or DataFrame
        User's demographic and expense data
    models : dict
        Dictionary of trained models for each expense category
    
    Returns:
    --------
    dict
        Dictionary of predicted savings for each category
    """
    # Convert dict to DataFrame if necessary
    if isinstance(user_data, dict):
        user_data = pd.DataFrame([user_data])
    
    predictions = {}
    
    for category, model in models.items():
        try:
            # Extract the actual category name
            category_name = category.replace('Potential_Savings_', '')
            
            # Make prediction
            prediction = model.predict(user_data)[0]
            
            # Store prediction
            predictions[category_name] = float(prediction)
        except Exception as e:
            logger.error(f"Error predicting for {category}: {str(e)}")
            predictions[category_name] = None
    
    return predictions

# Main function to run the entire preprocessing and model training pipeline
def main(file_path, output_dir='./models', viz_dir='./visualizations'):
    logger.info(f"Starting model training pipeline with data from {file_path}")
    
    # 1. Preprocess the data
    df, feature_columns, target_columns = preprocess_data(file_path)
    
    # 2. Train models
    models, model_performances = train_savings_models(df, feature_columns, target_columns)
    
    # 3. Save models
    save_models(models, output_dir)
    
    # 4. Visualize results
    visualize_model_results(df, feature_columns, model_performances, viz_dir)
    
    logger.info("Model training pipeline completed successfully")
    
    return models, feature_columns, target_columns

if __name__ == "__main__":
    # Use the actual file path to the dataset
    file_path = "../../data/data.csv"
    
    if not os.path.exists(file_path):
        logger.error(f"Dataset not found at {file_path}")
        print(f"Error: Dataset not found at {file_path}")
        print("Please ensure the dataset is downloaded and placed in the data directory.")
        exit(1)
    
    main(file_path)