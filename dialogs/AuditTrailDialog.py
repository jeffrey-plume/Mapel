from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog
import csv

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox
import csv

class AuditTrailDialog(QDialog):
    def __init__(self, audit_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audit Trail")
        self.resize(800, 600)

        # Main layout
        layout = QVBoxLayout(self)

        # Table widget for displaying data
        self.table = QTableWidget(self)
        layout.addWidget(self.table)

        # Configure table
        if audit_data:
            self.table.setRowCount(len(audit_data))
            self.table.setColumnCount(4)  # Adjust column count based on dictionary keys
            self.table.setHorizontalHeaderLabels(["Username", "Date", "Time", "Action"])
            self.populate_table(audit_data)
        else:
            QMessageBox.warning(self, "No Data", "No audit trail data found.")
            self.table.setRowCount(0)
            self.table.setColumnCount(0)

        # Export button
        export_button = QPushButton("Export to CSV", self)
        export_button.clicked.connect(self.export_to_csv)
        layout.addWidget(export_button)

    def populate_table(self, audit_data):
        """Fill the table with audit data."""
        for row_idx, row_data in enumerate(audit_data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(row_data["username"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row_data["date"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row_data["time"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row_data["action"]))

    def export_to_csv(self):
        """Export the table data to a CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Audit Trail", "", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Username", "Date", "Time", "Action"])
                    for row in range(self.table.rowCount()):
                        row_data = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                        writer.writerow(row_data)
                QMessageBox.information(self, "Success", "Audit trail exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export audit trail: {e}")

