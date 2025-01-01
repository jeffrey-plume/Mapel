import logging
import sys
import json
import logging
import os
from datetime import datetime
import tempfile

class UserFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "username": getattr(record, "username", "System"),
            "logger_name": record.name,
            "log_level": record.levelname,
            "message": record.getMessage(),
        }
        try:
            return json.dumps(log_entry)
        except TypeError:
            log_entry["message"] = str(record.getMessage())
            return json.dumps(log_entry)

def setup_logger(name, username="System", filename=datetime.now().strftime('%Y%m%d_%H%M%S')):
    
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        log_dir = os.path.join(os.getcwd(), "logs")  # Create logs directory
        os.makedirs(log_dir, exist_ok=True)  # Ensure the directory exists
        log_path = os.path.join(log_dir, filename)

        handler = logging.FileHandler(log_path)

        # Define custom format including username
        formatter = UserFormatter(
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    logger.log_path = log_path

    return logger

class UserFilter(logging.Filter):
    def __init__(self, username="System"):
        super().__init__()
        self.username = username

    def filter(self, record):
        record.username = self.username
        return True


