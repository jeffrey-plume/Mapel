from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt


class FileManagementDialog(QDialog):
    def __init__(self, file_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Management")
        self.resize(600, 400)

        # Use the provided file list
        self.file_list = file_list
        self.current_index = 0  # Track the currently displayed file

        # Main layout
        layout = QVBoxLayout(self)

        # Instruction label
        layout.addWidget(QLabel("Currently loaded files:"))

        # QListWidget for displaying files
        self.file_list_widget = QListWidget(self)
        self.populate_file_list()
        layout.addWidget(self.file_list_widget)

        # Navigation buttons (horizontal layout)
        button_layout = QHBoxLayout()
        self.previous_button = QPushButton("Previous", self)
        self.previous_button.clicked.connect(self.show_previous_file)
        self.previous_button.setDisabled(True)  # Initially disabled
        button_layout.addWidget(self.previous_button, alignment=Qt.AlignLeft)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next_file)
        self.next_button.setDisabled(len(self.file_list) <= 1)  # Disable if no next file
        button_layout.addWidget(self.next_button, alignment=Qt.AlignRight)

        layout.addLayout(button_layout)

    def populate_file_list(self):
        """Populate the QListWidget with the file list and highlight the current file."""
        self.file_list_widget.clear()
        for i, file_name in enumerate(self.file_list):
            item = self.file_list_widget.addItem(file_name)
            # Highlight the current file in blue
            if i == self.current_index:
                self.file_list_widget.item(i).setSelected(True)
                self.file_list_widget.item(i).setBackground(Qt.blue)
                self.file_list_widget.item(i).setForeground(Qt.white)

    def update_current_file_highlight(self):
        """Highlight the currently selected file."""
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if i == self.current_index:
                item.setSelected(True)
                item.setBackground(Qt.blue)
                item.setForeground(Qt.white)
            else:
                item.setSelected(False)
                item.setBackground(Qt.white)
                item.setForeground(Qt.black)


    def current_file(self):
        """Get the currently selected file from the file list."""
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            raise AttributeError("No file selected.")
        return selected_items[0].text()


    def show_previous_file(self):
        """Navigate to the previous file in the list."""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_current_file_highlight()

        # Update button states
        self.previous_button.setDisabled(self.current_index == 0)
        self.next_button.setDisabled(self.current_index >= len(self.file_list) - 1)

    def show_next_file(self):
        """Navigate to the next file in the list."""
        if self.current_index < len(self.file_list) - 1:
            self.current_index += 1
            self.update_current_file_highlight()

        # Update button states
        self.previous_button.setDisabled(self.current_index == 0)
        self.next_button.setDisabled(self.current_index >= len(self.file_list) - 1)

    def closeEvent(self, event):
        """Handle dialog close event."""
        QMessageBox.information(self, "Files Updated", f"{len(self.file_list)} file(s) remain in the list.")
        event.accept()

