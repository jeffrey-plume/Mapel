from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QMessageBox, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal


class FileManagementDialog(QDialog):
    file_list_updated  = pyqtSignal(str)

    def __init__(self, file_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Management")
        self.resize(600, 400)

        self.file_list = file_list
        self.current_index = 0

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Currently loaded files:"))

        self.file_list_widget = QListWidget(self)
        layout.addWidget(self.file_list_widget)

        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search files...")
        self.search_box.textChanged.connect(self.filter_file_list)
        layout.addWidget(self.search_box)

        self.populate_file_list()

        button_layout = QHBoxLayout()
        self.previous_button = QPushButton("Previous", self)
        self.previous_button.clicked.connect(self.show_previous_file)
        self.previous_button.setDisabled(True)
        button_layout.addWidget(self.previous_button)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.show_next_file)
        self.next_button.setDisabled(len(self.file_list) <= 1)
        button_layout.addWidget(self.next_button)

        self.remove_button = QPushButton("Remove", self)
        self.remove_button.clicked.connect(self.remove_current_file)
        button_layout.addWidget(self.remove_button)

        layout.addLayout(button_layout)

    def populate_file_list(self):
        self.file_list_widget.clear()
        for i, file_name in enumerate(self.file_list):
            item = self.file_list_widget.addItem(file_name)
            if i == self.current_index:
                self.file_list_widget.item(i).setSelected(True)
                self.file_list_widget.item(i).setBackground(Qt.blue)
                self.file_list_widget.item(i).setForeground(Qt.white)

    def update_current_file_highlight(self):
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

    def show_previous_file(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_current_file_highlight()
            self.file_list_updated.emit(self.file_list[self.current_index])
        self.previous_button.setDisabled(self.current_index == 0)
        self.next_button.setDisabled(self.current_index >= len(self.file_list) - 1)

    def show_next_file(self):
        if self.current_index < len(self.file_list) - 1:
            self.current_index += 1
            self.update_current_file_highlight()
            self.file_list_updated.emit(self.file_list[self.current_index])
        self.previous_button.setDisabled(self.current_index == 0)
        self.next_button.setDisabled(self.current_index >= len(self.file_list) - 1)


    def set_current_file(self, file_path):
        """Update the current file and reprocess the image."""
        if file_path not in self.image_paths:
            QMessageBox.warning(self, "File Error", f"File '{file_path}' is not in the loaded image list.")
            return
    
        # Update the current index based on the file path
        self.current_index = self.image_paths.index(file_path)
    
        # Reprocess and update the UI
        self.update_image()


    def remove_current_file(self):
        if self.file_list:
            removed_file = self.file_list.pop(self.current_index)
            QMessageBox.information(self, "File Removed", f"Removed: {removed_file}")
            self.current_index = min(self.current_index, len(self.file_list) - 1)
            self.populate_file_list()
            self.previous_button.setDisabled(self.current_index == 0)
            self.next_button.setDisabled(self.current_index >= len(self.file_list) - 1)
            self.file_list_updated.emit(self.file_list[self.current_index] if self.file_list else None)



    def filter_file_list(self, search_text):
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            item.setHidden(search_text.lower() not in item.text().lower())

    def closeEvent(self, event):
        QMessageBox.information(self, "Files Updated", f"{len(self.file_list)} file(s) remain in the list.")
        event.accept()


