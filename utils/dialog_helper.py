from PyQt5.QtWidgets import QDialog, QMessageBox
from typing import Tuple

class DialogHelper:
    @staticmethod
    def show_dialog(dialog_class, *args, **kwargs):
        """
        Helper function to open a QDialog and return the result.
        
        Args:
            dialog_class: The QDialog class to open.
            *args, **kwargs: Arguments to pass to the dialog class.
        
        Returns:
            bool: True if the dialog was accepted, False otherwise.
        """
        dialog = dialog_class(*args, **kwargs)
        return dialog.exec_() == QDialog.Accepted

    @staticmethod
    def show_error(parent, title, message):
        """Helper to display an error message."""
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def show_info(parent, title, message):
        """Helper to display an informational message."""
        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_warning(parent, title, message):
        """Helper to display a warning message."""
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_question(parent, title, message):
        """Helper to display a question dialog."""
        return QMessageBox.question(parent, title, message, 
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        
    def notify(self, message: str, level: str = "info"):
        """Centralized notification system."""
        if level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        # Extend to support other notification mechanisms (e.g., QMessageBox or CLI)

    def _execute_query(self, query: str, params: Tuple = (), fetch_one=False, fetch_all=False):
        try:
            with self.conn as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Database error during query execution. Query: {query}, Params: {params}, Error: {e}")
            raise

