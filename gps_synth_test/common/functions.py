import importlib
import os
import logging

logger = logging.getLogger(__name__)


def check_or_create_dir(directory):
    """
    Checks if a directory exists and creates it if it doesn't.

    Args:
        directory (str): The directory path.
        parent_directory (str): The parent directory path. Defaults to the current working directory.

    Returns:
        bool: True if the directory exists or was successfully created, False otherwise.
    """

    if os.path.exists(directory):
        return True
    else:
        try:
            os.makedirs(directory)
            return True
        except OSError as e:
            print(f"Failed to create directory '{directory}': {e}")
            return False

def class_getter(module_path: str, class_name: str) -> __build_class__: 
    module = importlib.import_module(module_path)
    class_result = getattr(module, class_name)

    return class_result

def write_data(data, output_path, geo = False): 
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if geo == True:
        data.to_file(output_path, driver = "GPKG")
    data.to_csv(output_path, sep = ',', index=False)

    logger.info(f"Data written to: {output_path}")

