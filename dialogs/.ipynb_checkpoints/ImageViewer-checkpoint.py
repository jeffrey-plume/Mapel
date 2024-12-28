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
    def __init__(self, image_paths=None, index=0):
        super().__init__()
        self.image_paths = image_paths #if image_paths else []
        self.current_index = index

        # Initialize UI
        self.setWindowTitle("Cellpose Image Viewer")
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
    
        # Get the current filename and check if it exists in the dictionary
        filenames = list(self.image_paths.keys())
        if self.current_index < 0 or self.current_index >= len(filenames):
            QMessageBox.information(self, "No Images", "Invalid image index.")
            return
    
        current_filename = filenames[self.current_index]
    
        # Load the image if not already loaded
        if self.image_paths[current_filename] is None:
            try:
                self.image_paths[current_filename] = self.read_image(current_filename)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image '{current_filename}': {e}")
                return
    
        # Get the loaded image
        img = self.image_paths[current_filename]
    
        # Display the image
        if img is not None:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.imshow(img, cmap='gray')
            ax.axis('off')
            self.canvas.draw()
        else:
            QMessageBox.warning(self, "Display Error", f"Image '{current_filename}' could not be displayed.")


    def read_image(self, image_path):
        """Read and validate an image."""
        try:
            return io.imread(image_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
            return None

#    def show_previous_image(self):
#        """Show the previous image."""
#        if self.current_index > 0:
#            self.current_index -= 1
#            self.update_image()
#
#    def show_next_image(self):
#        """Show the next image."""
#        if self.current_index < len(self.image_paths) - 1:
#            self.current_index += 1
#            self.update_image()



