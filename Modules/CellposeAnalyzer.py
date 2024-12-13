import os
import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel, QLineEdit, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from cellpose import io, models, plot
from scipy.ndimage import label, find_objects, center_of_mass


class CellposeAnalyzer(QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.image_paths = files
        self.current_index = 0

        self.diameter = 25  # Default diameter for Cellpose

        # Initialize Cellpose model
        self.model_type = "cyto3"
        try:
            self.model = models.CellposeModel(model_type=self.model_type, gpu=True)
        except Exception:
            self.model = models.CellposeModel(model_type=self.model_type, gpu=False)
            print("GPU not available. Using CPU instead.")

        # Initialize processed results
        self.processed_results = {path: {"image": None, "measurements": None} for path in self.image_paths}

        # Setup UI
        self.setup_ui()

        # Display the first image initially
        self.update_image()

    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Table for measurements
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)  # Number of columns for measurements
        self.table.setHorizontalHeaderLabels(["Segment ID", "Area", "Centroid", "Bounding Box", "Mean Intensity"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Model dropdown and controls
        self.model_dropdown = QComboBox(self)
        self.model_dropdown.addItems(['cyto3', 'cyto2', 'cyto', 'nuclei', 'tissuenet_cp3', 'livecell_cp3'])
        self.model_dropdown.setCurrentText(self.model_type)
        self.model_dropdown.currentTextChanged.connect(self.update_model)

        self.diameter_input = QLineEdit(self)
        self.diameter_input.setText(str(self.diameter))
        self.diameter_input.setFixedWidth(50)
        self.diameter_input.returnPressed.connect(self.update_diameter_from_input)

        self.diameter_minus_button = QPushButton("-", self)
        self.diameter_minus_button.clicked.connect(self.decrease_diameter)

        self.diameter_plus_button = QPushButton("+", self)
        self.diameter_plus_button.clicked.connect(self.increase_diameter)

        self.analyze_all_button = QPushButton("Analyze All", self)
        self.analyze_all_button.clicked.connect(self.analyze_all_images)

        # Navigation buttons
        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.show_previous_image)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next_image)

        # Layouts
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Model:"))
        controls_layout.addWidget(self.model_dropdown)
        controls_layout.addWidget(QLabel("Diameter:"))
        controls_layout.addWidget(self.diameter_minus_button)
        controls_layout.addWidget(self.diameter_input)
        controls_layout.addWidget(self.diameter_plus_button)
        controls_layout.addWidget(self.analyze_all_button)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.prev_button)
        nav_layout.addStretch()
        nav_layout.addLayout(controls_layout)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)

        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.canvas, stretch=3)
        main_layout.addWidget(self.table, stretch=1)
        main_layout.addLayout(nav_layout)

    def analyze_all_images(self):
        """Process all images in the list."""
        for path in self.image_paths:
            if self.processed_results[path]["measurements"] is None:
                img, masks, flows, styles = self.process_image(path)
                self.processed_results[path]["image"] = img
                self.processed_results[path]["measurements"] = self.calculate_segment_measurements(img, masks)

        QMessageBox.information(self, "Analysis Complete", "All images have been analyzed.")


    def process_image(self, image_path):
        """Processes the image with the Cellpose model."""
     
        img = io.imread(image_path)
        masks, flows, styles = self.model.eval(img, diameter=self.diameter)
        return img, masks, flows, styles

    def update_diameter_from_input(self):
        """Update the diameter value when the input field is used."""
        try:
            new_diameter = int(self.diameter_input.text())
            if 5 <= new_diameter <= 500:
                self.diameter = new_diameter
                self.processed_results[self.image_paths[self.current_index]]['images'] = None  # Clear cache for the current image
                self.update_image()
            else:
                self.diameter_input.setText(str(self.diameter))  # Reset to valid value
        except ValueError:
            self.diameter_input.setText(str(self.diameter))  # Reset to current value

    def increase_diameter(self):
        """Increase the diameter by a small amount."""
        if self.diameter < 100:
            self.diameter += 1
            self.diameter_input.setText(str(self.diameter))
            self.processed_results[self.image_paths[self.current_index]]['images'] = None  # Clear cache for the current image
            self.update_image()

    def decrease_diameter(self):
        """Decrease the diameter by a small amount."""
        if self.diameter > 5:
            self.diameter -= 1
            self.diameter_input.setText(str(self.diameter))
            self.processed_results[self.image_paths[self.current_index]]['images'] = None  # Clear cache for the current image
            self.update_image()


    def calculate_current_measurements(self):
        """Calculate measurements for the current segmentation."""
        if 0 <= self.current_index < len(self.image_paths):
            # Ensure the image is processed
            if self.processed_results[self.image_paths[self.current_index]]['measurements'] is None:
                self.processed_results[self.image_paths[self.current_index]]['measurements'] = self.process_image(
                    self.image_paths[self.current_index]
                )
    
            img, masks, flows, styles = self.processed_results[self.image_paths[self.current_index]]['measurements']
            mask = masks  # Use the mask
    
            # Calculate segment measurements
            measurements = self.calculate_segment_measurements(img, mask)
            return measurements
    
    

        
    def update_model(self, model_type):
        """Updates the Cellpose model based on the dropdown selection."""
        self.model_type = model_type
        self.model = models.CellposeModel(model_type=self.model_type, gpu=True)
        self.processed_results[self.image_paths[self.current_index]]['images'] = {}  # Clear cache
        self.update_image()
        
    def update_image(self):
        """Updates the displayed image and measurements."""
        try:
            if 0 <= self.current_index < len(self.image_paths):
                # Process the image if not already processed
                if self.processed_results[self.image_paths[self.current_index]]['measurements'] is None:
                    self.processed_results[self.image_paths[self.current_index]]['measurements'] = self.process_image(
                        self.image_paths[self.current_index]
                    )
    
                img, mask, flow, styles = self.processed_results[self.image_paths[self.current_index]]['measurements']
    
                # Clear the figure and create a new subplot
                self.figure.clear()
                ax = self.figure.add_subplot(111)
    
                # Use Cellpose's built-in segmentation visualization
                plot.show_segmentation(self.figure, img, mask, flow[0])
                ax.axis('off')
    
                # Redraw the canvas to update the display
                self.canvas.draw()
    
                # Update the measurements table
                measurements = self.calculate_segment_measurements(img, mask)
                self.update_table(measurements)
    
                # Enable/disable buttons based on boundaries
                self.prev_button.setEnabled(self.current_index > 0)
                self.next_button.setEnabled(self.current_index < len(self.image_paths) - 1)
        except Exception as e:
            print(f"Error in update_image: {e}")

    def update_table(self, measurements):
        """Populate the measurements table with data."""
        self.table.setRowCount(len(measurements))  # Set the number of rows
    
        for row, measurement in measurements.iterrows():
            self.table.setItem(row, 0, QTableWidgetItem(str(measurement["Segment ID"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(measurement["Area"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(measurement["Centroid"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(measurement["Bounding Box"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(measurement["Mean Intensity"])))


    def show_previous_image(self):
        """Displays the previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_image()
    
    def show_next_image(self):
        """Displays the next image."""
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.update_image()
            
    def calculate_current_measurements(self):
        """Calculate measurements for the current segmentation."""
        if 0 <= self.current_index < len(self.image_paths):
            # Ensure the image is processed
            if self.processed_results[self.image_paths[self.current_index]]['measurements'] is None:
                self.processed_results[self.image_paths[self.current_index]]['measurements'] = self.process_image(self.processed_results[self.image_paths[self.current_index]]['images'])
    
            img, masks, flows, styles = self.processed_results[self.image_paths[self.current_index]]['measurements']
            mask = masks[0]  # Use the first mask
    
            # Calculate segment measurements
            measurements = calculate_segment_measurements(img, mask)
            return measurements

    def calculate_segment_measurements(self, img, mask):
        """Calculate common measurements for each segment in the mask."""
        mask = mask.astype(np.int32)
        labeled_mask, num_segments = label(mask)
    
        measurements = []
        for segment_id in range(1, num_segments + 1):  # Exclude background
            segment_mask = (labeled_mask == segment_id)
            area = np.sum(segment_mask)
            centroid = center_of_mass(segment_mask)
            bounding_box = find_objects(segment_mask)[0]  # Bounding box slice
            mean_intensity = np.mean(img[segment_mask])
    
            measurements.append({
                "Segment ID": segment_id,
                "Area": area,
                "Centroid": centroid,
                "Bounding Box": bounding_box,
                "Mean Intensity": mean_intensity
            })
    
        return pd.DataFrame(measurements)


def main(files):
    analyzer = CellposeAnalyzer(files)
    analyzer.show()

