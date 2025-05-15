import sqlite3
import datetime

# Connect to database
conn = sqlite3.connect('finance.db')
cursor = conn.cursor()

# Add test user profile
cursor.execute('''
INSERT OR REPLACE INTO user_profiles (user_id, age, dependents, occupation)
VALUES ('user123', 30, 0, 'Software Developer')
''')

# Add some sample transactions
categories = ['Groceries', 'Transport', 'Utilities', 'Entertainment', 'Healthcare', 'Education', 'Eating Out', 'Miscellaneous']

for i, category in enumerate(categories):
    for day in range(1, 6):  # Add multiple transactions over several days
        cursor.execute('''
        INSERT INTO transactions (user_id, date, category, amount, description)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            'user123',
            (datetime.datetime.now() - datetime.timedelta(days=i*3 + day)).strftime('%Y-%m-%d'),
            category,
            float(50.0 + i * 10 + day),
            f'Sample {category} expense #{day}'
        ))

conn.commit()
conn.close()
print('Test data added successfully')