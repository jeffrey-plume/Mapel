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
import numpy as np
from skimage.measure import regionprops, label
import logging

class CellposeAnalyzer(ImageViewer):
    def __init__(self, image_paths=None, index=0, logger = None, diameter=25):
        """
        Subclass of ImageViewer that integrates Cellpose analysis.
        """
        self.diameter = diameter
        self.model = models.Cellpose(model_type='cyto3', gpu=True)
        self.output = {key: None for key in image_paths.keys()}
        self.title = 'CellposeAnalyzer'
        self.masks = {}  # Store masks for each image

        # Initialize the parent class (ImageViewer)
        super().__init__(image_paths=image_paths, index=index, logger=logger)

    def analyze(self, image_path):
        """
        Read an image and apply Cellpose analysis.
        """
        # Load the image
        if isinstance(image_path, np.ndarray):
            img = image_path
        else:
            try:
                img = io.imread(image_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image from path: {e}")
                return None

        # Handle grayscale images
        if len(img.shape) == 2:  # Grayscale image
            img = np.stack([img, np.zeros_like(img)], axis=-1)

        try:
            # Perform Cellpose evaluation
            masks, flows, styles, _ = self.model.eval(img, diameter=self.diameter, channels=[1, 2])
            self.masks[self.filenames[self.current_index]] = masks  # Store masks for tabulation
            mask_RGB = plot.mask_overlay(img, masks)
            return mask_RGB
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cellpose evaluation failed: {e}")
            return None

    def tabulate(self):
        """
        Compute segmentation metrics for each object and return headers and data.
        """
        if not self.masks:
            QMessageBox.warning(self, "No Masks", "No segmentation masks available for tabulation.")
            return [], []
    
        headers = ["Filename", "Label", "Area", "Perimeter", "Major Axis Length", "Minor Axis Length", "Eccentricity"]
        table_data = []
    
        for filename, masks in self.masks.items():
            if masks is None:
                continue
            labeled_mask = label(masks)
            properties = regionprops(labeled_mask)
    
            for prop in properties:
                row = [
                    filename, prop.label, prop.area, prop.perimeter,
                    prop.major_axis_length, prop.minor_axis_length, prop.eccentricity
                ]
                table_data.append(row)
    
        return headers, table_data
