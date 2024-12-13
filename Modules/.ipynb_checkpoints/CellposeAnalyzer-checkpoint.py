import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSlider, QLabel
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from cellpose import io, models


class CellposeAnalyzer(QMainWindow):
    def __init__(self, images):
        super().__init__()
        self.setWindowTitle("Cellpose Analyzer")
        self.setGeometry(100, 100, 600, 600)

        self.images = images
        self.current_index = 0
        self.processed_images = [None] * len(images)  # Cache for processed images
        self.diameter = 25  # Default diameter for Cellpose

        # Central widget to hold everything
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Image display area
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedSize(500, 500)

        # Navigation buttons
        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.show_previous_image)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next_image)

        # Slider for adjusting diameter
        self.diameter_slider = QSlider(Qt.Horizontal, self)
        self.diameter_slider.setMinimum(5)
        self.diameter_slider.setMaximum(100)
        self.diameter_slider.setValue(self.diameter)
        self.diameter_slider.valueChanged.connect(self.update_diameter)

        self.diameter_label = QLabel(f"Diameter: {self.diameter}", self)

        # Layout for buttons and slider
        control_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev_button)
        button_layout.addStretch()  # Adds spacing between buttons
        button_layout.addWidget(self.next_button)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Adjust Diameter:"))
        slider_layout.addWidget(self.diameter_slider)
        slider_layout.addWidget(self.diameter_label)

        control_layout.addLayout(button_layout)
        control_layout.addLayout(slider_layout)

        # Main layout for the central widget
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.canvas)
        layout.addLayout(control_layout)

        # Display the first image initially
        self.update_image()

    def process_image(self, image_path, diameter):
        """Reads and processes the image."""
        img = io.imread(image_path)
        masks, flows, styles = models.CellposeModel(model_type='tissuenet_cp3').eval(img, diameter=diameter, channels=[0, 0])
        return masks, flows, styles

    def update_diameter(self, value):
        """Update the diameter value and reprocess the current image."""
        self.diameter = value
        self.diameter_label.setText(f"Diameter: {self.diameter}")
        # Clear cache for the current image and reprocess
        self.processed_images[self.current_index] = None
        self.update_image()

    def update_image(self):
        """Updates the displayed image based on the current index."""
        if 0 <= self.current_index < len(self.images):
            # Process the image if not already processed
            if self.processed_images[self.current_index] is None:
                self.processed_images[self.current_index] = self.process_image(self.images[self.current_index], self.diameter)[0]

            # Display the processed image
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.imshow(self.processed_images[self.current_index], cmap='gray')
            ax.axis('off')
            self.canvas.draw()

            # Enable/disable buttons based on boundaries
            self.prev_button.setEnabled(self.current_index > 0)
            self.next_button.setEnabled(self.current_index < len(self.images) - 1)

    def show_previous_image(self):
        """Displays the previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_image()

    def show_next_image(self):
        """Displays the next image."""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.update_image()


if __name__ == "__main__":
    # Example usage
    app = QApplication(sys.argv)
    images = ["C:/Users/Lenovo/OneDrive/Documents/GitHub/Shiva/Icons/download.png"]  # Replace with actual paths
    viewer = CellposeAnalyzer(images)
    viewer.show()
    sys.exit(app.exec_())

