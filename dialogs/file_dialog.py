from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton

class FileManagementDialog(QDialog):
    def __init__(self, file_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Management")
        self.resize(600, 400)

        # Use the shared file list
        self.file_list = file_list

        # Main layout
        layout = QVBoxLayout(self)

        # Instructions
        layout.addWidget(QLabel("Currently selected files:"))

        # QListWidget for displaying files
        self.file_list_widget = QListWidget(self)
        self.populate_file_list()
        layout.addWidget(self.file_list_widget)

        # Buttons
        remove_button = QPushButton("Remove Selected", self)
        remove_button.clicked.connect(self.remove_selected_files)
        layout.addWidget(remove_button)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def populate_file_list(self):
        """Populate the QListWidget with the shared file list."""
        self.file_list_widget.clear()
        for file in self.file_list:
            self.file_list_widget.addItem(file)

    def remove_selected_files(self):
        """Remove selected files from the shared file list."""
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "No files selected for removal.")
            return

        for item in selected_items:
            file_name = item.text()
            if file_name in self.file_list:
                self.file_list.remove(file_name)  # Remove from the shared file list
        self.populate_file_list()  # Refresh the QListWidget
