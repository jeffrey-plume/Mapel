import inspect
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal, Qt


class ControllerDialog(QWidget):
    param_changed = pyqtSignal(str, int)  # Signal to notify about parameter changes (param name, new value)

    def __init__(self, instance, parent=None):
        super().__init__(parent)


        self.instance = instance

        # Extract unique parameters from the __init__ method
        self.unique_params = self.get_unique_params()

        # Layout for controls
        self.layout = QVBoxLayout(self)
        self.spin_boxes = {}

        # Create a spin box for each unique parameter
        for param, value in self.unique_params.items():
                    
            self.setWindowTitle(param)  # Set initial title
            self.setGeometry(500, 500, 50, 100)

            self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.CustomizeWindowHint)
            #label = QLabel(f"{param}:")
            spin_box = QSpinBox()
            spin_box.setRange(0, 1000)  # Adjust range as needed
            spin_box.setValue(value)
            spin_box.valueChanged.connect(lambda x, p=param: self.emit_param_changed(p, x))

            #self.layout.addWidget(label)
            self.layout.addWidget(spin_box)
            self.spin_boxes[param] = spin_box

        self.setLayout(self.layout)

    def get_unique_params(self):
        """Get parameters unique to the subclass __init__ method."""
        # Get parameter names for the subclass __init__
        subclass_params = inspect.signature(self.instance.__class__.__init__).parameters
        subclass_param_names = set(subclass_params.keys())

        # Get parameter names for the parent class __init__
        parent_params = inspect.signature(super(self.instance.__class__, self.instance).__init__).parameters
        parent_param_names = set(parent_params.keys())

        # Identify unique parameters
        unique_param_names = subclass_param_names - parent_param_names

        # Return a dictionary of unique parameters with their current values
        return {
            param: getattr(self.instance, param, subclass_params[param].default)
            for param in unique_param_names if param != "self"
        }

    def emit_param_changed(self, param, value):
        """Emit the param_changed signal and update the instance."""
        setattr(self.instance, param, value)
        self.param_changed.emit(param, value)
