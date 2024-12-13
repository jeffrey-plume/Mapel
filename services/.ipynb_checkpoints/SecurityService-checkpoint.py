import os
import json
import secrets
import sqlite3
import base64
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives import hashes, padding as sym_padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from PyQt5.QtWidgets import QMessageBox
import uuid
import hashlib  # Import added here for MAC address hashing

class SecurityService:
    """Unified service for encryption, decryption, and user management."""

    def __init__(self, db_path='user_credentials.db'):
        self.db_path = db_path

    # ---------------- User Management and Key Operations ------------------
    def generate_rsa_key_pair(self):
        """Generate an RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return private_key, private_key.public_key()

    def encrypt_private_key(self, private_key_pem, secure_handler, salt):
        """Encrypt the private key using AES-CBC."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(secure_handler)
        iv = secrets.token_bytes(16)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
        padded_private_key = padder.update(private_key_pem) + padder.finalize()

        encrypted_private_key = encryptor.update(padded_private_key) + encryptor.finalize()
        return b64encode(iv + encrypted_private_key).decode('utf-8')

    def generate_master_key(self):
        """Generate a new random 32-byte master key."""
        return os.urandom(32)

    def decrypt_master_key(self, master_password):
        """Decrypt the master key using the provided password."""
        try:
            with open(self.master_key_file, "rb") as f:
                data = f.read()

            # Extract salt, IV, and encrypted master key from the file
            salt, iv, encrypted_master_key = data[:16], data[16:32], data[32:]

            # Derive decryption key from the master password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            decryption_key = kdf.derive(master_password.encode())

            # Set up AES decryption in CBC mode
            cipher = Cipher(algorithms.AES(decryption_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()

            # Decrypt the master key
            decrypted_data = decryptor.update(encrypted_master_key) + decryptor.finalize()

            # Remove PKCS7 padding
            unpadder = sym_padding.PKCS7(algorithms.AES.block_size).unpadder()
            master_key = unpadder.update(decrypted_data) + unpadder.finalize()

            return master_key

        except Exception as e:
            print(f"Decryption failed: {e}")
            return None


    def register_user(self, username, password, secure_handler):
        """Register a new user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                raise ValueError("User already exists.")

            private_key, public_key = self.generate_rsa_key_pair()
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            salt = secrets.token_hex(16)
            encrypted_private_key = self.encrypt_private_key(private_key_pem, secure_handler, salt)
            password_hash = self.hash_password(password, salt)

            cursor.execute(
                '''
                INSERT INTO users (username, password_hash, salt, encrypted_private_key, public_key)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (username, password_hash, salt, encrypted_private_key, public_key_pem)
            )
            conn.commit()
        finally:
            conn.close()

    # ---------------- Encryption and Decryption Methods ------------------

    def encrypt_file(self, data, public_key, output_file, parent=None):
        """Encrypt a dictionary and save it as a JSON file."""
        try:
            aes_key = os.urandom(32)
            iv = os.urandom(16)

            encrypted_aes_key = public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            plaintext = json.dumps(data).encode('utf-8')
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()

            encrypted_data = {
                "iv": b64encode(iv).decode('utf-8'),
                "tag": b64encode(encryptor.tag).decode('utf-8'),
                "encrypted_aes_key": b64encode(encrypted_aes_key).decode('utf-8'),
                "ciphertext": b64encode(ciphertext).decode('utf-8')
            }

            with open(output_file, 'w') as f:
                json.dump(encrypted_data, f)

            QMessageBox.information(parent, "Success", "File encrypted successfully.")
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Failed to encrypt the file: {e}")

    def decrypt_file(self, input_file, private_key, parent=None):
        """Decrypt a JSON file."""
        try:
            # Read the encrypted data from the JSON file
            with open(input_file, 'r') as f:
                encrypted_data = json.load(f)

            # Decode the encrypted data
            iv = b64decode(encrypted_data["iv"])
            tag = b64decode(encrypted_data["tag"])
            encrypted_aes_key = b64decode(encrypted_data["encrypted_aes_key"])
            ciphertext = b64decode(encrypted_data["ciphertext"])

            # Decrypt the AES key using the private key
            aes_key = private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Decrypt the ciphertext
            cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Convert decrypted bytes back to dictionary
            decrypted_data = json.loads(plaintext.decode('utf-8'))

            QMessageBox.information(parent, "Success", "File decrypted successfully.")
            return decrypted_data
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Failed to decrypt the file: {e}")
            return None

    # ----------------- Utility Methods -----------------


    def hash_password(self, password, salt):
        """Hash a password using PBKDF2 with SHA-256."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
            backend=default_backend()
        )
        return b64encode(kdf.derive(password.encode())).decode('utf-8')