from abc import ABC, abstractmethod
import osmnx as ox
import pandas as pd
import numpy as np
import random
import math
import shapely
from datetime import timedelta
from typing import List, Tuple, Union
from networkx import MultiDiGraph
from pandas import DataFrame, Timestamp
from geopandas import GeoDataFrame
from pyproj import Transformer, CRS, Geod
from shapely.geometry import LineString, Point

# User class is a parent class of all child classes specified in user package
# User class is an abtract class and is not meant to be initiated
# User class has a combination of concrete and abstract methods:
# # concrete methods are meant to be called in child classes with super() function
# # abstract methods are meant to show what methods should be in a child class, but their implementation is a subject of this child class

crs_4326 = CRS.from_epsg(4326)


class User(ABC):
    def __init__(self, user_id: int, Network, profile_user_config):
        self.user_id = user_id
        self.Network = Network
        self.date_range = pd.date_range(profile_user_config['DATE_BEGGINING'],
                                        profile_user_config['DATE_END'], freq='d')
        self.radius_buffer_h_w = profile_user_config["RADIUS_BUFFER_H_W"]
        self.radius_buffer_h_r = profile_user_config["RADIUS_BUFFER_H_R"]
        self.mean_move_speed_ms = profile_user_config['MEAN_MOVE_SPEED_MS']
        self.proximity_to_road = profile_user_config['PROXIMITY_TO_ROAD']
        self.transformer_to_WGS = Transformer.from_crs(
            Network.graph_crs, crs_4326, always_xy=True)

        self.home_id = None
        self.work_id = None
        self.regular_loc_array = None

        self.data_array = []

    def get_random_id_within_buffer(self, 
                                    center_point: Point, 
                                    radius_buffer: int, 
                                    gdf_locations: GeoDataFrame) -> Union[int,None]:
        """
        Find a random id of a location which is within a buffer, created around center point with specified distance. 
        A center point should be surronded with some amount of needed locations, otherwise None 

        Args: 
            center_point (Point): A point around which create a buffer
            radius_buffer (int): A radius of a buffer
            gdf_locations (GeoDataFrame): Locations to filter with condition "within a buffer"
        
        Returns: 
            int: Random id among filtered loctions or None if home anchor is too near to border of a place
        """
        
        buffer = shapely.buffer(center_point, distance=radius_buffer)
        index_list = gdf_locations[gdf_locations.within(buffer)].index
        # TODO: 20 is arbitary threshold, e.g. there could be just a case that a place does not have 
        # some types of locations in many quantaties, think about how logically define this value 
        # and make it as another positional argument
        if len(index_list)>=20:
            random_id = random.choice(gdf_locations[gdf_locations.within(buffer)].index)
            return random_id
        else:
            return None

    def get_meaningful_locations(self,
                                 gdf_hw: GeoDataFrame,
                                 gdf_event: GeoDataFrame,
                                 radius_buffer_h_w: int,
                                 radius_buffer_h_r: int) -> None:
        """
        Create meaningful locations for a user: one home, one work, several regular events
        The distribution of meaningful locations should follow some distance conditions. 
        Store computed anchors in correponding instance attributes

        Args: 
            gdf_hw (GeoDataFrame): Set of locations of a network to choose from for home and work anchors
            gdf_event (GeoDataFrame): Set of locations of a network to choose from for regular event anchors
            radius_buffer_h_w (int): Radius to create a buffer around home anchor to search for work anchor
            radius_buffer_h_w (int): Radius to create a buffer around home anchor to search for regular event anchors
        """

        home_id = random.randint(0, len(gdf_hw)-1)
        home_geometry = gdf_hw.iloc[home_id]['geometry']
        # TODO: too conditionally nested think about a better approach
        while True:

            work_id = self.get_random_id_within_buffer(home_geometry, radius_buffer_h_w, gdf_hw)
            # if there are not many possible work anchor locations around
            if work_id == None:
                # chnage home id 
                home_id = random.randint(0, len(gdf_hw)-1)
                home_geometry = gdf_hw.iloc[home_id]['geometry']
                continue
            # if the same just choose another work id, but don't change home anchor
            elif home_id == work_id:
                continue

            else: 
                regular_locations_ids = []
                number_of_regular_locations = random.randint(3, 5)
                i = 0
                while i <= number_of_regular_locations:
                    regular_id = self.get_random_id_within_buffer(home_geometry, radius_buffer_h_r, gdf_event)

                    # if there are not many possible regular event anchors around increase search radius
                    if regular_id == None:
                        radius_buffer_h_r += 100
                        continue
                    # if id is already used, chooses another one
                    elif regular_id in regular_locations_ids or regular_id==home_id or regular_id==work_id:
                        continue
                    else:
                        regular_locations_ids.append(regular_id)
                        i += 1

                self.home_id = home_id
                self.work_id = work_id
                self.regular_loc_array = regular_locations_ids
                break

    def get_regular_or_random_loc(self,
                                  gdf_event: GeoDataFrame,
                                  regular_location_ids: List[int],
                                  number_of_events: int) -> List[int]:
        """
        Randomly create a list with specified number of event ids, which could be either from regular event locations or completely accidental

        Args: 
            gdf_event (GeoDataFrame): Set of locations of a network to choose from for regular event anchors
            regular_location_ids (List[int]): List of regular event locations' ids
            number_of_events (int): A number of event ids tom create

        Returns: 
            List[int]: List of event ids for a userto visit within a day
        """
        event_id_list = []
        while len(event_id_list) < number_of_events:
            choose_reg_or_random = random.choices(
                ["reg", "random"], weights=[0.6, 0.4], k=1)[0]
            if choose_reg_or_random == "reg":
                event_id = random.choice(regular_location_ids)
            else:
                event_id = random.randint(0, len(gdf_event)-1)

            if event_id not in event_id_list:
                event_id_list.append(event_id)
            else:
                continue

        return event_id_list

    def get_info_about_loc(self, df_loc: DataFrame, list_of_ids: List[int]) -> List[List[Union[int, float]]]:
        """
        Based on id of a location find some information about it and store in a list

        Args: 
            df_loc (DataFrame): Set of locations of a network and their features to search in based on id 
            list_of_ids (List[int]): List of locations' ids to derive some information about

        Returns:
            List[List[Union[int, float]]]: List of lists, each element has three items: nearest node id and lat and lon coordinates of location's centroid
        """

        list_of_info = []
        for loc_id in list_of_ids:
            list_of_info.append([df_loc.iloc[loc_id]['nearest_node_id'],
                                df_loc.iloc[loc_id]['geometry'].x,
                                df_loc.iloc[loc_id]['geometry'].y])

        return list_of_info

    def create_list_of_locations(self,
                                 gdf_hw: GeoDataFrame,
                                 gdf_event: GeoDataFrame,
                                 home_id: int,
                                 work_id: int,
                                 regular_location_ids: List[int],
                                 day_of_week: int,) -> List[List[Union[int, float]]]:
        """
        Based on day of week define type and number of locations to visit for a user within a day
        and derive information about them

        Args:
            gdf_hw (GeoDataFrame): Set of locations (and their features) of a network to use from for home and work anchors
            gdf_event (GeoDataFrame): Set of locations (and their features) of a network to use for regular and random event anchors
            home_id (int): Id of home anchor
            work_id (int): Id of work anchor
            regular_location_ids (List[int]): List of regular event locations' ids
            day_of_week (int): _description_

        Returns: 
            List[List[Union[int, float]]]: List of lists, each element has three items: nearest node id and lat and lon coordinates of location's centroid

        """
        if day_of_week < 6:
            number_of_events = random.choices(
                [0, 1, 2, 3], weights=[0.6, 0.25, 0.1, 0.05], k=1)[0]
            list_of_ids = [home_id, work_id]
        else:
            number_of_events = random.choices(
                [0, 1, 2, 3, 4], weights=[0.1, 0.2, 0.30, 0.25, 0.15], k=1)[0]
            list_of_ids = [home_id]

        event_id_list = self.get_regular_or_random_loc(
            gdf_event, regular_location_ids, number_of_events)

        list_of_locations_not_event = self.get_info_about_loc(
            gdf_hw, list_of_ids)
        list_of_locations_event = self.get_info_about_loc(
            gdf_event, event_id_list)

        list_of_locations = list_of_locations_not_event + list_of_locations_event

        return list_of_locations

    def get_static_points(self,
                          user_id: int,
                          data_array: List[List[Union[int, float, Timestamp]]],
                          startlon: float,
                          startlat: float,
                          time_start: Timestamp,
                          time_end: Timestamp) -> Timestamp:
        """
        Generate the nearby points around some coordinates (the centroid point of a user’s location)

        Args: 
            userd_id (int): Id of a user
            data_array (List[List[Union[int, float, Timestamp]]]): List to store user's GPS data (user_id, lon, lat, timestamp)
            startlon (float): Longitude of a point where to start generating nearby points (more precisely their coordinates)
            startlat (float): Latitude of a point where to start generating nearby points (more precisely their coordinates)
            time_start (Timestamp): Timestamp from which to start generating static points
            time_end (Timestamp): Upper timestamp limit of genaration 

        Returns:
            Timestamp: Time from which to start generating GPS data for another activity 
        """
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

    def get_points_on_path(self,
                           path: LineString,
                           number_of_points: int) -> List[Point]:
        """
        Generate mostly equally distanced points along path between its start and end point

        Args: 
            path (LineString): A line along which to generate points
            number_of_points (int): Number of points to generate along the path (it includes the start and end point)

        Returns: 
            List[Point]: List of points placed on the path 
        """

        distances = np.linspace(0, path.length, number_of_points)
        points = [path.interpolate(distance) for distance in distances]

        return points

    def get_chaotic_point(self,
                          point_start: Point,
                          point_end: Point,
                          radius_of_buffer: int,
                          proximity_to_road: int) -> Point:
        """
        Produce one chaotic point between two points
        meaning that with very high likelihood it will not be located on the path but near to it. 
        Applied to make a movement look more humanlike

        Args: 
            point_start (Point): _description_
            point_end (Point): _description_
            radius_of_buffer (int): A radius to define a potential space for a chaotic point
            proximity_to_road (int): A distance to define how a chaotic point should be from a path

        Returns: 
            Point: A chaotic point
        """

        points_intersection = point_start.buffer(
            radius_of_buffer).intersection(point_end.buffer(radius_of_buffer))
        path_between_points = LineString([point_start, point_end])
        final_intersection = points_intersection.intersection(
            path_between_points.buffer(proximity_to_road))
        min_x, min_y, max_x, max_y = final_intersection.bounds
        while True:
            chaotic_point = Point(
                [random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
            if chaotic_point.within(final_intersection):
                return chaotic_point
            else:
                continue

    def get_moving_points(self,
                          user_id: int,
                          data_array: List[List[Union[int, float, Timestamp]]],
                          graph_proj: MultiDiGraph,
                          nodes: GeoDataFrame,
                          start_node: int,
                          end_node: int,
                          start_coords: Tuple[float, float],
                          end_coords: Tuple[float, float],
                          mean_move_speed_ms: Union[int, float],
                          proximity_to_road: int,
                          time_start: Timestamp) -> Timestamp:
        """
        First create route between origin and destination locations, interpolate this path with points, 
        and create GPS data while moving from point to point

        Args: 
            userd_id (int): Id of a user
            data_array (List[List[Union[int, float, Timestamp]]]): List to store user's GPS data (user_id, lon, lat, timestamp)
            graph_proj (MultiDiGraph): Projected graph of a network
            nodes (GeoDataFrame): Nodes of netwrok's projected graph
            start_node (int): Id of the nearest node to a start location
            end_node (int): Id of the nearest node to an end location
            start_coords Tuple[float, float]: Lon and lat of start location
            end_coords Tuple[float, float]: Lon and lat of end location
            mean_move_speed_ms Union[int, float]: _description_
            proximity_to_road (int): A distance to define how a chaotic point should be from a path
            time_start (Timestamp): Timestamp from which to start generating moving points

         Returns:
            Timestamp: Time from which to start generating GPS data for another activity 
        """
        # get the shortest route from start to end node
        route = ox.distance.shortest_path(
            graph_proj, start_node, end_node, weight="length")
        route_nodes = nodes.loc[route]
        route_list = list(route_nodes.geometry.values)
        # add start location's coordinates to the beggining
        # add end location's coordinates to the end
        # not all always locations are near to a network
        route_list.insert(0, Point(start_coords[0], start_coords[1]))
        route_list.append(Point(end_coords[0], end_coords[1]))
        path = LineString(route_list)

        # to make sure that the time difference between
        # two consecutive points is not higher than 10 seconds
        # To mimic GPS tracking frequency (it could be even 1 second, but then the amount of data could be enormous)
        min_dist_between_conseq_points = mean_move_speed_ms * 10

        if path.length <= min_dist_between_conseq_points:
            number_of_points = 2
        else:
            number_of_points = math.ceil(
                path.length/min_dist_between_conseq_points)

        points = self.get_points_on_path(path, number_of_points)

        # iterate through each point of created route
        for i in range(number_of_points):
            # even though the actual path and points are in projected CRS
            # the final coordinates should be in WGS 84
            endLon, endLat = self.transformer_to_WGS.transform(
                points[i].x, points[i].y)
            # if not a last point calculate a chaotic point
            if i != number_of_points-1:
                chaotic_point = self.get_chaotic_point(
                    points[i], points[i+1], min_dist_between_conseq_points, proximity_to_road)
                distance_to_chaotic_point = LineString(
                    [points[i], chaotic_point]).length
                # discard situations when start point and a chaotic point are too close and thus time difference would be too small
                # we build the model and don't want to use a lot of memory
                if distance_to_chaotic_point < mean_move_speed_ms*2:
                    time_to_chaotic_point = 2
                else:
                    time_to_chaotic_point = distance_to_chaotic_point/mean_move_speed_ms

                # Add current point's coordinates and the time it was registered in data array
                time_gps = time_start.round(freq='S')
                data_array.append([user_id, time_gps, endLon, endLat])

                # Add time taken to reach a chaotic point
                time_start += timedelta(seconds=time_to_chaotic_point)

                # Change the current coordinates to coordinate of a chaotic point and project to WGS 84
                endLon, endLat = self.transformer_to_WGS.transform(
                    chaotic_point.x, chaotic_point.y)
                # Lenght from chaotic point to the next point or maybe it will be more clear - end point
                distance_to_next_point = LineString(
                    [chaotic_point, points[i+1]]).length
                # discard to precise situations
                if distance_to_next_point < mean_move_speed_ms*2:
                    time_to_next_point = 2
                else:
                    time_to_next_point = distance_to_next_point/mean_move_speed_ms

                # Add chaotic point's coordinates and the time it was registered in data array
                time_gps = time_start.round(freq='S')
                data_array.append([user_id, time_gps, endLon, endLat])

                # Add time taken to reach a the next point
                # It will become a start time of the next iteration of a loop
                time_start += timedelta(seconds=time_to_next_point)

            # if last point in the route - add it and its time to data array
            else:
                endLon, endLat = self.transformer_to_WGS.transform(
                    points[i].x, points[i].y)
                time_gps = time_start.round(freq='S')
                data_array.append([user_id, time_gps, endLon, endLat])

        return time_start.round(freq='S')

    @abstractmethod
    def random_plot_of_day(self):
        pass

    @abstractmethod
    def generate_gps(self):
        pass
