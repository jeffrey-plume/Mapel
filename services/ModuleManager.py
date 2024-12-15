import os
import importlib.util
from PyQt5.QtWidgets import QAction


class ModuleManager:
    """Manages loading and running of modules from the 'Modules' directory."""

    def __init__(self):
        """
        Initialize the ModuleManager.

        Args:
            module_menu (QMenu): The menu where modules will be displayed.
            status_label (QLabel): Label to display selected module status.
            run_action (QAction): Action to enable/disable the 'Run' option.
            run_button_action (QAction): Button to enable/disable the 'Run' button.
        """
        self.status_label = "No Module Selected"
        self.options = {}
        self.selected_option = None

    def load_module_options(self):
        """Load available modules from the 'Modules' folder."""
        module_dir = os.path.join(os.getcwd(), "Modules")  # Adjust path as needed
        if not os.path.exists(module_dir):
            raise FileNotFoundError(f"Module folder not found: {module_dir}")

        # Clear existing options
        self.options = {}

        # Scan for Python files in the module directory
        for file_name in os.listdir(module_dir):
            if file_name.endswith(".py") and not file_name.startswith("__"):  # Exclude __init__.py
                self.options[file_name[:-3]] = file_name[:-3]  # Remove .py extension
        return(self.options)

    def load_module(self, module_name):
        """Load the specified module dynamically."""
        module_dir = os.path.join(os.getcwd(), "Modules")
        module_path = os.path.join(module_dir, f"{module_name}.py")

        if not os.path.exists(module_path):
            raise ImportError(f"Module file not found: {module_path}")

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, module_name):
            raise ImportError(f"Class '{module_name}' not found in module '{module_name}'.")

        return getattr(module, module_name)

