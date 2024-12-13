from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox
from models.user_model import UserModel
import logging

# Configure logger
logger = logging.getLogger(__name__)

class RegisterDialog(QDialog):
    def __init__(self, user_model: UserModel, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register")
        self.setup_ui()
        self.user_model = user_model

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
        self.register_button.clicked.connect(self.handle_register)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_label)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(self.register_button)
        self.setLayout(layout)


    def handle_register(self):
        """Handle the registration process."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        if not self.user_model.validate_inputs(username, password, confirm_password):
            return

        self.user_model.username = username

        try:
            # Attempt to register the user
            self.user_model.register_user(password)
            QMessageBox.information(self, "Success", "User registered successfully!")
            logger.info(f"User '{self.user_model.username}' registered successfully.")
            self.user_model.log_action("User registered")
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

