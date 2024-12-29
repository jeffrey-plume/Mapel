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
            "username": [],
            "data_hash": [],
            "signature": [],
            "date": [],
            "time": [],
            "comments": [],
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
            print(encrypted_key)
            serialized_data = SecurityService.serialize_dict(data)

            # Hash the data and generate the signature
            data_hash = SecurityService.hash_data(serialized_data)
            print(data_hash)

            signature = SecurityService.sign_hash(data_hash, encrypted_key)
            print(signature)

            # Append results to the signatures dictionary
            self.signatures["username"].append(username)
            self.signatures["data_hash"].append(data_hash)
            self.signatures["signature"].append(signature)
            self.signatures["date"].append(now.strftime("%Y-%m-%d"))
            self.signatures["time"].append(now.strftime("%H:%M:%S"))
            self.signatures["comments"].append(comments)

            logger.info(f"Results signed successfully by {username}.")
            return signature
        except Exception as e:
            logger.error(f"Failed to sign results: {e}")
            raise ValueError("Signing failed. Please check your inputs.")


    def prepare_signatures_data(self) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Prepare the signatures data for display.

        Returns:
            Tuple[List[Dict[str, str]], List[str]]:
                - A list of dictionaries, where each dict is a row for the table.
                - A list of column headers for the table.
        """
        try:
            # Prepare data rows for the table
            table_data = [
                {
                    "Username": self.signatures["username"][i],
                    "Data Hash": self.signatures["data_hash"][i],
                    "Signature": self.signatures["signature"][i],
                    "Date": self.signatures["date"][i],
                    "Time": self.signatures["time"][i],
                    "Comments": self.signatures["comments"][i],
                }
                for i in range(len(self.signatures["signature"]))
            ]

            # Define the column headers
            column_headers = ["Username", "Data Hash", "Signature", "Date", "Time", "Comments"]

            return table_data, column_headers
        except Exception as e:
            logger.error(f"Failed to prepare signatures data: {e}")
            raise ValueError("Failed to prepare signatures data.")
