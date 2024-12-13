import sys
import os
import sqlite3
import secrets
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox
)
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding
from base64 import b64encode

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super(RegisterDialog, self).__init__(parent)
        self.setWindowTitle("Register New User")
        self.setGeometry(150, 150, 300, 200)

        # Username and password inputs
        self.username_label = QLabel("Username:", self)
        self.username_input = QLineEdit(self)

        self.password_label = QLabel("Password:", self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)

        # Register button
        self.register_button = QPushButton("Register", self)
        self.register_button.clicked.connect(self.handle_registration)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.register_button)
        self.setLayout(layout)

    def generate_rsa_key_pair(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key

    def create_salt(self):
        return secrets.token_hex(16)  # Generates a 32-character hex string

    def encrypt_private_key(self, private_key_pem, master_key, salt):
        # Derive an encryption key from the master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,  # Use a unique, random salt
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(master_key)
        iv = secrets.token_bytes(16)  # Generate a random 16-byte IV for AES

        # Encrypt the private key using AES-CBC
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Add padding to the private key
        padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
        padded_private_key = padder.update(private_key_pem) + padder.finalize()

        encrypted_private_key = encryptor.update(padded_private_key) + encryptor.finalize()

        # Store the IV with the encrypted private key
        return b64encode(iv + encrypted_private_key).decode('utf-8')

    def handle_registration(self):
        # Get username and password
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password cannot be empty.")
            return

        try:
            # Open database connection
            conn = sqlite3.connect('user_credentials.db')
            cursor = conn.cursor()

            # Check if the user already exists
            cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Error", "User already exists")
                return

            # Generate RSA key pair
            private_key, public_key = self.generate_rsa_key_pair()

            # Serialize keys
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Load master key from file
            with open("./dist/main/masterKey.bin", 'rb') as key_file:
                master_key = key_file.read()

            # Create a unique salt for this user
            salt = self.create_salt()

            # Encrypt the private key with a master key and user's salt
            encrypted_private_key = self.encrypt_private_key(private_key_pem, master_key, salt.encode())

            # Hash the password with the salt using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,
                backend=default_backend()
            )
            password_hash = b64encode(kdf.derive(password.encode())).decode('utf-8')

            # Store user in the database
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, encrypted_private_key, public_key)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, salt, encrypted_private_key, public_key_pem))

            conn.commit()
            QMessageBox.information(self, "Success", "User registered successfully")
            self.accept()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
        finally:
            if conn:
                conn.close()  # Ensure the connection is closed
