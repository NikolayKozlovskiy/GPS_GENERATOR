import osmnx  as ox
from networkx import MultiDiGraph
from typing import List
from geopandas import GeoDataFrame

class Network:
    def __init__(self, place_name, profile_config) -> None:
        self.place_name = place_name
        self.network_type = profile_config['NETWORK_PARAMS']['NETWORK_TYPE']
        self.osm_tags_for_hw = profile_config['NETWORK_PARAMS']['OSM_TAGS_FOR_HOME_AND_WORK']
        self.osm_tags_for_event = profile_config['NETWORK_PARAMS']['OSM_TAGS_FOR_EVENT']

        self.graph_proj = None
        self.graph_crs = None
        self.nodes = None
        self.gdf_locations = None
        self.gdf_hw = None
        self.gdf_event = None

    def create_graph(self, place_name: str, network_type: str) -> None:
        graph = ox.graph_from_place(place_name, network_type=network_type) 
        graph_proj = ox.project_graph(graph)

        self.graph_proj = graph_proj
    
    def create_locations(self, osm_tags_for_hw: List,  osm_tags_for_event: List, place_name: str, graph_proj: MultiDiGraph) -> None:
        combined_osm_tags = osm_tags_for_hw + osm_tags_for_event
        gdf_locations = ox.features_from_place(place_name, tags=dict.fromkeys(combined_osm_tags, True))
        geometry_condition = ~(gdf_locations['geometry'].isna()|gdf_locations['geometry'].empty)
        columns_to_save = ['name', 'geometry'] + combined_osm_tags
        nodes = ox.graph_to_gdfs(graph_proj, nodes=True, edges=False)
        graph_crs = nodes.crs
        gdf_locations = gdf_locations[geometry_condition][columns_to_save].to_crs(graph_crs)
        gdf_locations['center_x']=gdf_locations['geometry'].centroid.x
        gdf_locations['center_y']=gdf_locations['geometry'].centroid.y
        gdf_locations['nearest_node_id'], gdf_locations['distance_to_node']=ox.distance.nearest_nodes\
                                            (graph_proj, gdf_locations['center_x'], gdf_locations['center_y'], return_dist = True)
        
        self.graph_crs = graph_crs
        self.nodes = nodes
        self.gdf_locations = gdf_locations
    
    def get_specific_type_of_locations(self, gdf_locations: GeoDataFrame, filter_columns: List) -> GeoDataFrame: 
        delete_columns = self.osm_tags_for_hw + self.osm_tags_for_event
        return  gdf_locations[gdf_locations[filter_columns].notnull().any(axis=1)][list(set(gdf_locations.columns) - set(delete_columns))]\
                                                                                                                            .reset_index()

    def run(self): 

        self.create_graph(self.place_name, self.network_type)
        self.create_locations(self.osm_tags_for_hw, self.osm_tags_for_event, self.place_name, self.graph_proj)

        filter_columns_hw = self.osm_tags_for_hw
        filter_columns_event = self.osm_tags_for_event

        self.gdf_hw = self.get_specific_type_of_locations(self.gdf_locations, filter_columns_hw)
        self.gdf_event = self.get_specific_type_of_locations(self.gdf_locations, filter_columns_event)

        print('Network class is ready')


