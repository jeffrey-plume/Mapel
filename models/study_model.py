import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple, Dict
from services.SecurityService import SecurityService
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
class StudyModel:
    def __init__(self, file_path="file.db"):
        self.logger = logging.getLogger(__name__)  # Logger for this class
        self.file_path = file_path
        self.conn = self._get_connection()  # Persistent connection
        self._initialize_db()

    def _get_connection(self):
        """Establish and return a persistent database connection."""
        try:
            conn = sqlite3.connect(self.file_path)
            print(f"Connected to database: {self.file_path}")
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise




    def _initialize_db(self):
        """Initialize the database schema."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    action TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS electronic_signatures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            raise

    def _fetch_all(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """
        Execute a query and fetch all rows from the result.
    
        Args:
            query (str): The SQL query to execute.
            params (Tuple): The parameters to bind to the query.
    
        Returns:
            List[Tuple]: A list of rows from the query result.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            self.log_action(self.current_user, f"Database error: {e}")
            return []

    def _execute_query(self, query: str, params: tuple):
        """Execute a query with parameters."""
        try:
            with self._get_connection() as conn:
                conn.execute(query, params)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
    
    def log_action(self, username, action):
        try:
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
            time = now.strftime('%H:%M:%S')
            params = (username, date, time, action)
            logger.debug(f"Logging action with params: {params}, Type: {type(params)}")
            query = '''
                INSERT INTO audit_trail (username, date, time, action)
                VALUES (?, ?, ?, ?)
            '''
            self._execute_query(query, params)
        except Exception as e:
            logger.error(f"Failed to log action '{action}' for user '{username}': {e}")


    def get_audit_trail(self) -> List[Dict[str, str]]:
        """
        Retrieve all rows from the audit_trail table.
    
        Returns:
            List[Dict[str, str]]: A list of dictionaries containing audit trail data.
        """
        query = "SELECT username, date, time, action FROM audit_trail ORDER BY date DESC, time DESC"
        rows = self._fetch_all(query)

        # Convert rows into a list of dictionaries for easier use
        return [
            {"username": row[0], "date": row[1], "time": row[2], "action": row[3]}
            for row in rows
         ]

            
            
    def close_connection(self):
        """Close the persistent database connection."""
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                print("Database connection closed.")
            except sqlite3.Error as e:
                print(f"Error closing connection: {e}")
                raise

    def __del__(self):
        """Ensure the connection is closed when the object is destroyed."""
        self.close_connection()



