import sqlite3

def add_profile_columns():
    conn = sqlite3.connect('alumni_network.db')
    cursor = conn.cursor()

    # List of new columns to add with their definitions
    new_columns = [
        ('profile_picture', 'TEXT'),
        ('location', 'TEXT'),
        ('current_status', 'TEXT'),
        ('job_role', 'TEXT'),
        ('website', 'TEXT'),
        ('bio', 'TEXT'),
        ('linkedin', 'TEXT'),
        ('github', 'TEXT')
    ]

    # Add each column if it doesn't exist
    for column_name, data_type in new_columns:
        try:
            cursor.execute(f'''
                ALTER TABLE users
                ADD COLUMN {column_name} {data_type}
            ''')
            print(f"Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {column_name} already exists")
            else:
                print(f"Error adding column {column_name}: {e}")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def init_db():
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect('alumni_network.db')
    cursor = conn.cursor()

    # Create users table if it doesn't exist (original schema)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY
