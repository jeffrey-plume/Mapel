from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox
from models.user_model import UserModel
import logging
from services.SecurityService import SecurityService

logger = logging.getLogger(__name__)

class RegisterDialog(QDialog):
    def __init__(self, user_model: UserModel, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register")
        self.setFixedSize(400, 250)
        self.user_model = user_model
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI elements."""
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        self.register_button = QPushButton("Register")
        self.register_button.setEnabled(False)
        self.register_button.clicked.connect(self.handle_register)

        # Enable register button only when inputs are valid
        self.username_input.textChanged.connect(self.check_inputs)
        self.password_input.textChanged.connect(self.check_inputs)
        self.confirm_password_input.textChanged.connect(self.check_inputs)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_label)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(self.register_button)
        self.setLayout(layout)

    def check_inputs(self):
        """Enable the register button only if all fields are filled."""
        self.register_button.setEnabled(
            bool(self.username_input.text().strip() and
                 self.password_input.text().strip() and
                 self.confirm_password_input.text().strip())
        )

    def handle_register(self):
        """Handle the registration process."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        is_valid, error_message = SecurityService.validate_inputs(username, password, confirm_password)
        if not is_valid:
            QMessageBox.warning(self, "Invalid Input", error_message)
            logger.warning(f"Input validation failed: {error_message}")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            logger.warning("Password and confirm password do not match.")
            return

        self.user_model.username = username

        try:
            self.user_model.register_user(password)
            logger.info(f"User '{self.user_model.username}' registered successfully.")
            self.user_model.log_action("User registered")
            QMessageBox.information(self, "Success", "Registration successful! You can now log in.")
            self.accept()  # Close the dialog with QDialog.Accepted
        except ValueError as e:
            if "already exists" in str(e).lower():
                QMessageBox.warning(self, "Error", "Username already exists. Please choose a different one.")
                logger.warning(f"Registration failed: Username '{self.user_model.username}' already exists.")
            else:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Registration failed with error: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Registration failed: {str(e)}")
            logger.error(f"Unexpected error during registration: {str(e)}")
