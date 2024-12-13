import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple, Dict
from services.SecurityService import SecurityService
import logging
from hmac import compare_digest
from PyQt5.QtWidgets import QMessageBox
import numpy as np
import os

class UserModel:
    def __init__(self, db_path='user_credentials.db', username=None):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._initialize_db()
        self.username = username
        self._ensure_admin_exists()


    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def _initialize_db(self):
        """Create necessary tables if they don't exist."""
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
            ''',
            "audit_trail": '''
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    action TEXT NOT NULL
                )
            '''
        }
         
        for table_name, query in table_definitions.items():
            try:
                self._execute_query(query)
            except sqlite3.Error as e:
                self.logger.error(f"Failed to initialize table {table_name}: {e}")


    
    def _ensure_admin_exists(self):
        """Ensure there is at least one admin in the database."""
        query = "SELECT 1 FROM users WHERE admin = 1 LIMIT 1"
        if not self._execute_query(query, fetch_one=True):
            try:
                self.username = "".join([chr(x) for x in np.random.randint(65, 90, 5)])
                secure_password = "".join([chr(x) if np.random.randint(1, 100) % 2 == 0 else str(x) for x in np.random.randint(65, 90, 16)])
                self.register_user(secure_password, is_admin=True)
                self.logger.info(f"Default admin credentials: username={self.username}, password='{secure_password}'")
    
                QMessageBox.information(None, "First Time Login", f"Default admin credentials: username={self.username}, password={secure_password} \\ Update by going to Utilites > User Management")
            except Exception as e:
                self.logger.error(f"Failed to create default admin: {str(e)}")

    def _execute_query(self, query: str, params: Tuple = (), fetch_one=False, fetch_all=False):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Database error during query execution: {str(e)}")
            raise


    def register_user(self, password: str, is_admin: bool = False):
        """
        Register a new user.
    
        Args:
            user (str): Username of the user.
            password (str): Password for the user.
            is_admin (bool): Whether the user has admin privileges.
        """
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
            self.logger.error(f"Database error during registration of '{user}': {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during registration of '{user}': {str(e)}")
            raise 
    
    def get_user_credentials(self):
        """
        Retrieve user credentials for a specific username.
    
        Args:
            user (str): Username to fetch credentials for.
    
        Returns:
            Optional[Dict[str, str]]: User credentials or None if the user doesn't exist.
        """
        if not self.username:
            self.logger.warning("Cannot fetch credentials: Username is not provided.")
            return None
    
        query = '''
            SELECT password_hash, salt, encrypted_private_key, public_key, admin
            FROM users WHERE username = ?
        '''
        result = self._execute_query(query, (self.username,), fetch_one=True)
    
        if not result:
            self.logger.warning(f"User '{self.username}' does not exist.")
            return None
        return {
            "password_hash": result[0],
            "salt": result[1],
            "encrypted_private_key": result[2],
            "public_key": result[3],
            "admin": bool(result[4])
            }


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


    def verify_credentials(self, user: str, password: str) -> bool:
        """
        Verify user credentials by comparing the password hash.
    
        Args:
            username (str): Username.
            password (str): Password.
    
        Returns:
            bool: True if credentials are valid, False otherwise.
        """

        if not self.validate_inputs(user, password):
            return
            
        user_data = self.get_user_credentials()
        
        if self.username  != user :
            self.logger.warning(f"User mismatch for '{user}'.")
            return False
    
        derived_hash = SecurityService.hash_password(password, user_data["salt"])
        
        if compare_digest(user_data["password_hash"], derived_hash):
            self.logger.info(f"User '{self.username}' authenticated successfully.")
            return True
        else:
            self.logger.warning(f"Password mismatch for user '{self.username}'.")
            
            return False

    def validate_inputs(self, username: str, password: str, confirm_password: Optional[str] = None) -> bool:
        """
        Validate the username and password inputs.
        
        Args:
            username (str): The username to validate.
            password (str): The password to validate.
            confirm_password (Optional[str]): Optional. Confirm password to validate against.
    
        Returns:
            bool: True if all inputs are valid, False otherwise.
        """
        # Check for empty fields
        if not username or not password or (confirm_password is not None and not confirm_password):
            QMessageBox.warning(self, "Error", "All fields are required.")
            return False
    
        # Validate username length and spaces
        if len(username) < 3:
            QMessageBox.warning(self, "Error", "Username must be at least 3 characters long.")
            return False
        if ' ' in username:
            QMessageBox.warning(self, "Error", "Username cannot contain spaces.")
            return False
    
        # Validate password length and spaces
        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters long.")
            return False
        if ' ' in password:
            QMessageBox.warning(self, "Error", "Password cannot contain spaces.")
            return False
    
        # Check password confirmation if provided
        if confirm_password is not None and password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return False
    
        return True

    
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

    def get_audit_trail(self) -> List[Dict[str, str]]:
        """
        Retrieve all rows from the audit trail table.
    
        Returns:
            List[Dict[str, str]]: A list of dictionaries containing audit trail data.
        """
        query = "SELECT username, date, time, action FROM audit_trail ORDER BY date DESC, time DESC"
        rows = self._execute_query(query, fetch_all=True)
        return [
            {"username": row[0], "date": row[1], "time": row[2], "action": row[3]}
            for row in rows
        ]  # Closing square bracket added here



