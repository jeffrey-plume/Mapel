from PyQt5.QtWidgets import QDialog, QMessageBox

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
