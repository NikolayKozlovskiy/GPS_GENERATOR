import importlib
import os
import shutil
import logging
import pyarrow as pa
import pyarrow.dataset as ds
import uuid
from pandas import DataFrame
from typing import List, Type, Optional


def delete_directory(directory: str) -> None:
    """
    Delete a directory both Empty or Non-Empty

    Args:
        directory (str): The directory path
    """

    try:
        shutil.rmtree(directory)
    except OSError as e:
        print(f"Unable to handle input directory path '{directory}': {e}")
        raise


def check_or_create_dir(directory: str) -> None:
    """
    Check if a directory exists and create it if it doesn't

    Args:
        directory (str): The directory path
    """

    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError as e:
        print(f"Unable to handle input directory path '{directory}': {e}")
        raise


def class_getter(module_path: str, class_name: str) -> Type:
    """
    Create a pecified class

    Args: 
        module_path (str): _description_
        class_name (str): _description_

    Returns: 
        Type: A class (https://stackoverflow.com/a/23198094)
    """
    module = importlib.import_module(module_path)
    class_result = getattr(module, class_name)

    return class_result


def write_df_to_parquet(df: DataFrame, base_dir: str, partition_cols: Optional[List[str]] = None) -> None:
    """
    Writes dataframe to Parquet
    If df is empty, writes a file
    When using the same path, but with data, the file gets overwritten

    Args: 
        df (DataFrame): Dataframe to write in parquet
        base_dir (str): Base directory where to write data
        partition_cols (Optional[List[str]] = None): A list of columns to use for partitioning, if None use [profile_name]
    """

    partition_cols = [
        "profile_name"] if partition_cols is None else partition_cols

    # If empty df was saved earlier, we need to delete it
    # in order to save the partitioned stuff
    if os.path.exists(base_dir) and os.path.isfile(base_dir):
        os.remove(base_dir)

    table = pa.Table.from_pandas(df)

    del (df)

    # if path exists - overwrite
    # if path is unqiue - append
    ds.write_dataset(table, base_dir=base_dir, format='parquet', partitioning=partition_cols,
                     existing_data_behavior='overwrite_or_ignore',
                     partitioning_flavor='hive', basename_template='part-{i}' + f'{uuid.uuid4().hex}.parquet')
