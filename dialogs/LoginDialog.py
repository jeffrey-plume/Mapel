from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import QTimer
from dialogs.RegisterDialog import RegisterDialog  # Import RegisterDialog
from models.user_model import UserModel  # Import UserModel
import logging

logger = logging.getLogger(__name__)  # Logger for application-level tracking

class LoginDialog(QDialog):
    def __init__(self, user_model: UserModel, parent=None):
        super().__init__(parent)
        self.user_model = user_model  # Injected UserModel
        self.setWindowTitle("Login")
        self.setup_ui()

        self.login_attempts = 0
        self.max_attempts = 3
        self.lockout_duration = 10000  # Lockout duration in milliseconds (10 seconds)
        self.lockout_timer = None  # Timer for lockout

    def setup_ui(self):
        """Setup the UI elements."""
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

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

        if not self.validate_inputs(username, password):
            return

        try:
            self.user_model.username = username
            
            if self.user_model.verify_credentials(username, password):

                self.user_model.log_action("Login successful")
                logger.info(f"User '{username}' logged in successfully.")

                self.accept()  # Close the dialog with QDialog.Accepted
            else:
                self.handle_failed_login(username)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")
            logger.error(f"Unexpected error during login: {str(e)}")

    def handle_failed_login(self, username):
        """Handle a failed login attempt."""
        self.login_attempts += 1
        self.password_input.clear()
        self.password_input.setFocus()

        # Log and audit failed login attempts
        self.user_model.log_action("Login failed")
        logger.warning(f"Login failed for user '{username}'.")

        if self.login_attempts >= self.max_attempts:
            self.lock_out_user()
            QMessageBox.information(
                self,
                "Warning",
                f"Invalid username or password.  {self.login_attempts} of {self.max_attempts} attempts. Please try again later",
            )

    def lock_out_user(self):
        """Lock out the user temporarily after too many failed login attempts."""

        # Log and audit the lockout event
        self.user_model.log_action("User locked out")
        logger.warning(
            f"User '{self.username_input.text().strip()}' locked out due to too many failed login attempts."
        )

        # Disable the login button and start the lockout timer
        self.login_button.setDisabled(True)
        self.lockout_timer = QTimer(self)
        self.lockout_timer.setInterval(self.lockout_duration)
        self.lockout_timer.setSingleShot(True)
        self.lockout_timer.timeout.connect(self.reset_login_attempts)
        self.lockout_timer.start()

    def reset_login_attempts(self):
        """Reset login attempts and re-enable the login button."""
        self.login_attempts = 0
        self.login_button.setEnabled(True)
        logger.info("Login attempts reset.")

    def validate_inputs(self, username, password):
        """Validate the username and password inputs."""
        if not username or not password:
            QMessageBox.warning(self, "Error", "Both username and password are required.")
            return False
        if len(username) < 3:
            QMessageBox.warning(self, "Error", "Username must be at least 3 characters long.")
            return False
        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters long.")
            return False
        if ' ' in username or ' ' in password:
            QMessageBox.warning(self, "Error", "Username and password cannot contain spaces.")
            return False
        return True

    def handle_register(self):
        """Open the Register Dialog."""
        register_dialog = RegisterDialog(self.user_model, self)
        if register_dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "User registered successfully! Please login.")
            logger.info("New user registered successfully.")
