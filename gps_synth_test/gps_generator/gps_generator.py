import pandas as pd
import os
import logging 
from datetime import datetime
from gps_synth_test.common.functions import class_getter, write_data
from gps_synth_test.common.columns import ColNames

class GPS_Generator():
    def __init__(self, config) -> None:
      self.config = config
      self.logger = logging.getLogger(__name__)
      self.place_name = config['GPS_GENERATION']['COMMON']['PLACE_NAME']
      self.date_range = pd.date_range(config['GPS_GENERATION']['COMMON']['DATE_BEGGINING'],\
                                      config['GPS_GENERATION']['COMMON']['DATE_END'], freq = 'd')
      self.time_generated = datetime.now().strftime(format = "%Y%m%d%H%M%S")
      self.network_dictionary = {}
      self.users_dictionary = {}

    def create_network(self, profile_config):

      network_class = class_getter(profile_config['NETWORK_PARAMS']['NETWORK_MODULE_PATH'], profile_config['NETWORK_PARAMS']['NETWORK_CLASS'])

      new_network = network_class(self.place_name, profile_config)

      new_network.run()

      self.network_dictionary[profile_config['PROFILE_NAME']] = new_network

      self.logger.info(f"Network for profile '{profile_config['PROFILE_NAME']}' is generated")

    def generate_users(self, date_range, profile_config, id_counter = 1): 

      Network = self.network_dictionary[profile_config['PROFILE_NAME']]
      users_array = []

      for user in range(profile_config['NUM_USERS']): 
        user_class = class_getter(profile_config['USER_PARAMS']['USER_MODULE_PATH'], profile_config['USER_PARAMS']['USER_CLASS'])
        new_user = user_class(id_counter, date_range, Network, profile_config)
        users_array.append(new_user)
        id_counter += 1 
      
      self.users_dictionary[profile_config['PROFILE_NAME']] = users_array

      self.logger.info(f"Users for profile '{profile_config['PROFILE_NAME']}' is generated, number of users: {profile_config['NUM_USERS']}")

    def generate_meaningful_locations_for_users(self, profile_config): 

      users = self.users_dictionary[profile_config['PROFILE_NAME']]

      for user in users: 
        user.get_meaningful_locations()

      self.logger.info(f"Meaningful locations for users of profile '{profile_config['PROFILE_NAME']}' is generated")

    def generate_gps_data_for_users(self, profile_config): 

      users = self.users_dictionary[profile_config['PROFILE_NAME']]

      for user in users: 
        user.generate_gps()

      self.logger.info(f"GPS data for users of profile '{profile_config['PROFILE_NAME']}' is generated")

    def output_gps(self, profiles, config_output): 
      self.logger.info(f"Writting GPS data")
      gps_data = []
      gps_data_df = pd.DataFrame(columns = [ColNames.user_id, ColNames.timestamp, ColNames.lon, ColNames.lat, ColNames.profile])
      for profile in profiles: 
        users = self.users_dictionary[self.config['GPS_GENERATION']['PROFILES'][profile]['PROFILE_NAME']]
        for user in users: 
          gps_data += user.data_array
        gps_data_profile_df = pd.DataFrame(gps_data, columns = [ColNames.user_id, ColNames.timestamp, ColNames.lon, ColNames.lat]).\
                              sort_values(by = [ColNames.user_id, ColNames.timestamp])
        gps_data_profile_df[ColNames.profile] = self.config['GPS_GENERATION']['PROFILES'][profile]['PROFILE_NAME']

        gps_data_df = pd.concat([gps_data_df, gps_data_profile_df], ignore_index = True)

      gps_output_folder = config_output['GPS']
      output_path = os.path.join(gps_output_folder, 'synthGPS_' + str(self.time_generated) + '.csv')     
      write_data(gps_data_df, output_path)


    def output_network_tables(self, profiles, config_output): 

      self.logger.info(f"Writting Network tables")

      for profile in profiles: 
        profile_name = self.config['GPS_GENERATION']['PROFILES'][profile]['PROFILE_NAME']
        network = self.network_dictionary[profile_name]
        network_output_folder = config_output['NETWORK_TABLES']

        output_path_hw = os.path.join(network_output_folder, profile_name +'\hw_' + str(self.time_generated) + '.gpkg')
        output_path_event = os.path.join(network_output_folder, profile_name +'\event_' + str(self.time_generated) + '.gpkg') 
        write_data(network.gdf_hw, output_path_hw, geo = True)
        write_data (network.gdf_event, output_path_event, geo = True)

    def output_metadata(self, profiles, config_output): 

      self.logger.info(f"Writting metadata")

      for profile in profiles: 
        profile_name = self.config['GPS_GENERATION']['PROFILES'][profile]['PROFILE_NAME']
        network = self.network_dictionary[profile_name]
        users = self.users_dictionary[profile_name]

        metadata_data_df = pd.DataFrame([[user.user_id,
                            network.gdf_hw.iloc[user.home_id]['osmid'], 
                            network.gdf_hw.iloc[user.work_id]['osmid'], 
                            network.gdf_event.iloc[user.regular_loc_array]['osmid'].values, 
                            user.profile] for user in users],
                            columns = [ColNames.user_id, ColNames.home_id, ColNames.work_id, ColNames.regular_loc_array, ColNames.profile])
        metadata_output_folder = config_output['METADATA']
        output_path = os.path.join(metadata_output_folder, 'metadata_' + str(self.time_generated) + '.csv')     
        write_data(metadata_data_df, output_path)

    
    def run(self):
      
      profiles = self.config['GPS_GENERATION']['PROFILES'].keys()

      for profile in profiles: 
        profile_config = self.config['GPS_GENERATION']['PROFILES'][profile]
        self.logger.info(f"Started generating process for profile: {profile_config['PROFILE_NAME']}")
        self.create_network(profile_config)
        self.generate_users(self.date_range, profile_config)
        self.generate_meaningful_locations_for_users(profile_config)
        self.generate_gps_data_for_users(profile_config)

      self.logger.info(f"Started writing results")
      self.output_gps(profiles, self.config['OUTPUT'])
      self.output_network_tables(profiles, self.config['OUTPUT'])
      self.output_metadata(profiles, self.config['OUTPUT'])

       
