import os
import importlib.util
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMessageBox
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt
from dialogs.ImageViewer import ImageViewer



class ModuleManager(QWidget):
    def __init__(self, module_name="Importer", module="__Importer", image_paths=None, index=0, parent=None):
        super().__init__(parent)
        self.image_paths = image_paths if image_paths else {}
        self.current_index = index
        self.module_name = module_name
        self.processor_class = module
        print(f"ModuleManager initialized with module: {module_name}")  # Debug log

        

    def update_current_index(self, index):
        """
        Update the current index with a new value.

        Args:
            index (int): The new current index.
        """
        if 0 <= index < len(self.image_paths):
            self.current_index = index
        else:
            QMessageBox.warning(None, "Invalid Index", "Index out of range.")

    def load_module(self, module_name):
        """
        Dynamically load a module and return the class.
    
        Args:
            module_name (str): The name of the module to load.
    
        Returns:
            class: The loaded module class.
        """
        module_dir = os.path.join(os.getcwd(), "Modules")
        module_path = os.path.join(module_dir, f"{module_name}.py")
        print(module_path)
        print(module_name)
        if not os.path.exists(module_path):
            raise ImportError(f"Module file not found: {module_path}")
    
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    
        if hasattr(module, module_name):
            return getattr(module, module_name)  # Return the loaded class
        else:
            raise ImportError(f"Class '{module_name}' not found in module '{module_name}'")


    def compute(self):
        """Process the current image using the selected module and display the results."""
        if not self.image_paths or not self.processor_class:
            QMessageBox.information(self, "No Images or Module", "No images or module to process.")
            return

        # Get the current filename
        filenames = list(self.image_paths.keys())
        if not (0 <= self.current_index < len(filenames)):
            QMessageBox.warning(self, "Invalid Index", "Current index is out of range.")
            return

        current_filename = filenames[self.current_index]

        try:
            # Instantiate the processor and process the image
            processor = self.processor_class(image_paths=self.image_paths, index=self.current_index)
            processor.compute()
            return processor
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Processing failed for image '{current_filename}': {e}")
            return

    @staticmethod
    def read_image(image_path):
        """Read an image from the given path."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File not found: {image_path}")
        from cellpose import io
        return io.imread(image_path)

