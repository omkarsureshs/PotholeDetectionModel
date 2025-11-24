import json
import os
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Any
import uuid
import hashlib
import secrets

class PotholeMapService:
    def __init__(self, db_path='pothole_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with user authentication - FIXED SCHEMA"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced Users table with authentication - FIXED COLUMNS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                username TEXT UNIQUE,
                password_hash TEXT,
                salt TEXT,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                email_verified BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                ip_address TEXT,
                user_agent TEXT,
                total_reports INTEGER DEFAULT 0,
                reputation_points INTEGER DEFAULT 0,  -- FIXED: consistent naming
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,  -- ADDED
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP   -- ADDED
            )
        ''')
        
        # Sessions table for login sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_token TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Potholes table with proper user association
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS potholes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                size REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT,
                address TEXT,
                road_condition TEXT,
                annotated_image_path TEXT,
                detection_data TEXT,
                is_verified BOOLEAN DEFAULT 0,
                verification_score INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Detection sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                total_potholes INTEGER DEFAULT 0,
                avg_severity REAL DEFAULT 0,
                area_coverage TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # User stats table for better analytics - FIXED COLUMNS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                total_reports INTEGER DEFAULT 0,
                high_severity_reports INTEGER DEFAULT 0,
                medium_severity_reports INTEGER DEFAULT 0,
                low_severity_reports INTEGER DEFAULT 0,
                reputation_points INTEGER DEFAULT 0,  -- FIXED: consistent naming
                last_activity DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # CREATE TEST USERS - ADDED THIS SECTION
        test_users = [
            ('demo@example.com', 'demo', 'demo123'),
            ('test@test.com', 'test', 'test123'),
            ('admin@example.com', 'admin', 'admin123')
        ]
        
        for email, username, password in test_users:
            # Check if user already exists
            cursor.execute('SELECT user_id FROM users WHERE email = ?', (email,))
            if not cursor.fetchone():
                user_id = str(uuid.uuid4())
                password_hash, salt = self.hash_password(password)
                
                # Insert user
                cursor.execute('''
                    INSERT INTO users (user_id, email, username, password_hash, salt)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, email, username, password_hash, salt))
                
                # Initialize user statistics
                cursor.execute('''
                    INSERT INTO user_statistics (user_id) VALUES (?)
                ''', (user_id,))
                
                print(f"✅ Created test user: {email}")
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully with test users!")
    
    # =========================================================================
    # USER AUTHENTICATION METHODS - FIXED VERSION
    # =========================================================================
    
    def hash_password(self, password, salt=None):
        """Hash password with salt - FIXED VERSION"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use pbkdf2_hmac correctly
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        ).hex()
        return password_hash, salt
    
    def verify_password(self, password, password_hash, salt):
        """Verify password against hash - FIXED VERSION"""
        test_hash, _ = self.hash_password(password, salt)
        return test_hash == password_hash
    
    def create_user(self, email, username, password, ip_address=None, user_agent=None):
        """Create new user account - FIXED VERSION"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = ? OR username = ?', (email, username))
        if cursor.fetchone():
            conn.close()
            return None, "User already exists"
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash, salt = self.hash_password(password)
        
        try:
            cursor.execute('''
                INSERT INTO users 
                (user_id, email, username, password_hash, salt, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, email, username, password_hash, salt, ip_address, user_agent))
            
            # Initialize user statistics
            cursor.execute('''
                INSERT INTO user_statistics (user_id) VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            print(f"✅ New user created: {email}")
            return user_id, None
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"❌ Error creating user {email}: {str(e)}")
            return None, f"Error creating user: {str(e)}"
    
    def authenticate_user(self, email, password, ip_address=None, user_agent=None):
        """Authenticate user and create session - FIXED VERSION"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user with password hash and salt - FIXED QUERY
        cursor.execute('''
            SELECT user_id, password_hash, salt, username, email, is_active 
            FROM users WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            print(f"❌ User not found: {email}")
            return None, "Invalid email or password"
        
        user_id, stored_hash, salt, username, user_email, is_active = user
        
        if not is_active:
            conn.close()
            return None, "Account deactivated"
        
        # Verify password
        if not self.verify_password(password, stored_hash, salt):
            conn.close()
            print(f"❌ Invalid password for: {email}")
            return None, "Invalid email or password"
        
        try:
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = ?, last_active = ? WHERE user_id = ?
            ''', (datetime.now(), datetime.now(), user_id))
            
            # Create session
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=30)
            
            cursor.execute('''
                INSERT INTO user_sessions 
                (session_token, user_id, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_token, user_id, expires_at, ip_address, user_agent))
            
            # Get user statistics for response - FIXED QUERY
            cursor.execute('''
                SELECT total_reports, reputation_points FROM user_statistics WHERE user_id = ?
            ''', (user_id,))
            stats = cursor.fetchone()
            
            conn.commit()
            conn.close()
            
            user_data = {
                'user_id': user_id,
                'username': username,
                'email': user_email,
                'session_token': session_token,
                'statistics': {
                    'total_reports': stats[0] if stats else 0,
                    'reputation_points': stats[1] if stats else 0
                }
            }
            
            print(f"✅ Login successful for: {email}")
            return user_data, None
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"❌ Authentication error for {email}: {str(e)}")
            return None, f"Authentication error: {str(e)}"
    
    def validate_session(self, session_token):
        """Validate user session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT us.user_id, us.expires_at, u.username, u.email, u.role
            FROM user_sessions us
            JOIN users u ON us.user_id = u.user_id
            WHERE us.session_token = ? AND us.expires_at > ? AND u.is_active = 1
        ''', (session_token, datetime.now()))
        
        session = cursor.fetchone()
        conn.close()
        
        if session:
            return {
                "user_id": session[0],
                "username": session[2],
                "email": session[3],
                "role": session[4]
            }
        return None
    
    def logout_user(self, session_token):
        """Invalidate user session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
            conn.commit()
            conn.close()
            print(f"✅ User logged out")
            return True
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"❌ Error logging out user: {e}")
            return False
    
    def get_user_profile(self, user_id):
        """Get complete user profile - FIXED VERSION"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.user_id, u.email, u.username, u.role, u.created_at, u.last_login,
                   us.total_reports, us.high_severity_reports, us.medium_severity_reports,
                   us.low_severity_reports, us.reputation_points
            FROM users u
            LEFT JOIN user_statistics us ON u.user_id = us.user_id
            WHERE u.user_id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                "user_id": user[0],
                "email": user[1],
                "username": user[2],
                "role": user[3],
                "created_at": user[4],
                "last_login": user[5],
                "statistics": {
                    "total_reports": user[6] or 0,
                    "high_severity_reports": user[7] or 0,
                    "medium_severity_reports": user[8] or 0,
                    "low_severity_reports": user[9] or 0,
                    "reputation_points": user[10] or 0
                }
            }
        return None
    
    # =========================================================================
    # EXISTING METHODS (updated for consistency)
    # =========================================================================
    
    def get_or_create_user(self, request):
        """Get or create user based on request data"""
        user_id = request.cookies.get('user_id')
        if not user_id:
            user_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user IP and user agent
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE user_id = ?', (user_id,))
        user_exists = cursor.fetchone()
        
        if not user_exists:
            # Create new user (anonymous) with generated email
            # Generate a unique email for anonymous users
            anonymous_email = f"anonymous_{user_id}@local.app"
            anonymous_username = f"anon_{user_id[:8]}"
            
            try:
                cursor.execute('''
                    INSERT INTO users (user_id, email, username, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, anonymous_email, anonymous_username, ip_address, user_agent))
                
                # Initialize user statistics
                cursor.execute('''
                    INSERT INTO user_statistics (user_id) VALUES (?)
                ''', (user_id,))
            except sqlite3.IntegrityError:
                # User already exists, just update last_active
                cursor.execute('''
                    UPDATE users SET last_active = ? WHERE user_id = ?
                ''', (datetime.now(), user_id))
        else:
            # Update last active
            cursor.execute('''
                UPDATE users SET last_active = ? WHERE user_id = ?
            ''', (datetime.now(), user_id))
        
        conn.commit()
        conn.close()
        return user_id
    
    def save_pothole_data(self, detection_data: Dict[str, Any], user_id: str, request=None):
        """Save pothole detection data to database with user association"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Save session info
            cursor.execute('''
                INSERT INTO detection_sessions 
                (session_id, user_id, total_potholes, avg_severity, area_coverage)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, user_id, len(detection_data.get('detections', [])), 0.5, 'Unknown'))
            
            # Update user report count
            cursor.execute('''
                UPDATE users SET total_reports = total_reports + 1 WHERE user_id = ?
            ''', (user_id,))
            
            # Update user statistics
            cursor.execute('''
                UPDATE user_statistics 
                SET total_reports = total_reports + 1,
                    last_activity = ?
                WHERE user_id = ?
            ''', (datetime.now(), user_id))
            
            # Save individual potholes
            for detection in detection_data.get('detections', []):
                location = detection.get('location') or detection_data.get('location')
                severity = detection.get('severity', {})
                
                if location and 'latitude' in location and 'longitude' in location:
                    # Store detection data as JSON for full record
                    detection_json = json.dumps(detection)
                    
                    cursor.execute('''
                        INSERT INTO potholes 
                        (user_id, latitude, longitude, severity, confidence, size, 
                         timestamp, image_path, detection_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        location['latitude'],
                        location['longitude'],
                        severity.get('level', 'medium'),
                        detection.get('confidence', 0.5),
                        detection.get('bbox', [0, 0, 100, 100])[2] * detection.get('bbox', [0, 0, 100, 100])[3],
                        datetime.now().isoformat(),
                        f"detection_{session_id}.jpg",
                        detection_json
                    ))
            
            conn.commit()
            conn.close()
            print(f"✅ Saved pothole data for user: {user_id}")
            return session_id
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"❌ Error saving pothole data: {e}")
            return None
    
    def get_potholes_by_area(self, ne_lat: float, ne_lng: float, sw_lat: float, sw_lng: float):
        """Get potholes within a bounding box with user info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                p.id, p.latitude, p.longitude, p.severity, p.confidence, 
                p.size, p.timestamp, p.user_id, u.total_reports,
                CASE 
                    WHEN p.severity = 'high' THEN 3
                    WHEN p.severity = 'medium' THEN 2
                    ELSE 1
                END as severity_weight
            FROM potholes p
            LEFT JOIN users u ON p.user_id = u.user_id
            WHERE p.latitude BETWEEN ? AND ? 
            AND p.longitude BETWEEN ? AND ?
            ORDER BY p.timestamp DESC
        ''', (sw_lat, ne_lat, sw_lng, ne_lng))
        
        potholes = []
        for row in cursor.fetchall():
            potholes.append({
                'id': row[0],
                'latitude': row[1],
                'longitude': row[2],
                'severity': row[3],
                'confidence': row[4],
                'size': row[5],
                'timestamp': row[6],
                'user_id': row[7],
                'user_reports': row[8],
                'severity_weight': row[9]
            })
        
        conn.close()
        return potholes
    
    def get_user_potholes(self, user_id: str):
        """Get all potholes reported by a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, latitude, longitude, severity, confidence, size, timestamp
            FROM potholes 
            WHERE user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id,))
        
        potholes = []
        for row in cursor.fetchall():
            potholes.append({
                'id': row[0],
                'latitude': row[1],
                'longitude': row[2],
                'severity': row[3],
                'confidence': row[4],
                'size': row[5],
                'timestamp': row[6]
            })
        
        conn.close()
        return potholes
    
    def get_heatmap_data(self):
        """Get data formatted for heatmap visualization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                latitude, 
                longitude,
                CASE 
                    WHEN severity = 'high' THEN 0.8
                    WHEN severity = 'medium' THEN 0.5
                    ELSE 0.3
                END as weight
            FROM potholes
        ''')
        
        heatmap_data = []
        for row in cursor.fetchall():
            heatmap_data.append({
                'location': {'lat': row[0], 'lng': row[1]},
                'weight': row[2]
            })
        
        conn.close()
        return heatmap_data
    
    def get_statistics(self):
        """Get overall pothole statistics with user data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Pothole statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_potholes,
                AVG(CASE 
                    WHEN severity = 'high' THEN 3
                    WHEN severity = 'medium' THEN 2
                    ELSE 1
                END) as avg_severity,
                SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_severity,
                SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium_severity,
                SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low_severity
            FROM potholes
        ''')
        
        stats = cursor.fetchone()
        
        # User statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_users,
                SUM(total_reports) as total_reports
            FROM users
        ''')
        
        user_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_potholes': stats[0] if stats else 0,
            'avg_severity': round(stats[1], 2) if stats and stats[1] else 0,
            'high_severity': stats[2] if stats else 0,
            'medium_severity': stats[3] if stats else 0,
            'low_severity': stats[4] if stats else 0,
            'total_users': user_stats[0] if user_stats else 0,
            'total_reports': user_stats[1] if user_stats else 0
        }

    def get_recent_potholes(self, limit: int = 50):
        """Get most recent potholes for map display"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                p.id, p.latitude, p.longitude, p.severity, p.confidence, 
                p.size, p.timestamp, p.user_id, u.total_reports
            FROM potholes p
            LEFT JOIN users u ON p.user_id = u.user_id
            ORDER BY p.timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        potholes = []
        for row in cursor.fetchall():
            potholes.append({
                'id': row[0],
                'latitude': row[1],
                'longitude': row[2],
                'severity': row[3],
                'confidence': row[4],
                'size': row[5],
                'timestamp': row[6],
                'user_id': row[7],
                'user_reports': row[8]
            })
        
        conn.close()
        return potholes

    def delete_user_data(self, user_id: str):
        """Delete all data for a specific user (GDPR compliance)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete user's potholes
            cursor.execute('DELETE FROM potholes WHERE user_id = ?', (user_id,))
            # Delete user's sessions
            cursor.execute('DELETE FROM detection_sessions WHERE user_id = ?', (user_id,))
            # Delete user statistics
            cursor.execute('DELETE FROM user_statistics WHERE user_id = ?', (user_id,))
            # Delete user sessions
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            # Delete user
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting user data: {e}")
            return False
        finally:
            conn.close()

# Global instance
map_service = PotholeMapService()