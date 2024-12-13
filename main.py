import sys
import sqlite3
import logging
from PyQt5.QtWidgets import QApplication, QDialog
from dialogs.LoginDialog import LoginDialog
from ui.main_window import MainWindow
from models.user_model import UserModel

# Set up logging at the module level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting the application.")
        app = QApplication(sys.argv)

        # Initialize services
        db_connection = sqlite3.connect('user_credentials.db')
        user_model = UserModel()

        logger.info("Services initialized successfully.")

        # Launch LoginDialog
        login_dialog = LoginDialog(user_model)

        if login_dialog.exec_() == QDialog.Accepted:

            logger.info(f"User '{user_model.username}' logged in successfully.")
            main_window = MainWindow(user_model)
            main_window.show()

            sys.exit(app.exec_())  # Exit only when the application closes
        else:
            logger.info("Login canceled by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        # Close the database connection
        db_connection.close()
        logger.info("Application closed.")

if __name__ == "__main__":
    main()
