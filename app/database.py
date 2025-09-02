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
        
        # Create reactor experiments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reactor_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                experiment_name TEXT NOT NULL,
                tsv_file_path TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                number_of_tries INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL,
                error_message TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create reactor parameters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reactor_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                parameter_value TEXT NOT NULL,
                parameter_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES reactor_experiments (id) ON DELETE CASCADE
            )
        ''')
        
        # Create reactor results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reactor_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                result_type TEXT NOT NULL,
                result_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES reactor_experiments (id) ON DELETE CASCADE
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
        """Clean up expired sessions and return the number of deleted sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP'
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count

    # Reactor Experiment Methods
    def create_reactor_experiment(self, user_id: int, experiment_name: str, tsv_file_path: str) -> int:
        """Create a new reactor experiment and return the experiment ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO reactor_experiments (user_id, experiment_name, tsv_file_path) VALUES (?, ?, ?)',
            (user_id, experiment_name, tsv_file_path)
        )
        
        experiment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        if experiment_id is None:
            raise Exception("Failed to create experiment - no ID returned")
        return experiment_id
    
    def store_reactor_parameters(self, experiment_id: int, parameters: Dict[str, Any]) -> bool:
        """Store reactor parameters for an experiment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for param_name, param_value in parameters.items():
                param_type = type(param_value).__name__
                cursor.execute(
                    'INSERT INTO reactor_parameters (experiment_id, parameter_name, parameter_value, parameter_type) VALUES (?, ?, ?, ?)',
                    (experiment_id, param_name, str(param_value), param_type)
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error storing parameters: {e}")
            return False
        finally:
            conn.close()
    
    def get_reactor_parameters(self, experiment_id: int) -> Dict[str, Any]:
        """Get reactor parameters for an experiment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT parameter_name, parameter_value, parameter_type FROM reactor_parameters WHERE experiment_id = ?',
            (experiment_id,)
        )
        
        parameters = {}
        for row in cursor.fetchall():
            param_name, param_value, param_type = row
            
            # Convert back to original type
            if param_type == 'int':
                parameters[param_name] = int(param_value)
            elif param_type == 'float':
                parameters[param_name] = float(param_value)
            elif param_type == 'bool':
                parameters[param_name] = param_value.lower() == 'true'
            elif param_type == 'list':
                # Handle list parameters (like adj_factor)
                try:
                    import json
                    parameters[param_name] = json.loads(param_value)
                except:
                    parameters[param_name] = param_value
            else:
                parameters[param_name] = param_value
        
        conn.close()
        return parameters
    
    def update_experiment_status(self, experiment_id: int, status: str, error_message: str = None) -> bool:
        """Update experiment status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if status == 'running':
                cursor.execute(
                    'UPDATE reactor_experiments SET status = ?, started_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (status, experiment_id)
                )
            elif status in ['completed', 'failed']:
                cursor.execute(
                    'UPDATE reactor_experiments SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ? WHERE id = ?',
                    (status, error_message or '', experiment_id)
                )
            else:
                cursor.execute(
                    'UPDATE reactor_experiments SET status = ? WHERE id = ?',
                    (status, experiment_id)
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating status: {e}")
            return False
        finally:
            conn.close()
    
    def store_reactor_results(self, experiment_id: int, results: Dict[str, Any]) -> bool:
        """Store reactor simulation results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            import json
            for result_type, result_data in results.items():
                cursor.execute(
                    'INSERT INTO reactor_results (experiment_id, result_type, result_data) VALUES (?, ?, ?)',
                    (experiment_id, result_type, json.dumps(result_data))
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error storing results: {e}")
            return False
        finally:
            conn.close()
    
    def get_reactor_results(self, experiment_id: int) -> Dict[str, Any]:
        """Get reactor simulation results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT result_type, result_data FROM reactor_results WHERE experiment_id = ?',
            (experiment_id,)
        )
        
        results = {}
        import json
        for row in cursor.fetchall():
            result_type, result_data = row
            try:
                results[result_type] = json.loads(result_data)
            except:
                results[result_type] = result_data
        
        conn.close()
        return results
    
    def get_user_experiments(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all experiments for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, experiment_name, status, number_of_tries, created_at, started_at, completed_at
            FROM reactor_experiments 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        experiments = []
        for row in cursor.fetchall():
            experiments.append({
                'id': row[0],
                'experiment_name': row[1],
                'status': row[2],
                'number_of_tries': row[3],
                'created_at': row[4],
                'started_at': row[5],
                'completed_at': row[6]
            })
        
        conn.close()
        return experiments

    def increment_experiment_tries(self, experiment_id: int) -> bool:
        """Increment the number of tries for an experiment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'UPDATE reactor_experiments SET number_of_tries = number_of_tries + 1 WHERE id = ?',
                (experiment_id,)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error incrementing tries: {e}")
            return False
        finally:
            conn.close()

    def mark_experiment_failed_permanently(self, experiment_id: int, error_message: str) -> bool:
        """Mark an experiment as permanently failed (exceeded max tries)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'UPDATE reactor_experiments SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ? WHERE id = ?',
                ('failed_permanently', error_message, experiment_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error marking experiment permanently failed: {e}")
            return False
        finally:
            conn.close()

    def reset_timed_out_experiments(self) -> int:
        """Reset experiments that have been running for too long"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get timeout minutes from environment variable
            timeout_minutes = int(os.getenv('EXPERIMENT_TIMEOUT_MINUTES', '15'))
            
            cursor.execute('''
                UPDATE reactor_experiments 
                SET status = 'pending', 
                    number_of_tries = number_of_tries + 1,
                    started_at = NULL,
                    error_message = 'Experiment timed out and will be retried'
                WHERE status = 'running' 
                AND started_at < datetime('now', '-{} minutes')
            '''.format(timeout_minutes))
            
            reset_count = cursor.rowcount
            conn.commit()
            return reset_count
        except Exception as e:
            conn.rollback()
            print(f"Error resetting timed out experiments: {e}")
            return 0
        finally:
            conn.close()

    def get_experiment_by_id(self, experiment_id: int) -> Optional[Dict[str, Any]]:
        """Get experiment details by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, experiment_name, tsv_file_path, status, number_of_tries,
                   created_at, started_at, completed_at, error_message
            FROM reactor_experiments 
            WHERE id = ?
        ''', (experiment_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'experiment_name': row[2],
                'tsv_file_path': row[3],
                'status': row[4],
                'number_of_tries': row[5],
                'created_at': row[6],
                'started_at': row[7],
                'completed_at': row[8],
                'error_message': row[9]
            }
        return None

    def get_pending_experiments(self) -> List[Dict[str, Any]]:
        """Get all pending experiments for processing"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, experiment_name, tsv_file_path, number_of_tries, created_at 
            FROM reactor_experiments 
            WHERE status = 'pending'
            ORDER BY created_at ASC
        ''')
        
        experiments = []
        for row in cursor.fetchall():
            experiments.append({
                'id': row[0],
                'user_id': row[1],
                'experiment_name': row[2],
                'tsv_file_path': row[3],
                'number_of_tries': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        return experiments

# Global database instance
db = DatabaseManager() 