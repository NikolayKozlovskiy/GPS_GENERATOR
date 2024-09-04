from typing import List

import osmnx as ox
from networkx import MultiDiGraph
from pandas import DataFrame


class Network:
    def __init__(self, profile_network_config):
        self.network_name = profile_network_config["NETWORK_NAME"]
        self.place_name = profile_network_config["PLACE_NAME"]
        self.network_type = profile_network_config["NETWORK_TYPE"]
        self.osm_tags_for_hw = profile_network_config["OSM_TAGS_FOR_HOME_AND_WORK"]
        self.osm_tags_for_event = profile_network_config["OSM_TAGS_FOR_EVENT"]

        self.graph_proj = None
        self.graph_crs = None
        self.nodes = None

        self.gdf_hw = None
        self.gdf_event = None

    def prepare_graph(self, place_name: str, network_type: str) -> None:
        """
        Prepare all needed graph's features to properly create movements along this graph
        and store them in instance attributes of a Network class

        Args:
            place_name (str): A name of place in which a graph should be derived
            network_type (str): What type of street network to get if custom_filter is None
        """
        graph = ox.graph_from_place(place_name, network_type=network_type)
        graph_proj = ox.project_graph(graph)
        nodes = ox.graph_to_gdfs(graph_proj, nodes=True, edges=False)
        graph_crs = nodes.crs

        self.graph_proj = graph_proj
        self.graph_crs = graph_crs
        self.nodes = nodes

    def create_locations(
        self,
        place_name: str,
        osm_tags_for_hw: List[str],
        osm_tags_for_event: List[str],
        graph_proj: MultiDiGraph,
        graph_crs: int,
    ) -> DataFrame:
        """
        Derive OSM locations based on specified tags, leave only those that have geometry,
        derived centorid of the locations (since some of them could be not a Point but Polygon/MultiPolygon),
        find nearest network's node to a locationa and calculates distance to it (some locations can be quite far from network)

        Args:
            place_name (str): A name of place in which OSM locations should be derived
            osm_tags_for_hw (List[str]): List of OSM tags to use for search location of home/work anchor points
            osm_tags_for_event (List[str]): List of OSM tags to use for search location of event anchor points
            graph_proj (MultiDiGraph): A graph with nodes and edges
            graph_crs (int): EPSG of a graph's CRS

        Returns:
            Dataframe: All locations from OSM filtered by tag and geometry coditions, and with several new computed columns
        """
        combined_osm_tags = osm_tags_for_hw + osm_tags_for_event
        gdf_locations = ox.features_from_place(
            place_name, tags=dict.fromkeys(combined_osm_tags, True)
        )
        geometry_condition = ~(
            gdf_locations["geometry"].isna() | gdf_locations["geometry"].empty
        )
        columns_to_save = ["name", "geometry"] + combined_osm_tags

        gdf_locations = gdf_locations[geometry_condition][columns_to_save].to_crs(
            graph_crs
        )
        gdf_locations["geometry"] = gdf_locations["geometry"].centroid
        gdf_locations["nearest_node_id"], gdf_locations["distance_to_node"] = (
            ox.distance.nearest_nodes(
                graph_proj,
                gdf_locations["geometry"].x,
                gdf_locations["geometry"].y,
                return_dist=True,
            )
        )

        return gdf_locations

    def get_specific_type_of_locations(
        self,
        gdf_locations: DataFrame,
        filter_columns: List[str],
        delete_columns: List[str],
    ) -> DataFrame:
        """
        Take location dataframe and filtered it by the condition that there should be at least one not null value
        in tag columns connected to some anchor point and then delete all unnecessary columns (columns with tag information)

        Args:
            df_locations (DataFrame): All locations to be used for anchor points of users
            filter_columns (List[str]): List of OSM tags (and also column names) to check for nulls
            delete_columns (List[str]): List of OSM tags (and also column names) to delete after filtering

        Returns:
            DataFrame: Filtered locations dataframe
        """

        return gdf_locations[gdf_locations[filter_columns].notnull().any(axis=1)][
            list(set(gdf_locations.columns) - set(delete_columns))
        ].reset_index()

    def run(self):
        # pylint: disable=missing-function-docstring
        # prepare graph and enrich instance attributes
        self.prepare_graph(self.place_name, self.network_type)
        # create location for anchor points
        gdf_locations = self.create_locations(
            self.place_name,
            self.osm_tags_for_hw,
            self.osm_tags_for_event,
            self.graph_proj,
            self.graph_crs,
        )

        filter_columns_hw = self.osm_tags_for_hw
        filter_columns_event = self.osm_tags_for_event

        delete_columns = filter_columns_hw + filter_columns_event

        # filter locations for home and work anchor points and store in df_hw attribute
        self.gdf_hw = self.get_specific_type_of_locations(
            gdf_locations, filter_columns_hw, delete_columns
        )
        # filter locations for event anchor points and store in df_event attribute
        self.gdf_event = self.get_specific_type_of_locations(
            gdf_locations, filter_columns_event, delete_columns
        )

        del gdf_locations
