import h5py
import os
from datetime import datetime
import logging
import tempfile
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog
from services.SecurityService import SecurityService


import h5py
import os
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class StudyModel(QObject):
    files_imported = pyqtSignal(dict)  # Signal emitted after files are imported

    def __init__(self, user_model, file_path=None):
        super().__init__()
        self.file_path = file_path or f"{os.path.join(tempfile.gettempdir(), 'new_study.mapel')}"
        self.username = user_model.username
        self.audit_trail = self.initialize_audit_trail()
        self.signatures = self.initialize_signatures()
        self.data = {}

    @staticmethod
    def initialize_audit_trail():
        return {"username": [], "action": [], "date": [], "time": []}

    @staticmethod
    def initialize_signatures():
        return {"username": [], "data_hash": [], "signature": [], "date": [], "time": [], "comments": []}

    def log_action(self, action):
        """Log an action in the audit trail."""
        now = datetime.now()
        self.audit_trail["username"].append(self.username)
        self.audit_trail["action"].append(action)
        self.audit_trail["date"].append(now.strftime("%Y-%m-%d"))
        self.audit_trail["time"].append(now.strftime("%H:%M:%S"))

    def open_file(self):
        """Open an existing file and load its data."""
        file_path, _ = QFileDialog.getOpenFileName(None, "Open File", "", "Mapel Files (*.mapel)")
        if file_path:
            self.file_path = file_path
            self.load_data()
            self.log_action(f"File opened: {file_path}")

    def save_file(self):
        """Save data to the current file."""
        self._save_to_hdf5(self.file_path)
        self.log_action(f"File saved: {self.file_path}")

    def save_as(self):
        """Save data to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(None, "Save File As", "", "Mapel Files (*.mapel)")
        if file_path:
            self.file_path = file_path
            self.save_file()

    def load_data(self):
        """Load data from the HDF5 file."""
        try:
            with h5py.File(self.file_path, "r") as hdf:
                self.data = {key: hdf[key][()] for key in hdf.keys()}
            self.log_action(f"Data loaded from: {self.file_path}")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load file: {e}")

    def _save_to_hdf5(self, file_path):
        """Save data to an HDF5 file."""
        try:
            with h5py.File(file_path, "w") as hdf:
                for key, value in {"audit_trail": self.audit_trail, "signatures": self.signatures, "data": self.data}.items():
                    hdf.create_dataset(key, data=value)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to save file: {e}")

    def create_new_file(self):
        """Create a new file."""
        self.file_path = f"{os.path.join(tempfile.gettempdir(), 'new_study.mapel')}"
        self.data = {}
        self.results = {}
        self.audit_trail = self.initialize_audit_trail()
        self.signatures = self.initialize_signatures()
        self.log_action("New file created.")

    def import_files(self):
        """Import multiple files."""
        file_filters = "Images (*.png *.jpg *.jpeg *.bmp *.gif);;Text Files (*.txt *.csv);;All Files (*.*)"
        files, _ = QFileDialog.getOpenFileNames(None, "Import Files", "", file_filters)
        if files:
            for file_path in files:
                self.data[file_path] = None
            self.files_imported.emit(self.data)
            self.log_action(f"Imported {len(files)} files.")


    def log_action(self, action: str):
        """Add an action to the audit trail."""
        if not self.username:
            raise ValueError("Username is not set. Cannot log action.")

        now = datetime.now()
        self.audit_trail["username"].append(self.username)
        self.audit_trail["action"].append(action)
        self.audit_trail["date"].append(now.strftime("%Y-%m-%d"))
        self.audit_trail["time"].append(now.strftime("%H:%M:%S"))
      



    




