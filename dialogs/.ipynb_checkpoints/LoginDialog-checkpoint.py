from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QPushButton, QComboBox
)
import sqlite3
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives import padding as sym_padding
from base64 import b64decode, b64encode
import secrets


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Login")
        self.setGeometry(150, 150, 300, 250)  # Adjust size to fit all widgets

        # Username and password inputs
        self.username_label = QLabel("Username:", self)
        self.username_input = QLineEdit(self)

        self.password_label = QLabel("Password:", self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)

        # Reason dropdown
        self.reason_label = QLabel("Reason:", self)
        self.reason_dropdown = QComboBox(self)
        self.reason_dropdown.addItems(["User Login", "File Created", "File Completed", "File Reviewed"])

        # Login button
        self.login_button = QPushButton("Sign", self)
        self.login_button.clicked.connect(self.handle_login)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.reason_label)
        layout.addWidget(self.reason_dropdown)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

        # Limit login attempts
        self.login_attempts = 0
        self.max_attempts = 3

    def handle_login(self):
        # Get username and password
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # Increment login attempts
        self.login_attempts += 1

        # Retrieve the salt from the database
        salt = self.get_salt(username)

        if not salt:
            QMessageBox.warning(self, "Error", "Invalid username or password")
            self.password_input.clear()
            return

        # Hash the password with the retrieved salt using PBKDF2
        password_hash = self.hash_password(password, salt)

        # Check credentials in the database
        if self.verify_credentials(username, password_hash):
            self.current_user = username
            self.action = self.reason_dropdown.currentText()
            data_to_sign = f'Signed by {username} \n{datetime.now():%Y-%m-%d %H:%M:%S} \nReason: {self.action}'


            # Retrieve and decrypt the user's private key
            private_key = self.retrieve_and_decrypt_private_key(username, salt)
            if private_key:
                # Sign data using the private key
                
                signature = self.sign_data(private_key, data_to_sign.encode())

                if signature:
                    QMessageBox.information(self, "Digital Signature", f'{data_to_sign} \n{signature.hex()}')
                    self.info = signature.hex()
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create a digital signature.")
            else:
                QMessageBox.warning(self, "Error", "Failed to retrieve or decrypt private key.")
        else:

            QMessageBox.warning(self, "Error", "Invalid username or password")
            self.password_input.clear()  # Clear the password field after a failed attempt

            # Check if max attempts reached
            if self.login_attempts >= self.max_attempts:
                QMessageBox.critical(self, "Error", "Maximum login attempts reached. Please try again later.")
                self.reject()

    def hash_password(self, password, salt):
        # Hash the password with the provided salt using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
            backend=default_backend()
        )
        return b64encode(kdf.derive(password.encode())).decode()

    def get_salt(self, username):
        try:
            # Connect to the SQLite database to retrieve the salt for the given username
            conn = sqlite3.connect('user_credentials.db')
            cursor = conn.cursor()
            cursor.execute('SELECT salt FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return result[0]
            else:
                return None
        except sqlite3.Error as e:

            QMessageBox.critical(self, "Database Error", "An error occurred while accessing the database.")
            return None

    def verify_credentials(self, username, password_hash):
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect('user_credentials.db')
            cursor = conn.cursor()

            # Query to check if the username and password hash match
            cursor.execute('''
            SELECT * FROM users WHERE username = ? AND password_hash = ?
            ''', (username, password_hash))
            result = cursor.fetchone()

            conn.close()
            return result is not None  # If a matching record is found, return True
        except sqlite3.Error as e:

            QMessageBox.critical(self, "Database Error", "An error occurred while accessing the database.")
            return False

    def retrieve_and_decrypt_private_key(self, username, salt):
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect('user_credentials.db')
            cursor = conn.cursor()
            cursor.execute('SELECT encrypted_private_key FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            conn.close()

            if result:
                encrypted_private_key = b64decode(result[0])
                master_key = self.read_master_key('./dist/main/masterKey.bin')
                return self.decrypt_private_key(encrypted_private_key, master_key, salt.encode())
            else:
                return None
        except sqlite3.Error as e:

            QMessageBox.critical(self, "Database Error", "An error occurred while accessing the database.")
            return None

    def decrypt_private_key(self, encrypted_private_key, master_key, salt):
        try:
            iv = encrypted_private_key[:16]
            encrypted_data = encrypted_private_key[16:]

            # Derive the encryption key from the master key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,  # Ensure this salt matches the one used during encryption
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(master_key)

            # Decrypt the private key using AES-CBC
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_private_key = decryptor.update(encrypted_data) + decryptor.finalize()

            # Remove padding
            unpadder = sym_padding.PKCS7(algorithms.AES.block_size).unpadder()
            private_key_pem = unpadder.update(padded_private_key) + unpadder.finalize()

            # Load the private key object from the PEM data
            return serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=default_backend()
            )
        except Exception as e:
            return None

    def sign_data(self, private_key, data):
        try:
            signature = private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return signature
        except Exception as e:

            return None

    def read_master_key(self, file_path):
        with open(file_path, 'rb') as key_file:
            master_key = key_file.read()
        return master_key

