from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
)
from services.SecurityService import SecurityService


class UserAccessDialog(QDialog):
    def __init__(self, user_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Access Management")
        #self.resize(400, 500)

        self.user_model = user_model
        self.is_admin = self.user_model.get_user_credentials()["admin"]

        # Main layout
        main_layout = QVBoxLayout(self)

        # User Selection Section
        user_layout = QVBoxLayout()
        user_label = QLabel("Select User:")
        self.user_dropdown = QComboBox(self)
        self.populate_user_dropdown()
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.user_dropdown)
        main_layout.addLayout(user_layout)

        # Current Password Section (Only for standard users)
        if not self.is_admin:
            current_password_layout = QVBoxLayout()
            current_password_label = QLabel("Current Password:")
            self.current_password_input = QLineEdit(self)
            self.current_password_input.setEchoMode(QLineEdit.Password)
            current_password_layout.addWidget(current_password_label)
            current_password_layout.addWidget(self.current_password_input)
            main_layout.addLayout(current_password_layout)

        # New Password Section
        password_layout = QVBoxLayout()
        password_label = QLabel("New Password:")
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)

        confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_input = QLineEdit(self)
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(confirm_password_label)
        password_layout.addWidget(self.confirm_password_input)
        main_layout.addLayout(password_layout)

        # Role Selection Section (Admins only)
        role_layout = QVBoxLayout()
        role_label = QLabel("Role:")
        self.role_dropdown = QComboBox(self)  # Ensure role_dropdown is always initialized
        if self.is_admin:
            self.role_dropdown.addItems(["Standard", "Admin"])
        else:
            self.role_dropdown.setEnabled(False)  # Disable dropdown for standard users

        role_layout.addWidget(role_label)
        role_layout.addWidget(self.role_dropdown)
        main_layout.addLayout(role_layout)

        # Buttons Section
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save Changes", self)
        save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(save_button)

        if self.is_admin:
            delete_button = QPushButton("Delete User", self)
            delete_button.clicked.connect(self.delete_user)
            button_layout.addWidget(delete_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)  # Close the dialog without saving
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        # Prepopulate the role dropdown based on the selected user
        self.user_dropdown.currentIndexChanged.connect(self.update_role_dropdown)

    def populate_user_dropdown(self):
        """Populate the user dropdown with all users and select the current user."""
        users = self.user_model.get_all_users()
        current_user = self.user_model.get_user_credentials()["username"]

        for user in users:
            username = user["username"]
            is_admin = user["admin"]
            self.user_dropdown.addItem(f"{username} ({'Admin' if is_admin else 'Standard'})", username)

        # Set the current user as the default selection
        index = self.user_dropdown.findData(current_user)
        if index != -1:
            self.user_dropdown.setCurrentIndex(index)

    def update_role_dropdown(self):
        """Update the role dropdown based on the selected user's current role."""
        selected_user = self.user_dropdown.currentData()
        if selected_user:
            user_data = self.user_model.get_user_credentials(user=selected_user)
            if user_data:
                current_role = "Admin" if user_data["admin"] else "Standard"
                self.role_dropdown.setCurrentText(current_role)
                self.role_dropdown.setEnabled(self.is_admin and selected_user != self.user_model.username)

    def clear_password_fields(self):
        """Clear all password-related input fields."""
        self.current_password_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()

    def save_changes(self):
        """Handle saving changes to the selected user."""
        selected_user = self.user_dropdown.currentData()
        new_password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        # For standard users, verify their current password
        if not self.is_admin:
            current_password = self.current_password_input.text().strip()
            if not self.user_model.verify_credentials(current_password):
                QMessageBox.warning(self, "Error", "Current password is incorrect.")
                return

        # Validate and update password
        if new_password:
            validation_error = self.validate_password(new_password)
            if validation_error:
                QMessageBox.warning(self, "Error", validation_error)
                return
            if new_password != confirm_password:
                QMessageBox.warning(self, "Error", "New passwords do not match.")
                return

        try:
            messages = []
            # Update password
            if new_password:
                salt = SecurityService.generate_salt()
                password_hash = SecurityService.hash_password(new_password, salt)
                self.user_model.update_user(selected_user, password_hash=password_hash, salt=salt)
                self.user_model.log_action(f"Updated password for user '{selected_user}'.")
                messages.append("Password updated.")

            # Update role if admin
            if self.is_admin and self.role_dropdown.isEnabled():
                new_role = self.role_dropdown.currentText()
                is_admin = 1 if new_role == "Admin" else 0
                user_data = self.user_model.get_user_credentials(user=selected_user)
                current_role = user_data["admin"]
                if selected_user == self.user_model.username and new_role == "Standard":
                    QMessageBox.warning(self, "Error", "You cannot demote yourself.")
                    return
                if is_admin != current_role:
                    self.user_model.update_user(selected_user, admin=is_admin)
                    self.user_model.log_action(f"Changed role for user '{selected_user}' to '{new_role}'.")
                    messages.append(f"Role changed to {new_role}.")

            self.clear_password_fields()
            QMessageBox.information(self, "Success", " ".join(messages))
            self.close()
        except Exception as e:
            self.user_model.log_action(f"Failed to update user '{selected_user}': {e}")
            QMessageBox.critical(self, "Error", f"Failed to update user: {e}")

    def delete_user(self):
        """Delete the selected user (Admins only)."""
        selected_user = self.user_dropdown.currentData()
        if selected_user == self.user_model.username:
            QMessageBox.warning(self, "Error", "You cannot delete your own account.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete user '{selected_user}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                self.user_model.delete_user(selected_user)
                self.user_model.log_action(f"Deleted user '{selected_user}'.")
                QMessageBox.information(self, "Success", f"User '{selected_user}' has been deleted.")
                self.populate_user_dropdown()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete user: {e}")



    def validate_password(self, password):
        """Validate the password based on defined criteria."""
        if len(password) < 8:
            return "Password must be at least 8 characters long."
        if not any(char.isdigit() for char in password):
            return "Password must include at least one number."
        if not any(char.isupper() for char in password):
            return "Password must include at least one uppercase letter."
        if not any(char.islower() for char in password):
            return "Password must include at least one lowercase letter."
        if not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for char in password):
            return "Password must include at least one special character."
        return None

 


