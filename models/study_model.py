import h5py
import os
from datetime import datetime
import logging
import tempfile
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog
from services.SecurityService import SecurityService


from h5py import File, Group
import os
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class StudyModel(QObject):
    files_imported = pyqtSignal(dict)  # Signal emitted after files are imported

    def __init__(self, data_dict, file_path=None):
        super().__init__()
        self.file_path = file_path or f"{os.path.join(tempfile.gettempdir(), 'new_study.mapel')}"
        self.data = {}


    def open_file(self):
        """Open an existing file and load its data."""
        file_path, _ = QFileDialog.getOpenFileName(None, "Open File", "", "Mapel Files (*.mapel)")
        if file_path:
            self.file_path = file_path
            self.load_data()


    def save_file(self):

        if self.file_path:
            # Function to recursively save nested dictionary to HDF5
            try:
                # Save nested dictionary to HDF5 file
                with File(self.file_path, 'w') as h5f:
                    self._save_dict_to_hdf5(self.processed_images, h5f)

                self.unsaved_changes = False
            except Exception as e:
                print(f"An error occurred: {e}")
            
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
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load file: {e}")

    def _save_dict_to_hdf5(data_dict, h5_group):
        for key, value in data_dict.items():
            if isinstance(value, dict):
                # If the value is a dictionary, create a group
                subgroup = h5_group.create_group(str(key))
                save_dict_to_hdf5(value, subgroup)
            else:
                # Otherwise, save the array
                h5_group.create_dataset(str(key), data=value)

    def create_new_file(self):
        """Create a new file."""
        self.file_path = f"{os.path.join(tempfile.gettempdir(), 'new_study.mapel')}"
        self.data = {}

    def import_files(self):
        """Import multiple files."""
        file_filters = "Images (*.png *.jpg *.jpeg *.bmp *.gif);;Text Files (*.txt *.csv);;All Files (*.*)"
        files, _ = QFileDialog.getOpenFileNames(None, "Import Files", "", file_filters)
        if files:
            for file_path in files:
                self.data[file_path] = None
            self.files_imported.emit(self.data)


      



    




