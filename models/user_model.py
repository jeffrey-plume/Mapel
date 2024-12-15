import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple, Dict
from services.SecurityService import SecurityService
import logging
from hmac import compare_digest
from PyQt5.QtWidgets import QMessageBox
import numpy as np
import os
import secrets
import string

class UserModel:
    def __init__(self, conn = sqlite3.connect('user_credentials.db'), username=None):
        self.logger = logging.getLogger(__name__)
        self.conn = conn
        self.username = username
        self._ensure_admin_exists()

    
    def _ensure_admin_exists(self):
        """Ensure at least one admin user exists in the database."""
        try:
            # Step 1: Initialize tables
            self._initialize_tables()
    
            # Step 2: Check if an admin user already exists
            if self._admin_exists():
                self.logger.info("Admin user already exists.")
                return
    
            # Step 3: Create a default admin user if none exists
            admin_credentials = self._create_default_admin()
            self.logger.info(f"Default admin created: {admin_credentials['username']}")
            return admin_credentials
    
        except Exception as e:
            self.logger.error(f"Error ensuring admin existence: {e}")
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
                self.logger.info(f"Table '{table_name}' initialized successfully.")
            except sqlite3.Error as e:
                self.logger.error(f"Failed to initialize table '{table_name}': {e}")
                raise
    

    def _admin_exists(self) -> bool:
        """Check if at least one admin user exists in the database."""
        query = "SELECT 1 FROM users WHERE admin = 1 LIMIT 1"
        return bool(self._execute_query(query, fetch_one=True))
    
    
    def _generate_secure_credentials() -> Dict[str, str]:
        """Generate secure credentials for a default admin."""
        username = "Admin_" + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        password_characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(password_characters) for _ in range(16))
        return {"username": username, "password": password}
    
    
    def _create_default_admin(self) -> Dict[str, str]:
        """Create a default admin user and return the credentials."""
        credentials = self._generate_secure_credentials()
        self.username = credentials["username"]
        try:
            self.register_user(credentials["password"], is_admin=True)
            return credentials
        except Exception as e:
            self.logger.error(f"Failed to create default admin user: {e}")
            raise

        # Initialize tables
        for table_name, query in table_definitions.items():
            try:
                self._execute_query(query)
            except sqlite3.Error as e:
                self.logger.error(f"Failed to initialize table '{table_name}': {e}")
                raise
    
        # Check if an admin exists
        query = "SELECT 1 FROM users WHERE admin = 1 LIMIT 1"
        if self._execute_query(query, fetch_one=True):
            self.logger.info("Admin user already exists.")
            return
    
        # Generate secure default admin credentials
        admin_username = "Admin_" + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        password_characters = string.ascii_letters + string.digits + string.punctuation
        admin_password = ''.join(secrets.choice(password_characters) for _ in range(16))
    
        # Register default admin
        self.username = admin_username
        try:
            self.register_user(admin_password, is_admin=True)
            self.logger.info(f"Default admin credentials created: username={admin_username}, password={admin_password}")
            QMessageBox.information(
                None,
                "First Time Login",
                f"Default admin credentials created:\n\n"
                f"Username: {admin_username}\nPassword: {admin_password}\n\n"
                f"Please update them immediately under Utilities > User Management."
            )
        except Exception as e:
            self.logger.error(f"Failed to create default admin user: {e}")
            raise


    def _execute_query(self, query: str, params: Tuple = (), fetch_one=False, fetch_all=False):
        try:
            with self.conn as conn:
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
    
    
        
    def get_user_credentials(self, user = None):
        """
        Retrieve user credentials for a specific username.
    
        Args:
            user (str): Username to fetch credentials for.
    
        Returns:
            Optional[Dict[str, str]]: User credentials or None if the user doesn't exist.
        """
        if not user:
            user = self.username
    
        query = '''
            SELECT password_hash, salt, encrypted_private_key, public_key, admin
            FROM users WHERE username = ?
        '''
        result = self._execute_query(query, (user,), fetch_one=True)
    
        if not result:
            self.logger.warning(f"User '{user}' does not exist.")
            return None
        return {
            "username": user,
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

    def verify_credentials(self, password: str) -> bool:
        """Verify user credentials by comparing the password hash."""
        if not SecurityService.validate_inputs(self.username, password):
            return False
    
        user_data = self.get_user_credentials()
        if not user_data:
            self.logger.warning(f"User '{self.username}' does not exist.")
            return False
    
        derived_hash = SecurityService.hash_password(password, user_data["salt"])
        if compare_digest(user_data["password_hash"], derived_hash):
            self.logger.info(f"User '{self.username}' authenticated successfully.")
            return True
    
        self.logger.warning(f"Password mismatch for user '{self.username}'.")
        return False


    
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

    def get_audit_trail(self, limit: int = 50, offset: int = 0) -> List[Dict[str, str]]:
        query = """
            SELECT username, date, time, action
            FROM audit_trail
            ORDER BY date DESC, time DESC
            LIMIT ? OFFSET ?
        """
        rows = self._execute_query(query, (limit, offset), fetch_all=True)
        return [{"username": row[0], "date": row[1], "time": row[2], "action": row[3]} for row in rows]


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

