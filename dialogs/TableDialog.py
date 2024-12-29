from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QHeaderView
)
import csv
import os
from typing import Tuple

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout

class TableDialog(QDialog):
    def __init__(self, table_data, column_headers, title="Table View", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)

        # Create main layout
        self.layout = QVBoxLayout(self)

        # Create table widget
        self.table = QTableWidget(self)
        self.table.setRowCount(len(table_data))
        self.table.setColumnCount(len(column_headers))
        self.table.setHorizontalHeaderLabels(column_headers)

        # Populate table with data
        for row_idx, row_data in enumerate(table_data):
            for col_idx, cell_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))

        # Adjust table to fit contents
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        # Add table to the layout
        self.layout.addWidget(self.table)

        # Add buttons for closing or exporting
        self.button_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)

        self.button_layout.addWidget(self.close_button)
        self.button_layout.addWidget(self.export_button)
        self.layout.addLayout(self.button_layout)

    def export_to_csv(self):
        """
        Export the table data to a CSV file.
        """
        import csv
        from PyQt5.QtWidgets import QFileDialog

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if not file_path:
            return

        try:
            with open(file_path, "w", newline='', encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                # Write headers
                writer.writerow([self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())])
                # Write table data
                for row in range(self.table.rowCount()):
                    row_data = [self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(self.table.columnCount())]
                    writer.writerow(row_data)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to save CSV: {e}")




