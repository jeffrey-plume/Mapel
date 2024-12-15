import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel, QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from cellpose import io, models, plot
from scipy.ndimage import label, find_objects, center_of_mass


class CellposeAnalyzer(QMainWindow):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.original_image = None
        self.processed_results = None  # Holds processed image and measurements
        self.diameter = 25  # Default diameter for Cellpose
        self.model_type = "cyto3"  # Default model type for Cellpose

        try:
            self.model = models.CellposeModel(model_type=self.model_type, gpu=True)
        except Exception:
            self.model = models.CellposeModel(model_type=self.model_type, gpu=False)
            QMessageBox.warning(self, "Warning", "GPU not available. Using CPU instead.")

        # Setup the user interface
        self.setup_ui()

        # Load and process the image immediately
        self.load_and_process_image()

    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Cellpose Analyzer")
        self.resize(800, 600)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Matplotlib figure and canvas for image display
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas, stretch=3)

        # Table for displaying measurements
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Segment ID", "Area", "Centroid", "Bounding Box", "Mean Intensity"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table, stretch=1)

        # Export button
        self.export_button = QPushButton("Export Measurements")
        self.export_button.clicked.connect(self.export_measurements)
        layout.addWidget(self.export_button)

    def load_and_process_image(self):
        """Load the image, process it with Cellpose, and update the UI."""
        try:
            # Load image
            self.original_image = io.imread(self.file_path)

            # Process the image
            masks, flows, styles, _ = self.model.eval(self.original_image, diameter=self.diameter, channels=[0, 0])

            # Save results
            self.processed_results = {
                "image": self.original_image,
                "masks": masks,
                "flows": flows,
                "styles":styles
            }

            # Update UI
            self.update_image_and_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process the image: {str(e)}")

    def update_image_and_table(self):
        """Update the displayed image and measurements."""
        if not self.processed_results:
            QMessageBox.warning(self, "Warning", "No processed results available.")
            return

        try:
            # Update the displayed image
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            plot.show_segmentation(
                ax,
                self.processed_results["image"],
                self.processed_results["masks"],
                self.processed_results["flows"][0]
            )
            ax.axis("off")
            self.canvas.draw()

            # Update the measurements table
            measurements = self.calculate_measurements()
            self.populate_table(measurements)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update the display: {str(e)}")

    def calculate_measurements(self):
        """Calculate common measurements for each segment."""
        image = self.processed_results["image"]
        masks = self.processed_results["masks"]

        labeled_mask, num_segments = label(masks)
        measurements = []

        for segment_id in range(1, num_segments + 1):  # Exclude background
            segment_mask = (labeled_mask == segment_id)
            area = np.sum(segment_mask)
            centroid = center_of_mass(segment_mask)
            bounding_box = find_objects(segment_mask)[0]  # Bounding box slice
            mean_intensity = np.mean(image[segment_mask])

            measurements.append({
                "Segment ID": segment_id,
                "Area": area,
                "Centroid": f"({centroid[0]:.2f}, {centroid[1]:.2f})",
                "Bounding Box": f"[{bounding_box.start}, {bounding_box.stop}]",
                "Mean Intensity": mean_intensity
            })

        return pd.DataFrame(measurements)

    def populate_table(self, measurements):
        """Populate the table with measurements."""
        self.table.setRowCount(len(measurements))
        for row, measurement in measurements.iterrows():
            self.table.setItem(row, 0, QTableWidgetItem(str(measurement["Segment ID"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(measurement["Area"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(measurement["Centroid"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(measurement["Bounding Box"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(measurement["Mean Intensity"])))

    def export_measurements(self):
        """Export the measurements to a CSV file."""
        if not self.processed_results:
            QMessageBox.warning(self, "Warning", "No measurements to export.")
            return

        try:
            measurements = self.calculate_measurements()
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Measurements", "", "CSV Files (*.csv)")

            if file_path:
                measurements.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", f"Measurements exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export measurements: {str(e)}")


def main(file_path):
    app = QApplication(sys.argv)
    analyzer = CellposeAnalyzer(file_path)
    analyzer.show()
    sys.exit(app.exec_())

