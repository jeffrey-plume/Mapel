import os
import importlib.util
import h5py 
import json

def load_module(module_name, module_dir):
    """
    Dynamically load a module and return the class.

    Args:
        module_name (str): The name of the module to load.
        module_dir (str): Path to the directory containing modules.

    Returns:
        class: The loaded module class.
    """
    module_path = os.path.join(module_dir, f"{module_name}.py")
    if not os.path.exists(module_path):
        raise ImportError(f"Module file not found: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, module_name):
        return getattr(module, module_name)  # Return the loaded class
    else:
        raise ImportError(f"Class '{module_name}' not found in module '{module_name}'")


def save_dict_to_hdf5(data_dict, h5_group):
    for key, value in data_dict.items():
        if value is None:
            h5_group.create_dataset(str(key), data="None")
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
                value = value.decode('utf-8')
            data_dict[key] = None if value == "None" else value.strip('"').replace('\\\\', '\\')
            print(f"Key: {key}, Value: {value}")  # Debugging output

    return data_dict



