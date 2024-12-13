from dialogs.AuditTrailDialog import AuditTrailDialog  # Dialog for viewing audit trails
from dialogs.UserAccessDialog import UserAccessDialog  # Dialog for user management
from dialogs.file_dialog import FileManagementDialog  # File Management Dialog
from dialogs.PasswordDialog import PasswordDialog
from models.study_model import StudyModel  # For managing study-specific data
from models.user_model import UserModel  # For managing user credentials
from utils.dialog_helper import DialogHelper  # Utility for displaying dialogs
from PyQt5.QtCore import QSize, QFile, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox, QVBoxLayout, QWidget, QToolBar, QMenu, QLabel, QDialog
from datetime import datetime
import os
import tempfile
import importlib.util


class MainWindow(QMainWindow):
    def __init__(self, user_model):
        super().__init__()
        self.setWindowTitle("Mapel")
        self.setGeometry(300, 100, 300, 100)

        self.unsaved_changes = False
        self.file_path = None
        self.open_windows = []  # List to track all open windows

        self.user_model = user_model
        self.study_model = self.create_file()
        self.selected_option = None

        # State variables
        self.export = {
            'audit_trail': {},
            'signatures': {},
            'data': {},
            'results': {},
            'metadata': {
                'program_version': 1.0,
                'date_created': datetime.now(),
                'user': self.study_model.username,
                'public_key': self.study_model.get_user_credentials()['public_key']
            }
        }

        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Setup menu bar and toolbar
        self.create_menu_bar()
        self.create_toolbar()
        # Add QLabel for module status
        self.module_status_label = QLabel("No module loaded", self)
        self.module_status_label.setStyleSheet(
            "color: red; font-weight: bold; font-size: 14px; background-color: black;"
        )
        self.main_layout.addWidget(self.module_status_label)
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self.create_action("New File", self.create_file))
        file_menu.addAction(self.create_action("Open File", self.open_file))
        file_menu.addAction(self.create_action("Save File", self.save_file))
        file_menu.addAction(self.create_action("Save As", self.save_as))
        file_menu.addSeparator()
        file_menu.addAction(self.create_action("Import", lambda: self.select_files("Images")))
        file_menu.addSeparator()
        file_menu.addAction(self.create_action("Exit", self.close))

        # Analyze menu
        analysis_menu = menu_bar.addMenu("Analyze")
        self.module_menu = QMenu("Module", self)
        analysis_menu.addMenu(self.module_menu)

        # Add Run action
        self.run_action = self.create_action("Run", self.run_selected_option)
        self.run_action.setDisabled(True)  # Initially disabled
        analysis_menu.addAction(self.run_action)
        analysis_menu.addAction(self.create_action("Sign Results", self.sign_results))

        # Utilities menu
        utilities_menu = menu_bar.addMenu("Utilities")
        utilities_menu.addAction(self.create_action("File Management", self.open_file_management))
        utilities_menu.addSeparator()
        utilities_menu.addAction(self.create_action("Study Audit Trail", self.view_study_audit_trail))

        # System menu
        system_menu = menu_bar.addMenu("System")
        system_menu.addAction(self.create_action("System Audit Trail", self.view_system_audit_trail))
        system_menu.addSeparator()
        system_menu.addAction(self.create_action("User Management", self.open_user_management))
        self.load_module_options()

    def create_toolbar(self):
        """Create the toolbar with small buttons."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setIconSize(QSize(24, 24))  # Small icons
        self.addToolBar(Qt.TopToolBarArea, toolbar)  # Anchor toolbar to the top

        # Add actions to toolbar
        toolbar.addAction(self.create_action("New", self.create_file, "icons/new_file.png"))
        toolbar.addAction(self.create_action("Open", self.open_file, "icons/open_file.png"))
        toolbar.addAction(self.create_action("Save", self.save_file, "icons/save_file.png"))
        toolbar.addSeparator()

        # Add the Run button
        self.run_button_action = QAction(QIcon("icons/run.png"), "Run", self)
        self.run_button_action.triggered.connect(self.run_selected_option)
        self.run_button_action.setDisabled(True)  # Initially disabled
        toolbar.addAction(self.run_button_action)

        toolbar.addSeparator()
        toolbar.addAction(self.create_action("Import", lambda: self.select_files("Images"), "icons/import_file.png"))
        toolbar.addSeparator()
        toolbar.addAction(self.create_action("Audit Trail", self.view_study_audit_trail, "icons/audit_logo.png"))
        toolbar.addAction(self.create_action("Sign Results", self.sign_results, "icons/signature_logo.png"))
        

    def create_action(self, name, handler, icon=None):
        """Helper to create actions for menu and toolbar."""
        action = QAction(name, self)
        if icon and os.path.exists(icon):
            action.setIcon(QIcon(icon))
        else:
            action.setIconVisibleInMenu(False)  # Use text-only action if icon is missing
        action.triggered.connect(handler)
        return action

    
    def serialize_dict(self, data_dict: dict) -> dict:
        """
        Recursively serialize a dictionary, converting unsupported data types.

        Args:
            data_dict (dict): Dictionary to serialize.

        Returns:
            dict: Serialized dictionary with JSON-compatible data types.
        """
        serialized = {}
        for key, value in data_dict.items():
            if isinstance(value, dict):
                # Recursively handle nested dictionaries
                serialized[key] = self.serialize_dict(value)
            elif isinstance(value, (list, tuple)):  # Handle list or tuple
                serialized[key] = list(value)
            else:
                # Convert unsupported types to strings
                serialized[key] = value
        return serialized

    
    def sign_results(self):
        """Sign the processed results using the user's private key."""
        # Open password dialog
        password_dialog = PasswordDialog(self)
        if password_dialog.exec_() == QDialog.Accepted:
            password = password_dialog.password
    
            try:
                # Fetch user credentials
                user_credentials = self.user_model.get_user_credentials()
                if not user_credentials:
                    QMessageBox.critical(self, "Error", "User credentials not found.")
                    return
    
                encrypted_private_key = user_credentials["encrypted_private_key"]
                salt = user_credentials["salt"]
    
                # Decrypt private key
                private_key = self.security_service.decrypt_private_key(
                    encrypted_private_key, password, salt
                )
                if not private_key:
                    QMessageBox.critical(self, "Error", "Failed to decrypt the private key. Invalid password?")
                    return
    
                # Serialize and hash the processed results
                if not hasattr(self, "processed_results") or not self.processed_results:
                    QMessageBox.warning(self, "Warning", "No processed results available for signing.")
                    return
    
                data_to_sign = serialize_dict(self.processed_results)
                data_hash = hashlib.sha256(data_to_sign.encode()).digest()
    
                # Sign the hashed data
                signature = private_key.sign(
                    data_hash,
                    padding.PSS(
                        mgf=padding.MGF1(SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    SHA256()
                )
    
                # Handle signed results
                QMessageBox.information(self, "Success", "Data signed successfully!")
                print(f"Signature: {signature.hex()}")  # For debugging or saving
    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Signing failed: {e}")
                print(f"Error during signing: {e}")

    
    def load_module_options(self):
        """Load available modules from the 'module' folder."""
        module_dir = os.path.join(os.getcwd(), "Modules")  # Adjust path as needed
        if not os.path.exists(module_dir):
            DialogHelper.show_error(self, "Error", f"Module folder not found: {module_dir}")
            return
    
        # Clear existing options
        self.options = {}
        self.module_menu.clear()
    
        # Scan for Python files in the module directory
        for file_name in os.listdir(module_dir):
            if file_name.endswith(".py") and not file_name.startswith("__"):  # Exclude __init__.py
                module_name = file_name[:-3]  # Remove .py extension
                self.add_checkable_option(module_name)

    def add_checkable_option(self, option_name):
        """Add a checkable option to the 'Module' submenu."""
        action = QAction(option_name, self)
        action.setCheckable(True)  # Make the option checkable
        action.triggered.connect(lambda checked, opt=option_name: self.update_selection(opt))
        self.module_menu.addAction(action)
        self.options[option_name] = action  # Store the action for reference

    def update_selection(self, selected_option):
        """Update the internal variable and ensure only the selected option is checked."""
        # Uncheck all options
        for option_name, action in self.options.items():
            if option_name == selected_option:
                action.setChecked(True)  # Check the selected option
            else:
                action.setChecked(False)  # Uncheck others

        # Update the internal variable
        self.selected_option = selected_option
        self.module_status_label.setText(f"Selected Module: {self.selected_option}")
        self.module_status_label.setStyleSheet(
                "color: black; font-weight: bold; font-size: 14px; background-color: black;"
            )
        self.run_action.setDisabled(False)  # Enable Run action
        self.run_button_action.setDisabled(False)  # Enable Run button
        print(f"Selected Module: {self.selected_option}")  # For debugging


    def _remove_window(self, processor):
        """Safely remove a processor window from the open windows list."""
        if processor in self.open_windows:
            self.open_windows.remove(processor)

    def run_selected_option(self):
        """Run the selected module."""
        if not self.selected_option:
            DialogHelper.show_error(self, "Error", "No module selected.")
            return
    
        module_dir = os.path.join(os.getcwd(), "Modules")
        module_path = os.path.join(module_dir, f"{self.selected_option}.py")
    
        if not os.path.exists(module_path):
            DialogHelper.show_error(self, "Error", f"Module file not found: {module_path}")
            return
    
        try:
            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(self.selected_option, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
    
            # Check for a class with the same name as the module
            if hasattr(module, self.selected_option):
                processor_class = getattr(module, self.selected_option)  # Get the class
                processor = processor_class(self.selected_files)  # Instantiate the class
                processor.show()
                self.open_windows.append(processor)
                # Handle results when the processor is closed
                #def on_processor_closed():
                if hasattr(processor, "processed_results") and processor.processed_results:
                    self.processed_results = processor.processed_results    
                # Connect destroyed signal and track open windows
                self._remove_window(processor)
            else:
                DialogHelper.show_info(self, "Info", f"Module '{self.selected_option}' loaded but no valid entry point found.")
        except Exception as e:
            DialogHelper.show_error(self, "Error", f"Failed to run module '{self.selected_option}': {e}")



    def select_files(self, file_type):
        """Open a file dialog to select multiple files based on the file type."""
        file_filters = {
            "Images": "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
            "Text": "Text Files (*.txt *.csv)",
        }

        file_filter = file_filters.get(file_type, "All Files (*.*)")
        files, _ = QFileDialog.getOpenFileNames(self, f"Select {file_type} Files", "", file_filter)

        if files:
            self.selected_files = files
            self.study_model.log_action( f"Selected {len(self.selected_files)} {self.selected_files} files")
            self.export['data'] = {x :None for x in self.selected_files}
            QMessageBox.information(self, "Files Selected", f"{len(self.selected_files)} files added.")

            if file_type == "Images":
                self.import_images(self.selected_files)

    def import_images(self, images):
        """Open the image viewer for the selected images."""
        if images:
            if hasattr(self, 'image_viewer') and self.image_viewer.isVisible():
                QMessageBox.information(self, "Image Viewer", "Image Viewer is already open.")
                return

            self.image_viewer = ImageViewer(images)
            self.image_viewer.show()

            self.study_model.log_action( f"Opened Image Viewer with {len(images)} images")
        else:
            QMessageBox.warning(self, "No Images", "No image files selected.")

    def open_file_management(self):
        """Open the File Management dialog."""
        dialog = FileManagementDialog(self.selected_files, parent=self)
        dialog.exec_()
        self.study_model.log_action( "Opened File Management dialog")

    def create_file(self):
        """Create a new file."""
        try:
            #file_path, _ = QFileDialog.getSaveFileName(self, "Create New File", "", "Shiva Files (*.shiva)")
            if self.unsaved_changes:
                reply = QMessageBox.question(self, "Unsaved Changes",
                                             "You have unsaved changes. Do you want to save before exiting?",
                                             QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    self.save_file()
                    event.accept()
                elif reply == QMessageBox.No:
                    event.accept()
                else:
                    event.ignore()
                    return
                if self.study_model:
                    self.study_model.conn.close()  # Safely close the existing connection
                    
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".shiva")
            file_path = temp_file.name
            temp_file.close()  # Close the file so it can be used elsewhere  
            
            study_model = StudyModel(file_path)
            self.unsaved_changes = False
            study_model.log_action( f"Created new file: {file_path}")
            #DialogHelper.show_info(self, "Success", f"New file created at {self.file_path}")
            return study_model
        except Exception as e:
            DialogHelper.show_error(self, "Error", f"Failed to create file: {e}")


    def open_file(self):
        """Open an existing file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Shiva Files (*.shiva)")
            if file_path:
                self.file_path = file_path
                self.study_model = StudyModel(self.file_path)
                self.unsaved_changes = False
                self.study_model.log_action( f"Opened file: {file_path}")
                DialogHelper.show_info(self, "Success", f"File opened: {self.file_path}")
        except Exception as e:
            self.user_model.log_action( f"Failed to open file: {str(e)}")
            DialogHelper.show_error(self, "Error", f"Failed to open file: {e}")


        

    def save_file(self):
        """Save the current file and modified images."""
        if not self.file_path:
            self.save_as()


    def save_as(self):
        """Save the current file as a new file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "Shiva Files (*.shiva)")
            if file_path:
                self.file_path = file_path
                if self.study_model:
                    self.study_model.conn.close()
                self.study_model = StudyModel(self.file_path)
                self.save_file()
        except Exception as e:
            DialogHelper.show_error(self, "Error", f"Failed to save file as: {e}")

    def view_system_audit_trail(self):
        """Open the system audit trail dialog."""
        audit_data = self.user_model.get_audit_trail()  # Fetch system audit data
        dialog = AuditTrailDialog(audit_data, self)
        dialog.exec_()
    
    def view_study_audit_trail(self):
        """Open the study-specific audit trail dialog."""
        if not self.study_model:
            QMessageBox.warning(self, "Error", "No study file is open.")
            return
        audit_data = self.study_model.get_audit_trail()  # Fetch study-specific audit data
        dialog = AuditTrailDialog(audit_data, self)
        dialog.exec_()
        
    def closeEvent(self, event):
        """Handle unsaved changes and close all open windows."""
        if self.unsaved_changes:
            reply = QMessageBox.question(self, "Unsaved Changes",
                                         "You have unsaved changes. Do you want to save before exiting?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_file()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
                return
    
        self.close_all_windows()
        self.user_model.log_action(action = "Application closed")
        event.accept()

   
    def close_all_windows(self):
        """Close all open processor windows."""
        for window in self.open_windows:
            if window:
                window.close()
        self.open_windows.clear()

    def open_user_management(self):
        """Open the user management dialog."""
        is_admin = [True if self.user_model.get_user_credentials()['admin'] == 1 else False]
        dialog = UserAccessDialog(self.user_model, self.user_model.username, is_admin)
        dialog.exec_()



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = Start()
    app.exec_()