# Standard library imports
import os
import json
import logging
from datetime import datetime
import tempfile
import importlib.util
import h5py 
import numpy as np

# PyQt5 imports
from PyQt5.QtCore import QSize, QFile, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QMessageBox, QVBoxLayout,
    QWidget, QToolBar, QMenu, QLabel, QDialog
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
from models.user_model import UserModel
from utils.dialog_helper import DialogHelper




class MainWindow(QMainWindow):
    def __init__(self, user_model, logger = None, parent=None):
        super().__init__()
        self.setGeometry(300, 100, 400, 100)
        self.file_path = os.path.join(tempfile.gettempdir(), f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.mapel")

        self.open_windows = []
        self.user_model = user_model
        self.unsaved_changes = False
        self.data_signer = DataSigner(self.user_model)

        self.logger = logger or setup_logger(name=__name__,  username=user_model.username, filename=f'{self.file_path}.log')
        self.logger.filename = self.file_path.replace(".mapel", ".log")
        self.user_model.logger = self.logger


        self.file_management_dialog = None
        self.results = {}
        self.selected_option = None
        self.options = {}
        self.processor = {}
        self.loaded_modules = {}
        self.file_list = []
        self.directory = None
        self.filenames = []
        self.current_index = 0

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.create_menu_bar()
        self.create_toolbar()

        self.module_status_label = QLabel("No module loaded", self)
        self.module_status_label.setStyleSheet(
            "color: red; font-weight: bold; font-size: 14px;"
        )
        self.main_layout.addWidget(self.module_status_label)


    def create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()
    
        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self.create_action("New File", self.create_new_file))
        file_menu.addAction(self.create_action("Open File", self.open_file))
        file_menu.addAction(self.create_action("Save File", self.save_file))
        file_menu.addAction(self.create_action("Save As", self.save_as))
        file_menu.addSeparator()
        file_menu.addAction(self.create_action("Import", self.import_files))
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

        utilities_menu.addAction(self.create_action("Open Table View", self.open_tabular))
        utilities_menu.addAction(self.create_action("Open Image View", self.open_image))
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
        toolbar.addAction(self.create_action("New", self.create_new_file, "icons/new_file.png"))
        toolbar.addAction(self.create_action("Open", self.open_file, "icons/open_file.png"))
        toolbar.addAction(self.create_action("Save", self.save_file, "icons/save_file.png"))
        toolbar.addSeparator()

        # Add Import Files action
        import_action = QAction("Import Files", self)
        import_action.setIcon(QIcon("icons/import_file.png"))
        import_action.triggered.connect(self.import_files)
        toolbar.addAction(import_action)
        toolbar.addSeparator()
    
        # Add Tabular button
        toolbar.addAction(self.create_action("Tabular", self.open_tabular, "icons/tabular.png"))
    
        # Add Image button
        toolbar.addAction(self.create_action("Image", self.open_image, "icons/imager.png"))
    

        # Add the Run button
        self.run_button_action = QAction(QIcon("icons/run.png"), "Run", self)
        self.run_button_action.triggered.connect(self.run_selected_option)
        self.run_button_action.setDisabled(True)
        toolbar.addAction(self.run_button_action)
    
        toolbar.addAction(self.create_action("Audit Trail", self.view_audit_trail, "icons/audit_logo.png"))
        toolbar.addAction(self.create_action("Sign Results", self.sign_results, "icons/signature_logo.png"))

    def open_tabular(self):
        """Placeholder to open the Tabular dialog."""
        QMessageBox.information(self, "Open Tabular", "This will open the Tabular dialog.")
        # TODO: Replace with the logic to open TableDialog
        # For now, simulate file import
        self.import_files()
    
    def open_image(self):
        """Open the image viewer and load the first file in the imported list."""
        # Ensure a module is selected; if not, use 'files' as the default
        if not self.file_list:
            QMessageBox.warning(self, "No Files", "No files available to open in the viewer.")
            return

        
        try:
            viewer = ImageViewer(image_paths = self.results['Importer'], index=0)
            
            if self.file_management_dialog:
                self.file_management_dialog.current_index_changed.connect(viewer.set_current_index)

            # Keep a reference to the viewer window to prevent garbage collection
            self.open_windows.append(viewer)
            viewer.show()
            self.results['Images'] = viewer.image_paths
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open the image viewer: {str(e)}")


    def sign_results(self):
        """
        Sign the results stored in the study model.
        Prompts the user for credentials, validates them, and signs the data.
        """
        self.results['Audit_Trail'] = self.get_audit_trail()
        if not self.results['Audit_Trail']:
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

        if "Signatures" not in self.results:
            self.results["Signatures"] = []
            
        # Initialize DataSigner and sign the data
        try:
            data_signer = self.data_signer
            
            signature = data_signer.sign_results(
                username=self.user_model.username,
                password=credentials[0],
                comments=credentials[1],
                data=self.results
             )

            self.results["Signatures"].append(signature)
            
            QMessageBox.information(self, "Signing Successful", f"Signed: \n{signature['username']} \n{signature['timestamp']} \n{signature['signature']}")
        except Exception as e:
            QMessageBox.critical(self, "Signing Failed", f"An error occurred while signing the results: {e}")


    def get_signatures_table_data(self):
        """
        Prepare table data for displaying signatures.
    
        Returns:
            tuple: Table data (list of rows) and headers (list of column names).
        """
        if "Signatures" not in self.results or not self.results["Signatures"]:
            QMessageBox.warning(self, "No Signatures", "No signatures found.")
            return None
    
        headers = ["Timestamp", "Username", "Hash", "Comments", "Signature"]
        table_data = [
            [entry["timestamp"], entry["username"], entry["data_hash"], entry["comments"], entry["signature"]]
            for entry in self.results["Signatures"]
        ]
        return table_data, headers

    def view_signatures(self):
        """
        Display the saved signatures in a table dialog.
        """
        try:
            result = self.get_signatures_table_data()
            if not result:
                return  # No action if no signatures are found
    
            table_data, headers = result
            dialog = TableDialog(table_data, headers, title="Signatures", parent=self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display signatures: {e}")
            self.logger.error("Failed to display signatures: %s", str(e))
    

            
    def create_action(self, name, handler, icon=None):
        """Helper to create actions for menu and toolbar."""
        action = QAction(name, self)
        if icon and os.path.exists(icon):
            action.setIcon(QIcon(icon))
        else:
            action.setIconVisibleInMenu(False)  # Use text-only action if icon is missing
        action.triggered.connect(handler)
        return action
        

    def load_module_options(self):
        """Load available modules from the 'Modules' folder."""
        module_dir = os.path.join(os.getcwd(), "Modules")
        if not os.path.exists(module_dir):
            QMessageBox.critical(self, "Error", "Module folder not found.")
            return

        self.module_menu.clear()
        self.options = {}
        for file_name in os.listdir(module_dir):
            if file_name.endswith(".py") and not file_name.startswith("__"):

                module_name = file_name[:-3]
                
                try:
                    self.options[module_name] = None
                    self.loaded_modules[module_name] = self.load_module(module_name)
                    self.add_checkable_option(module_name)
                except Exception as e:
                    QMessageBox.warning(self, "Module Load Error", f"Failed to load module '{module_name}': {e}")

    def add_checkable_option(self, option_name):
        """Add a checkable option to the 'Module' submenu."""
        action = QAction(option_name, self.module_menu)
        action.setCheckable(True)  # Make the option checkable
        action.triggered.connect(lambda checked, opt=option_name: self.update_selection(opt))
        self.module_menu.addAction(action)
        self.options[option_name] = action  # Store the action for reference


    def load_module(self, module_name):
        """
        Dynamically load a module and return the class.
    
        Args:
            module_name (str): The name of the module to load.
    
        Returns:
            class: The loaded module class.
        """
        module_dir = os.path.join(os.getcwd(), "Modules")
        module_path = os.path.join(module_dir, f"{module_name}.py")

        
        if not os.path.exists(module_path):
            raise ImportError(f"Module file not found: {module_path}")
    
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, module_name):
            return getattr(module, module_name)  # Return the loaded class
        else:
            raise ImportError(f"Class '{module_name}' not found in module '{module_name}'")


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

        
        self.results[selected_option] = {key:None for key in self.filename}
        
        self.selected_option = selected_option
        self.run_action.setDisabled(False)  # Enable Run action
        self.run_button_action.setDisabled(False)  # Enable Run button
        self.open_module_window()
       

    def open_module_window(self):
        """Process the current image using the selected module and display the results."""
        if not self.results[self.selected_option] or not self.loaded_modules[self.selected_option]:
            QMessageBox.information(self, "No Images or Module", "No images or module to process.")
            return

        if not (0 <= self.current_index < len(self.file_list)):
            QMessageBox.warning(self, "Invalid Index", "Current index is out of range.")
            return


        try:
            # Instantiate the processor and process the image
            processor_class = self.loaded_modules[self.selected_option]
            self.processor = processor_class(image_paths=self.results[self.selected_option], index=self.current_index)
            
            if self.file_management_dialog:
                self.file_management_dialog.current_index_changed.connect(self.processor.set_current_index)

            # Keep a reference to the viewer window to prevent garbage collection
            self.open_windows.append(self.processor)
            self.processor.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Processing failed for image '{current_filename}': {e}")
            return
        
    def run_selected_option(self):
        self.processor.compute()
        self.results[self.selected_option] = self.processor.image_paths
        self.processor.update_image()
        

    def open_file_management(self):
        """
        Open the File Management dialog.
    
        Args:
            file_list (list): List of file paths to manage.
        """    
        if not self.file_list:
            QMessageBox.warning(self, "No Files", "The imported file list is empty.")
            self.logger.warning("Attempted to open File Management dialog with no files.")
            return
    
        file_list = self.file_list
        filename = self.filenames
        
        self.results['Importer'] = {file:path for file, path in zip(filename, file_list)}  # Initialize files dictionary
        self.logger.info("File list initialized with %d files.", len(file_list))
    
        # Check if the dialog is already open
        if self.file_management_dialog and self.file_management_dialog.isVisible():
            QMessageBox.information(self, "File Management", "File Management is already open.")
            self.logger.info("File Management dialog is already open.")
            return
    
        try:
            # Initialize the FileManagementDialog
            self.file_management_dialog = FileManagementDialog(self.results['Importer'])
    
            # Properly connect signal for current index change
            self.file_management_dialog.current_index_changed.connect(self.update_current_index)
    
            self.open_windows.append(self.file_management_dialog)
            self.file_management_dialog.show()
    
            self.logger.info("FileManagementDialog opened with %d files.", len(self.results['Importer']))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open File Management dialog: {e}")
            self.logger.error("Error opening File Management dialog: %s", str(e))


    def update_current_index(self, index):
        """
        Update the current index for the file management system.
    
        Args:
            index (int): The new index to set.
        """
        if not self.file_list:
            self.logger.warning("Attempted to set an invalid index")
            return
        
        if 0 <= index < len(self.file_list):
            self.logger.info("Updating file %s", self.file_list[index])
            self.current_index = index
        else:
            QMessageBox.warning(None, "Invalid Index", "Index out of range.")
            self.logger.warning("Attempted to set an invalid index")


    def create_new_file(self):
        """Create a new file."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before creating a new file?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
    
            if reply == QMessageBox.Yes:
                if self.save_file():  # Assuming save_file() returns success status
                    self.logger.info("Unsaved changes saved before creating a new file.")
                else:
                    QMessageBox.critical(self, "Error", "Failed to save changes.")
                    return
            elif reply == QMessageBox.Cancel:
                self.logger.info("New file creation canceled by the user.")
                return
    
        # Reset for new file
        self.unsaved_changes = False
        filename = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = os.path.join(tempfile.gettempdir(), f"{filename}.mapel")
        self.results = {}
        self.logger.info("New file created successfully.")

        # Notify the user
        QMessageBox.information(
            self,
            "New File Created",
            f"A new file has been created: {self.file_path}"
        )




    def save_as(self):
        """Save data to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(None, "Save File As", "", "Mapel Files (*.mapel)")
        if file_path:
            if not file_path.endswith(".mapel"):
                file_path += ".mapel"
    
            try:
                self.file_path = file_path
                self.save_file()
                self.unsaved_changes = False
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to save file: {e}")
                
                
    def open_file(self):
        """Open an HDF5 file and load its data."""
        # Open a file dialog and get the selected file path
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Mapel (*.mapel);;Text Files (*.mapel)")

        if file_path:

            try:

                def load_dict_from_hdf5(h5_group):
                    data_dict = {}
                    for key, item in h5_group.items():
                        if item =="None":
                            item = None
                        if isinstance(item, h5py.Group):
                            data_dict[str(key)] = load_dict_from_hdf5(item)
                        else:
                            data_dict[str(key)] = item[()]
                    return data_dict
            
                # Load nested dictionary back from HDF5 file
                with h5py.File(file_path, 'r') as h5f:
                    self.results = load_dict_from_hdf5(h5f)

                self.file_path = file_path

                # Update file path and file list
                self.file_list = list(self.results.get("Importer", {}).values())
                self.filenames = list(self.results.get("Importer", {}).keys())

                print(self.filenames)
                QMessageBox.information(self, "File Opened", f"Successfully opened file: {file_path}")
                self.open_file_management()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
                
    def save_file(self):
        """Save the current data to the file path."""
        if self.file_path:
            # Function to recursively save nested dictionary to HDF5
            def save_dict_to_hdf5(data_dict, h5_group):
                for key, value in data_dict.items():
                    if value is None:
                        h5_group.create_dataset(str(key), data="None")
                    elif isinstance(value, dict):
                        # If the value is a dictionary, create a group
                        subgroup = h5_group.create_group(str(key))
                        save_dict_to_hdf5(value, subgroup)
                    else:
                        # Otherwise, save the array
                        h5_group.create_dataset(str(key), data=value)
            try:
                

                with h5py.File(self.file_path, 'w') as h5f:
                    save_dict_to_hdf5(self.results, h5f)

                self.unsaved_changes = False
                QMessageBox.information(self, "File Saved", f"File successfully saved to: {self.file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"An error occurred while saving the file: {e}")
        else:
            self.show_save_file_dialog()


    def import_files(self):
        """Import multiple files."""
        file_filters = "Images (*.png *.jpg *.jpeg *.bmp *.gif);;Text Files (*.txt *.csv);;All Files (*.*)"
        files, _ = QFileDialog.getOpenFileNames(None, "Import Files", "", file_filters)
        if files:
            directory = os.path.dirname(files[0]) if files else None
            
            # Extract filenames only
            filenames = [os.path.basename(file)[:-4] for file in files]
            
            # Store files for further processing
            self.file_list = files  # Full file[:-3] paths
            self.results['metadata'] = {'directory':directory, 'files':filenames}
            self.directory = directory
            self.filenames = filenames
            self.open_file_management()

    def get_audit_trail(self):
        """
        Retrieve and parse the audit trail log file.
        
        Returns:
            tuple: A tuple containing table_data (list) and headers (list) or None if an error occurs.
        """
        try:
            log_path = os.path.join(os.getcwd(), "logs", "audit_trail.log")
            if not os.path.exists(log_path):
                QMessageBox.warning(self, "Audit Trail", "No audit trail file found.")
                return None
            
            with open(log_path, "r") as log_file:
                try:
                    logs = [json.loads(line) for line in log_file]
                except json.JSONDecodeError as e:
                    QMessageBox.critical(self, "Error", f"Failed to parse audit trail data: {e}")
                    return None
            
            if not logs:
                QMessageBox.information(self, "Audit Trail", "The audit trail is empty.")
                return None
    
            headers = ["Timestamp", "Username", "Action"]
            table_data = [
                [log["timestamp"], log["username"], log["message"]] for log in logs
            ]
            return table_data, headers
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load audit trail: {e}")
            return None
    
    def view_audit_trail(self):
        """
        Display the audit trail in a table dialog.
        """
        try:
            result = self.get_audit_trail()
            if not result:
                return  # No action if audit trail is empty or not found
    
            table_data, headers = result
            dialog = TableDialog(table_data, headers, title="Audit Trail", parent=self)
            dialog.exec_()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load audit trail: {e}")

    def closeEvent(self, event):
        """
        Handle unsaved changes, prompt the user, and close all open windows.
        """
        try:
            # Check for unsaved changes
            if self.unsaved_changes:
                reply = QMessageBox.question(
                    self, 
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save before exiting?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )
                if reply == QMessageBox.Yes:
                    self.save_file()
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
            self.user_model.log_action(action="Application closed")
            self.logger.info("Application closed successfully.")
            event.accept()
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while closing the application: {str(e)}")
            self.logger.error("Error during closeEvent: %s", str(e))
            event.ignore()
    
    def close_all_windows(self):
        """
        Close all open processor windows and clear the tracking list.
        """
        try:
            self.logger.info("Closing all open processor windows.")
            for window in self.open_windows:
                if window and not window.isHidden():
                    window.close()
                    self.logger.info("Closed window: %s", window.windowTitle())
            self.open_windows.clear()
            self.logger.info("All open windows closed successfully.")
        except Exception as e:
            self.logger.error("Error while closing windows: %s", str(e))
            QMessageBox.critical(self, "Error", f"An error occurred while closing windows: {str(e)}")
    
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


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Initialize UserModel (Mock or replace with actual implementation)
    user_model = UserModel()

    # Create and show the MainWindow
    window = MainWindow(user_model=user_model)
    window.show()

    sys.exit(app.exec_())
