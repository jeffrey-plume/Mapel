from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import QTimer
from dialogs.RegisterDialog import RegisterDialog  # Import RegisterDialog
from models.user_model import UserModel  # Import UserModel
import logging
from services.SecurityService import SecurityService

logger = logging.getLogger(__name__)  # Logger for application-level tracking

class LoginDialog(QDialog):
    def __init__(self, user_model, parent=None):
        super().__init__(parent)
        self.user_model = user_model  # Injected UserModel
        self.setWindowTitle("Welcome to Mapel")
        self.setup_ui()

        self.login_attempts = 0
        self.max_attempts = 3
        self.lockout_duration = 10000  # Lockout duration in milliseconds (10 seconds)
        self.lockout_timer = None  # Timer for lockout

    def setup_ui(self):
        """Setup the UI elements."""
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)

        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.handle_register)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)
        self.setLayout(layout)

    def handle_login(self):
        """Handle user login."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # Validate inputs
        is_valid, error_message = SecurityService.validate_inputs(username, password)
        if not is_valid:
            QMessageBox.warning(self, "Invalid Input", error_message)
            logger.warning(f"Login input validation failed: {error_message}")
            return

        # Attempt to verify credentials
        self.user_model.username = username  # Update username in UserModel
        try:
            if self.user_model.verify_credentials(password):
                logger.info(f"User '{username}' logged in successfully.")
                self.accept()  # Close the dialog with QDialog.Accepted
            else:
                self.handle_failed_login()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")
            logger.error(f"Login error: {e}")

    def handle_failed_login(self):
        """Handle a failed login attempt."""
        self.login_attempts += 1
        self.password_input.clear()
        self.password_input.setFocus()

        # Log and audit the failed login attempt
        self.user_model.log_action(f"Login failed for user '{self.user_model.username}'")
        logger.warning(f"Login failed for user '{self.user_model.username}'.")

        if self.login_attempts >= self.max_attempts:
            self.lock_out_user()
            return

        remaining_attempts = self.max_attempts - self.login_attempts
        QMessageBox.warning(
            self,
            "Login Failed",
            f"Invalid username or password. You have {remaining_attempts} attempts remaining."
        )

    def lock_out_user(self):
        """Lock out the user temporarily."""
        if self.user_model.username:
            self.user_model.log_action(f"User '{self.user_model.username}' locked out.")
            logger.warning(f"User '{self.user_model.username}' locked out due to too many failed attempts.")
        else:
            logger.warning("Lockout triggered for an unknown user.")
        
        self.login_button.setDisabled(True)
        self.password_input.clear()
    
        QMessageBox.critical(
            self,
            "Account Locked",
            f"Too many failed login attempts. Try again in {self.lockout_duration // 1000} seconds."
        )
    
        self.lockout_timer = QTimer(self)
        self.lockout_timer.setInterval(self.lockout_duration)
        self.lockout_timer.setSingleShot(True)
        self.lockout_timer.timeout.connect(self.reset_login_attempts)
        self.lockout_timer.start()


    def reset_login_attempts(self):
        """Reset login attempts and re-enable login."""
        self.login_attempts = 0
        self.login_button.setEnabled(True)
        QMessageBox.information(self, "Lockout Ended", "You can try logging in again.")
        logger.info("Login attempts reset.")

    def handle_register(self):
        """Open the Register Dialog."""
        try:
            register_dialog = RegisterDialog(self.user_model, self)
            if register_dialog.exec_() == QDialog.Accepted:
                QMessageBox.information(self, "Success", "User registered successfully. Please log in.")
                logger.info("New user registered successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Registration failed: {e}")
            logger.error(f"Registration error: {e}")

