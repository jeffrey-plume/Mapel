import os
import importlib.util
import h5py 
import json
import numpy as np
from datetime import datetime
import importlib.util
import os

def load_module(module_name, module_dir):
    """
    Dynamically load a module from a directory.

    Args:
        module_name (str): Name of the module to load.
        module_dir (str): Path to the directory containing the module.

    Returns:
        module: Loaded module class.
    """
    module_path = os.path.join(module_dir, f"{module_name}.py")
    if not os.path.exists(module_path):
        raise ImportError(f"Module file not found: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, module_name):
        return getattr(module, module_name)
    raise ImportError(f"Class '{module_name}' not found in module '{module_name}'")



def save_dict_to_hdf5(data_dict, h5_group):
    for key, value in data_dict.items():
        if value is None:
            h5_group.create_dataset(str(key), data="None")
        elif isinstance(value, np.ndarray):
            h5_group.create_dataset(str(key), data=value)
        elif isinstance(value, datetime):
            h5_group.create_dataset(str(key), data=str(value))
        elif isinstance(value, dict):
            subgroup = h5_group.create_group(str(key))
            save_dict_to_hdf5(value, subgroup)
        else:
            h5_group.create_dataset(str(key), data=json.dumps(value))

def load_dict_from_hdf5(h5_group):
    data_dict = {}
    for key, item in h5_group.items():
        if isinstance(item, h5py.Group):
            data_dict[key] = load_dict_from_hdf5(item)
        else:
            value = item[()]
            if isinstance(value, bytes):
                value = value.decode('utf-8').strip('"').replace('\\\\', '\\')
            data_dict[key] = None if value == "None" else value

    return data_dict


import os
from dialogs.ImageViewer import ImageViewer

def load_module_options():
    """Load available modules from the 'Modules' folder."""
    module_dir = os.path("Modules")
    if not os.path.exists(module_dir):
        return

    loaded_modules = {}

    loaded_modules['Imager'] = ImageViewer
    for file_name in os.listdir(module_dir):
        if file_name.endswith(".py") and not file_name.startswith("__"):
            module_name = file_name[:-3]
            try:
                loaded_modules[module_name] = load_module(module_name, module_dir)
            except Exception as e:
                return

    return loaded_modules

