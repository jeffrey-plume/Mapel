from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
    QLabel, QLineEdit, QComboBox, QMessageBox, QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from cellpose import io, models, plot
import os
import sys
from dialogs.ImageViewer import ImageViewer



class CellposeAnalyzer(ImageViewer):
    def __init__(self, image_paths=None, index=0, model_type="cyto", diameter=25, gpu=True):
        """
        Subclass of ImageViewer that integrates Cellpose analysis.
        """
        # Initialize the parent class (ImageViewer)
        super().__init__(image_paths=image_paths, index=index)

        # Additional attributes specific to CellposeAnalyzer
        self.model_type = model_type
        self.diameter = diameter
        self.gpu = gpu
        self.segmented_images = {}

        # Initialize the Cellpose model
        self.model = models.CellposeModel(model_type=model_type, gpu=gpu)

        # Process and display the current image
        self.compute()

    def compute(self):
        """Process the current image using Cellpose and display the segmentation result."""
        if not self.image_paths:
            QMessageBox.information(self, "No Images", "No images to process.")
            return

        filenames = list(self.image_paths.keys())
        current_filename = filenames[self.current_index]

        # Load the image if not already loaded
        if self.image_paths[current_filename] is None:
            try:
                img = io.imread(current_filename)
                self.image_paths[current_filename] = img
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
                return

        # Process the image using Cellpose
        img = self.image_paths[current_filename]
        try:
            masks, flows, styles = models.CellposeModel(model_type='cyto3').eval(img,
                            diameter=25, channels=[1,2])
            mask_RGB = plot.mask_overlay(img, masks)
            self.image_paths[current_filename] = mask_RGB
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process image: {e}")
            return

        # Display the segmented image
        self.display_image(title="Segmented Image")

