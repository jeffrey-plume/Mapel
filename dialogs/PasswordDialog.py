from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox, QTextEdit

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Password and Comments")
        self.setFixedSize(300, 200)

        self.password = None
        self.comments = None

        # UI Elements
        self.label_password = QLabel("Enter your password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.label_comments = QLabel("Enter comments (optional):")
        self.comments_input = QTextEdit()

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.handle_submit)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label_password)
        layout.addWidget(self.password_input)
        layout.addWidget(self.label_comments)
        layout.addWidget(self.comments_input)
        layout.addWidget(self.submit_button)
        self.setLayout(layout)

    def handle_submit(self):
        self.password = self.password_input.text().strip()
        self.comments = self.comments_input.toPlainText().strip()

        if not self.password:
            QMessageBox.warning(self, "Error", "Password cannot be empty.")
        else:
            self.accept()  # Close the dialog with success
