# init_database.py
import sqlite3
import os
import hashlib
import secrets

def init_database():
    """Initialize the database with proper schema"""
    db_path = 'pothole_detection.db'
    
    # Remove existing database to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Removed old database")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            total_reports INTEGER DEFAULT 0,
            reputation_points INTEGER DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT
        )
    ''')
    
    # Create potholes table
    cursor.execute('''
        CREATE TABLE potholes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pothole_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            confidence REAL NOT NULL,
            severity TEXT NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bbox_width REAL,
            bbox_height REAL,
            session_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Insert test users
    test_users = [
        ('user_001', 'demo@example.com', 'demo', 'demo123'),
        ('user_002', 'test@test.com', 'test', 'test123'),
        ('user_003', 'admin@example.com', 'admin', 'admin123')
    ]
    
    for user_id, email, username, password in test_users:
        # Simple password hashing (use proper hashing in production)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO users (user_id, email, username, password_hash)
            VALUES (?, ?, ?, ?)
        ''', (user_id, email, username, password_hash))
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully!")
    print("📊 Created tables: users, potholes, sessions")
    print("👤 Test users created:")
    print("   - demo@example.com / demo123")
    print("   - test@test.com / test123")
    print("   - admin@example.com / admin123")

if __name__ == '__main__':
    init_database()