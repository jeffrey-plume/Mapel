from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
    QLabel, QLineEdit, QComboBox, QMessageBox, QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from cellpose import io
import os


class ImageViewer(QMainWindow):
    def __init__(self, image_paths=None, title = "Image Viewer", index=0):
        super().__init__()
        self.image_paths = {key:None for key in list(image_paths.keys())} 
        self.image_files = list(image_paths.values())
        self.current_index = index
        self.title = title
        
        # Initialize UI
        self.setWindowTitle(self.title)
        self.resize(600, 450)

        # Image display
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)



        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.canvas, alignment=Qt.AlignCenter)
      #  main_layout.addLayout(controls_layout)

        # Display the first image if available
        if self.image_paths:
            self.update_image()

    def set_current_index(self, index):
        """Slot to update the current index and refresh the image."""
        if 0 <= index < len(self.image_paths):
            self.current_index = index
            self.update_image()
        else:
            QMessageBox.warning(self, "Invalid Index", "Index out of range.")

    def update_image(self):
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
        current_path = filepaths[self.current_index].decode('utf-8')

        print(current_path)

        # Load the image if not already loaded
        if self.image_paths[current_filename] is None:
            try:
                self.image_paths[current_filename] = self.read_image(current_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image '{current_filename}': {e}")
                return

        self.display_image()
    
    def display_image(self, title="Image"):
        """Display the provided image."""

        filenames = list(self.image_paths.keys())
        if self.current_index < 0 or self.current_index >= len(filenames):
            QMessageBox.information(self, "No Images", "Invalid image index.")
            return
    
        current_filename = filenames[self.current_index]

        img = self.image_paths[current_filename]
        

        if img is not None:
            self.setWindowTitle(title)
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

