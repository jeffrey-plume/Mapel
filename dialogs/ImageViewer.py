from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
    QLabel, QLineEdit, QComboBox, QMessageBox, QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from cellpose import io
import os


class ImageViewer(QMainWindow):
    def __init__(self, image_paths=None, index=0):
        super().__init__()
        self.image_paths = {key:None for key in list(image_paths.keys())} 
        self.image_files = list(image_paths.values())
        self.current_index = index
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)  # Ensure the timer triggers only once
        self.update_timer.timeout.connect(self._delayed_update_param)
        # Initialize UI
        self.title = 'Image Viewer'
        #self.resize(600, 450)
        
        # Image display
        self.figure = Figure()
        self.figure.tight_layout()
        self.canvas = FigureCanvas(self.figure)

        # Parameters to update
        self.param_name = None
        self.param_value = None

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.canvas, alignment=Qt.AlignCenter)
      #  main_layout.addLayout(controls_layout)

        # Display the first image if available
        if self.image_paths:
            self.compute()


    def update_param(self, param_name, value):
        """
        Update parameters with a delay and recompute the image.

        Args:
            param_name (str): The parameter name to update.
            value (int/float): The new value for the parameter.
        """
        self.param_name = param_name
        self.param_value = value
        self.update_timer.start(300)  # Delay of 500 ms (adjust as needed)

    def _delayed_update_param(self):
        """
        Perform the delayed parameter update.
        """
        if self.param_name and hasattr(self, self.param_name):
            setattr(self, self.param_name, self.param_value)
            self.set_current_index(self.current_index)
        else:
            QMessageBox.warning(self, "Parameter Error", f"Parameter '{self.param_name}' not found.")
            
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
    
        filenames = list(self.image_paths.keys())
        filepaths = self.image_files
        if self.current_index < 0 or self.current_index >= len(filenames):
            QMessageBox.information(self, "No Images", "Invalid image index.")
            return
    
        current_filename = filenames[self.current_index]
    
        # Load the image if not already loaded
        if self.image_paths[current_filename] is None:
            try:
                current_path = os.path.normpath(filepaths[self.current_index].strip('"'))
                self.image_paths[current_filename] = self.read_image(current_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image '{current_filename}': {e}")
                return
    
        # Update the window title to include the current filename
        self.setWindowTitle(f"{self.title} - {current_filename}")
    
        self.display_image()

    
    def display_image(self):
        """Display the current image."""
        filenames = list(self.image_paths.keys())
        if self.current_index < 0 or self.current_index >= len(filenames):
            QMessageBox.information(self, "No Images", "Invalid image index.")
            return
    
        current_filename = filenames[self.current_index]
        img = self.image_paths[current_filename]
    
        if img is not None:
            # Update the title with the current image name
            self.setWindowTitle(f"{self.title} - {current_filename}")
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.imshow(img, cmap='gray')
            ax.axis("off")
            self.canvas.draw()
        else:
            QMessageBox.warning(self, "Display Error", "The image could not be displayed.")
    

    def read_image(self, image_path):
        """Read and validate an image."""
        try:
            return io.imread(image_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
            return None
