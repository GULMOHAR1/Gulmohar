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
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        graduation_year INTEGER NOT NULL,
        user_type TEXT NOT NULL,
        is_profile_completed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create posts table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        image_url TEXT,
        link_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # Create likes table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS likes (
        like_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (post_id) REFERENCES posts (post_id)
    )
    ''')

    # Create comments table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (post_id) REFERENCES posts (post_id)
    )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def add_connections_tables():
    conn = sqlite3.connect('alumni_network.db')
    cursor = conn.cursor()

    # Create connections table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS connections (
        connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users (user_id),
        FOREIGN KEY (receiver_id) REFERENCES users (user_id)
    )
    ''')

    # Add department column to users table if it doesn't exist
    try:
        cursor.execute('''
            ALTER TABLE users 
            ADD COLUMN department TEXT
        ''')
        print("Added department column to users table")
    except sqlite3.OperationalError:
        print("Department column already exists")

    conn.commit()
    conn.close()

def add_events_table():
    conn = sqlite3.connect('alumni_network.db')
    cursor = conn.cursor()

    # Create events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        date DATE NOT NULL,
        time TIME NOT NULL,
        location TEXT,
        organizer_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organizer_id) REFERENCES users (user_id)
    )
    ''')

    # Create event_participants table for RSVPs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS event_participants (
        event_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'going',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (event_id, user_id),
        FOREIGN KEY (event_id) REFERENCES events (event_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    add_profile_columns()
    add_connections_tables()
    add_events_table()
    print("Database initialized and updated successfully!") 