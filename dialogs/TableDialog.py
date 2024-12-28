from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QHeaderView
)
import csv
import os
from typing import Tuple

class TableDialog(QDialog):  # Inherit from QDialog
    def __init__(self, table_data, column_headers, title, parent=None):
        super(TableDialog, self).__init__(parent)  # Properly initialize QDialog
        self.setWindowTitle(title)
        self.resize(800, 600)

        if table_data is None or table_data.empty:
            QMessageBox.warning(self, "No Data", "No data available to export.")
            return

        # Main layout
        layout = QVBoxLayout(self)

        # Table widget for displaying data
        self.table = QTableWidget(self)
        layout.addWidget(self.table)

        # Configure table
        if not table_data.empty:  # Check if DataFrame is not empty
            self.table.setRowCount(len(table_data))
            self.table.setColumnCount(len(column_headers))
            self.table.setHorizontalHeaderLabels(column_headers)
            self.populate_table(table_data, column_headers)
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Dynamic resizing
        else:
            QMessageBox.warning(self, "No Data", "No data available to display.")
            self.table.setRowCount(0)
            self.table.setColumnCount(0)

        # Export button
        self.export_button = QPushButton("Export to CSV", self)
        self.export_button.clicked.connect(self.export_to_csv)
        layout.addWidget(self.export_button)

        # Disable export button if no data
        self.export_button.setEnabled(not table_data.empty)

    def populate_table(self, table_data, column_headers):
        """Fill the table with data."""
        for row_idx, row_data in table_data.iterrows():  # Iterate over DataFrame rows
            for col_idx, header in enumerate(column_headers):
                value = row_data.get(header, "")
                if value == "":
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem("(Missing)"))
                else:
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def export_to_csv(self):
        """Export the table data to a CSV file."""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No data available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Table", "", "CSV Files (*.csv)")
        if file_path:
            # Confirm overwrite if file exists
            if os.path.exists(file_path):
                reply = QMessageBox.question(
                    self,
                    "Overwrite Confirmation",
                    f"The file '{file_path}' already exists. Do you want to overwrite it?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

            try:
                with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    # Write headers
                    headers = [self.table.horizontalHeaderItem(col).text() for col in range(self.table.columnCount())]
                    writer.writerow(headers)

                    # Write data rows
                    for row in range(self.table.rowCount()):
                        row_data = [
                            self.table.item(row, col).text() if self.table.item(row, col) else ""
                            for col in range(self.table.columnCount())
                        ]
                        writer.writerow(row_data)
                QMessageBox.information(self, "Success", "Table exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export table: {e}")




