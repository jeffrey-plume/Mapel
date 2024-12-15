import h5py
import os
from datetime import datetime
import logging
import tempfile
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import os
import logging

logger = logging.getLogger(__name__)

class StudyModel(QObject):  # Inherit from QObject
    files_imported = pyqtSignal(list)  # Signal emitted after files are imported

    def __init__(self, user_model, file_path=None):
        super().__init__()  # Initialize QObject
        self.file_path = file_path or tempfile.NamedTemporaryFile(delete=False, suffix=".mapel").name
        self.username = user_model.username
        self.user_model = user_model
        self.date_saved = None
        self.audit_trail = self.initialize_audit_trail()
        self.signatures = self.initialize_signatures()
        self.data = {}
        self.results = {}
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def initialize_audit_trail():
        return {"username": [], "action": [], "date": [], "time": []}

    @staticmethod
    def initialize_signatures():
        return {"username": [], "data_hash": [], "signature": [], "date": [], "time": [], "comments": []}

        self.data = None
        self.results = None

    def get_audit_trail(self):
        """Retrieve the audit trail for display or processing."""
        return [
            {
                "Username": username,
                "Action": action,
                "Date": date,
                "Time": time,
            }
            for username, action, date, time in zip(
                self.audit_trail["username"],
                self.audit_trail["action"],
                self.audit_trail["date"],
                self.audit_trail["time"],
            )
        ]


    def open_file(self):
                
        """Open an existing file."""
            
        try:
            file_path, _ = QFileDialog.getOpenFileName(None, "Open File", "", "Mapel Files (*.mapel)")
            if file_path:
                self.file_path = file_path
                self.load_data()
        except Exception as e:
            self.log_action( f"Failed to open file: {str(e)}")
            DialogHelper.show_error(None, "Error", f"Failed to open file: {e}")


        self.file_path = file_path
        logger.info(f"File opened: {file_path}")

    def save_file(self):
        """Save data to the current file."""
        if not self.file_path:
            raise ValueError("No file path specified.")
        self._save_to_hdf5(self.file_path)

    def save_as(self):
        """Save the current file as a new file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(None, "Save File As", "", "Mapel Files (*.mapel)")
            if file_path:
                self._save_to_hdf5(file_path)
        except Exception as e:
            logger.error(f"Failed to save file as: {e}")
            raise IOError(f"Failed to save file as: {e}")
    
    def _save_data_to_hdf5(self, file_path):
        """Internal method to save data to an HDF5 file."""
        try:
            with h5py.File(file_path, "w") as hdf:
                data = {
                    "audit_trail": self.audit_trail,
                    "signatures": self.signatures,
                    "data": self.data,
                    "results": self.results
                }
                self._save_data_to_hdf5(hdf, data)
            logger.info(f"File saved successfully: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise IOError(f"Failed to save file: {e}")


    def create_new_file(self):
        """Create a new file."""
        try:
            with h5py.File(self.file_path, "w") as hdf:
                hdf.attrs["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"New file created: {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            raise IOError(f"Failed to create file: {e}")

  

    def load_data(self):
        """Load data from the current file."""
        if not self.file_path:
            raise ValueError("No file path specified.")
        
        try:
            with h5py.File(self.file_path, "r") as hdf:
                data = self._load_data_from_hdf5(hdf)
                # Update instance attributes with loaded data
                self.audit_trail = data.get("audit_trail", {})
                self.signatures = data.get("signatures", {})
                self.data = data.get("data")
                self.results = data.get("results")
            logger.info(f"Data loaded successfully from: {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to load file: {e}")
            raise IOError(f"Failed to load file: {e}")

    def _load_data_from_hdf5(self, hdf):
        """Helper function to recursively load data from HDF5."""
        data = {}
        for key in hdf:
            if isinstance(hdf[key], h5py.Group):
                data[key] = self._load_data_from_hdf5(hdf[key])
            else:
                data[key] = hdf[key][:]
        return data

    def close(self):
        """Save the current state to the HDF5 file."""
        try:
            self.save_file()
            logger.info("File closed and saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save data during close: {e}")

    def log_action(self, action: str):
        """Add an action to the audit trail."""
        if not self.username:
            raise ValueError("Username is not set. Cannot log action.")

        now = datetime.now()
        self.audit_trail["username"].append(self.username)
        self.audit_trail["action"].append(action)
        self.audit_trail["date"].append(now.strftime("%Y-%m-%d"))
        self.audit_trail["time"].append(now.strftime("%H:%M:%S"))
        logger.info(f"Action logged: {action}")

    def sign_results(self):
        """Sign the results stored in the study model."""
        password_dialog = PasswordDialog(self.user_model)
        if password_dialog.exec_() != QDialog.Accepted:
            logger.info("Signing canceled by user.")
            return
    
        try:
            now = datetime.now()
            encrypted_key = self.user_model.get_private_key(password_dialog.password)
            data_hash = SecurityService.hash_data(SecurityService.serialize_dict(self.data))
            signature = SecurityService.sign_hash(data_hash, encrypted_key)
    
            self.signatures["username"].append(self.username)
            self.signatures["data_hash"].append(data_hash)
            self.signatures["signature"].append(signature)
            self.signatures["date"].append(now.strftime("%Y-%m-%d"))
            self.signatures["time"].append(now.strftime("%H:%M:%S"))
            self.signatures["comments"].append(password_dialog.comments)
    
            self.log_action("Results signed successfully.")
            logger.info("Results signed successfully.")
            return signature
        except Exception as e:
            logger.error(f"Failed to sign results: {e}")
            raise



    def import_files(self, parent=None):
        """Open a file dialog to select multiple files."""
        if not self:
            QMessageBox.warning(parent, "Error", "No study file is loaded. Please create or open a file first.")
            return
    
        # File filters (customize as needed)
        file_filters = "Images (*.png *.jpg *.jpeg *.bmp *.gif);;Text Files (*.txt *.csv);;All Files (*.*)"
        
        files, _ = QFileDialog.getOpenFileNames(parent or None, "Import Files", "", file_filters)
    
        if files:
            # Assuming `self.data` is where you want to store the imported file paths
            for file_path in files:
                # Example logic to add files to `self.data`
                #file_name = os.path.basename(file_path)
                self.data[file_path] = None

            self.files_imported.emit(list(self.data.keys()))
            # Log the action and inform the user
            self.log_action(f"Imported {len(files)} files.")




