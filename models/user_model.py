from datetime import datetime
from hmac import compare_digest
from services.SecurityService import SecurityService
import logging
from typing import Tuple, Optional, Dict
import pandas as pd
import sqlite3

class UserModel:
    def __init__(self,  conn = sqlite3.connect('user_credentials.db')):
        self.conn = conn
        self.logger = logging.getLogger(__name__)
        self.failed_attempts = {}  # {username: {"count": int, "lockout_end": datetime}}
        self.max_attempts = 3
        self.lockout_duration = 600  # Lockout duration in seconds
        self.username = None

    def get_user_credentials(self, username=None):
        """
        Retrieve user credentials for a specific username.

        Args:
            username (str): Username to fetch credentials for.

        Returns:
            Optional[Dict[str, str]]: User credentials or None if the user doesn't exist.
        """
        if not username:
            username = self.username

        query = '''
            SELECT password_hash, salt, encrypted_private_key, public_key, admin
            FROM users WHERE username = ?
        '''
        result = self._execute_query(query, (username,), fetch_one=True)

        if not result:
            self.logger.warning(f"User '{username}' does not exist.")
            return None

        return {
            "username": username,
            "password_hash": result[0],
            "salt": result[1],
            "encrypted_private_key": result[2],
            "public_key": result[3],
            "admin": bool(result[4])
        }

    def verify_credentials(self, username, password):
        """
        Verify user credentials.

        Args:
            username (str): Username.
            password (str): Password.

        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        if self.is_locked_out(username):
            self.logger.warning(f"User '{username}' is locked out.")
            return False

        user_data = self.get_user_credentials(username)

        if not user_data:
            return False

        derived_hash = SecurityService.hash_password(password, user_data["salt"])
        return compare_digest(user_data["password_hash"], derived_hash)

    def track_failed_attempt(self, username):
        """
        Track a failed login attempt and lock the user if necessary.

        Args:
            username (str): Username of the user who failed login.

        Returns:
            bool: True if the user is locked out, False otherwise.
        """
        now = datetime.now()

        if username not in self.failed_attempts:
            self.failed_attempts[username] = {"count": 0, "lockout_end": None}

        attempt_data = self.failed_attempts[username]
        attempt_data["count"] += 1

        if attempt_data["count"] >= self.max_attempts:
            attempt_data["lockout_end"] = now.timestamp() + self.lockout_duration
            self.logger.warning(f"User '{username}' locked out due to too many failed attempts.")
            return True

        return False

    def is_locked_out(self, username):
        """
        Check if a user is currently locked out.

        Args:
            username (str): Username to check.

        Returns:
            bool: True if the user is locked out, False otherwise.
        """
        if username not in self.failed_attempts:
            return False

        attempt_data = self.failed_attempts[username]
        now = datetime.now().timestamp()

        if attempt_data["lockout_end"] and now < attempt_data["lockout_end"]:
            return True

        if attempt_data["lockout_end"] and now >= attempt_data["lockout_end"]:
            self.reset_failed_attempts(username)

        return False

    def reset_failed_attempts(self, username):
        """
        Reset the failed login attempts for a user.

        Args:
            username (str): Username to reset attempts for.
        """
        if username in self.failed_attempts:
            del self.failed_attempts[username]
            self.logger.info(f"Login attempts reset for user '{username}'.")

    def _execute_query(self, query, params=(), fetch_one=False, fetch_all=False):
        """
        Execute a database query.

        Args:
            query (str): SQL query.
            params (tuple): Query parameters.
            fetch_one (bool): Fetch one row.
            fetch_all (bool): Fetch all rows.

        Returns:
            Any: Query result.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            raise

    

    
    def _initialize_tables(self):
        """Create required database tables if they do not already exist."""
        table_definitions = {
            "users": '''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    encrypted_private_key TEXT NOT NULL,
                    public_key TEXT NOT NULL,
                    admin INTEGER NOT NULL DEFAULT 0
                )
            '''
        }
    
        for table_name, query in table_definitions.items():
            try:
                self._execute_query(query)
                self.logger.info(f"Table '{table_name}' initialized successfully.")
            except sqlite3.Error as e:
                self.logger.error(f"Failed to initialize table '{table_name}': {e}")
                raise
    
    def ensure_admin_exists(self):
        """Ensure at least one admin user exists, or create a default admin."""
        try:
            self._initialize_tables()  # Ensure tables exist
            if self._admin_exists():
                self.logger.info("Admin user already exists.")
                return
            self._create_default_admin()
        except Exception as e:
            self.logger.error(f"Error ensuring admin existence: {e}")
            raise
    
    def _admin_exists(self) -> bool:
        """Check if at least one admin user exists."""
        query = "SELECT 1 FROM users WHERE admin = 1 LIMIT 1"
        return bool(self._execute_query(query, fetch_one=True))
    
    def _create_default_admin(self):
        """Create a default admin user."""
        try:
            credentials = self._generate_secure_credentials()
            self.register_user(credentials["username"], credentials["password"], is_admin=True)
            self.logger.info(f"Default admin created: {credentials['username']}")
            QMessageBox.information(
                None,
                "First Time Login",
                f"Default admin credentials created:\n\n"
                f"Username: {credentials['username']}\nPassword: {credentials['password']}\n\n"
                f"Please update them immediately under Utilities > User Management."
            )
        except Exception as e:
            self.logger.error(f"Failed to create default admin user: {e}")
            raise
    
    @staticmethod
    def _generate_secure_credentials() -> Dict[str, str]:
        """Generate secure credentials."""
        username = "Admin_" + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        password_characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(password_characters) for _ in range(16))
        return {"username": username, "password": password}



    def register_user(self, password: str, is_admin: bool = False):
        """Register a new user."""
        if self.get_user_credentials():
            raise ValueError(f"User '{self.username}' already exists.")
    
        try:
            salt = SecurityService.generate_salt()
            password_hash = SecurityService.hash_password(password, salt)
            private_key, public_key = SecurityService.generate_rsa_key_pair()
            encrypted_private_key = SecurityService.encrypt_private_key(private_key, password_hash)
            serialized_public_key = SecurityService.serialize_public_key(public_key)
    
            query = '''
                INSERT INTO users (username, password_hash, salt, encrypted_private_key, public_key, admin)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            self._execute_query(query, (
                self.username,
                password_hash,
                salt,
                encrypted_private_key,
                serialized_public_key,
                int(is_admin),
            ))
            self.logger.info(f"User '{self.username}' registered successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Database error during registration of '{self.username}': {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during registration of '{self.username}': {str(e)}")
            raise 
    
    
        


    def log_action(self, action: str):
        """Log user actions into the audit trail and application logs."""
        if not self.username:
            self.logger.warning("Cannot log action: No username provided.")
            return
    
        try:
            now = datetime.now()
            query = '''
                INSERT INTO audit_trail (username, date, time, action)
                VALUES (?, ?, ?, ?)
            '''
            self._execute_query(query, (
                self.username,
                now.strftime('%Y-%m-%d'),
                now.strftime('%H:%M:%S'),
                action
            ))
            self.logger.info(f"[AUDIT] {now} - User: {self.username}, Action: {action}")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to log action: {e}")



    
    def get_private_key(self, password: str) -> Optional[str]:
        """
        Retrieve and decrypt the private key for a user.
        
        Args:
            username (str): Username of the user.
            password (str): Password to decrypt the private key.
        
        Returns:
            Optional[str]: The decrypted private key or None if an error occurs.
        """
        user_data = self.get_user_credentials()

        if not user_data:
            self.logger.error(f"No credentials found for username: {self.username}")
            return None
        try:
            salt = user_data['salt']
            password_hash = SecurityService.hash_password(password, salt)
            return SecurityService.decrypt_private_key(user_data['encrypted_private_key'], password_hash)
        except Exception as e:
            self.logger.error(f"Error decrypting private key for '{self.username}': {e}")
            return None
            
    def delete_user(self, username: str):
        """
        Delete a user from the database.
    
        Args:
            username (str): Username to delete.
        """
        if not self.get_user_credentials():
            self.logger.warning(f"Attempted to delete non-existent user '{username}'.")
            return
    
        query = "DELETE FROM users WHERE username = ?"
        self._execute_query(query, (username,))
        self.log_action("User deleted")
        self.logger.info(f"User '{username}' deleted successfully.")


    def update_user(self, username: str, **fields):
        if not fields:
            raise ValueError("No fields provided to update.")

        set_clause = ", ".join([f"{key} = ?" for key in fields.keys()])
        query = f"UPDATE users SET {set_clause} WHERE username = ?"
        self._execute_query(query, (*fields.values(), username))
        self.log_action("User information updated")

    
    def get_audit_trail(self, limit: int = 50, offset: int = 0) -> pd.DataFrame:
        query = """
            SELECT username, date, time, action
            FROM audit_trail
            ORDER BY date DESC, time DESC
            LIMIT ? OFFSET ?
        """
        rows = self._execute_query(query, (limit, offset), fetch_all=True)
        # Convert rows to a DataFrame
        df = pd.DataFrame(rows, columns=["username", "date", "time", "action"])
        return df



    def get_all_users(self):
        """
        Retrieve all users and their roles from the database.
    
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing user details.
                Each dictionary includes:
                - "username": The username of the user.
                - "admin": Boolean indicating if the user is an admin.
        """
        query = "SELECT username, admin FROM users"
        try:
            rows = self._execute_query(query, fetch_all=True)
            # Transform rows into a list of dictionaries
            return [{"username": row[0], "admin": bool(row[1])} for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve users: {e}")
            return []

def __del__(self):
    try:
        self.conn.close()
        self.logger.info("Database connection closed.")
    except Exception as e:
        self.logger.error(f"Failed to close database connection: {e}")

