from datetime import datetime
from typing import List, Dict, Tuple
import logging
from services.SecurityService import SecurityService

logger = logging.getLogger(__name__)


class DataSigner:
    def __init__(self, user_model):
        """
        Initialize the DataSigner.

        Args:
            user_model: An instance of the user model for authentication and key retrieval.
            SecurityService: An instance of the security service for hashing and signing data.
        """
        self.user_model = user_model
        self.signatures = {
            "username": None,
            "data_hash": None,
            "signature": None,
            "timestamp": None,
            "comments": None,
        }

    def sign_results(self, username: str, password: str, comments: str, data: dict) -> str:
        """
        Sign the results of the provided data.

        Args:
            username (str): The username of the signer.
            password (str): The password for the user's private key.
            comments (str): Any additional comments about the signing.
            data (dict): The data to be signed.

        Returns:
            str: The generated signature.
        """

        
        if not self.user_model:
            logger.error(f"User not found: {e}")
            return
            
        user_model = self.user_model
        
        try:
            now = datetime.now()

            # Retrieve encrypted private key
            encrypted_key = user_model.get_private_key(password)
            serialized_data = SecurityService.serialize_dict(data)

            # Hash the data and generate the signature
            data_hash = SecurityService.hash_data(serialized_data)

            signature = SecurityService.sign_hash(data_hash, encrypted_key)

            # Append results to the signatures dictionary
            self.signatures["username"]=username
            self.signatures["data_hash"]=data_hash
            self.signatures["signature"]=signature.hex()
            self.signatures["timestamp"]=now
            self.signatures["comments"]=comments

            logger.info(f"Results signed successfully by {username}.")
            return self.signatures
        except Exception as e:
            logger.error(f"Failed to sign results: {e}")
            raise ValueError("Signing failed. Please check your inputs.")


 