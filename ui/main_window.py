from dialogs.TableDialog import TableDialog  # Dialog for viewing audit trails
from dialogs.UserAccessDialog import UserAccessDialog  # Dialog for user management
from dialogs.PasswordDialog import PasswordDialog
from services.SecurityService import SecurityService
from dialogs.FileManagementDialog import FileManagementDialog
from Modules.EmptyProcessor import EmptyProcessor  # Import the empty processor

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
    def __init__(self, user_model, parent=None):
        super().__init__()
        self.setWindowTitle("Mapel")
        self.setGeometry(300, 100, 300, 100)

        self.open_windows = []  # List to track all open windows
        self.user_model = user_model
        self.study_model = StudyModel(self.user_model)
        self.unsaved_changes = False


        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        # Connect the signal from StudyModel
        self.study_model.files_imported.connect(self.update_file_list_and_open_manager)
        
        self.file_list = []  # Shared file list
        self.file_management_dialog = None  # Initialize as None

        self.processor = EmptyProcessor(self.file_list)  # Default processor with empty file list
        self.processor_class = EmptyProcessor  # Default processor class
        # Default to EmptyProcessor

        
                # Setup menu bar and toolbar
        self.create_menu_bar()
        self.create_toolbar()
        
        # Add QLabel for module status
        self.module_status_label = QLabel("No module loaded", self)
        self.module_status_label.setStyleSheet(
            "color: red; font-weight: bold; font-size: 14px; background-color: black;"
        )
        
        self.main_layout.addWidget(self.module_status_label)
        self.study_model.create_new_file()

    def create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self.create_action("New File", self.study_model.create_new_file))
        file_menu.addAction(self.create_action("Open File", self.study_model.open_file))
        file_menu.addAction(self.create_action("Save File", self.study_model.save_file))
        file_menu.addAction(self.create_action("Save As", self.study_model.save_as))
        file_menu.addSeparator()


        file_menu.addAction(self.create_action("Import", self.study_model.import_files))
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
        analysis_menu.addAction(self.create_action("Sign Results", self.study_model.sign_results))

        # Utilities menu
        utilities_menu = menu_bar.addMenu("Utilities")
        utilities_menu.addAction(self.create_action("File Management", self.open_file_management))
        utilities_menu.addSeparator()
        utilities_menu.addAction(self.create_action("Study Audit Trail", self.view_study_audit_trail))
        # Add to your menu bar
        utilities_menu.addAction(self.create_action("View Signatures", self.view_signatures))
        


        # System menu
        system_menu = menu_bar.addMenu("System")
        system_menu.addAction(self.create_action("System Audit Trail", self.user_model.get_audit_trail))
        system_menu.addSeparator()
        system_menu.addAction(self.create_action("User Management", self.open_user_management))
        self.load_module_options()

    def create_toolbar(self):
        """Create the toolbar with small buttons."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setIconSize(QSize(24, 24))  # Small icons
        self.addToolBar(Qt.TopToolBarArea, toolbar)  # Anchor toolbar to the top

        # Add actions to toolbar
        toolbar.addAction(self.create_action("New", self.study_model.create_new_file, "icons/new_file.png"))
        toolbar.addAction(self.create_action("Open", self.study_model.open_file, "icons/open_file.png"))
        toolbar.addAction(self.create_action("Save", self.study_model.save_file, "icons/save_file.png"))
        toolbar.addSeparator()

        # Add the Run button
        self.run_button_action = QAction(QIcon("icons/run.png"), "Run", self)

        
        # Add Import Files action
        import_action = QAction("Import Files", self)
        import_action.setIcon(QIcon("icons/import_file.png"))  # Add an icon (optional)
        import_action.triggered.connect(self.study_model.import_files)  # Connect to StudyModel's import_files method
        toolbar.addAction(import_action)
        toolbar.addSeparator()

        # Add the Run button
        self.run_button_action = QAction(QIcon("icons/run.png"), "Run", self)
        self.run_button_action.triggered.connect(self.run_selected_option)
        self.run_button_action.setDisabled(True)  # Initially disabled
        toolbar.addAction(self.run_button_action)

        toolbar.addAction(self.create_action("Audit Trail", self.view_study_audit_trail, "icons/audit_logo.png"))
        toolbar.addAction(self.create_action("Sign Results", self.view_signatures, "icons/signature_logo.png"))


    def create_action(self, name, handler, icon=None):
        """Helper to create actions for menu and toolbar."""
        action = QAction(name, self)
        if icon and os.path.exists(icon):
            action.setIcon(QIcon(icon))
        else:
            action.setIconVisibleInMenu(False)  # Use text-only action if icon is missing
        action.triggered.connect(handler)
        return action

    def view_signatures(self):
            """
            Display the signed results in the TableDialog.
            """
            try:
                # Ensure signatures are available
                if not self.study_model.signatures["signature"]:
                    QMessageBox.information(self, "No Signatures", "No signatures available to display.")
                    return
        
                # Prepare the data for the TableDialog
                table_data, column_headers = self.study_model.prepare_signatures_data()
        
                # Show the table dialog
                table_dialog = TableDialog(table_data, column_headers, title="Signatures and Data Hashes", parent=self)
                table_dialog.exec_()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to display signatures: {e}")


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
        self.module_status_label.setStyleSheet("color: black; font-weight: bold; font-size: 14px; background-color: black;")
        self.run_action.setDisabled(False)  # Enable Run action
        self.run_button_action.setDisabled(False)  # Enable Run button
        print(f"Selected Module: {self.selected_option}")  # For debugging


    def load_module(self):
        """Load a processor module dynamically."""
        module_dir = os.path.join(os.getcwd(), "Modules")
        module_path = os.path.join(module_dir, f"{self.selected_option}.py")
    
        if not os.path.exists(module_path):
            QMessageBox.warning(self, "Error", f"Module not found: {module_path}")
            return
    
        module_name = os.path.splitext(os.path.basename(module_path))[0]
        try:
            # Dynamically load the module
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
    
            # Validate the module contains the required class
            if not hasattr(module, module_name):
                raise ImportError(f"Class '{module_name}' not found in module '{module_name}'")
    
            # Replace the current processor with the new one
            processor_class = getattr(module, module_name)
    
            if not self.file_list:
                QMessageBox.warning(self, "Error", "No files loaded. Cannot initialize processor.")
                return
    
            self.processor = processor_class(self.file_list, index=0)

            if isinstance(self.processor, QWidget):
                self.open_windows.append(self.processor)
                self.processor.show()
            print(f"Processor '{module_name}' loaded successfully.")
    
            # Reconnect the FileManagementDialog signal to the new processor
            if self.file_management_dialog and hasattr(self.processor, "set_current_index"):
                self.file_management_dialog.current_index_changed.disconnect()
                self.file_management_dialog.current_index_changed.connect(self.processor.set_current_index)
                print("Signal reconnected to the new processor.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load module: {e}")
            self.processor = EmptyProcessor(self.file_list)  # Fallback to EmptyProcessor


    def update_file_list_and_open_manager(self, file_list):
        """Update file list and open FileManagementDialog."""
        if not file_list:
            QMessageBox.warning(self, "No Files", "The imported file list is empty.")
            return
    
        self.file_list = file_list  # Update the file list in MainWindow
        print(f"MainWindow - File list updated: {self.file_list}")
    
        # Initialize or reset the processor with the new file list
        self.processor = EmptyProcessor(self.file_list)

        print("EmptyProcessor initialized with new file list.")
    
        # Open the FileManagementDialog
        self.open_file_management()

    def open_file_management(self):
        """Open the File Management dialog."""
        if not self.file_list:
            QMessageBox.warning(self, "No Files", "No files are currently loaded.")
            return
    
        # Initialize EmptyProcessor if no processor is active
        if not self.processor:
            print("No processor active. Initializing EmptyProcessor.")
            self.processor = EmptyProcessor(self.file_list)
    
        # Check if the FileManagementDialog is already open
        if self.file_management_dialog:
            if self.file_management_dialog.isVisible():
                QMessageBox.information(self, "File Management", "File Management is already open.")
                return
            else:
                # Disconnect previous signals before reconnecting
                self.file_management_dialog.current_index_changed.disconnect()
    
        # Create a new FileManagementDialog
        self.file_management_dialog = FileManagementDialog(self.file_list)
    
        # Connect the signal safely to the processor's method
        if hasattr(self.processor, "set_current_index"):
            self.file_management_dialog.current_index_changed.connect(self.processor.set_current_index)
            print("Signal connected to processor's 'set_current_index' method.")
        else:
            print("Warning: Processor does not have 'set_current_index' method.")
    
        # Add the dialog to open windows and show it
        self.open_windows.append(self.file_management_dialog)
        self.file_management_dialog.show()
        print(f"FileManagementDialog opened with files: {self.file_list}")




    def check_study_loaded(action_name="perform this action"):
        """Check if a study is loaded before proceeding."""
        if not self.study_model:
            QMessageBox.warning(self, "Error", f"No study file is loaded. Please create or open a study to {action_name}.")
            return False
        return True

    def run_selected_option(self):
        """Run the selected module."""
        try:
            self.load_module()
            QMessageBox.information(self, "Success", f"Module '{self.selected_option}' loaded and ready.")
        except ImportError as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run module: {e}")


    def view_study_audit_trail(self):
        """Open the study-specific audit trail dialog."""
        if not self.study_model:
            QMessageBox.warning(self, "Error", "No study file is open.")
            return
        audit_data = self.study_model.get_audit_trail()  # Get audit trail as list of dicts
        column_headers = ["Username", "Action", "Date", "Time"]  # Match the structure of your audit data
        
        dialog = TableDialog(table_data=audit_data, column_headers=column_headers, title="Audit Trail", parent = self)
        dialog.exec_()



        
    def closeEvent(self, event):
        """Handle unsaved changes and close all open windows."""
        if self.unsaved_changes:
            reply = QMessageBox.question(self, "Unsaved Changes",
                                         "You have unsaved changes. Do you want to save before exiting?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.study_model.save_file()
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
        dialog = UserAccessDialog(self.user_model)
        dialog.exec_()



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = Start()
    app.exec_()