from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox, QTextEdit, QComboBox
from PyQt5.QtCore import QTimer
import logging


class PasswordDialog(QDialog):
    def __init__(self, user_model, parent=None, logger = logging.getLogger(__name__)):
        super().__init__(parent)
        self.setWindowTitle("Enter Password and Comments")
        self.setFixedSize(300, 250)

        self.logger = logger
        self.password = None
        self.comments = None
        self.reason = None
        self.user_model = user_model
        self.submit_attempts = 0
        self.max_attempts = 3
        self.lockout_duration = 10000  # 10 seconds lockout duration in milliseconds

        self.setup_ui()

    def setup_ui(self, pw = None):
        """Initialize UI components."""
        self.label_password = QLabel("Enter your password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setText(pw)

        self.label_reason = QLabel("Select a reason:")
        self.reason_dropdown = QComboBox()
        self.reason_dropdown.addItems(["Authorship", "Review"])  # Add dropdown options

        self.label_comments = QLabel("Enter comments (optional):")
        self.comments_input = QTextEdit()

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.handle_submit)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)  # Close dialog without action

        layout = QVBoxLayout()
        layout.addWidget(self.label_password)
        layout.addWidget(self.password_input)
        layout.addWidget(self.label_comments)
        layout.addWidget(self.reason_dropdown)  # Add dropdown to layout

        layout.addWidget(self.comments_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)

    def handle_submit(self):
        """Handle password submission."""
        self.password = self.password_input.text().strip()
        self.comments = self.comments_input.toPlainText().strip()
        self.reason = self.reason_dropdown.currentText().strip()  # Get selected reason

        if not self.password:
            QMessageBox.warning(self, "Invalid Input", "Password cannot be empty.")
            return

        try:
            if self.user_model.verify_credentials(self.user_model.username, self.password):
                self.logger.info(f"User '{self.user_model.username}' authenticated successfully.")
                self.accept() 
                
                return [self.password, self.reason,  self.comments]
            else:
                self.handle_failed_submit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Submit failed: {e}")
            self.logger.error(f"Unexpected error during submit: {e}")

    def handle_failed_submit(self):
        """Handle failed submission attempts."""
        self.submit_attempts += 1
        self.password_input.clear()
        self.password_input.setFocus()

        self.user_model.log_action("Submit failed")
        self.logger.warning(f"Submit failed for user '{self.user_model.username}'.")

        if self.submit_attempts >= self.max_attempts:
            self.lock_out_user()
        else:
            remaining_attempts = self.max_attempts - self.submit_attempts
            QMessageBox.warning(
                self,
                "Submit Failed",
                f"Invalid password. You have {remaining_attempts} attempts remaining."
            )

    def lock_out_user(self):
        """Temporarily lock out the user."""
        self.submit_button.setDisabled(True)
        self.password_input.clear()
        self.user_model.log_action("User locked out")
        self.logger.warning(f"User '{self.user_model.username}' locked out due to too many failed attempts.")

        QMessageBox.critical(
            self,
            "Account Locked",
            f"Too many failed attempts. Try again in {self.lockout_duration // 1000} seconds."
        )

        QTimer.singleShot(self.lockout_duration, self.reset_submit_attempts)

    def reset_submit_attempts(self):
        """Reset submission attempts and re-enable the submit button."""
        self.submit_attempts = 0
        self.submit_button.setEnabled(True)
        QMessageBox.information(self, "Lockout Ended", "You can try submitting again.")
        self.logger.info("Submit attempts reset and lockout ended.")

