import pandas as pd
import os
import uuid
import logging
import pandas as pd
from datetime import datetime
from pyproj import Transformer, CRS
from typing import Any, List, Dict, Optional
from gps_synth.common.functions import class_getter, check_or_create_dir, delete_directory, write_df_to_parquet
from gps_synth.common.columns import ColNames
from gps_synth.network.network import Network
from gps_synth.common.abs_user import User

crs_4326 = CRS.from_epsg(4326)


class GPS_Generator():
    def __init__(self, config, base_dir):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.network_dictionary = {}
        self.users_dictionary = {}

        for folder in self.config["OUTPUT"]["FOLDERS"]:
            output_path = os.path.join(
                base_dir, self.config["OUTPUT"]["FOLDERS"][folder])
            if self.config["OUTPUT"]["DO_CLEAR_OUTPUT"] == True:
                delete_directory(output_path)
            check_or_create_dir(output_path)
            self.config["OUTPUT"]["FOLDERS"][folder] = output_path

    def create_network(self, profile_network_config: Any) -> Network:
        """
        Initialise Network class and run it

        Args: 
            profile_network_config (Any): YAML object with config params regarding network 

        Returns: 
            Network: Instance of Network class with completed run method
        """

        network_class = class_getter(
            profile_network_config['NETWORK_MODULE_PATH'], profile_network_config['NETWORK_CLASS'])

        network = network_class(profile_network_config)

        network.run()

        return network

    def generate_users(self, network: Network, profile_user_config: Any, id_counter: int = 1) -> List[User]:
        """
        Initialise User class and run it as many times as specified in NUM_USERS config param.
        Store instances in a list

        Args: 
            network (Network): An instance of Netwrok class to use for choosing anchoir points of a user
            profile_user_config (Any): YAML object with config params regarding users
            id_counter (int=1): Unique integer numbers 

        Returns: 
            List[User]: list of instances of User class with completed run method
        """
        users_array = []

        for _ in range(profile_user_config['NUM_USERS']):
            user_class = class_getter(
                profile_user_config['USER_MODULE_PATH'], profile_user_config['USER_CLASS'])
            new_user = user_class(id_counter,
                                  network, profile_user_config)
            users_array.append(new_user)
            id_counter += 1

        return users_array

    def execute_method_for_users(self, users: List[User], method_name: str) -> List[User]:
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

    def output_gps(self,
                   users_dictionary: Dict[str, List[User]],
                   gps_output_folder_path: str,
                   partition_columns: Optional[List[str]] = None) -> None:
        """
        Write users' synth GPS data with stated output schema for each profile

        Args:
            users_dictionary (Dict[str, List[User]]): A dictionary where key is a name of a profile and a value is a list of User instances belonging to this profile
            gps_output_folder_path (str): A path to a folder to store GPS results (created as by appending sub-path to the base/parent path)
        """

        self.logger.info(f"Writting GPS data")
        gps_data = []
        gps_data_df = pd.DataFrame(columns=[
                                   ColNames.user_id, ColNames.timestamp, ColNames.lon, ColNames.lat, ColNames.profile_name])

        for profile_name, users in users_dictionary.items():
            for user in users:
                gps_data += user.data_array
            gps_data_profile_df = pd.DataFrame(gps_data, columns=[ColNames.user_id, ColNames.timestamp, ColNames.lon, ColNames.lat]).\
                sort_values(by=[ColNames.user_id, ColNames.timestamp])
            gps_data_profile_df[ColNames.profile_name] = profile_name

            # if you borther with pd.concat FutureWarning, here is a solution
            # https://stackoverflow.com/questions/77254777/alternative-to-concat-of-empty-dataframe-now-that-it-is-being-deprecated
            gps_data_df = pd.concat(
                [gps_data_df, gps_data_profile_df], ignore_index=True)

        write_df_to_parquet(
            gps_data_df, gps_output_folder_path, partition_columns)

    def output_network_tables(self,
                              network_dictionary: Dict[str, Network],
                              network_output_folder_path: str,
                              partition_columns: Optional[List[str]] = None) -> None:
        """
        Write network data with stated output schema for each profile

        Args:
            network_dictionary (Dict[str, Network]): A dictionary where key is a name of a profile and a value is an instance of Network belonging to this profile
            network_output_folder_path (str): A path to a folder to store network data (created as by appending sub-path to the base/parent path)
        """

        self.logger.info(f"Writting Network tables")

        for profile_name, network in network_dictionary.items():

            network_df = pd.DataFrame(pd.concat([network.df_hw.assign(
                loc_type="hw"), network.df_event.assign(loc_type="event")], ignore_index=True))

            network_df = network_df.drop(
                columns=['nearest_node_id', 'distance_to_node'])

            transformer_to_WGS = Transformer.from_crs(
                network.graph_crs, crs_4326, always_xy=True)

            network_df[ColNames.centre_x], network_df[ColNames.centre_y] = transformer_to_WGS.transform(
                network_df[ColNames.centre_x], network_df[ColNames.centre_y])

            network_df[ColNames.profile_name] = profile_name

            write_df_to_parquet(
                network_df, network_output_folder_path, partition_columns)

    def output_metadata(self,
                        users_dictionary: Dict[str, List[User]],
                        network_dictionary: Dict[str, Network],
                        metadata_output_folder_path: str,
                        partition_columns: Optional[List[str]] = None) -> None:
        """
        Write metadata with stated output schema for each profile to see anchor locations for every user (e.g. for checking purposes) 

        Args:
            users_dictionary (Dict[str, List[User]]): A dictionary where key is a name of a profile and a value is a list of User instances belonging to this profile
            network_dictionary (Dict[str, Network]): A dictionary where key is a name of a profile and a value is an instance of Network belonging to this profile
            metadata_output_folder_path (str): A path to a folder to store GPS results (created as by appending sub-path to the base/parent path)
        """
        self.logger.info(f"Writting metadata")

        for profile_name, users in users_dictionary.items():
            network = network_dictionary[profile_name]

            metadata_data_df = pd.DataFrame([[user.user_id,
                                              network.df_hw.iloc[user.home_id]['osmid'],
                                              network.df_hw.iloc[user.work_id]['osmid'],
                                              network.df_event.iloc[user.regular_loc_array]['osmid'].values,
                                              profile_name] for user in users],
                                            columns=[ColNames.user_id, ColNames.home_id, ColNames.work_id, ColNames.regular_loc_array, ColNames.profile_name])

            write_df_to_parquet(
                metadata_data_df, metadata_output_folder_path, partition_columns)

    def run(self):

        profiles = self.config['PROFILES'].keys()

        # for each profile
        for profile in profiles:
            # get config params
            profile_config = self.config['PROFILES'][profile]
            # and profile name
            profile_name = profile_config['PROFILE_NAME']

            self.logger.info(
                f"Started generating process for profile: {profile_name}")

            profile_network_config = profile_config["NETWORK_PARAMS"]

            # check if a network was already created (some profile scan have identical network)
            # store Network in a dict
            if profile_network_config["USE_ALREADY_CREATED"]:
                network = self.network_dictionary[profile_name]
            else:
                network = self.create_network(profile_network_config)
                self.network_dictionary[profile_name] = network
            self.logger.info(
                f"Network for profile '{profile_name}' is generated")

            # generagte users of a profile
            users = self.generate_users(
                network, profile_config["USER_PARAMS"])
            self.logger.info(
                f"Users for profile '{profile_name}' is generated, number of users: {profile_name}")
            # create meaningful locations for each user
            users_with_mean_loc = self.execute_method_for_users(
                users, "get_meaningful_locations")
            self.logger.info(
                f"Meaningful locations for users of profile '{profile_name}' is generated")
            # generate synth gps data for each user
            users_with_gps = self.execute_method_for_users(
                users_with_mean_loc, "generate_gps")
            self.logger.info(
                f"Meaningful locations for users of profile '{profile_name}' is generated")
            # store users with gps data in a dict
            self.users_dictionary[profile_name] = users_with_gps

        # Write output results
        self.logger.info(f"Started writing results")

        self.output_gps(self.users_dictionary,
                        self.config['OUTPUT']["FOLDERS"]['GPS'])
        self.output_network_tables(
            self.network_dictionary,
            self.config['OUTPUT']["FOLDERS"]['NETWORK_TABLES'])
        self.output_metadata(
            self.users_dictionary, self.network_dictionary,
            self.config['OUTPUT']["FOLDERS"]['METADATA'])
