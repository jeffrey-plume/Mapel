import os
import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
    QLabel, QLineEdit, QComboBox, QMessageBox, QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from cellpose import io, models, plot
from scipy.ndimage import label, find_objects, center_of_mass
import pandas as pd


class CellposeAnalyzer(QMainWindow):
    def __init__(self, image_paths, index=0):
        super().__init__()
        self.image_paths = image_paths
        self.current_index = index
        self.processed_results = [None] * len(image_paths)
        self.diameter = 25

        # Initialize Cellpose model
        self.model_type = "cyto"
        self.initialize_model()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Image display
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Dropdown for model selection
        self.model_dropdown = QComboBox(self)
        self.model_dropdown.addItems(['cyto3', 'cyto2', 'cyto', 'nuclei', 'tissuenet_cp3', 'livecell_cp3',
                                       'yeast_PhC_cp3', 'yeast_BF_cp3', 'bact_phase_cp3', 'bact_fluor_cp3', 
                                       'deepbacs_cp3', 'cyto2_cp3'])
        self.model_dropdown.setCurrentText(self.model_type)
        self.model_dropdown.currentTextChanged.connect(self.update_model)

        # Diameter adjustment controls
        self.diameter_input = QLineEdit(self)
        self.diameter_input.setText(str(self.diameter))
        self.diameter_input.setFixedWidth(50)
        self.diameter_input.returnPressed.connect(self.update_diameter_from_input)

        self.diameter_minus_button = QPushButton("-", self)
        self.diameter_minus_button.setFixedWidth(30)
        self.diameter_minus_button.clicked.connect(self.decrease_diameter)

        self.diameter_plus_button = QPushButton("+", self)
        self.diameter_plus_button.setFixedWidth(30)
        self.diameter_plus_button.clicked.connect(self.increase_diameter)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)

        # Layout for controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Model:"))
        controls_layout.addWidget(self.model_dropdown)
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel("Diameter:"))
        controls_layout.addWidget(self.diameter_minus_button)
        controls_layout.addWidget(self.diameter_input)
        controls_layout.addWidget(self.diameter_plus_button)
        controls_layout.addStretch()

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.canvas, alignment=Qt.AlignCenter)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.progress_bar)

        # Display the first image
        self.update_image()

    def initialize_model(self):
        """Initialize the Cellpose model with the selected type and GPU availability."""
        try:
            self.model = models.CellposeModel(model_type=self.model_type, gpu=True, diam_mean=self.diameter)
        except Exception:
            self.model = models.CellposeModel(model_type=self.model_type, gpu=False, diam_mean=self.diameter)
            QMessageBox.warning(self, "Warning", "GPU not available. Using CPU instead.")


    def read_image(self, image_path):
        """Read an image file and validate it."""
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"File not found: {image_path}")
    
            if not os.access(image_path, os.R_OK):
                raise PermissionError(f"File is not readable: {image_path}")
    
            img = io.imread(image_path)
            if img is None:
                raise ValueError(f"Failed to load image: {image_path}")
            return img
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Could not read the file: {image_path}\n{e}")
            return None

    def process_image(self, image_path):
        """Process a single image."""
        img = self.read_image(image_path)
        if img is None:
            return None, None, None, None  # Skip processing if the image could not be loaded
    
        try:
            masks, flows, styles = self.model.eval(img, diameter=self.diameter, channels=[0, 0])
            return img, masks, flows, styles
        except Exception as e:
            QMessageBox.warning(self, "Processing Error", f"Failed to process image: {image_path}\n{e}")
            return None, None, None, None


    def update_diameter_from_input(self):
        """Update diameter from the user input field."""
        try:
            new_diameter = int(self.diameter_input.text())
            if 5 <= new_diameter <= 100:
                self.diameter = new_diameter
                self.processed_results[self.current_index] = None
                self.update_image()
            else:
                self.diameter_input.setText(str(self.diameter))
        except ValueError:
            self.diameter_input.setText(str(self.diameter))

    def increase_diameter(self):
        """Increase the diameter by 1."""
        if self.diameter < 100:
            self.diameter += 1
            self.diameter_input.setText(str(self.diameter))
            self.processed_results[self.current_index] = None
            self.update_image()

    def decrease_diameter(self):
        """Decrease the diameter by 1."""
        if self.diameter > 5:
            self.diameter -= 1
            self.diameter_input.setText(str(self.diameter))
            self.processed_results[self.current_index] = None
            self.update_image()

    def calculate_segment_measurements(self, img, masks):
        """Calculate measurements for each segmented object."""
        labeled_mask, num_segments = label(masks)
        measurements = []

        for segment_id in range(1, num_segments + 1):
            segment_mask = (labeled_mask == segment_id)
            area = np.sum(segment_mask)
            centroid = center_of_mass(segment_mask)
            bounding_box = find_objects(segment_mask)[0]
            mean_intensity = np.mean(img[segment_mask])
            measurements.append({
                "Segment ID": segment_id,
                "Area": area,
                "Centroid": f"({centroid[0]:.2f}, {centroid[1]:.2f})",
                "Bounding Box": f"[{bounding_box[0].start}:{bounding_box[0].stop}, {bounding_box[1].start}:{bounding_box[1].stop}]",
                "Mean Intensity": mean_intensity
            })

        return pd.DataFrame(measurements)

    def update_model(self, model_type):
        """Update the Cellpose model when the user selects a different type."""
        self.model_type = model_type
        self.initialize_model()
        self.processed_results = [None] * len(self.image_paths)
        self.update_image()

    def update_image(self):
        """Update the displayed image with segmentation results."""
        if 0 <= self.current_index < len(self.image_paths):
            if self.processed_results[self.current_index] is None:
                self.processed_results[self.current_index] = self.process_image(self.image_paths[self.current_index])
    
            img, masks, flows, styles = self.processed_results[self.current_index]
            if img is not None:
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                plot.show_segmentation(self.figure, img, masks, flows[0])
                ax.axis('off')
                self.canvas.draw()
    
    def set_current_file(self, file_path):
        """Update the current file and reprocess the image."""
        if file_path is None:  # Handle empty file list
            QMessageBox.information(self, "No Files", "No files to display.")
            return
    
        if file_path not in self.image_paths:
            QMessageBox.warning(self, "File Error", f"File '{file_path}' is not in the loaded image list.")
            return
    
        # Update the current index based on the file path
        self.current_index = self.image_paths.index(file_path)
    
        # Reprocess and update the UI
        self.update_image()


    def update_file_list(self, file_list):
        """Synchronize the file list with the File Management Dialog."""
        self.image_paths = file_list
        self.processed_results = [None] * len(self.image_paths)  # Reset results
        if self.current_index >= len(self.image_paths):  # Adjust current index if needed
            self.current_index = len(self.image_paths) - 1
        if self.current_index >= 0:
            self.update_image()
