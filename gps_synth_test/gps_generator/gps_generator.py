import pandas as pd
import os
import logging
import pandas as pd
import geopandas as gpd
from datetime import datetime
from gps_synth_test.common.functions import class_getter, write_data, check_or_create_dir
from gps_synth_test.common.columns import ColNames


class GPS_Generator():
    def __init__(self, base_dir, config) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.time_generated = datetime.now().strftime(format="%Y%m%d%H%M%S")
        self.network_dictionary = {}
        self.users_dictionary = {}

        for output in self.config["OUTPUT"]:
            output_path = os.path.join(base_dir, self.config["OUTPUT"][output])
            check_or_create_dir(output_path)
            self.config["OUTPUT"][output] = output_path

    def create_network(self, profile_network_config):

        network_class = class_getter(
            profile_network_config['NETWORK_MODULE_PATH'], profile_network_config['NETWORK_CLASS'])

        network = network_class(profile_network_config)

        network.run()

        return network

    def generate_users(self, network, profile_user_config, id_counter=1):

        users_array = []

        for _ in range(profile_user_config['NUM_USERS']):
            user_class = class_getter(
                profile_user_config['USER_MODULE_PATH'], profile_user_config['USER_CLASS'])
            new_user = user_class(id_counter,
                                  network, profile_user_config)
            users_array.append(new_user)
            id_counter += 1

        return users_array

    def execute_method_for_users(self, users, method_name):

        for user in users:
            method = getattr(user, method_name)
            method()
        return users

    def output_gps(self, users_dictionary, gps_output_folder):
        self.logger.info(f"Writting GPS data")
        gps_data = []
        gps_data_df = pd.DataFrame(columns=[
                                   ColNames.user_id, ColNames.timestamp, ColNames.lon, ColNames.lat, ColNames.profile])

        for profile_name, users in users_dictionary.items():
            for user in users:
                gps_data += user.data_array
            gps_data_profile_df = pd.DataFrame(gps_data, columns=[ColNames.user_id, ColNames.timestamp, ColNames.lon, ColNames.lat]).\
                sort_values(by=[ColNames.user_id, ColNames.timestamp])
            gps_data_profile_df[ColNames.profile] = profile_name

            gps_data_df = pd.concat(
                [gps_data_df, gps_data_profile_df], ignore_index=True)

        output_path = os.path.join(
            gps_output_folder, 'synthGPS_' + str(self.time_generated) + '.csv')

        write_data(gps_data_df, output_path)

    def output_network_tables(self, network_dictionary, network_output_folder):

        self.logger.info(f"Writting Network tables")

        for profile_name, network in network_dictionary.items():

            network_gdf = gpd.GeoDataFrame(pd.concat([network.gdf_hw.assign(
                loc_type="hw"), network.gdf_event.assign(loc_type="event")], ignore_index=True)).to_crs(4326)

            output_subfolder = os.path.join(
                network_output_folder, profile_name)

            os.makedirs(output_subfolder, exist_ok=True)

            output_path_network = os.path.join(
                output_subfolder, 'network_' + str(self.time_generated) + '.gpkg')

            write_data(network_gdf, output_path_network, geo=True)

    def output_metadata(self, users_dictionary, network_dictionary, metadata_output_folder):

        self.logger.info(f"Writting metadata")

        for profile_name, users in users_dictionary.items():
            network = network_dictionary[profile_name]

            metadata_data_df = pd.DataFrame([[user.user_id,
                                              network.gdf_hw.iloc[user.home_id]['osmid'],
                                              network.gdf_hw.iloc[user.work_id]['osmid'],
                                              network.gdf_event.iloc[user.regular_loc_array]['osmid'].values,
                                              user.profile] for user in users],
                                            columns=[ColNames.user_id, ColNames.home_id, ColNames.work_id, ColNames.regular_loc_array, ColNames.profile])

            output_path = os.path.join(
                metadata_output_folder, 'metadata_' + str(self.time_generated) + '.csv')
            write_data(metadata_data_df, output_path)

    def run(self):

        profiles = self.config['PROFILES'].keys()

        for profile in profiles:
            profile_config = self.config['PROFILES'][profile]
            profile_name = profile_config['PROFILE_NAME']

            self.logger.info(
                f"Started generating process for profile: {profile_name}")

            profile_network_config = profile_config["NETWORK_PARAMS"]

            if profile_network_config["USE_ALREADY_CREATED"]:
                network = self.network_dictionary[profile_name]
            else:
                network = self.create_network(profile_network_config)
                self.network_dictionary[profile_name] = network
            self.logger.info(
                f"Network for profile '{profile_name}' is generated")

            users = self.generate_users(
                network, profile_config["USER_PARAMS"])
            self.logger.info(
                f"Users for profile '{profile_name}' is generated, number of users: {profile_name}")

            users_with_mean_loc = self.execute_method_for_users(
                users, "get_meaningful_locations")
            self.logger.info(
                f"Meaningful locations for users of profile '{profile_name}' is generated")

            users_with_gps = self.execute_method_for_users(
                users_with_mean_loc, "generate_gps")
            self.logger.info(
                f"Meaningful locations for users of profile '{profile_name}' is generated")

            self.users_dictionary[profile_name] = users_with_gps

        self.logger.info(f"Started writing results")
        self.output_gps(self.users_dictionary, self.config['OUTPUT']['GPS'])
        self.output_network_tables(
            self.network_dictionary, self.config['OUTPUT']['NETWORK_TABLES'])
        self.output_metadata(
            self.users_dictionary, self.network_dictionary, self.config['OUTPUT']['METADATA'])
