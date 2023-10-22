import importlib
import os
import logging
from pandas import DataFrame
from geopandas import GeoDataFrame
from typing import NoReturn

logger = logging.getLogger(__name__)


def check_or_create_dir(directory: str) -> NoReturn:
    """
    Checks if a directory exists and creates it if it doesn't.

    Args:
        directory (str): The directory path.
        parent_directory (str): The parent directory path. Defaults to the current working directory.

    Returns:
        bool: True if the directory exists or was successfully created, False otherwise.
    """

    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError as e:
        print(f"Failed to create directory '{directory}': {e}")
        raise


def class_getter(module_path: str, class_name: str) -> __build_class__:
    module = importlib.import_module(module_path)
    class_result = getattr(module, class_name)

    return class_result


def write_data(data: DataFrame | GeoDataFrame, output_path: str, geo: bool = False):
    if geo == True:
        data.to_file(output_path, driver="GPKG")
    else:
        data.to_csv(output_path, sep=',', index=False)

    logger.info(f"Data written to: {output_path}")
