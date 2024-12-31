import sys
import sqlite3
import logging
import os
import traceback
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from dialogs.LoginDialog import LoginDialog
from ui.main_window import MainWindow
from models.user_model import UserModel
from datetime import datetime
from services.LoggingServices import setup_logger, UserFilter


def parse_args():
    """Parse command-line arguments if needed."""
    import argparse
    parser = argparse.ArgumentParser(description="Run the PyQt5 application.")
    parser.add_argument("--db-path", type=str, default="user_credentials.db", help="Path to the database file.")
    return parser.parse_args()


def initialize_database(db_path):
    """Initialize the SQLite database connection."""
    try:
        connection = sqlite3.connect(db_path)
        logging.info(f"Connected to database: {db_path}")
        return connection
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to the database: {e}")
        raise


def show_fatal_error(message):
    """Display a fatal error message to the user."""
    QMessageBox.critical(None, "Fatal Error", message)
    sys.exit(1)


def main():
    args = parse_args()

    logger = setup_logger(name=__name__, username="System", filename="audit_trail.log")

    try:
        logger.info("Starting the application.")
        app = QApplication(sys.argv)

        # Initialize database and services
        db_path = args.db_path
        db_connection = initialize_database(db_path)
        user_model = UserModel(db_connection)

        logger.info("Services initialized successfully.")

        # Launch LoginDialog
        login_dialog = LoginDialog(user_model=user_model)
        if login_dialog.exec_() != QDialog.Accepted:
            logger.info("Login canceled by user.")
            sys.exit(0)

        # Update logger with user-specific information
        user_filter = UserFilter(username="System")
        logger.addFilter(user_filter)
        user_filter.username = user_model.username

        logger.info(f"User {user_model.username} logged in.")

        # Launch MainWindow
        main_window = MainWindow(user_model, logger=logger)
        main_window.show()

        # Enter the main event loop
        sys.exit(app.exec_())

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        logger.error(error_message)
        logger.debug(traceback.format_exc())
        show_fatal_error(error_message)

    finally:
        # Ensure the database connection is closed
        try:
            if db_connection:
                db_connection.close()
                logger.info("Database connection closed.")
        except Exception as close_error:
            logger.error(f"Error closing database: {close_error}")


if __name__ == "__main__":
    main()
