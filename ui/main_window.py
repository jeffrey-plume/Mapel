# Standard library imports
import os
import json
import logging
from datetime import datetime
import tempfile
import numpy as np

# PyQt5 imports
from PyQt5.QtCore import QSize, QFile, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QMessageBox, QVBoxLayout,
    QWidget, QToolBar, QMenu, QLabel, QDialog, QProgressDialog, QApplication
)

# Application-specific imports
from dialogs.TableDialog import TableDialog
from dialogs.UserAccessDialog import UserAccessDialog
from dialogs.PasswordDialog import PasswordDialog
from dialogs.FileManagementDialog import FileManagementDialog
from dialogs.ImageViewer import ImageViewer
from services.SecurityService import SecurityService
from services.DataSigner import DataSigner
from services.LoggingServices import setup_logger
from services.FileManager import FileManager
from models.user_model import UserModel
from utils.file_utils import load_module
from dialogs.ControllerDialog import ControllerDialog



class MainWindow(QMainWindow):
    def __init__(self, user_model, logger=None, parent=None):
        super().__init__()
        self.setWindowTitle("Mapel")  # Set initial title

        self.setGeometry(300, 100, 400, 100)

        self.user_model = user_model
        self.logger = logger or setup_logger(name=__name__,  username=user_model.username)
        

        self.file_manager = FileManager(
            main_window=self,
            logger=logger
        )
        
        self.file_management_dialog = None
        self.selected_option = None
        self.options = {}
        self.processor = {}
        self.loaded_modules = {}
        self.file_list = []
        self.directory = None
        self.filenames = []
        self.current_index = 0
        self.open_windows = {}
        

        self.user_model.logger = self.logger
        self.file_manager.files_imported.connect(self.open_file_management)


        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.create_menu_bar()
        self.create_toolbar()

        self.module_status_label = QLabel("No module loaded", self)
        self.module_status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.main_layout.addWidget(self.module_status_label)


    def create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()
    
        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self.create_action("New File", self.file_manager.create_new_file))
        file_menu.addAction(self.create_action("Open File", self.file_manager.open_file))
        file_menu.addAction(self.create_action("Save File", self.file_manager.save_file))
        file_menu.addAction(self.create_action("Save As", self.file_manager.save_as))
        file_menu.addSeparator()
        file_menu.addAction(self.create_action("Import", self.file_manager.import_files))
        file_menu.addSeparator()
        file_menu.addAction(self.create_action("Exit", self.close))
    
        # Analyze menu
        analysis_menu = menu_bar.addMenu("Analyze")
    
        # Module options
        self.module_menu = QMenu("Module", self)
        self.load_module_options()
        analysis_menu.addMenu(self.module_menu)
        analysis_menu.addAction(self.create_action("File Management", self.open_file_management))

        # Add Run action
        self.run_action = self.create_action("Run", self.run_selected_option)
        self.run_action.setDisabled(True)  # Initially disabled
        analysis_menu.addAction(self.run_action)
        analysis_menu.addAction(self.create_action("Sign Results", self.sign_results))

    
        # Utilities menu
        utilities_menu = menu_bar.addMenu("Utilities")

        utilities_menu.addAction(self.create_action("Table View", lambda: self.update_selection('Imager'), "icons/imager.png"))
        utilities_menu.addAction(self.create_action("Image View", lambda: self.update_selection('Imager'), "icons/imager.png"))
        utilities_menu.addSeparator()

        utilities_menu.addAction(self.create_action("View Audit Trail", self.view_audit_trail))
        utilities_menu.addAction(self.create_action("View Signatures", self.view_signatures))


        # System menu
        system_menu = menu_bar.addMenu("System")
        system_menu.addAction(self.create_action("User Management", self.open_user_management))


    def create_toolbar(self):
        """Create the toolbar with small buttons."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setIconSize(QSize(24, 24))  # Small icons
        self.addToolBar(Qt.TopToolBarArea, toolbar)  # Anchor toolbar to the top
    
        # Add actions to toolbar
        toolbar.addAction(self.create_action("New", self.file_manager.create_new_file, "icons/new_file.png"))
        toolbar.addAction(self.create_action("Open", self.file_manager.open_file, "icons/open_file.png"))
        toolbar.addAction(self.create_action("Save", self.file_manager.save_file, "icons/save_file.png"))
        toolbar.addSeparator()

        # Add Import Files action
        import_action = QAction("Import Files", self)
        import_action.setIcon(QIcon("icons/import_file.png"))
        import_action.triggered.connect(self.file_manager.import_files)
        toolbar.addAction(import_action)
        toolbar.addSeparator()
    
        # Add Tabular button
        toolbar.addAction(self.create_action("Tabular", lambda: self.update_selection('Imager'), "icons/tabular.png"))
    
        # Add Image button
        toolbar.addAction(self.create_action("Image", lambda: self.update_selection('Imager'), "icons/imager.png"))
    

        # Add the Run button
        self.run_button_action = QAction(QIcon("icons/run.png"), "Run", self)
        self.run_button_action.triggered.connect(self.run_selected_option)
        self.run_button_action.setDisabled(True)
        toolbar.addAction(self.run_button_action)
    
        toolbar.addAction(self.create_action("Audit Trail", self.view_audit_trail, "icons/audit_logo.png"))
        toolbar.addAction(self.create_action("Sign Results", self.sign_results, "icons/signature_logo.png")) 



    def sign_results(self):
        """
        Sign the results stored in the study model.
        Prompts the user for credentials, validates them, and signs the data.
        """
        self.file_manager.results['Audit_Trail'] = self.file_manager.get_audit_trail()
        if not self.file_manager.results['Audit_Trail']:
            QMessageBox.warning(self, "Audit Trail Missing", "No audit trail data available.")
            return
    
        # Launch PasswordDialog to get user credentials
        password_dialog = PasswordDialog(user_model=self.user_model)
        if password_dialog.exec_() != QDialog.Accepted:
            QMessageBox.information(self, "Signing Canceled", "The signing process was canceled by the user.")
            return
    
        # Extract credentials and comments
        credentials = password_dialog.handle_submit()
        if not credentials:
            QMessageBox.warning(self, "Invalid Credentials", "Invalid username or password.")
            return

        if "Signatures" not in self.file_manager.results:
            self.file_manager.results["Signatures"] = []
            
        # Initialize DataSigner and sign the data
        try:
            data_signer = DataSigner(self.user_model)

            signature = data_signer.sign_results(
                username=self.user_model.username,
                password=credentials[0],
                comments=credentials[1],
                data=self.file_manager.results
             )

            self.file_manager.results["Signatures"].append(signature)
            
            QMessageBox.information(self, "Signing Successful", f"Signed: \n{signature['username']} \n{signature['timestamp']} \n{signature['signature']}")
        except Exception as e:
            QMessageBox.critical(self, "Signing Failed", f"An error occurred while signing the results: {e}")



    def update_selection(self, selected_option):
        """Update the selected module and ensure only one option is checked."""
        # Uncheck all options
        for option_name, action in self.options.items():
            if option_name == selected_option:
                action.setChecked(True)  # Check the selected option
            else:
                action.setChecked(False)  # Uncheck others
    
        self.module_status_label.setText(f"Selected Module: {selected_option}")
        self.module_status_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 14px; background-color: black;"
        )


        # Ensure the selected option exists in results
        if selected_option not in self.file_manager.results:
            self.file_manager.results[selected_option] = self.file_manager.results['Importer']
        
        
        self.selected_option = selected_option
        self.run_action.setDisabled(False)  # Enable Run action
        self.run_button_action.setDisabled(False)  # Enable Run button
        self.open_module_window()
       

    

            
    def create_action(self, name, handler, icon=None):
        """Helper to create actions for menu and toolbar."""
        action = QAction(name, self)
        if icon and os.path.exists(icon):
            action.setIcon(QIcon(icon))
        else:
            action.setIconVisibleInMenu(False)  # Use text-only action if icon is missing
        action.triggered.connect(handler)
        return action
        

    def add_checkable_option(self, option_name):
        """Add a checkable option to the 'Module' submenu."""
        action = QAction(option_name, self.module_menu)
        action.setCheckable(True)  # Make the option checkable
        action.triggered.connect(lambda checked, opt=option_name: self.update_selection(opt))
        self.module_menu.addAction(action)
        self.options[option_name] = action  # Store the action for reference
        # Standard library imports
    


    def load_module_options(self):
        """Load available modules from the 'Modules' folder."""
        module_dir = os.path.join(os.getcwd(), "Modules")
        if not os.path.exists(module_dir):
            QMessageBox.critical(None, "Error", "Module folder not found.")
            self.logger.error("Module folder not found at %s.", module_dir)
            return

        self.module_menu.clear()
        self.options.clear()
        self.loaded_modules['Imager'] = ImageViewer
        for file_name in os.listdir(module_dir):
            if file_name.endswith(".py") and not file_name.startswith("__"):
                module_name = file_name[:-3]
                try:
                    self.loaded_modules[module_name] = load_module(module_name, module_dir)
                    self.add_checkable_option(module_name)
                except Exception as e:
                    QMessageBox.warning(None, "Module Load Error", f"Failed to load module '{module_name}': {e}")
                    self.logger.error("Failed to load module '%s': %s", module_name, str(e))
    
    def update_current_index(self, index):
        """
        Update the current index for the file management system.
    
        Args:
            index (int): The new index to set.
        """
        if not self.file_manager.results['Importer']:
            self.logger.warning("Attempted to set an invalid index")
            return
        
        if 0 <= index < len(self.file_manager.results['Importer']):
            files_list = list(self.file_manager.results['Importer'].values())
            self.logger.info("Updating file %s", files_list[index])
            self.current_index = index
        else:
            QMessageBox.warning(None, "Invalid Index", "Index out of range.")
            self.logger.warning("Attempted to set an invalid index")

    
    def run_selected_option(self):
        """Run processing on all files in the selected module with a progress bar."""
        if not self.selected_option:
            QMessageBox.warning(self, "No Module Selected", "Please select a module before running Batch Run.")
            return
    
        if not self.file_manager.results[self.selected_option]:
            QMessageBox.warning(self, "No Files", "No files available to process for the selected module.")
            return
    
        file_list = self.file_manager.results['Importer']
        if not file_list:
            QMessageBox.warning(self, "No Files", "The file list is empty.")
            return
    
        # Initialize progress dialog
        progress_dialog = QProgressDialog("Processing files...", "Cancel", 0, len(file_list), self)
        progress_dialog.setWindowTitle("Batch Processing")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumWidth(300)
        
        progress_dialog.show()
    
        try:
            processor_class = self.loaded_modules[self.selected_option]
            processor = self.open_windows[self.selected_option]

            for idx in range(len(file_list)):
                if progress_dialog.wasCanceled():
                    self.logger.info("Batch processing canceled by the user.")
                    break

                processor.current_index = idx
                self.logger.info(f"Processing file {idx + 1}/{len(file_list)}")
                
                # Instantiate processor and process file
                processor.compute()
    
                # Update progress dialog
                progress_dialog.setValue(idx + 1)
                QApplication.processEvents()  # Keep UI responsive

            self.file_manager.results[self.selected_option] = processor.image_paths

            if progress_dialog.wasCanceled():
                QMessageBox.warning(self, "Batch Run Canceled", "Batch processing was canceled.")
            else:
                QMessageBox.information(self, "Batch Run Complete", f"Batch run completed successfully for {len(file_list)} files.")
                self.logger.info("Batch run completed successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Batch Run Failed", f"An error occurred during batch processing: {e}")
            self.logger.error("Error during batch run: %s", str(e))
        finally:
            progress_dialog.close()



    def open_module_window(self):
        """Process the current image using the selected module and display the results."""
        try:
            if not self.validate_selection():
                return
    
            file_list = self.file_manager.results[self.selected_option]
    
            processor_class = self.loaded_modules[self.selected_option]
            processor = processor_class(image_paths=file_list, index=self.current_index)
    
            if self.file_management_dialog:
                self.file_management_dialog.current_index_changed.disconnect()
                self.file_management_dialog.current_index_changed.connect(processor.set_current_index)
    
            # Keep a reference to prevent garbage collection
            self.open_windows[self.selected_option] = processor
            processor.show()
    
            if self.selected_option != 'Imager':
                control = ControllerDialog(processor)
                control.param_changed.connect(processor.update_param)
                control.show()
                self.open_windows['Controller'] = control
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Processing failed for image: {e}")
            self.logger.error("Error in open_module_window: %s", str(e))

    def validate_selection(self):
        """Validate that the current selection and results are valid."""
        if not self.file_manager.results.get(self.selected_option) or not self.loaded_modules.get(self.selected_option):
            QMessageBox.information(self, "No Images or Module", "No images or module to process.")
            return False
    
        if not (0 <= self.current_index < len(self.file_manager.results[self.selected_option])):
            QMessageBox.warning(self, "Invalid Index", "Current index is out of range.")
            return False
        return True


    def open_file_management(self):
        """
        Open the File Management dialog.
    
        Args:
            file_list (list): List of file paths to manage.
        """    
        if not self.file_manager.results['Importer']:
            QMessageBox.warning(self, "No Files", "The imported file list is empty.")
            self.logger.warning("Attempted to open File Management dialog with no files.")
            return
    
        file_dict = self.file_manager.results['Importer']        
        self.logger.info("File list initialized with %d files.", len(file_dict))
    
        # Check if the dialog is already open
        if self.file_management_dialog and self.file_management_dialog.isVisible():
            QMessageBox.information(self, "File Management", "File Management is already open.")
            self.logger.info("File Management dialog is already open.")
            return
    
        try:
            # Initialize the FileManagementDialog
            self.file_management_dialog = FileManagementDialog(file_dict)
    
            # Properly connect signal for current index change
            self.file_management_dialog.current_index_changed.connect(self.update_current_index)
    
            self.open_windows['File_Manager'] = self.file_management_dialog
            self.file_management_dialog.show()
    
            self.logger.info("FileManagementDialog opened with %d files.", len(self.file_manager.results['Importer']))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open File Management dialog: {e}")
            self.logger.error("Error opening File Management dialog: %s", str(e))

    def view_audit_trail(self):
        """
        Display the audit trail in a table dialog.
        """
        try:
            logs = self.file_manager.get_audit_trail()
            if not logs:
                return  # No action if audit trail is empty or not found
    
            headers = ["Timestamp", "Username", "Action"]
            table_data = [
                [log["timestamp"], log["username"], log["message"]] for log in logs
            ]
            dialog = TableDialog(table_data, headers, title="Audit Trail", parent=self)
            dialog.exec_()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load audit trail: {e}")


    def open_user_management(self):
        """
        Open the user management dialog.
        """
        try:
            self.logger.info("Opening User Management dialog.")
            dialog = UserAccessDialog(self.user_model)
            dialog.exec_()
            self.logger.info("User Management dialog closed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while opening User Management: {str(e)}")
            self.logger.error("Error opening User Management dialog: %s", str(e))

    def view_signatures(self):
        """
        Display the saved signatures in a table dialog.
        """
        try:
            result = self.file_manager.get_signatures_table_data()
            if not result:
                return  # No action if no signatures are found
    
            table_data, headers = result
            dialog = TableDialog(table_data, headers, title="Signatures", parent=self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display signatures: {e}")
            self.logger.error("Failed to display signatures: %s", str(e))


    def closeEvent(self, event):
        """
        Handle unsaved changes, prompt the user, and close all open windows.
        """
        try:
            # Check for unsaved changes
            if self.file_manager.unsaved_changes:
                reply = QMessageBox.question(
                    self, 
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save before exiting?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )
                if reply == QMessageBox.Yes:
                    self.file_manager.save_file()
                    self.logger.info("Unsaved changes saved before closing.")
                    event.accept()
                elif reply == QMessageBox.No:
                    self.logger.info("Unsaved changes discarded. Closing application.")
                    event.accept()
                else:
                    self.logger.info("Close event canceled by the user.")
                    event.ignore()
                    return
    
            # Close all open windows
            self.close_all_windows()
            
            # Log the application closure
            self.logger.info("Application closed successfully.")
            event.accept()
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while closing the application: {str(e)}")
            self.logger.error("Error during closeEvent: %s", str(e))
            event.ignore()
    
        
    def close_all_windows(self):
        try:
            self.logger.info("Closing all open processor windows.")
            for key, window in list(self.open_windows.items()):
                if window and not window.isHidden():
                    window.close()
                    self.logger.info(f"Closed window: {key}")
            self.open_windows.clear()
            self.logger.info("All open windows closed successfully.")
        except Exception as e:
            self.logger.error(f"Error while closing windows: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while closing windows: {e}")
    


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Initialize UserModel (Mock or replace with actual implementation)
    user_model = UserModel()

    # Create and show the MainWindow
    window = MainWindow(user_model=user_model)
    window.show()

    sys.exit(app.exec_())
