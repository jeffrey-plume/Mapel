import os
from datetime import datetime
import tempfile
import json
import logging
from PyQt5.QtCore import QObject, pyqtSignal
from utils.file_utils import save_dict_to_hdf5, load_dict_from_hdf5
import h5py 
import numpy as np
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QDialog
)


class FileManager(QObject):
    files_imported = pyqtSignal(list)  # Signal to notify about imported files

    def __init__(self, main_window, logger):
        super().__init__()

        self.main_window = main_window
        self.logger = logger
        self.file_path = logger.log_path.replace('.mapel', '.log')
        self.results = {}
        self.unsaved_changes = False

    def create_new_file(self):
        """Create a new file."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self.main_window,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before creating a new file?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
    
            if reply == QMessageBox.Yes:
                if self.save_file():
                    self.logger.info("Unsaved changes saved before creating a new file.")
                else:
                    QMessageBox.critical(self.main_window, "Error", "Failed to save changes.")
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

        QMessageBox.information(
            self.main_window,
            "New File Created",
            f"A new file has been created: {self.file_path}"
        )

    def open_file(self):
        """Open an HDF5 file, load its data, and return the results."""
        import os
    
        # Show file dialog to select an HDF5 file
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Open File", "", "Mapel (*.mapel);;All Files (*.*)"
        )
    
        if file_path:
            file_path = os.path.normpath(file_path)  # Normalize the file path
            try:
                # Load HDF5 file into a dictionary
                with h5py.File(file_path, 'r') as h5f:
                    results = load_dict_from_hdf5(h5f)
                    
                # Store the file path and results
                self.file_path = file_path
                self.results = results

                # Emit files_imported signal if 'Importer' key exists
                if 'Importer' in self.results:
                    filenames = list(self.results['Importer'].values())
                    self.files_imported.emit(filenames)
                else:
                    QMessageBox.warning(
                        self.main_window,
                        "Warning",
                        "No importer data found in the file."
                    )
    
  
                return self.results
            except Exception as e:
                import traceback
                QMessageBox.critical(
                    self.main_window,
                    "Error",
                    f"Failed to open file: {e}"
                )
                self.logger.error(f"Error loading file: {e}\n{traceback.format_exc()}")
                return None
        else:
            self.logger.info("No file selected for opening.")
            return None



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
                
    def save_file(self):
        """Save the current data to the file path."""
        if not self.file_path:
            self.save_as()
            if not self.file_path:  # User canceled save_as dialog
                return
    
        try:
            # Log the save attempt
            self.logger.info(f"Attempting to save file: {self.file_path}")
    
            # Get new audit trail entries
            new_audit = self.get_audit_trail()
            
            # Ensure 'Audit_Trail' exists in results
            if 'Audit_Trail' not in self.results or not self.results['Audit_Trail']:
                self.results['Audit_Trail'] = new_audit
            else:
                # Update existing audit trail with new entries
                self.results['Audit_Trail'].update(new_audit)
    
            # Save the results to the file
            with h5py.File(self.file_path, 'w') as h5f:
                save_dict_to_hdf5(self.results, h5f)
    
            # Mark changes as saved
            self.unsaved_changes = False
            QMessageBox.information(self.main_window, "File Saved", f"File successfully saved to: {self.file_path}")
            self.logger.info(f"File saved successfully: {self.file_path}")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Save Failed", f"An error occurred while saving the file: {e}")
            self.logger.error(f"Error saving file {self.file_path}: {e}")

        
        except Exception as e:
            import traceback
            error_message = f"An error occurred while saving the file: {e}"
            QMessageBox.critical(self.main_window, "Save Error", error_message)
            self.logger.error(f"{error_message}\n{traceback.format_exc()}")

    
    def import_files(self):
        """Import multiple files."""
        file_filters = "Images (*.png *.jpg *.jpeg *.bmp *.gif);;Text Files (*.txt *.csv);;All Files (*.*)"
        files, _ = QFileDialog.getOpenFileNames(None, "Import Files", "", file_filters)
        if files:
            directory = os.path.dirname(files[0]) if files else None
            
            # Extract filenames only
            filenames = [os.path.basename(file) for file in files]
            
            # Store files for further processing
            importer = {filename[:-4] :os.path.join(directory, filename) for filename in filenames}

            if 'Importer' not in self.results:
                self.results['Importer'] = importer
            else:
                self.results['Importer'].update(importer)
       
            self.logger.info("Files successfully imported.")

            self.files_imported.emit(filenames)

        else:
            self.logger.info("No files selected for import.")

    def get_audit_trail(self):
        """
        Retrieve and parse the audit trail log file.
        
        Returns:
            tuple: A tuple containing table_data (list) and headers (list) or None if an error occurs.
        """
        try:
            log_path = self.logger.log_path
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

            return logs
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load audit trail: {e}")
            return None
    





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


