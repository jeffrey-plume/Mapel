from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QAction, QMenu, QMessageBox
import os
from utils.file_utils import load_module
from dialogs.ImageViewer import ImageViewer
import logging

class ModuleManager(QObject):
    module_selected = pyqtSignal(str)  # Signal to notify when a module is selected

    def __init__(self, logger: logging.Logger, menu: QMenu, loaded_modules: dict = None):
        """
        Initialize the ModuleManager.

        Args:
            logger (logging.Logger): Logger instance.
            menu (QMenu): The 'Module' submenu to populate with options.
            loaded_modules (dict): Dictionary to store loaded modules (optional).
        """
        super().__init__()
        self.logger = logger
        self.module_menu = menu
        self.loaded_modules = loaded_modules or {}
        self.options = {}

    def add_checkable_option(self, option_name: str):
        """Add a checkable option to the 'Module' submenu."""
        action = QAction(option_name, self.module_menu)
        action.setCheckable(True)
        action.triggered.connect(lambda checked, opt=option_name: self.on_option_selected(opt, checked))
        self.module_menu.addAction(action)
        self.options[option_name] = action

    def load_module_options(self, module_dir: str):
        """Load available modules from the specified folder."""
        if not os.path.isdir(module_dir):
            QMessageBox.critical(None, "Error", f"{module_dir} is not a valid directory.")
            self.logger.error("%s is not a valid directory.", module_dir)
            return

        self.module_menu.clear()
        self.options.clear()
        self.loaded_modules.clear()

        # Register built-in modules
        self.loaded_modules['Imager'] = ImageViewer

        try:
            for file_name in os.listdir(module_dir):
                if file_name.endswith(".py") and not file_name.startswith("__"):
                    module_name = file_name[:-3]
                    try:
                        self.loaded_modules[module_name] = load_module(module_name, module_dir)
                        self.add_checkable_option(module_name)
                    except Exception as e:
                        QMessageBox.warning(None, "Module Load Error", f"Failed to load module '{module_name}': {e}")
                        self.logger.error("Failed to load module '%s': %s", module_name, str(e))
        except OSError as e:
            QMessageBox.critical(None, "Error", f"Unable to access module directory: {e}")
            self.logger.error("Unable to access module directory: %s", e)

    def on_option_selected(self, selected_option: str = None, checked: bool = False):
        """Handle the selection of a module option."""
        if not checked or not selected_option:
            return
        self.logger.info(f"Selected module: {selected_option}")
        for option_name, action in self.options.items():
            action.setChecked(option_name == selected_option)
        self.module_selected.emit(selected_option)


