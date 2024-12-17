from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt

class FileManagementDialog(QDialog):
    current_index_changed = pyqtSignal(int)  # Emit only the file index

    def __init__(self, file_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Manager")
        self.file_list = file_list
        self.current_index = 0  # Track the currently displayed file

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Loaded Files:"))
        self.file_list_widget = QListWidget(self)
        layout.addWidget(self.file_list_widget)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.previous_button = QPushButton("Previous")
        self.previous_button.clicked.connect(self.show_previous_file)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_file)
        buttons_layout.addWidget(self.previous_button)
        buttons_layout.addWidget(self.next_button)
        layout.addLayout(buttons_layout)

        self.populate_file_list()
        self.update_buttons()

    def populate_file_list(self):
        """Populate the list widget with file names."""
        self.file_list_widget.clear()
        for file in self.file_list:
            self.file_list_widget.addItem(file)
        self.update_current_file_highlight()

    def update_current_file_highlight(self):
        """Highlight the currently selected file."""
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            item.setSelected(i == self.current_index)

    def show_previous_file(self):
        """Navigate to the previous file."""
        if self.current_index > 0:
            self.current_index -= 1
            self.current_index_changed.emit(self.current_index)  # Emit index
            self.update_current_file_highlight()
            self.update_buttons()

    def show_next_file(self):
        """Navigate to the next file."""
        if self.current_index < len(self.file_list) - 1:
            self.current_index += 1
            self.current_index_changed.emit(self.current_index)  # Emit index
            self.update_current_file_highlight()
            self.update_buttons()

    def update_buttons(self):
        """Enable or disable navigation buttons."""
        self.previous_button.setDisabled(self.current_index == 0)
        self.next_button.setDisabled(self.current_index >= len(self.file_list) - 1)

