import os
import secrets
import uuid
import hashlib
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
import json

class SecurityService:
    """Service for encryption, decryption, and user credential management."""

    @staticmethod
    def generate_rsa_key_pair():
        """Generate a new RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key


    @staticmethod
    def hash_password(password: str, salt: bytes) -> str:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return b64encode(kdf.derive(password.encode())).decode()


    @staticmethod
    def hash_data(data: dict) -> str:
        """
        Hash the input data using SHA-256.

        Args:
            data (dict): The serialized data to hash.

        Returns:
            str: The SHA-256 hash as a hexadecimal string.
        """
        try:
            # Serialize the data dictionary
            serialized = json.dumps(SecurityService.serialize_dict(data), sort_keys=True)
            
            # Compute and return the SHA-256 hash
            return hashlib.sha256(serialized.encode('utf-8')).hexdigest()
        except Exception as e:
            raise ValueError("An error occurred during encryption.")



    @staticmethod
    def sign_hash(hash_value: str, private_key: rsa.RSAPrivateKey) -> bytes:
        """
        Sign the SHA-256 hash using the provided private key.
        """
        try:
            return private_key.sign(
                hash_value.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except Exception as e:
            raise ValueError("An error occurred during encryption.")


    @staticmethod
    def generate_salt(nchar=16) -> bytes:
        """Generate a unique salt."""
        return secrets.token_bytes(nchar)


    @staticmethod
    def decrypt_with_password(encrypted_data: bytes, password: str) -> bytes:
        """Decrypt data using a password-derived key."""
        salt = encrypted_data[:16]  # Extract the salt
        iv = encrypted_data[16:32]  # Extract the IV
        ciphertext = encrypted_data[32:]  # Extract the ciphertext

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
    
        # Decrypt and remove padding
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = PKCS7(algorithms.AES.block_size).unpadder()
        return unpadder.update(padded_data) + unpadder.finalize()

    @staticmethod
    def decrypt_private_key(encrypted_private_key: bytes, password: str) -> rsa.RSAPrivateKey:
        """Decrypt an RSA private key with a password."""
        decrypted_private_bytes = SecurityService.decrypt_with_password(encrypted_private_key, password)
        return serialization.load_pem_private_key(
            decrypted_private_bytes,
            password=None,
            backend=default_backend()
        )

    @staticmethod
    def serialize_public_key(public_key: rsa.RSAPublicKey) -> str:
        """Serialize a public key to PEM format."""
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    
    @staticmethod
    def deserialize_public_key(public_key_pem: str) -> rsa.RSAPublicKey:
        """Deserialize a PEM-encoded public key."""
        return serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )

    

    @staticmethod
    def encrypt_with_password(data: bytes, password: str) -> bytes:
        """Encrypt data using a password-derived key."""
        salt = SecurityService.generate_salt()  # Generate a unique salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        iv = secrets.token_bytes(16)  # Generate a unique IV
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
    
        # Apply PKCS7 padding
        padder = PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data) + padder.finalize()
    
        # Encrypt and return salt + iv + ciphertext
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return salt + iv + ciphertext


    @staticmethod
    def encrypt_private_key(private_key, password: str) -> bytes:
        """Encrypt an RSA private key with a password."""
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return SecurityService.encrypt_with_password(private_bytes, password)


        
    @staticmethod  
    def serialize_dict(data_dict: dict) -> dict:
        """
        Recursively serialize a dictionary, converting unsupported data types.
        
        Args:
            data_dict (dict): Dictionary to serialize.
        
        Returns:
            dict: Serialized dictionary with JSON-compatible data types.
        """
        serialized = {}
        for key, value in data_dict.items():
            if isinstance(value, dict):
                # Recursively handle nested dictionaries
                serialized[key] = SecurityService.serialize_dict(value)
            elif isinstance(value, (list, tuple)):  # Handle list or tuple
                serialized[key] = list(value)
            else:
                # Convert unsupported types to strings
                serialized[key] = value
        return serialized


    @staticmethod
    def validate_inputs(user: str, password: str, confirm_password= None):
        """
        Validate the username and password inputs.
    
        Args:
            username (str): The username to validate.
            password (str): The password to validate.
            confirm_password (Optional[str]): Optional. Confirm password to validate against.
    
        Returns:
            Tuple[bool, Optional[str]]: A tuple where the first value is True if inputs are valid,
                                        and the second value is an error message if invalid.
        """
        # Check for empty fields
        if not user or not password or (confirm_password is not None and not confirm_password):
            return False, "All fields are required."
    
        # Validate username length and spaces
        if len(user) < 3:
            return False, "Username must be at least 3 characters long."
        if " " in user:
            return False, "Username cannot contain spaces."
    
        # Validate password length and spaces
        if len(password) < 6:
            return False, "Password must be at least 6 characters long."
        if " " in password:
            return False, "Password cannot contain spaces."
    
        # Check password confirmation if provided
        if confirm_password is not None and password != confirm_password:
            return False, "Passwords do not match."
    
        return True, None

    @staticmethod
    def validate_password(password):
        """Validate the strength of the new password."""
        if len(password) < 8:
            return "Password must be at least 8 characters long."
        if not any(char.isdigit() for char in password):
            return "Password must contain at least one digit."
        if not any(char.isupper() for char in password):
            return "Password must contain at least one uppercase letter."
        if not any(char.islower() for char in password):
            return "Password must contain at least one lowercase letter."
        if not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/~`" for char in password):
            return "Password must contain at least one special character."
        return None


    
    @staticmethod
    def verify_signature(signature: bytes, hash_value: str, public_key: rsa.RSAPublicKey) -> bool:
        try:
            public_key.verify(
                signature,
                hash_value.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False
