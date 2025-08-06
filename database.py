import sqlite3
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from helpers import hash_string

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv('DB_PATH', 'users.db')
        self.init_database()
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize the database with required tables and default user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create default admin user if it doesn't exist
        admin_username = os.getenv('DEFAULT_ADMIN_USERNAME')
        admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')

        # Verify that admin_username and admin_password are set
        if not admin_username or not admin_password:
            raise Exception("DEFAULT_ADMIN_USERNAME and DEFAULT_ADMIN_PASSWORD must be set in environment variables.")
        
        if not self.get_user_by_username(admin_username):
            self.create_user(admin_username, admin_password)
        
        conn.commit()
        conn.close()
    
    def create_user(self, username: str, password: str) -> int:
        """Create a new user and return the user ID"""
        password_hash = hash_string(password)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        if user_id is None:
            raise Exception("Failed to create user - no ID returned")
        return user_id
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, username, password_hash, created_at FROM users WHERE username = ?',
            (username,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'password_hash': row[2],
                'created_at': row[3]
            }
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        """Authenticate user and return user ID if successful"""
        password_hash = hash_string(password)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def create_session(self, user_id: int, expires_in_hours: Optional[int] = None) -> Dict[str, Any]:
        """Create a new session for a user"""
        if expires_in_hours is None:
            expires_in_hours = int(os.getenv('SESSION_EXPIRY_HOURS', '24'))
        
        token_length = int(os.getenv('TOKEN_LENGTH', '32'))
        token = secrets.token_urlsafe(token_length)
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)',
            (user_id, token, expires_at)
        )
        
        conn.commit()
        conn.close()
        
        return {
            'token': token,
            'expires_at': expires_at.isoformat()
        }
    
    def get_session_user_id(self, token: str) -> Optional[int]:
        """Get user ID from valid session token"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?',
            (token, datetime.now())
        )
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def delete_session(self, token: str) -> bool:
        """Delete a session by token"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT username, created_at FROM users WHERE id = ?',
            (user_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'username': row[0],
                'created_at': row[1]
            }
        return None
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return number of deleted sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM sessions WHERE expires_at <= ?', (datetime.now(),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count

# Global database instance
db = DatabaseManager() 