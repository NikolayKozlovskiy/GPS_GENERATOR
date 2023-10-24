from abc import ABC
import osmnx as ox
import pandas as pd
import random
import math
from datetime import timedelta
from pyproj import Transformer, CRS, Geod
from shapely.geometry import LineString, Point
import numpy as np
from gps_synth.common.columns import ColNames

crs_4326 = CRS.from_epsg(4326)


class User(ABC):
    def __init__(self, user_id: int, Network, profile_user_config) -> None:
        self.user_id = user_id
        self.date_range = pd.date_range(profile_user_config['DATE_BEGGINING'],
                                        profile_user_config['DATE_END'], freq='d')
        self.Network = Network
        self.df_hw = Network.df_hw
        self.df_event = Network.df_event
        self.min_distance_h_w = profile_user_config['MIN_DISTANCE_H_W']
        self.min_distance_w_r = profile_user_config['MIN_DISTANCE_W_R']
        self.mean_velocity_ms = profile_user_config['MEAN_VELOCITY_MS']
        self.proximity_to_road = profile_user_config['PROXIMITY_TO_ROAD']
        self.transformer_to_WGS = Transformer.from_crs(
            Network.graph_crs, crs_4326, always_xy=True)

        self.home_id = None
        self.work_id = None
        self.regular_loc_array = None

        self.data_array = []
        self.gps_data = None

    def get_meaningful_locations(self, Network, df_hw, df_event, min_distance_h_w, min_distance_w_r):

        while True:
            home_id = random.randint(0, len(df_hw)-1)
            work_id = random.randint(0, len(df_hw)-1)
            home_node = Network.nodes.loc[df_hw.iloc[home_id]
                                          ['nearest_node_id']]
            work_node = Network.nodes.loc[df_hw.iloc[work_id]
                                          ['nearest_node_id']]
            distance_to_h = df_hw.iloc[home_id]['distance_to_node']
            distance_to_w = df_hw.iloc[work_id]['distance_to_node']
            final_distance = ox.distance.euclidean_dist_vec(home_node['y'], home_node['x'], work_node['y'], work_node['x'])\
                + distance_to_h+distance_to_w
            if final_distance >= min_distance_h_w:  # meters
                regular_locations_ids = []
                number_of_regular_locations = random.randint(3, 5)
                i = 0
                while i <= number_of_regular_locations:
                    regular_id = random.randint(0, len(df_event)-1)
                    regular_node = Network.nodes.loc[df_event.iloc[regular_id]
                                                     ['nearest_node_id']]
                    distance_to_reg_loc = df_event.iloc[regular_id]['distance_to_node']
                    if ox.distance.euclidean_dist_vec(regular_node['y'], regular_node['x'], work_node['y'], work_node['x'])\
                            + distance_to_reg_loc + distance_to_w >= min_distance_w_r:  # meters
                        regular_locations_ids.append(regular_id)
                        i += 1
                    else:
                        continue
                self.home_id = home_id
                self.work_id = work_id
                self.regular_loc_array = regular_locations_ids

                break
            else:
                continue

    def get_regular_or_random_loc(self, regular_location_ids, df_event, number_of_events):
        event_id_list = []
        while len(event_id_list) < number_of_events:
            random_id = [random.randint(0, len(df_event)-1)]
            array_of_ids = np.array(
                [regular_location_ids, random_id], dtype='object')
            choose_reg_or_random = np.random.choice(
                array_of_ids, 1, p=[0.6, 0.4])[0]
            event_id = np.random.choice(choose_reg_or_random)
            if event_id not in event_id_list:
                event_id_list.append(event_id)
            else:
                continue

        return event_id_list

    def get_info_about_loc(self, list_of_ids, df):
        list_of_info = []
        for loc_id in list_of_ids:
            list_of_info.append([df.iloc[loc_id]['nearest_node_id'],
                                df.iloc[loc_id][ColNames.centre_x], df.iloc[loc_id][ColNames.centre_y]])

        return list_of_info

    def create_list_of_locations(self, day_of_week, home_id, work_id, regular_loc_array, df_hw, df_event):
        if day_of_week < 6:
            number_of_events = np.random.choice(
                [0, 1, 2, 3], 1, p=[0.6, 0.25, 0.1, 0.05])[0]
            list_of_ids = [home_id, work_id]
        else:
            number_of_events = np.random.choice(
                [0, 1, 2, 3, 4], 1, p=[0.1, 0.2, 0.30, 0.25, 0.15])[0]
            list_of_ids = [home_id]

        event_id_list = self.get_regular_or_random_loc(
            regular_loc_array, df_event, number_of_events)

        list_of_locations_not_event = self.get_info_about_loc(
            list_of_ids, df_hw)
        list_of_locations_event = self.get_info_about_loc(
            event_id_list, df_event)

        list_of_locations = list_of_locations_not_event + list_of_locations_event

        return list_of_locations

    def get_static_points(self, startlon, startlat, user_id, data_array, time_start, time_end):
        time_start += timedelta(minutes=1)
        startlon, startlat = self.transformer_to_WGS.transform(
            startlon, startlat)
        while time_start < time_end:
            random_minutes = random.randint(1, 5)
            possible_forward_azimuth = random.randint(0, 360)
            possible_distance = random.randint(0, 5)  # metres
            endLon, endLat, _ = (Geod(ellps='WGS84')
                                 .fwd(startlon, startlat, possible_forward_azimuth, possible_distance))
            time_gps = time_start
            data_array.append([user_id, time_gps, endLon, endLat])
            time_start += timedelta(minutes=random_minutes)

        return time_start.round(freq='S')

    def get_points_on_path(self, path, number_of_points):
        distances = np.linspace(0, path.length, number_of_points)
        points = [path.interpolate(distance) for distance in distances]

        return points

    def get_chaotic_point(self, point_start, point_end, radius_of_buffer, proximity_to_road):
        points_intersection = point_start.buffer(
            radius_of_buffer).intersection(point_end.buffer(radius_of_buffer))
        path_between_points = LineString([point_start, point_end])
        final_intersection = points_intersection.intersection(
            path_between_points.buffer(proximity_to_road))
        min_x, min_y, max_x, max_y = final_intersection.bounds
        while True:
            chaotic_point = Point(
                [random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
            if (chaotic_point.within(final_intersection)):
                return chaotic_point
            else:
                continue

    def get_moving_points(self, Network, start_node, end_node,  start_coords, end_coords, user_id, data_array,
                          mean_velocity_ms, proximity_to_road, time_start):

        route = ox.distance.shortest_path(
            Network.graph_proj, start_node, end_node, weight="length")
        route_nodes = Network.nodes.loc[route]
        route_list = list(route_nodes.geometry.values)
        route_list.insert(0, Point(start_coords[0], start_coords[1]))
        route_list.append(Point(end_coords[0], end_coords[1]))
        path = LineString(route_list)

        length_of_distance_m = mean_velocity_ms * 10

        if path.length <= length_of_distance_m:
            number_of_points = 2
        else:
            number_of_points = math.ceil(path.length/length_of_distance_m)

        points = self.get_points_on_path(path, number_of_points)

        for i in range(number_of_points):
            endLon, endLat = self.transformer_to_WGS.transform(
                points[i].x, points[i].y)
            if i != number_of_points-1:
                chaotic_point = self.get_chaotic_point(
                    points[i], points[i+1], length_of_distance_m, proximity_to_road)
                distance_to_chaotic_point = LineString(
                    [points[i], chaotic_point]).length
                if distance_to_chaotic_point < mean_velocity_ms*2:
                    time_to_chaotic_point = 2
                else:
                    time_to_chaotic_point = distance_to_chaotic_point/mean_velocity_ms
                time_gps = time_start.round(freq='S')
                time_start += timedelta(seconds=time_to_chaotic_point)
                data_array.append([user_id, time_gps, endLon, endLat])

                endLon, endLat = self.transformer_to_WGS.transform(
                    chaotic_point.x, chaotic_point.y)
                distance_to_next_point = LineString(
                    [chaotic_point, points[i+1]]).length
                if distance_to_next_point < mean_velocity_ms*2:
                    time_to_next_point = 2
                else:
                    time_to_next_point = distance_to_next_point/mean_velocity_ms
                time_gps = time_start.round(freq='S')
                time_start += timedelta(seconds=time_to_next_point)
                data_array.append([user_id, time_gps, endLon, endLat])

            else:
                endLon, endLat = self.transformer_to_WGS.transform(
                    points[i].x, points[i].y)
                time_gps = time_start.round(freq='S')
                data_array.append([user_id, time_gps, endLon, endLat])

        return time_start.round(freq='S')


class User_walk(User):
    def __init__(self, user_id: int, Network, profile_user_config):
        super().__init__(user_id, Network, profile_user_config)
        self.child_class_name = "User_walk"

    def get_meaningful_locations(self):
        super().get_meaningful_locations(self.Network, self.df_hw,
                                         self.df_event, self.min_distance_h_w, self.min_distance_w_r)

    def random_plot(self, time_start, day, day_of_week, list_of_locations):

        i = 0

        if day_of_week >= 6 and len(list_of_locations) > 1:

            stay_activity_time = super().get_static_points(list_of_locations[i][1], list_of_locations[i][2], self.user_id, self.data_array,
                                                           time_start=time_start, time_end=day+timedelta(hours=random.randint(10, 14)))
        elif day_of_week < 6:

            stay_activity_time = super().get_static_points(list_of_locations[i][1], list_of_locations[i][2], self.user_id, self.data_array,
                                                           time_start=time_start, time_end=day+timedelta(hours=random.randint(7, 9)))

            moving_activity_time = super().get_moving_points(self.Network, list_of_locations[i][0], list_of_locations[i+1][0],
                                                             (list_of_locations[i][1], list_of_locations[i][2]), (
                                                                 list_of_locations[i+1][1], list_of_locations[i+1][2]),
                                                             self.user_id, self.data_array, self.mean_velocity_ms, self.proximity_to_road, time_start=stay_activity_time)

            stay_activity_time = super().get_static_points(list_of_locations[i+1][1], list_of_locations[i+1][2], self.user_id, self.data_array,
                                                           time_start=moving_activity_time, time_end=day+timedelta(hours=random.randint(17, 19)))

            i += 1

        else:
            stay_activity_time = super().get_static_points(list_of_locations[i][1], list_of_locations[i][2], self.user_id, self.data_array,
                                                           time_start=time_start, time_end=day+timedelta(hours=random.randint(22, 26)))

            next_time = stay_activity_time

            return stay_activity_time

        while i < (len(list_of_locations)-1):
            moving_activity_time = super().get_moving_points(self.Network, list_of_locations[i][0], list_of_locations[i+1][0],
                                                             (list_of_locations[i][1], list_of_locations[i][2]), (
                                                                 list_of_locations[i+1][1], list_of_locations[i+1][2]),
                                                             self.user_id, self.data_array, self.mean_velocity_ms, self.proximity_to_road, time_start=stay_activity_time)

            stay_activity_time = super().get_static_points(list_of_locations[i+1][1], list_of_locations[i+1][2], self.user_id, self.data_array,
                                                           time_start=moving_activity_time, time_end=moving_activity_time+timedelta(hours=random.randint(1, 3)))
            i += 1

        if i > 0:

            moving_activity_time = super().get_moving_points(self.Network, list_of_locations[i][0], list_of_locations[0][0],
                                                             (list_of_locations[i][1], list_of_locations[i][2]), (
                                                                 list_of_locations[0][1], list_of_locations[0][2]),
                                                             self.user_id, self.data_array, self.mean_velocity_ms, self.proximity_to_road, time_start=stay_activity_time)

            next_time = moving_activity_time

            return next_time

    def generate_gps(self):
        time_start = self.date_range[0]
        for i in range(len(self.date_range)):
            day = self.date_range[i]
            day_of_week = day.isoweekday()

            list_of_locations = super().create_list_of_locations(day_of_week, self.home_id,
                                                                 self.work_id, self.regular_loc_array, self.df_hw, self.df_event)

            time_start = self.random_plot(
                time_start, day, day_of_week, list_of_locations)
