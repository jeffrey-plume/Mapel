import sys
import sqlite3
import logging
import os
import traceback
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from dialogs.LoginDialog import LoginDialog
from ui.main_window import MainWindow
from models.user_model import UserModel

# Set up logging at the module level
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Mapel Application")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()

def setup_logging(debug: bool):
    """Configure logging based on debug mode."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level)
    logger.info("Debug mode enabled" if debug else "Running in standard mode")

def initialize_database(db_path: str) -> sqlite3.Connection:
    """Initialize and return a database connection."""
    try:
        connection = sqlite3.connect(db_path)
        logger.info(f"Connected to database at {db_path}")
        return connection
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database at {db_path}: {e}")
        raise

def show_fatal_error(message):
    """Display a fatal error message dialog."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Error")
    msg_box.setText(message)
    msg_box.exec_()

def main():
    args = parse_args()
    setup_logging(args.debug)

    try:
        logger.info("Starting the application.")
        app = QApplication(sys.argv)

        # Initialize database and services
        DB_PATH = os.getenv("DB_PATH", "user_credentials.db")
        db_connection = initialize_database(DB_PATH)
        user_model = UserModel(db_connection)

        logger.info("Services initialized successfully.")

        # Launch LoginDialog
        login_dialog = LoginDialog(user_model=user_model)
        if login_dialog.exec_() != QDialog.Accepted:
            logger.info("Login canceled by user.")
            sys.exit(0)

        # Launch MainWindow
        main_window = MainWindow(user_model)
        main_window.show()

        sys.exit(app.exec_())  # Exit only when the application closes

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        logger.error(error_message)
        logger.debug(traceback.format_exc())
        show_fatal_error(error_message)
    finally:
        # Ensure the database connection is closed
        if 'db_connection' in locals() and db_connection:
            db_connection.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    main()
