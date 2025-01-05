from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
    QLabel, QLineEdit, QComboBox, QMessageBox, QFileDialog, QProgressBar, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from cellpose import io
import os
import numpy as np
import logging

class ImageViewer(QMainWindow):
    def __init__(self, image_paths=None, index=0, logger = logging.getLogger(__name__)):
        super().__init__()
        self.image_paths = image_paths
        self.output = {key: None for key in image_paths.keys()}
        self.filenames = list(image_paths.keys())
        self.logger = logger
        self.current_index = index
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_param)

        # Initialize UI
        self.title = 'Image Viewer'

        # Image display
        self.figure = Figure()
        self.figure.tight_layout()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.pending_param = None
        self.pending_value = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.canvas, alignment=Qt.AlignCenter)

        if self.image_paths:
            self.compute()

    def update_param(self):
        """Execute the parameter update after the timer times out."""
        if self.pending_param and self.pending_value:
            param = self.pending_param
            value = self.pending_value

            if not isinstance(param, str):
                raise ValueError(f"Parameter name must be a string. Got {type(param)} instead.")
            if hasattr(self, param):
                setattr(self, param, value)
            else:
                QMessageBox.warning(self, "Invalid Parameter", f"Attribute {param} does not exist.")
                return

            self.output[self.filenames[self.current_index]] = self.analyze(
                self.image_paths[self.filenames[self.current_index]]
            )
            self.display_image(self.output[self.filenames[self.current_index]])

    def debounce_update(self, param, value):
        """Start the timer to delay updating parameters."""
        if param is None or value is None:
            QMessageBox.warning(self, "Invalid Input", "Parameter or value is invalid.")
            return
        self.pending_param = param
        self.pending_value = value
        self.update_timer.start(300)

    def set_current_index(self, index):
        """Slot to update the current index and refresh the image."""
        if 0 <= index < len(self.image_paths):
            self.current_index = index
            self.compute()
        else:
            QMessageBox.warning(self, "Invalid Index", "Index out of range.")

    def compute(self):
        """Display the current image."""
        if not self.image_paths:
            QMessageBox.information(self, "No Images", "No images to display.")
            return

        image_path = self.image_paths.get(self.filenames[self.current_index], None)
        if image_path is None:
            QMessageBox.critical(self, "Error", f"Image path for '{self.filenames[self.current_index]}' not found.")
            return

        if isinstance(image_path, np.ndarray):
            self.output[self.filenames[self.current_index]] = image_path
        else:
            try:
                self.output[self.filenames[self.current_index]] = self.analyze(image_path)
                if self.output[self.filenames[self.current_index]] is None:
                    QMessageBox.critical(self, "Error", f"Failed to load image '{self.filenames[self.current_index]}'.")
                    return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image '{self.filenames[self.current_index]}': {e}")
                return

        self.display_image(self.output[self.filenames[self.current_index]])

    def tabulate(self):
        """
        Export file metadata for use in a table.
        """
        if not self.image_paths:
            QMessageBox.information(self, "No Files", "No image files to export metadata for.")
            return [], []
    
        # Prepare column headers
        headers = ["Filename", "Dimensions (Loaded)", "File Size (KB)"]
    
        # Prepare table data
        table_data = []
        for filename, path in self.image_paths.items():
            dimensions = "N/A"  # Default if dimensions can't be determined
            file_size = "N/A"   # Default if file size can't be determined
    
            # Determine dimensions
            if isinstance(path, np.ndarray):
                dimensions = str(path.shape)
            else:
                try:
                    img = io.imread(path)
                    dimensions = str(img.shape)
                except Exception as e:
                    self.logger.warning(f"Failed to load image for dimensions: {path}, Error: {e}")
    
            # Determine file size
            if os.path.exists(path) and not isinstance(path, np.ndarray):
                try:
                    file_size = f"{os.path.getsize(path) / 1024:.2f} KB"
                except Exception as e:
                    self.logger.warning(f"Failed to get file size: {path}, Error: {e}")
    
            # Add row to table data
            table_data.append([filename, dimensions, file_size])
    
        # Log data for debugging
        self.logger.info(f"Headers: {headers}")
        self.logger.info(f"Table Data: {table_data}")
    
        # Return data for integration with TableDialog
        return headers, table_data

    def display_image(self, img):
        """Display the current image."""
        if img is not None:
            self.setWindowTitle(f"{type(self).__name__} - {self.filenames[self.current_index]}")
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
            ax.imshow(img, cmap='gray')
            ax.axis("off")
            self.canvas.draw()
        else:
            QMessageBox.warning(self, "Display Error", "The image could not be displayed.")


    def analyze(self, image_path):
        """Read and return the image."""
        if isinstance(image_path, np.ndarray):
            return image_path
        else:
            try:
                return io.imread(image_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
                return None

