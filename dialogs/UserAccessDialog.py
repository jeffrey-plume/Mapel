from PyQt5.QtWidgets import (
    QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox, QApplication, QTextEdit
)
from services.SecurityService import SecurityService
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextOption


class UserAccessDialog(QDialog):
    def __init__(self, user_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Management")
       # self.resize(500, 600)

        self.user_model = user_model
        self.is_admin = self.user_model.get_user_credentials()["admin"]

        # Main layout
        main_layout = QGridLayout(self)

        # Row index for grid layout
        row = 0

        # User Selection Section
        user_label = QLabel("Select User:")
        self.user_dropdown = QComboBox(self)
        self.populate_user_dropdown()
        self.user_dropdown.setCurrentText(self.user_model.username)
        self.user_dropdown.setEditable(True)  # Enable typing in new values
        self.user_dropdown.currentIndexChanged.connect(self.update_user_info)
        
        main_layout.addWidget(user_label, row, 0)
        main_layout.addWidget(self.user_dropdown, row, 1, 1, 2)  # Span across two columns
        row += 1


        # Role Selection Section (Admins only)
        role_label = QLabel("Role:")
        self.role_dropdown = QComboBox(self)
        if self.is_admin:
            self.role_dropdown.addItems(["Standard", "Admin"])
        else:
            self.role_dropdown.addItems(["Standard"])
            self.role_dropdown.setEnabled(False)

        main_layout.addWidget(role_label, row, 0)
        main_layout.addWidget(self.role_dropdown, row, 1, 1, 2)
        row += 1

        current_password_label = QLabel("Current Password:")
        self.current_password_input = QLineEdit(self)
        self.current_password_input.setEchoMode(QLineEdit.Password)

        # New Password Section
        password_label = QLabel("New Password:")
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_input = QLineEdit(self)
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        main_layout.addWidget(current_password_label, row, 0)
        main_layout.addWidget(self.current_password_input, row, 1, 1, 2)
        row += 1
        main_layout.addWidget(password_label, row, 0)
        main_layout.addWidget(self.password_input, row, 1, 1, 2)
        row += 1
        main_layout.addWidget(confirm_password_label, row, 0)
        main_layout.addWidget(self.confirm_password_input, row, 1, 1, 2)
        row += 1



        # Public Key Section
        public_key_label = QLabel("Public Key:")
        self.public_key_display = QTextEdit(self)
        self.public_key_display.setReadOnly(True)  # Ensure the text is not editable
        self.public_key_display.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)  # Enable word wrapping
        self.public_key_display.setFixedHeight(80)  # Adjust height to show approximately four lines
        copy_key_button = QPushButton("Copy Public Key")
        copy_key_button.clicked.connect(self.copy_public_key_to_clipboard)

        main_layout.addWidget(public_key_label, row, 0)
        main_layout.addWidget(self.public_key_display, row, 1)
        main_layout.addWidget(copy_key_button, row, 2)
        row += 1

        # Buttons Section
        save_button = QPushButton("Save Changes", self)
        save_button.clicked.connect(self.save_changes)

        delete_button = QPushButton("Delete User", self)
        delete_button.clicked.connect(self.delete_user)
        delete_button.setEnabled(self.is_admin)

        new_user_button = QPushButton("Create New User", self)
        new_user_button.clicked.connect(self.register_user)
        new_user_button.setEnabled(self.is_admin)

        main_layout.addWidget(save_button, row, 0)
        main_layout.addWidget(delete_button, row, 1)
        main_layout.addWidget(new_user_button, row, 2)

        # Prepopulate the role dropdown and public key based on the selected user
        self.user_dropdown.currentIndexChanged.connect(self.update_user_info)
        self.update_user_info()

    def copy_public_key_to_clipboard(self):
        public_key = self.public_key_display.text
        if public_key:
            QApplication.clipboard().setText(public_key)
            QMessageBox.information(self, "Success", "Public key copied to clipboard.")
        else:
            QMessageBox.warning(self, "Error", "No public key available to copy.")

    def populate_user_dropdown(self):
        """Populate the dropdown with all users."""
        self.user_dropdown.clear()  # Clear existing items
        users = self.user_model.get_all_users()
        for user in users:
            username = user["username"]
            self.user_dropdown.addItem(username)  # Add username directly
    


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

    
    def register_user(self):
        """Register a new user (Admins only)."""
    
        # Ensure only admins can create new users
        if not self.is_admin:
            QMessageBox.warning(self, "Error", "Only admins can create new users.")
            return
    
        # Get new username and password inputs
        new_username = self.user_dropdown.currentText()

        new_password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
    
        # Get role for the new user
        is_admin = 1 if self.role_dropdown.currentData()=='Admin' else 0
    
        # Validate new username
        if not new_username:
            QMessageBox.warning(self, "Error", "Username cannot be empty.")
            return

        
        # Check for duplicate usernames
        existing_users = [user["username"] for user in self.user_model.get_all_users()]
        if new_username in existing_users:
            QMessageBox.warning(self, "Error", "Username already exists.")
            return
    
        # Validate password
        if not new_password:
            QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
    
        validation_error = SecurityService.validate_password(new_password)
        if validation_error:
            QMessageBox.warning(self, "Error", validation_error)
            return
    
        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return


        # Register the new user
        try:

            self.user_model.register_user(
                username=new_username,
                password=new_password,
                is_admin=is_admin,
            )
    
            self.user_model.log_action(
                f"Registered new user '{new_username}' with role {'Admin' if is_admin else 'Standard'}."
            )
            QMessageBox.information(
                self,
                "Success",
                f"User '{new_username}' created successfully with the role "
                f"{'Admin' if is_admin else 'Standard'}.",
            )
    
            # Clear input fields and refresh user list
            self.password_input.clear()
            self.confirm_password_input.clear()
            self.populate_user_dropdown()
    
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to register user '{new_username}': {e}"
            )

    def save_changes(self):
        """Save changes to the selected user's credentials and role (Admins only)."""

        # Confirm the action with the admin
        confirm = QMessageBox.question(
            self,
            "Confirm Changes",
            f"Are you sure you want to make changes to '{selected_user}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return


        try:
            # Get new username and password inputs
            new_username = self.user_dropdown.currentText()
    
            new_password = self.password_input.text().strip()
            confirm_password = self.confirm_password_input.text().strip()
            current_password = self.current_password_input.text().strip()
    
            # Get role for the new user
            is_admin = 1 if self.role_dropdown.currentData()=='Admin' else 0
        
            # Validate new username
            if not new_username:
                QMessageBox.warning(self, "Error", "Username cannot be empty.")
                return
    
            
            # Check for duplicate usernames
            existing_users = [user["username"] for user in self.user_model.get_all_users()]
            if new_username in existing_users:
                QMessageBox.warning(self, "Error", "Username already exists.")
                return
        
            # Validate password
            if not new_password:
                QMessageBox.warning(self, "Error", "Password cannot be empty.")
                return
        
            validation_error = SecurityService.validate_password(new_password)
            if validation_error:
                QMessageBox.warning(self, "Error", 'validation_error')
                return
        
            if new_password != confirm_password:
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return

            if not self.is_admin:
                if not self.user_model.verify_credentials(selected_user, current_password):
                    QMessageBox.warning(self, "Error", "Password Incorrect.")
                    return

            # Update the user's credentials and role
            self.user_model.update_user(
                username=selected_user,
                password=new_password,
                is_admin=is_admin
            )
    
            # Log the changes
            self.user_model.log_action(
                f"Updated credentials for user '{selected_user}': "
                f"Role set to {'Admin' if is_admin else 'Standard'}, "
                f"Password {'updated' if new_password else 'unchanged'}."
            )
    
            # Show success message and refresh the UI
            QMessageBox.information(self, "Success", f"User '{selected_user}' has been updated.")
            self.populate_user_dropdown()
    
            # Clear the password input fields
            self.password_input.clear()
            self.confirm_password_input.clear()
    
        except Exception as e:
            # Handle errors and display a message
            self.user_model.log_action(f"Failed to update user '{selected_user}': {e}")
            QMessageBox.critical(self, "Error", f"Failed to update user: {e}")


    def delete_user(self):
        """Delete the selected user (Admins only)."""
    
        # Ensure only admins can delete users
        if not self.is_admin:
            QMessageBox.warning(self, "Error", "Only admins can delete users.")
            return
    
        # Get the selected user
        selected_user = self.user_dropdown.currentData()
        if not selected_user:
            QMessageBox.warning(self, "Error", "No user selected.")
            return
    
        # Prevent deleting the currently logged-in user
        current_user = self.user_model.get_user_credentials()["username"]
        if selected_user == current_user:
            QMessageBox.warning(self, "Error", "You cannot delete your own account.")
            return
    
        # Confirm the deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete user '{selected_user}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
    
        # Attempt to delete the user
        try:
            self.user_model.delete_user(selected_user)  # Call the appropriate delete method
            self.user_model.log_action(f"Deleted user '{selected_user}'.")
            QMessageBox.information(self, "Success", f"User '{selected_user}' has been deleted.")
            self.populate_user_dropdown()  # Refresh the dropdown list
        except Exception as e:
            self.user_model.log_action(f"Failed to delete user '{selected_user}': {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete user: {e}")

    
    def update_user_info(self):
        """Update the role dropdown and public key based on the selected user."""
        selected_user = self.user_dropdown.currentText()  # Use currentText for directly populated dropdowns
        if not selected_user:
            self.role_dropdown.setCurrentIndex(0)  # Reset to "Standard"
            self.public_key_display.clear()
            return
    
        try:
            user_data = self.user_model.get_user_credentials(username=selected_user)

            if user_data:
                # Update role dropdown
                current_role = "Admin" if user_data.get("admin", 0) else "Standard"
                self.role_dropdown.setCurrentText(current_role)
                self.role_dropdown.setEnabled(self.is_admin)
                self.user_dropdown.setEnabled(self.is_admin)

                # Update public key
                public_key = user_data.get("public_key", "N/A")
                self.public_key_display.setText(public_key)
            else:
                # Handle unknown user
                self.role_dropdown.setCurrentIndex(0)
                self.public_key_display.clear()
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch user info: {e}")




