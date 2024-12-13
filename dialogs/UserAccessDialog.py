from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox


class UserAccessDialog(QDialog):
    def __init__(self, user_model, current_user, is_admin, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Access Management")
        self.resize(400, 400)

        self.user_model = user_model
        self.current_user = current_user
        self.is_admin = is_admin

        # Main layout
        layout = QVBoxLayout(self)

        # Dropdown for selecting users
        self.user_dropdown = QComboBox(self)
        self.populate_user_dropdown()
        layout.addWidget(QLabel("Select User:"))
        layout.addWidget(self.user_dropdown)

        # Current password verification
        self.current_password_input = QLineEdit(self)
        self.current_password_input.setEchoMode(QLineEdit.Password)
        self.current_password_input.setPlaceholderText("Current Password")
        layout.addWidget(QLabel("Current Password:"))
        layout.addWidget(self.current_password_input)

        # Password reset fields
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("New Password")
        layout.addWidget(QLabel("New Password:"))
        layout.addWidget(self.password_input)

        self.confirm_password_input = QLineEdit(self)
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        layout.addWidget(QLabel("Confirm Password:"))
        layout.addWidget(self.confirm_password_input)

        # Role selection
        layout.addWidget(QLabel("Role:"))
        self.role_dropdown = QComboBox(self)
        self.role_dropdown.addItems(["Standard", "Admin"])
        layout.addWidget(self.role_dropdown)

        # Disable role dropdown for non-admin users
        self.role_dropdown.setEnabled(self.is_admin)

        # Buttons
        save_button = QPushButton("Save Changes", self)
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        # Prepopulate the role dropdown based on the selected user
        self.user_dropdown.currentIndexChanged.connect(self.update_role_dropdown)

    def populate_user_dropdown(self):
        """Populate the user dropdown with all users."""
        users = self.user_model.get_all_users()
        for username, is_admin in users:
            self.user_dropdown.addItem(f"{username} ({'Admin' if is_admin else 'Standard'})", username)

    def update_role_dropdown(self):
        """Update the role dropdown based on the selected user's current role."""
        selected_user = self.user_dropdown.currentData()
        user_data = self.user_model.get_user_credentials(selected_user)
        if user_data:
            is_admin = user_data[-1]  # The 'admin' field is the last item in the tuple
            current_role = "Admin" if is_admin else "Standard"
            self.role_dropdown.setCurrentText(current_role)

            # Disable role dropdown for non-admins or when the current user is not an admin
            self.role_dropdown.setEnabled(self.is_admin and selected_user != self.current_user)

    def save_changes(self):
        """Handle saving changes to the selected user."""
        selected_user = self.user_dropdown.currentData()
        current_password = self.current_password_input.text()
        new_password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not self.user_model.verify_credentials(self.current_user, current_password):
            QMessageBox.warning(self, "Error", "Current password is incorrect.")
            return

        if new_password and new_password != confirm_password:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return

        try:
            # Update password if provided
            if new_password:
                salt = self.user_model.get_salt(selected_user)
                password_hash = self.user_model.security_service.hash_password(new_password, salt)
                self.user_model.update_user(selected_user, password_hash=password_hash)
                self.user_model._log_action(self.current_user, f"Updated password for user '{selected_user}'.")

            # Update role if admin and role dropdown is enabled
            if self.is_admin and self.role_dropdown.isEnabled():
                new_role = self.role_dropdown.currentText()
                is_admin = 1 if new_role == "Admin" else 0
                current_role = "Admin" if self.user_model.get_user_credentials(selected_user)[-1] else "Standard"
                
                if is_admin != (current_role == "Admin"):
                    self.user_model.update_user(selected_user, admin=is_admin)
                    self.user_model._log_action(self.current_user, f"Changed role for user '{selected_user}' to '{new_role}'.")

            QMessageBox.information(self, "Success", "Changes saved successfully!")
            self.close()
        except Exception as e:
            self.user_model._log_action(self.current_user, f"Failed to update user '{selected_user}': {e}")
            QMessageBox.critical(self, "Error", f"Failed to update user: {e}")
