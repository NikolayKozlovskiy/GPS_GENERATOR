
import random
from datetime import timedelta
from pandas import Timestamp
from typing import List, Union

from gps_synth.common.abs_user import User


class User_employed_walk(User):
    def __init__(self, user_id: int, Network, profile_user_config):
        super().__init__(user_id, Network, profile_user_config)
        self.child_class_name = "User_walk"

    def get_meaningful_locations(self):
        super().get_meaningful_locations(self.Network.nodes,
                                         self.Network.df_hw,
                                         self.Network.df_event,
                                         self.min_distance_h_w,
                                         self.min_distance_w_r)

    def random_plot_of_day(self,
                           time_start: Timestamp,
                           beggining_of_day: Timestamp,
                           day_of_week: int,
                           list_of_locations: List[List[Union[int, float]]]) -> Timestamp:
        """
        Create GPS data for a day following to some extend a random plot (there are some rules, e.g. on weekends 
        user can stay at home longer than at work days) but time boundaries vary. Store result users' data_array attribute

        Args: 
            time_start (Timestamp): Timestamp from which to start generating GPS data for a day
            beggining_of_day (Timestamp): Conventional timestamp of day beggining (e.g. 10.12.2023 00:00:00), 
                                          needed to create "absolute" boundaries of some activities
            day_of_week (int): _description_
            list_of_locations (List[List[Union[int, float]]])): List of lists, each element has three items: 
                                                                nearest node id and lat and lon coordinates of location's centroid

        Returns:
            Timestamp: Time from which to start generating GPS data for the next day                                                        

        """

        i = 0

        # if it is weekends and the number of locations to visit/stay is more than 1 (some events apart from home)
        # stay at home till 10-14 p.m.
        if day_of_week >= 6 and len(list_of_locations) > 1:

            stay_activity_time = super().get_static_points(self.user_id,
                                                           self.data_array,
                                                           list_of_locations[i][1],
                                                           list_of_locations[i][2],
                                                           time_start=time_start,
                                                           time_end=beggining_of_day+timedelta(hours=random.randint(10, 14)))
        # if it is a weekday
        elif day_of_week < 6:
            # stay at home between 7-9 p.m.
            stay_activity_time = super().get_static_points(self.user_id,
                                                           self.data_array,
                                                           list_of_locations[i][1],
                                                           list_of_locations[i][2],
                                                           time_start=time_start,
                                                           time_end=beggining_of_day+timedelta(hours=random.randint(7, 9)))
            # go to work
            moving_activity_time = super().get_moving_points(self.user_id,
                                                             self.data_array,
                                                             self.Network.graph_proj,
                                                             self.Network.nodes,
                                                             list_of_locations[i][0],
                                                             list_of_locations[i+1][0],
                                                             (list_of_locations[i][1],
                                                              list_of_locations[i][2]),
                                                             (list_of_locations[i+1][1],
                                                              list_of_locations[i+1][2]),
                                                             self.mean_velocity_ms,
                                                             self.proximity_to_road,
                                                             time_start=stay_activity_time)
            # stay at work till 17-19 p.m.
            stay_activity_time = super().get_static_points(self.user_id,
                                                           self.data_array,
                                                           list_of_locations[i+1][1],
                                                           list_of_locations[i+1][2],
                                                           time_start=moving_activity_time,
                                                           time_end=beggining_of_day+timedelta(hours=random.randint(17, 19)))

            i += 1

        else:
            # it is a weekedn and a user decided to stay at home whole day
            # poor they
            stay_activity_time = super().get_static_points(self.user_id,
                                                           self.data_array,
                                                           list_of_locations[i][1],
                                                           list_of_locations[i][2],
                                                           time_start=time_start,
                                                           time_end=beggining_of_day+timedelta(hours=random.randint(22, 26)))

            # day is finished
            return stay_activity_time

        # if there are some event locatiions to visit
        while i < (len(list_of_locations)-1):
            # first move to this event location
            moving_activity_time = super().get_moving_points(self.user_id,
                                                             self.data_array,
                                                             self.Network.graph_proj,
                                                             self.Network.nodes,
                                                             list_of_locations[i][0],
                                                             list_of_locations[i+1][0],
                                                             (list_of_locations[i][1],
                                                              list_of_locations[i][2]),
                                                             (list_of_locations[i+1][1],
                                                              list_of_locations[i+1][2]),
                                                             self.mean_velocity_ms,
                                                             self.proximity_to_road,
                                                             time_start=stay_activity_time)
            # stay at event location between 1-3 hours
            stay_activity_time = super().get_static_points(self.user_id,
                                                           self.data_array,
                                                           list_of_locations[i+1][1],
                                                           list_of_locations[i+1][2],
                                                           time_start=moving_activity_time,
                                                           time_end=moving_activity_time+timedelta(hours=random.randint(1, 3)))
            # repeat the process till the last event location
            i += 1

        # finally move to home
        # this condition is needed to handle situation when a user decieds to stay at home whole day (i=0)
        # no need to move from home to home
        if i > 0:

            moving_activity_time = super().get_moving_points(self.user_id,
                                                             self.data_array,
                                                             self.Network.graph_proj,
                                                             self.Network.nodes,
                                                             list_of_locations[i][0],
                                                             list_of_locations[0][0],
                                                             (list_of_locations[i][1],
                                                              list_of_locations[i][2]),
                                                             (list_of_locations[0][1],
                                                              list_of_locations[0][2]),
                                                             self.mean_velocity_ms,
                                                             self.proximity_to_road,
                                                             time_start=stay_activity_time)
            # day is finished
            return moving_activity_time

    # kind of run method but with understandable naming
    def generate_gps(self):
        # start time of generating GPS data for whole date range of a user
        time_start = self.date_range[0]
        # for each day of specified date range of a user
        for i in range(len(self.date_range)):
            day = self.date_range[i]
            day_of_week = day.isoweekday()

            list_of_locations = super().create_list_of_locations(self.Network.df_hw,
                                                                 self.Network.df_event,
                                                                 self.home_id,
                                                                 self.work_id,
                                                                 self.regular_loc_array,
                                                                 day_of_week)

            time_start = self.random_plot_of_day(
                time_start, day, day_of_week, list_of_locations)
