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
    def __init__(self, image_paths=None, index=0, diameter=25):
        """
        Subclass of ImageViewer that integrates Cellpose analysis.
        """
        self.diameter = diameter
        self.model = models.Cellpose(model_type='cyto3')
        # Initialize the parent class (ImageViewer)
        super().__init__(image_paths=image_paths, index=index)

        self.image_files = image_paths

        # Additional attributes specific to CellposeAnalyzer
        self.current_index = index
        self.image_paths = {key:None for key in list(image_paths.keys())} 
        self.image_files = list(image_paths.values())
        

    def compute(self):
        """Process the current image using Cellpose and display the segmentation result."""
        if not self.image_paths:
            QMessageBox.information(self, "No Images", "No images to process.")
            return

        filenames = list(self.image_paths.keys())
        filepaths = self.image_files
        if self.current_index < 0 or self.current_index >= len(filenames):
            QMessageBox.information(self, "No Images", "Invalid image index.")
            return
    
        current_filename = filenames[self.current_index]
    
        # Load the image if not already loaded
        if self.image_paths[current_filename] is None:
            try:
                current_path = filepaths[self.current_index]
                self.image_paths[current_filename] = self.read_image(current_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image '{current_filename}': {e}")
                return

        # Process the image using Cellpose
        img = self.image_paths[current_filename]
        try:
            masks, flows, styles, _ = self.model.eval(img,
                            diameter=self.diameter, channels=[1,2])
            mask_RGB = plot.mask_overlay(img, masks)
            self.image_paths[current_filename] = mask_RGB

            
            self.title = f"CellposeAnalyzer- {current_filename}"
        
            self.display_image()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process image: {e}")
            return



