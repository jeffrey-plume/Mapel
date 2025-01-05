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

class ImageViewer(QMainWindow):
    def __init__(self, image_paths=None, index=0):
        super().__init__()
        self.image_paths = image_paths
        self.output = {key: None for key in image_paths.keys()}
        self.filenames = list(image_paths.keys())

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

            self.output[self.filenames[self.current_index]] = self.read_image(
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
                self.output[self.filenames[self.current_index]] = self.read_image(image_path)
                if self.output[self.filenames[self.current_index]] is None:
                    QMessageBox.critical(self, "Error", f"Failed to load image '{self.filenames[self.current_index]}'.")
                    return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image '{self.filenames[self.current_index]}': {e}")
                return

        self.display_image(self.output[self.filenames[self.current_index]])

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


    def read_image(self, image_path):
        """Read and return the image."""
        if isinstance(image_path, np.ndarray):
            return image_path
        else:
            try:
                return io.imread(image_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
                return None

