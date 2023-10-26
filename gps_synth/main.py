import yaml
import sys
import os
import logging
import datetime
from typing import Any
from gps_synth.common.functions import class_getter, check_or_create_dir


def main(config_file_path: str) -> None:
    """
    Load config, setup logger, initialise GPS_Generator class and run it

    Args: 
        config_file_path (str): Relative path to config file spceified as the second parameter in terminal command
    """

    base_dir = os.getcwd()

    config = yaml.safe_load(open(str(config_file_path), "r"))
    set_up_logger(config, base_dir)

    logger = logging.getLogger(__name__)

    logger.info('Run main.py')

    GPS_GENERATOR = class_getter(
        config['INIT']['GPS_GENERATOR_PATH'], config['INIT']['GPS_GENERATOR_CLASS'])

    GPS_GENERATOR = GPS_GENERATOR(config, base_dir)

    GPS_GENERATOR.run()


def set_up_logger(config: Any, base_dir: str) -> None:
    """
    The function creates a log_dir folder (by appending sub-path to the base/parent path) to store logs 
    and sets up a logger

    Args: 
        config (Any): YAML object with all specified config params
        base_dir (str): The string path to GPS_Generator folder
    """

    log_dir = os.path.join(base_dir, config['LOGGING']['LOG_DIR'])
    check_or_create_dir(log_dir)

    log_file_path = os.path.join(log_dir,
                                 f"{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}.log")
    logging.getLogger(__name__)
    logging.basicConfig(
        format=config['LOGGING']['FORMAT'],
        handlers=[
            logging.FileHandler(log_file_path, 'w'),
            logging.StreamHandler()
        ],
        datefmt=config['LOGGING']['DATEFMT'],
        level=config['LOGGING']['LEVEL']
    )


if __name__ == '__main__':
    main(sys.argv[1])
