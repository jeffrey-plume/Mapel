import os
import cv2
import numpy as np
from h5py import File
from PyQt5.QtWidgets import QMessageBox
from models.study_model import StudyModel  # For managing study-specific data

class FileSaver:
    def __init__(self, file_path, processed_images, study_model, current_user):
        """
        Initialize the FileSaver object.

        :param file_path: Base file path for saving.
        :param processed_images: Dictionary of processed images and metadata.
        :param study_model: Study model object for audit logging and database handling.
        :param current_user: Username of the person performing the action.
        """
        self.file_path = file_path
        self.processed_images = processed_images
        self.study_model = study_model
        self.current_user = current_user
        self.unsaved_changes = True

    def save_dict_to_hdf5(self, data_dict, h5_group):
        """
        Recursively save a nested dictionary to an HDF5 group.

        :param data_dict: Dictionary to save.
        :param h5_group: HDF5 group object.
        """
        for key, value in data_dict.items():
            if isinstance(value, dict):
                subgroup = h5_group.create_group(str(key))
                self.save_dict_to_hdf5(value, subgroup)
            else:
                h5_group.create_dataset(str(key), data=value)

    def save_file(self, image=None):
        """
        Save the current file and modified images.

        :param image: Specific image to save (if applicable).
        """
        if not self.file_path:
            self.save_as()
            return

        try:
            # Save nested dictionary to HDF5 file
            h5_path = self.file_path
            with File(h5_path, 'w') as h5f:
                self.save_dict_to_hdf5(self.processed_images, h5f)

            # Save processed images to disk
            for index, img in enumerate(self.processed_images.values()):
                if isinstance(img, np.ndarray):
                    image_path = self.file_path
                    cv2.imwrite(image_path, (img * 255).astype("uint8"))

            # Log the action in the study audit trail
            self.study_model.log_action(
                username=self.current_user,
                action=f"Saved file and modified images to {h5_path}"
            )

            # Commit changes to the database
            if self.study_model.conn:
                self.study_model.conn.commit()

            self.unsaved_changes = False
            print("File and images saved successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            QMessageBox.critical(None, "Error", f"Failed to save file: {e}")

    def save_as(self):
        """
        Save file using a new path. For now, just prompt the user.
        """
        print("Save as functionality is not implemented.")
        QMessageBox.information(None, "Save As", "Save as functionality is not yet implemented.")

