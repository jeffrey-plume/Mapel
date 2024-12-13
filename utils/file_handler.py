import mimetypes
import pandas as pd
import logging
from dialogs.ImageViewerWindow import ImageViewerWindow  # Dialog for user management


class FileHandler:
    """Utility class for handling file imports."""
    
    def __init__(self, audit_service=None):
        """Optional audit service for logging actions."""
        self.audit_service = audit_service

    def parse_file_type(self, file_path):
        """Determine the type of the file based on its MIME type."""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            raise ValueError(f"Could not determine file type for: {file_path}")
        return mime_type

    def import_image(self, file_path):
        """Import all selected files dynamically and display images if applicable."""
        if not file_path:
            QMessageBox.warning(self, "No Files", "No files selected for import.")
            return
    
        try:
            # Process files and check if there are images
            image_files = [file for file in file_path if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
            self.file_handler.process_files(image_files)
            QMessageBox.information(self, "Success", f"{len(image_files)} files processed successfully!")
    
            # Open the ImageViewerWindow if images are present
            if image_files:
                viewer_window = ImageViewerWindow(image_files, parent=self)
                viewer_window.show()
            else:
                QMessageBox.information(self, "No Images", "No image files to display.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process files: {e}")        
            print(f"Image imported: {file_path}")
        self.log_action("Image imported", file_path)

    def import_text(self, file_path):
        """Handle text file import."""
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        print(f"Text file imported: {file_path}")
        print(content)  # Replace with actual text handling logic.
        self.log_action("Text file imported", file_path)

    def import_csv(self, file_path):
        """Handle CSV file import."""
        df = pd.read_csv(file_path)
        print(f"CSV file imported: {file_path}")
        print(df.head())  # Replace with actual CSV handling logic.
        self.log_action("CSV file imported", file_path)
        return df

    def import_excel(self, file_path):
        """Handle Excel file import."""
        df = pd.read_excel(file_path)
        print(f"Excel file imported: {file_path}")
        print(df.head())  # Replace with actual Excel handling logic.
        self.log_action("Excel file imported", file_path)
        return df

    def process_files(self, file_paths):
        """Process multiple files, dynamically determining their types."""
        for file_path in file_paths:
            try:
                mime_type = self.parse_file_type(file_path)
                if mime_type.startswith("image/"):
                    self.import_image(file_path)
                elif mime_type == "text/plain":
                    self.import_text(file_path)
                elif mime_type == "text/csv":
                    self.import_csv(file_path)
                elif mime_type in {"application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}:
                    self.import_excel(file_path)
                else:
                    raise ValueError(f"Unsupported MIME type: {mime_type}")
            except Exception as e:
                self.log_error(f"Error processing file {file_path}: {e}")
                print(f"Error processing file {file_path}: {e}")

    def log_action(self, action, details):
        """Log actions to the audit trail or console."""
        if self.audit_service:
            self.audit_service.log_action("System", action, details)
        else:
            logging.info(f"{action} - {details}")

    def log_error(self, error_message):
        """Log errors to the audit trail or console."""
        if self.audit_service:
            self.audit_service.log_action("System", "Error", error_message)
        else:
            logging.error(error_message)
