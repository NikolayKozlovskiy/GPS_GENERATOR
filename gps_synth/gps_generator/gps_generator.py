import logging
import os
import uuid
from typing import Any, Dict, List, Optional

import geopandas as gpd
import pandas as pd
from pyproj import CRS

from gps_synth.common.abs_user import User
from gps_synth.common.columns import ColNames
from gps_synth.common.functions import (
    check_or_create_dir,
    class_getter,
    delete_directory,
    write_df_to_parquet,
)
from gps_synth.network.network import Network

crs_4326 = CRS.from_epsg(4326)


class GPS_Generator:
    def __init__(self, config, base_dir):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.network_dictionary = {}
        self.users_dictionary = {}
        # to connect users/profiles with their corresponding network
        self.users_network_dict = {}

        for output in self.config["OUTPUTS"]:
            output_path = os.path.join(base_dir, self.config["OUTPUTS"][output]["PATH"])
            if self.config["DO_CLEAR_OUTPUT"] is True:
                delete_directory(output_path)
            check_or_create_dir(output_path)
            self.config["OUTPUTS"][output]["PATH"] = output_path

    def create_network(self, profile_network_config: Any) -> Network:
        """
        Initialise Network class and run it

        Args:
            profile_network_config (Any): YAML object with config params regarding network

        Returns:
            Network: Instance of Network class with completed run method
        """

        network_class = class_getter(
            profile_network_config["NETWORK_MODULE_PATH"],
            profile_network_config["NETWORK_CLASS"],
        )

        network = network_class(profile_network_config)

        network.run()

        return network

    def generate_users(self, network: Network, profile_user_config: Any) -> List[User]:
        """
        Initialise User class and run it as many times as specified in NUM_USERS config param.
        Store instances in a list

        Args:
            network (Network): An instance of Netwrok class to use for choosing anchoir points of a user
            profile_user_config (Any): YAML object with config params regarding users

        Returns:
            List[User]: list of instances of User class with completed run method
        """
        users_array = []

        user_class = class_getter(
            profile_user_config["USER_MODULE_PATH"], profile_user_config["USER_CLASS"]
        )

        for _ in range(profile_user_config["NUM_USERS"]):
            # ensure uniqueness of user ids in case of appending parquets
            user_id = uuid.uuid4().hex
            new_user = user_class(user_id, network, profile_user_config)
            users_array.append(new_user)

        return users_array

    def execute_method_for_users(
        self, users: List[User], method_name: str
    ) -> List[User]:
        """
        Loop through users and execute specified instance method

        Args:
            users (List[User]): List of User instances
            method_name (str): name of a method you want to execute

        Returns:
            List[User]: List of User instances with executed method
        """

        for user in users:
            method = getattr(user, method_name)
            method()
        return users

    def output_gps(
        self,
        users_dictionary: Dict[str, List[User]],
        gps_output_folder_path: str,
        partition_columns: Optional[List[str]] = None,
        existing_data_behavior: Optional[str] = None,
    ) -> None:
        """
        Write users' synth GPS data with stated output schema for each profile

        Args:
            users_dictionary (Dict[str, List[User]]): A dictionary where key is a name of a profile and a value is a list of User instances belonging to this profile
            gps_output_folder_path (str): A path to a folder to store GPS results (created as by appending sub-path to the base/parent path)
            partition_columns (List[str]): Columsn to use for partitioning
            existing_data_behavior (str): Controls how the dataset will handle data that already exists in the destination
        """

        self.logger.info("Writing GPS data")
        gps_data = []
        gps_data_df = pd.DataFrame(
            columns=[
                ColNames.user_id,
                ColNames.timestamp,
                ColNames.lon,
                ColNames.lat,
                ColNames.profile_name,
            ]
        )

        for profile_name, users in users_dictionary.items():
            for user in users:
                gps_data += user.data_array
            gps_data_profile_df = pd.DataFrame(
                gps_data,
                columns=[
                    ColNames.user_id,
                    ColNames.timestamp,
                    ColNames.lon,
                    ColNames.lat,
                ],
            ).sort_values(by=[ColNames.user_id, ColNames.timestamp])
            # pylint: disable=unsupported-assignment-operation
            gps_data_profile_df[ColNames.profile_name] = profile_name

            # if you borther with pd.concat FutureWarning, here is a solution
            # https://stackoverflow.com/questions/77254777/alternative-to-concat-of-empty-dataframe-now-that-it-is-being-deprecated
            gps_data_df = pd.concat(
                [gps_data_df, gps_data_profile_df], ignore_index=True
            )

        write_df_to_parquet(
            gps_data_df,
            gps_output_folder_path,
            partition_columns,
            existing_data_behavior,
        )

    def output_network_tables(
        self,
        network_dictionary: Dict[str, Network],
        network_output_folder_path: str,
        partition_columns: List[str],
        existing_data_behavior: str,
    ) -> None:
        """
        Write network data with stated output schema for each profile

        Args:
            network_dictionary (Dict[str, Network]): A dictionary where key is a name of a profile and a value is an instance of Network belonging to this profile
            network_output_folder_path (str): A path to a folder to store network data (created as by appending sub-path to the base/parent path)
            partition_columns (List[str]): Columsn to use for partitioning
            existing_data_behavior (str): Controls how the dataset will handle data that already exists in the destination
        """

        self.logger.info("Writing Network tables")

        for network_name, network in network_dictionary.items():

            network_gdf = gpd.GeoDataFrame(
                pd.concat(
                    [
                        network.gdf_hw.assign(loc_type="hw"),
                        network.gdf_event.assign(loc_type="event"),
                    ],
                    ignore_index=True,
                )
            ).to_crs(4326)

            network_gdf[ColNames.centre_x] = network_gdf["geometry"].x
            network_gdf[ColNames.centre_y] = network_gdf["geometry"].y

            network_df = network_gdf.drop(
                columns=["nearest_node_id", "distance_to_node", "geometry"]
            )

            network_df[ColNames.network_name] = network_name

            write_df_to_parquet(
                network_df,
                network_output_folder_path,
                partition_columns,
                existing_data_behavior,
            )

    def output_metadata(
        self,
        users_dictionary: Dict[str, List[User]],
        network_dictionary: Dict[str, Network],
        users_network_dict: Dict[str, str],
        metadata_output_folder_path: str,
        partition_columns: Optional[List[str]] = None,
        existing_data_behavior: Optional[str] = None,
    ) -> None:
        """
        Write metadata with stated output schema for each profile to see anchor locations for every user (e.g. for checking purposes)

        Args:
            users_dictionary (Dict[str, List[User]]): A dictionary where key is a name of a profile and a value is a list of User instances belonging to this profile
            network_dictionary (Dict[str, Network]): A dictionary where key is a name of a profile and a value is an instance of Network belonging to this profile
            users_netwrok_dict (Dict[str, str]): Dictionaru to connect users to their network
            metadata_output_folder_path (str): A path to a folder to store GPS results (created as by appending sub-path to the base/parent path)
            partition_columns (List[str]): Columsn to use for partitioning
            existing_data_behavior (str): Controls how the dataset will handle data that already exists in the destination
        """
        self.logger.info("Writing metadata")

        for profile_name, users in users_dictionary.items():

            network_name = users_network_dict[profile_name]

            network = network_dictionary[network_name]

            # network_name is needed to make it clear in what particular network to search for locations by ids
            # alternatice way is to look in config
            metadata_data_df = pd.DataFrame(
                [
                    [
                        user.user_id,
                        network.gdf_hw.iloc[user.home_id]["osmid"],
                        network.gdf_hw.iloc[user.work_id]["osmid"],
                        network.gdf_event.iloc[user.regular_loc_array]["osmid"].values,
                        profile_name,
                        network_name,
                    ]
                    for user in users
                ],
                columns=[
                    ColNames.user_id,
                    ColNames.home_id,
                    ColNames.work_id,
                    ColNames.regular_loc_array,
                    ColNames.profile_name,
                    ColNames.network_name,
                ],
            )

            write_df_to_parquet(
                metadata_data_df,
                metadata_output_folder_path,
                partition_columns,
                existing_data_behavior,
            )

    def run(self):
        # pylint: disable=missing-function-docstring
        profiles = self.config["PROFILES"].keys()

        # for each profile
        for profile in profiles:
            # get config params
            profile_config = self.config["PROFILES"][profile]
            # and profile name
            profile_name = profile_config["PROFILE_NAME"]

            self.logger.info("Started generating process for profile: %s", profile_name)

            profile_network_config = profile_config["NETWORK_PARAMS"]

            # check if a network was already created (some profile scan have identical network
            if profile_network_config["USE_ALREADY_CREATED"] is True:
                # reuse already created network
                try:
                    network = self.network_dictionary[
                        profile_network_config["NETWORK_NAME"]
                    ]
                except KeyError as e:
                    self.logger.warning(
                        "%d : the network called %s is not yet created",
                        e,
                        profile_network_config["NETWORK_NAME"],
                    )
                    raise

            else:
                # create a unique Network
                # store Network in a dict
                network = self.create_network(profile_network_config)
                self.network_dictionary[profile_network_config["NETWORK_NAME"]] = (
                    network
                )
            self.logger.info(
                "Network for profile '%d' is generated, network name: %s",
                profile_name,
                profile_network_config["NETWORK_NAME"],
            )

            self.users_network_dict[profile_name] = profile_network_config[
                "NETWORK_NAME"
            ]

            # generagte users of a profile
            profile_users_config = profile_config["USER_PARAMS"]
            users = self.generate_users(network, profile_users_config)
            self.logger.info(
                "Users for profile '%d' is generated, number of users: %s",
                profile_name,
                profile_users_config["NUM_USERS"],
            )
            # create meaningful locations for each user
            users_with_mean_loc = self.execute_method_for_users(
                users, "get_meaningful_locations"
            )
            self.logger.info(
                "Meaningful locations for users of profile '%s' is generated",
                profile_name,
            )
            # generate synth gps data for each user
            users_with_gps = self.execute_method_for_users(
                users_with_mean_loc, "generate_gps"
            )
            self.logger.info(
                "GPD data for users of profile '%s' is generated", profile_name
            )
            # store users with gps data in a dict
            self.users_dictionary[profile_name] = users_with_gps

        # Write output results
        self.logger.info("Started writing results")

        self.output_gps(self.users_dictionary, self.config["OUTPUTS"]["GPS"]["PATH"])
        self.output_network_tables(
            self.network_dictionary,
            self.config["OUTPUTS"]["NETWORK_TABLES"]["PATH"],
            self.config["OUTPUTS"]["NETWORK_TABLES"]["PARTITION_COLUMNS"],
            self.config["OUTPUTS"]["NETWORK_TABLES"]["EXISTING_DATA_BEHAVIOUR"],
        )
        self.output_metadata(
            self.users_dictionary,
            self.network_dictionary,
            self.users_network_dict,
            self.config["OUTPUTS"]["METADATA"]["PATH"],
        )
