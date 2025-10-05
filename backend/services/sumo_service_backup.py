import os
import time
import threading
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional
from models.eta_predictor import ETAPredictor, calculate_traffic_density, get_time_of_day_fraction
from models.entities import Junction, Road, Zone, Vehicle
# Database support removed - using in-memory only

import json
import random
from sumolib import net as sumo_net
import traci
import traci.constants as tc
from tqdm import tqdm

class SUMOSimulation:
    """
    SUMO simulation service for traffic simulation and ETA prediction
    """
    
    def __init__(self, sumo_config_path: str, sim_config_path: str):
        """
        Initialize the SUMO simulation with configuration files
        """
        self.sumo_config_path = sumo_config_path
        self.sim_config_path = sim_config_path
        
        # Load configuration
        with open(sim_config_path) as f:
            self.config = json.load(f)
        
        # Extract network file path from SUMO config
        import xml.etree.ElementTree as ET
        tree = ET.parse(sumo_config_path)
        root = tree.getroot()
        net_file_elem = root.find('.//net-file')
        if net_file_elem is not None:
            net_file_path = os.path.join(os.path.dirname(sumo_config_path), net_file_elem.get('value'))
            self.net = sumo_net.readNet(net_file_path)
        else:
            # Fallback to direct path
            self.net = sumo_net.readNet(sumo_config_path)
        
        # Initialize simulation state
        self.simulation_running = False
        self.simulation_thread = None
        self.current_step = 0
        self.data_loaded = False  # Flag to track if all static data is loaded
        
        # Initialize data structures
        self.vehicles = {}
        self.junctions = {}
        self.roads = {}
        self.zones = {}
        self.vehicles_in_route = set()  # Set to track vehicles currently in route
        self.schedule = {}  # Dictionary to store vehicle schedule
        self.ground_truth_labels = []  # List to store ground truth trip data
        
        # Load all static data
        self.load_static_data()
        
        # Initialize other components
        self.eta_predictor = ETAPredictor()
        
        # Initialize logger
        import logging
        self.log = logging.getLogger(__name__)
        
        # Network data for visualization
        self.network_data = None
        self.network_bounds = None
    
    def load_static_data(self):
        """
        Load all static data in the correct order:
        1. Roads and junctions
        2. Zones
        3. Vehicles
        4. Schedule
        """
        print("🚀 Loading static data...")
        
        # Step 1: Load roads and junctions
        print("📊 Step 1: Loading roads and junctions...")
        self.read_zones_and_roads_from_sumo()
        
        # Step 2: Load vehicles
        print("🚗 Step 2: Loading vehicles...")
        self.populate_vehicles_from_config(self.config)
        
        # Step 3: Load schedule (before clearing zones)
        print("📅 Step 3: Loading schedule...")
        self.schedule_from_config(self.config)
        
        # Step 4: Clear roads and zones (prepare for simulation)
        print("🧹 Step 4: Preparing for simulation...")
        self.clear_roads_and_zones()
        
        # Mark data as loaded
        self.data_loaded = True
        print("✅ All static data loaded successfully!")
    
    def is_data_loaded(self) -> bool:
        """
        Check if all static data has been loaded
        """
        return self.data_loaded
        
    def start_simulation(self) -> bool:
        """
        Start SUMO simulation
        """
        if not self.is_data_loaded():
            print("❌ Cannot start simulation: Data not loaded yet")
            return False
            
        try:
            # For now, just mark simulation as running without actually starting SUMO
            # This is a simplified version for the demo
            self.simulation_running = True
            
            # Start simulation thread (simplified)
            self.simulation_thread = threading.Thread(target=self.run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Error starting SUMO simulation: {e}")
            return False
    
    def stop_simulation(self):
        """
        Stop SUMO simulation
        """
        self.simulation_running = False
    
    def add_vehicle(self, route: List[str], vehicle_id: str = None) -> str:
        """
        Add a new vehicle to the simulation (simplified for demo)
        
        Args:
            route: List of edge IDs for the route
            vehicle_id: Optional custom vehicle ID
        
        Returns:
            Vehicle ID
        """
        if vehicle_id is None:
            vehicle_id = f"vehicle_{len(self.vehicles) + 1}"
        
        try:
            # Add vehicle to our internal tracking
            self.vehicles[vehicle_id] = {
                'id': vehicle_id,
                'position': (100 + len(self.vehicles) * 50, 200),
                'speed': 10.0 + len(self.vehicles) * 2,
                'route': route,
                'last_update': time.time()
            }
            
            return vehicle_id
            
        except Exception as e:
            print(f"Error adding vehicle: {e}")
            return None
    
    def get_vehicle_position(self, vehicle_id: str) -> Tuple[float, float]:
        """
        Get vehicle position
        
        Args:
            vehicle_id: Vehicle ID
        
        Returns:
            (x, y) position tuple
        """
        if vehicle_id in self.vehicles:
            return self.vehicles[vehicle_id]['position']
        return (0, 0)
    
    def get_vehicle_speed(self, vehicle_id: str) -> float:
        """
        Get vehicle speed
        
        Args:
            vehicle_id: Vehicle ID
        
        Returns:
            Speed in m/s
        """
        if vehicle_id in self.vehicles:
            return self.vehicles[vehicle_id]['speed']
        return 0.0
    
    def predict_eta(self, vehicle_id: str, destination: Tuple[float, float]) -> float:
        """
        Predict ETA for a vehicle to reach destination
        
        Args:
            vehicle_id: Vehicle ID
            destination: (x, y) destination coordinates
        
        Returns:
            Predicted ETA in seconds
        """
        if vehicle_id not in self.vehicles:
            return 0.0
        
        vehicle = self.vehicles[vehicle_id]
        current_pos = vehicle['position']
        current_speed = vehicle['speed']
        
        # Calculate distance to destination
        distance = ((destination[0] - current_pos[0])**2 + 
                   (destination[1] - current_pos[1])**2)**0.5
        
        # Calculate traffic density
        traffic_density = calculate_traffic_density(
            list(self.vehicles.values()), 
            1000.0  # Road length
        )
        
        # Get time of day
        time_of_day = get_time_of_day_fraction()
        
        # Predict ETA using the model
        eta = self.eta_predictor.predict_eta(
            distance=distance,
            current_speed=current_speed,
            traffic_density=traffic_density,
            time_of_day=time_of_day
        )
        
        return eta
    
    def get_route_distance(self, start: Tuple[float, float], 
                          end: Tuple[float, float]) -> float:
        """
        Calculate route distance between two points
        
        Args:
            start: Start coordinates (x, y)
            end: End coordinates (x, y)
        
        Returns:
            Distance in meters
        """
        return ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
    
    def calculate_route(self, start_coords: Tuple[float, float], 
                       end_coords: Tuple[float, float]) -> Dict:
        """
        Calculate the shortest route between two points using SUMO
        
        Args:
            start_coords: Start coordinates (x, y) in network coordinates
            end_coords: End coordinates (x, y) in network coordinates
        
        Returns:
            Dictionary containing route information
        """
        try:
            print(f"🔍 Calculating route from {start_coords} to {end_coords}")
            
            # Find the nearest edges to the start and end points
            start_edge = self._find_nearest_edge(start_coords)
            end_edge = self._find_nearest_edge(end_coords)
            
            print(f"📍 Found edges: start={start_edge}, end={end_edge}")
            
            if not start_edge or not end_edge:
                return {
                    "success": False,
                    "error": "Could not find suitable edges for route calculation"
                }
            
            # Use SUMO's duarouter to calculate the route
            route_edges = self._calculate_route_edges(start_edge, end_edge)
            print(f"🛣️ Route edges: {route_edges}")
            
            if not route_edges:
                return {
                    "success": False,
                    "error": "No valid route found between the points"
                }
            
            # Calculate route distance and estimated travel time
            route_distance = self._calculate_route_distance(route_edges)
            print(f"📏 Route distance: {route_distance}")
            
            if route_distance <= 0:
                return {
                    "success": False,
                    "error": f"Invalid route distance: {route_distance}"
                }
            
            estimated_time = self._estimate_travel_time(route_distance)
            print(f"⏱️ Estimated time: {estimated_time}")
            
            return {
                "success": True,
                "route_edges": route_edges,
                "start_edge": start_edge,
                "end_edge": end_edge,
                "distance": route_distance,
                "estimated_time": estimated_time,
                "start_coords": start_coords,
                "end_coords": end_coords
            }
            
        except Exception as e:
            print(f"❌ Route calculation error: {str(e)}")
            return {
                "success": False,
                "error": f"Route calculation failed: {str(e)}"
            }
    
    def calculate_route_by_edges(self, start_edge: str, end_edge: str) -> Dict:
        """
        Calculate the shortest route between two edges using SUMO
        
        Args:
            start_edge: Starting edge ID
            end_edge: Ending edge ID
        
        Returns:
            Dictionary containing route information
        """
        try:
            print(f"🔍 Calculating route from edge {start_edge} to {end_edge}")
            
            # Validate that both edges exist in the network
            if not self._edge_exists(start_edge):
                return {
                    "success": False,
                    "error": f"Start edge '{start_edge}' not found in network"
                }
            
            if not self._edge_exists(end_edge):
                return {
                    "success": False,
                    "error": f"End edge '{end_edge}' not found in network"
                }
            
            # Calculate route between edges
            route_edges = self._calculate_route_edges(start_edge, end_edge)
            print(f"🛣️ Route edges: {route_edges}")
            
            if not route_edges:
                return {
                    "success": False,
                    "error": "No valid route found between the edges"
                }
            
            # Calculate route distance and estimated travel time
            try:
                route_distance = self._calculate_route_distance(route_edges)
                print(f"📏 Route distance: {route_distance}")
                
                if route_distance <= 0:
                    return {
                        "success": False,
                        "error": f"Invalid route distance: {route_distance}"
                    }
                
                estimated_time = self._estimate_travel_time(route_distance)
                print(f"⏱️ Estimated time: {estimated_time}")
                
                return {
                    "success": True,
                    "route_edges": route_edges,
                    "start_edge": start_edge,
                    "end_edge": end_edge,
                    "distance": route_distance,
                    "estimated_time": estimated_time
                }
            except Exception as e:
                print(f"❌ Distance calculation error: {str(e)}")
                return {
                    "success": False,
                    "error": f"Distance calculation failed: {str(e)}"
                }
            
        except Exception as e:
            print(f"❌ Route calculation error: {str(e)}")
            return {
                "success": False,
                "error": f"Route calculation failed: {str(e)}"
            }
    
    def _edge_exists(self, edge_id: str) -> bool:
        """
        Check if an edge exists in the network
        
        Args:
            edge_id: Edge ID to check
        
        Returns:
            True if edge exists, False otherwise
        """
        if not self.network_data or 'edges' not in self.network_data:
            return False
        
        exists = any(edge.get('id') == edge_id for edge in self.network_data['edges'])
        
        if not exists:
            # Debug: Show some sample edge IDs for comparison
            sample_edges = [edge.get('id') for edge in self.network_data['edges'][:10]]
            print(f"❌ Edge '{edge_id}' not found. Sample edge IDs: {sample_edges}")
        
        return exists
    
    def _find_nearest_edge(self, coords: Tuple[float, float]) -> Optional[str]:
        """
        Find the nearest edge to the given coordinates
        
        Args:
            coords: Coordinates (x, y) in network coordinates
        
        Returns:
            Edge ID of the nearest edge, or None if not found
        """
        if not self.network_data or not self.network_data.get('edges'):
            print(f"❌ No network data or edges available")
            return None
        
        print(f"🔍 Looking for nearest edge to {coords}")
        print(f"📊 Total edges available: {len(self.network_data['edges'])}")
        
        min_distance = float('inf')
        nearest_edge = None
        
        # network_data['edges'] is a list, not a dictionary
        for edge_data in self.network_data['edges']:
            if not edge_data.get('lanes'):
                continue
                
            # Check each lane of the edge
            for lane in edge_data['lanes']:
                if not lane.get('shape'):
                    continue
                    
                # Calculate distance to the lane
                for i in range(len(lane['shape']) - 1):
                    x1, y1 = float(lane['shape'][i][0]), float(lane['shape'][i][1])
                    x2, y2 = float(lane['shape'][i + 1][0]), float(lane['shape'][i + 1][1])
                    
                    # Calculate distance from point to line segment
                    distance = self._point_to_line_distance(coords, (x1, y1), (x2, y2))
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_edge = edge_data['id']  # Get edge ID from the edge data
        
        print(f"✅ Found nearest edge: {nearest_edge} (distance: {min_distance})")
        return nearest_edge
    
    def _point_to_line_distance(self, point: Tuple[float, float], 
                               line_start: Tuple[float, float], 
                               line_end: Tuple[float, float]) -> float:
        """
        Calculate the distance from a point to a line segment
        
        Args:
            point: Point coordinates (x, y)
            line_start: Line start coordinates (x, y)
            line_end: Line end coordinates (x, y)
        
        Returns:
            Distance in meters
        """
        # Ensure all coordinates are floats
        px, py = float(point[0]), float(point[1])
        x1, y1 = float(line_start[0]), float(line_start[1])
        x2, y2 = float(line_end[0]), float(line_end[1])
        
        # Calculate the distance from point to line segment
        A = px - x1
        B = py - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        
        param = dot / len_sq
        
        if param < 0:
            xx, yy = x1, y1
        elif param > 1:
            xx, yy = x2, y2
        else:
            xx = x1 + param * C
            yy = y1 + param * D
        
        return ((px - xx) ** 2 + (py - yy) ** 2) ** 0.5
    
    def _calculate_route_edges(self, start_edge: str, end_edge: str) -> List[str]:
        """
        Calculate the route edges between start and end edges using BFS pathfinding
        
        Args:
            start_edge: Starting edge ID
            end_edge: Ending edge ID
        
        Returns:
            List of edge IDs forming the route
        """
        if start_edge == end_edge:
            return [start_edge]
        
        if not self.network_data or 'edges' not in self.network_data:
            return [start_edge, end_edge]
        
        print(f"🔍 Finding path from {start_edge} to {end_edge}")
        
        # Build adjacency list from network data
        adjacency = self._build_adjacency_list()
        print(f"🔍 Built adjacency list with {len(adjacency)} edges")
        
        # Show some sample connections
        sample_connections = [(k, len(v)) for k, v in list(adjacency.items())[:5]]
        print(f"🔍 Sample connections: {sample_connections}")
        
        # Use BFS to find shortest path
        route = self._find_shortest_path(adjacency, start_edge, end_edge)
        
        if not route:
            print(f"❌ No path found from {start_edge} to {end_edge}")
            return [start_edge, end_edge]
        
        print(f"✅ Found path: {route}")
        return route
    
    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """
        Build adjacency list from network data
        """
        adjacency = {}
        
        if not self.network_data or 'edges' not in self.network_data:
            return adjacency
        
        # First, collect all edge IDs
        for edge in self.network_data['edges']:
            edge_id = edge.get('id')
            if edge_id:
                adjacency[edge_id] = []
        
        # Build connections based on network topology
        # This is a simplified approach - in reality, you'd use SUMO's junction data
        for edge in self.network_data['edges']:
            edge_id = edge.get('id')
            if not edge_id:
                continue
                
            # Find edges that share coordinates (simplified connection detection)
            edge_coords = self._get_edge_coordinates(edge)
            if not edge_coords:
                continue
                
            for other_edge in self.network_data['edges']:
                other_id = other_edge.get('id')
                if not other_id or other_id == edge_id:
                    continue
                    
                other_coords = self._get_edge_coordinates(other_edge)
                if not other_coords:
                    continue
                
                # Check if edges are connected (share an endpoint)
                if self._are_edges_connected(edge_coords, other_coords):
                    if other_id not in adjacency[edge_id]:
                        adjacency[edge_id].append(other_id)
        
        return adjacency
    
    def _get_edge_coordinates(self, edge: Dict) -> List[Tuple[float, float]]:
        """
        Get coordinates for an edge
        """
        if 'lanes' not in edge or not edge['lanes']:
            return []
        
        # Use the first lane's coordinates
        lane = edge['lanes'][0]
        if 'shape' not in lane:
            return []
        
        shape = lane['shape']
        if isinstance(shape, list) and len(shape) > 0:
            if isinstance(shape[0], dict):
                # Dictionary format: [{'x': x1, 'y': y1}, {'x': x2, 'y': y2}]
                return [(float(point['x']), float(point['y'])) for point in shape]
            elif isinstance(shape[0], (list, tuple)) and len(shape[0]) >= 2:
                # Coordinate pairs format: [[x1, y1], [x2, y2]]
                return [(float(coord[0]), float(coord[1])) for coord in shape]
        
        return []
    
    def _are_edges_connected(self, coords1: List[Tuple[float, float]], 
                           coords2: List[Tuple[float, float]]) -> bool:
        """
        Check if two edges are connected (share an endpoint)
        """
        if not coords1 or not coords2:
            return False
        
        # Get endpoints of both edges
        start1, end1 = coords1[0], coords1[-1]
        start2, end2 = coords2[0], coords2[-1]
        
        # Check if any endpoint of edge1 matches any endpoint of edge2
        tolerance = 10.0  # Increased tolerance to 10 meters
        for p1 in [start1, end1]:
            for p2 in [start2, end2]:
                distance = ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
                if distance < tolerance:
                    return True
        
        return False
    
    def _find_shortest_path(self, adjacency: Dict[str, List[str]], 
                          start: str, end: str) -> List[str]:
        """
        Find shortest path using BFS
        """
        if start not in adjacency or end not in adjacency:
            return []
        
        if start == end:
            return [start]
        
        # BFS
        queue = [(start, [start])]
        visited = {start}
        
        while queue:
            current, path = queue.pop(0)
            
            for neighbor in adjacency.get(current, []):
                if neighbor == end:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    
    def _calculate_route_distance(self, route_edges: List[str]) -> float:
        """
        Calculate the total distance of a route
        
        Args:
            route_edges: List of edge IDs
        
        Returns:
            Total distance in meters
        """
        total_distance = 0.0
        
        if not self.network_data or 'edges' not in self.network_data:
            print("❌ No network data available for distance calculation")
            return 0.0
        
        edges = self.network_data['edges']
        print(f"🔍 Calculating distance for route edges: {route_edges}")
        
        for edge_id in route_edges:
            # Find the edge in the list
            edge_data = None
            for edge in edges:
                if edge.get('id') == edge_id:
                    edge_data = edge
                    break
            
            if not edge_data:
                print(f"❌ Edge {edge_id} not found in network data")
                continue
                
            if 'lanes' not in edge_data:
                print(f"❌ Edge {edge_id} has no lanes")
                continue
                
            print(f"🔍 Processing edge {edge_id} with {len(edge_data['lanes'])} lanes")
            print(f"🔍 Edge data keys: {list(edge_data.keys())}")
            
            # Calculate edge length from its lanes
            edge_length = 0.0
            for i, lane in enumerate(edge_data['lanes']):
                print(f"🔍 Lane {i}: {lane.get('id', 'unknown')} - keys: {list(lane.keys())}")
                if 'shape' not in lane:
                    print(f"❌ Lane {lane.get('id', 'unknown')} has no shape")
                    continue
                
                print(f"🔍 Lane {lane.get('id', 'unknown')} shape data: {lane['shape']}")
                print(f"🔍 Lane {lane.get('id', 'unknown')} shape type: {type(lane['shape'])}")
                print(f"🔍 Lane {lane.get('id', 'unknown')} shape length: {len(lane['shape']) if hasattr(lane['shape'], '__len__') else 'N/A'}")
                    
                if len(lane['shape']) <= 1:
                    print(f"❌ Lane {lane.get('id', 'unknown')} has insufficient shape points")
                    continue
                    
                # Calculate length of the lane
                lane_length = 0.0
                shape_data = lane['shape']
                
                # Handle different shape data formats
                if isinstance(shape_data, list) and len(shape_data) > 0:
                    if isinstance(shape_data[0], dict):
                        # Shape data is list of dictionaries: [{'x': x1, 'y': y1}, {'x': x2, 'y': y2}]
                        print(f"🔍 Processing dictionary format with {len(shape_data)} points")
                        for i in range(len(shape_data) - 1):
                            try:
                                x1 = float(shape_data[i]['x'])
                                y1 = float(shape_data[i]['y'])
                                x2 = float(shape_data[i + 1]['x'])
                                y2 = float(shape_data[i + 1]['y'])
                                segment_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                                lane_length += segment_length
                                print(f"🔍 Segment {i}: ({x1:.2f},{y1:.2f}) -> ({x2:.2f},{y2:.2f}) = {segment_length:.2f}m")
                            except (KeyError, ValueError, TypeError) as e:
                                print(f"❌ Error processing dictionary segment {i}: {e}")
                                continue
                    elif isinstance(shape_data[0], (list, tuple)) and len(shape_data[0]) >= 2:
                        # Shape data is list of coordinate pairs: [[x1, y1], [x2, y2]]
                        print(f"🔍 Processing coordinate pairs format with {len(shape_data)} points")
                        for i in range(len(shape_data) - 1):
                            try:
                                x1, y1 = float(shape_data[i][0]), float(shape_data[i][1])
                                x2, y2 = float(shape_data[i + 1][0]), float(shape_data[i + 1][1])
                                segment_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                                lane_length += segment_length
                                print(f"🔍 Segment {i}: ({x1:.2f},{y1:.2f}) -> ({x2:.2f},{y2:.2f}) = {segment_length:.2f}m")
                            except (IndexError, ValueError, TypeError) as e:
                                print(f"❌ Error processing coordinate pairs segment {i}: {e}")
                                continue
                    else:
                        print(f"❌ Unknown shape data format: {type(shape_data[0]) if shape_data else 'empty'}")
                        continue
                else:
                    print(f"❌ Invalid shape data: {type(shape_data)}")
                    continue
                
                print(f"📏 Lane {lane.get('id', 'unknown')} length: {lane_length}")
                edge_length = max(edge_length, lane_length)
            
            print(f"📏 Edge {edge_id} total length: {edge_length}")
            total_distance += edge_length
        
        print(f"📏 Total route distance: {total_distance}")
        return total_distance
    
    def _estimate_travel_time(self, distance: float) -> float:
        """
        Estimate travel time based on distance
        
        Args:
            distance: Distance in meters
        
        Returns:
            Estimated travel time in seconds
        """
        # Simple estimation: assume average speed of 30 km/h (8.33 m/s)
        average_speed = 8.33  # m/s
        
        if distance <= 0:
            return 0.0
            
        return distance / average_speed
    
    def get_all_vehicles(self) -> List[Dict]:
        """
        Get all vehicles in the simulation
        
        Returns:
            List of vehicle dictionaries
        """
        return list(self.vehicles.values())
    
    def is_simulation_running(self) -> bool:
        """
        Check if simulation is running
        
        Returns:
            True if simulation is running
        """
        return self.simulation_running
    
    def get_network_data(self) -> Dict:
        """
        Extract network data from SUMO XML file for visualization
        
        Returns:
            Dictionary containing edges, junctions, and bounds
        """
        if self.network_data is not None:
            return self.network_data
            
        try:
            # Parse the network XML file
            network_file = os.path.join(os.path.dirname(self.sumo_config_path), "urban_three_zones.net.xml")
            tree = ET.parse(network_file)
            root = tree.getroot()
            
            edges = []
            junctions = []
            
            # Extract location bounds
            location = root.find('location')
            if location is not None:
                conv_boundary = location.get('convBoundary', '0,0,1000,1000')
                bounds = [float(x) for x in conv_boundary.split(',')]
                self.network_bounds = {
                    'min_x': bounds[0],
                    'min_y': bounds[1], 
                    'max_x': bounds[2],
                    'max_y': bounds[3]
                }
            else:
                # Default bounds if not found
                self.network_bounds = {'min_x': 0, 'min_y': -6264, 'max_x': 18000, 'max_y': 5000}
            
            # Extract edges (roads)
            for edge in root.findall('edge'):
                edge_id = edge.get('id')
                if edge_id and not edge_id.startswith(':'):  # Skip internal edges
                    lanes = []
                    for lane in edge.findall('lane'):
                        shape = lane.get('shape', '')
                        if shape:
                            # Parse shape coordinates
                            coords = []
                            for point in shape.split():
                                x, y = point.split(',')
                                coords.append({'x': float(x), 'y': float(y)})
                            lanes.append({
                                'id': lane.get('id'),
                                'shape': coords,
                                'speed': float(lane.get('speed', 13.89))
                            })
                    
                    if lanes:
                        # Generate a meaningful road name from edge ID
                        road_name = self._generate_road_name(edge_id)
                        edges.append({
                            'id': edge_id,
                            'name': road_name,
                            'lanes': lanes
                        })
            
            # Extract junctions
            for junction in root.findall('junction'):
                junction_id = junction.get('id')
                if junction_id and not junction_id.startswith(':'):  # Skip internal junctions
                    x = float(junction.get('x', 0))
                    y = float(junction.get('y', 0))
                    junctions.append({
                        'id': junction_id,
                        'x': x,
                        'y': y
                    })
            
            self.network_data = {
                'edges': edges,
                'junctions': junctions,
                'bounds': self.network_bounds
            }
            
            print(f"Parsed network: {len(edges)} edges, {len(junctions)} junctions")
            print(f"Network bounds: {self.network_bounds}")
            
            return self.network_data
            
        except Exception as e:
            print(f"Error parsing network file: {e}")
            # Return empty data on error
            return {
                'edges': [],
                'junctions': [],
                'bounds': {'min_x': 0, 'min_y': 0, 'max_x': 1000, 'max_y': 1000}
            }
    
    def _generate_road_name(self, edge_id: str) -> str:
        """
        Generate a meaningful road name from edge ID
        
        Args:
            edge_id: SUMO edge identifier (e.g., "-E0", "AB1", etc.)
            
        Returns:
            Human-readable road name
        """
        # Remove leading dash if present
        clean_id = edge_id.lstrip('-')
        
        # Handle different edge ID patterns
        if clean_id.startswith('E'):
            # Expressway pattern: E0 -> Expressway E0
            return f"Expressway {clean_id}"
        elif clean_id.startswith('A'):
            # Avenue pattern: AB1 -> Avenue AB1
            return f"Avenue {clean_id}"
        elif clean_id.startswith('S'):
            # Street pattern: S1 -> Street S1
            return f"Street {clean_id}"
        elif clean_id.startswith('R'):
            # Road pattern: R1 -> Road R1
            return f"Road {clean_id}"
        elif clean_id.startswith('B'):
            # Boulevard pattern: B1 -> Boulevard B1
            return f"Boulevard {clean_id}"
        else:
            # Default pattern: any other ID -> Road [ID]
            return f"Road {clean_id}"
    
    def read_zones_and_roads_from_sumo(self):
        """
        Read zones and roads from SUMO network file
        """
        print("📥 Loading entities from SUMO network...")
        self._load_entities_from_sumo()
    
    def _load_entities_from_database(self):
        """
        Load entities from database into memory
        """
        # Load junctions
        try:
            db_junctions = get_all_junctions(self.db_session)
            for db_junc in db_junctions:
                junction = Junction(
                    junction_id=db_junc.id,
                    x=db_junc.x,
                    y=db_junc.y,
                    junc_type=db_junc.type,
                    zone=db_junc.zone
                )
                self.junctions[db_junc.id] = junction
            print(f"✅ Loaded {len(self.junctions)} junctions from database")
        except Exception as e:
            print(f"⚠️  Error loading junctions: {e}")
            self.junctions = {}
        
        # Load roads
        try:
            db_roads = get_all_roads(self.db_session)
            for db_road in db_roads:
                road = Road(
                    road_id=db_road.id,
                    from_junction=db_road.from_junction,
                    to_junction=db_road.to_junction,
                    speed=db_road.speed,
                    length=db_road.length,
                    num_lanes=db_road.num_lanes,
                    zone=db_road.zone
                )
                road.density = db_road.density
                road.avg_speed = db_road.avg_speed
                self.roads[db_road.id] = road
            print(f"✅ Loaded {len(self.roads)} roads from database")
        except Exception as e:
            print(f"⚠️  Error loading roads: {e}")
            self.roads = {}
        
        # Load zones
        try:
            db_zones = get_all_zones(self.db_session)
            for db_zone in db_zones:
                zone = Zone(zone_id=db_zone.id, description=db_zone.description)
                
                # Load zone edges
                zone_edges = get_zone_edges(self.db_session, db_zone.id)
                for edge in zone_edges:
                    zone.add_edge(edge.id)
                
                # Load zone junctions
                zone_junctions = get_zone_junctions(self.db_session, db_zone.id)
                for junction in zone_junctions:
                    zone.add_junction(junction.id)
                
                self.zones[db_zone.id] = zone
                print(f"✅ Loaded zone {db_zone.id} from database with {len(zone.edges)} edges and {len(zone.junctions)} junctions")
            
            print(f"✅ Successfully loaded {len(self.junctions)} junctions, {len(self.roads)} roads, {len(self.zones)} zones from database")
            
           
            
        except Exception as e:
            print(f"⚠️  Database loading failed: {e}")
            print("📥 Rolling back database session...")
            try:
                self.db_session.rollback()
                print("✅ Database session rolled back successfully")
            except Exception as rollback_error:
                print(f"⚠️  Rollback error: {rollback_error}")
            
            # If database loading fails, try SUMO loading
            print("📥 Trying SUMO loading...")
            try:
                self._load_entities_from_sumo_and_save()
                print("✅ Loaded entities from SUMO")
            except Exception as e2:
                print(f"⚠️  SUMO loading also failed: {e2}")
                print("📥 Rolling back database session...")
                try:
                    self.db_session.rollback()
                    print("✅ Database session rolled back successfully")
                except Exception as rollback_error:
                    print(f"⚠️  Rollback error: {rollback_error}")
                
                # If both fail, create minimal entities to allow the system to work
                print("📥 Creating minimal entities to allow system to work...")
                self.junctions = {}
                self.roads = {}
                self.zones = {}
                self.vehicles = {}
        
        
    
    def _load_entities_from_sumo_and_save(self):
        """
        Load entities from SUMO network and save to database
        """
        zone_objects = {}

        # 1. Collect junctions by zone attribute
        print("📊 Processing junctions...")
        junction_count = 0
        for junction in self.net.getNodes():
            zone_attr = junction.getParam("zone")
            if not zone_attr:
                continue
            zone_id = zone_attr.upper()
            if zone_id not in zone_objects:
                zone_objects[zone_id] = Zone(zone_id)
                print(f"Zone {zone_id} created.")
            
            junction_count += 1
            if junction_count % 100 == 0:
                print(f"📊 Processed {junction_count} junctions...")

            # Create junction entity
            junc = Junction(
                junction_id=junction.getID(),
                x=junction.getCoord()[0],
                y=junction.getCoord()[1],
                junc_type=junction.getType(),
                zone=zone_id
            )
            self.junctions[junc.id] = junc
            
            # Save to database
            junction_data = {
                "id": junc.id,
                "x": junc.x,
                "y": junc.y,
                "type": junc.type,
                "zone": junc.zone,
                "node_type": junc.node_type
            }
            try:
                add_junction(self.db_session, junction_data)
            except Exception as e:
                # Skip if already exists, don't print for every duplicate
                pass
            zone_objects[zone_id].add_junction(junc.id)

        # 2. Collect edges by zone attribute and update junction connections
        print("🛣️  Processing roads...")
        road_count = 0
        for edge in self.net.getEdges():
            zone_attr = edge.getParam("zone")
            if not zone_attr:
                continue
            
            road_count += 1
            if road_count % 100 == 0:
                print(f"🛣️  Processed {road_count} roads...")
            zone_id = zone_attr.upper()
            if zone_id not in zone_objects:
                zone_objects[zone_id] = Zone(zone_id)
                print(f"Zone {zone_id} created.")

            # Create road entity
            road = Road(
                road_id=edge.getID(),
                from_junction=edge.getFromNode().getID(),
                to_junction=edge.getToNode().getID(),
                speed=edge.getSpeed(),
                length=edge.getLength(),
                num_lanes=len(edge.getLanes()),
                zone=zone_id
            )
            self.roads[road.id] = road
            zone_objects[zone_id].add_edge(road.id)
            
            # Save to database
            road_data = {
                "id": road.id,
                "from_junction": road.from_junction,
                "to_junction": road.to_junction,
                "speed": road.speed,
                "length": road.length,
                "num_lanes": road.num_lanes,
                "zone": road.zone,
                "density": road.density,
                "avg_speed": road.avg_speed
            }
            try:
                add_road(self.db_session, road_data)
            except Exception as e:
                # Skip if already exists, don't print for every duplicate
                pass

            # Update junction connections
            from_junction = self.junctions.get(road.from_junction)
            to_junction = self.junctions.get(road.to_junction)
            if from_junction:
                from_junction.add_outgoing(road.id)
            if to_junction:
                to_junction.add_incoming(road.id)

        # 3. Save zones to database
        for zone in zone_objects.values():
            self.zones[zone.id] = zone
            zone_data = {
                "id": zone.id,
                "description": zone.description
            }
            try:
                add_zone(self.db_session, zone_data)
            except Exception as e:
                # Skip if already exists, don't print for every duplicate
                pass
            
            # Save zone-edge and zone-junction relationships
            for edge_id in zone.edges:
                add_zone_edge(self.db_session, zone.id, edge_id)
            for junction_id in zone.junctions:
                add_zone_junction(self.db_session, zone.id, junction_id)
            
            print(f"✅ Saved zone {zone.id} to database")
        
        print(f"✅ Successfully loaded and saved {len(self.junctions)} junctions, {len(self.roads)} roads, {len(self.zones)} zones")
        

    def get_zones(self):
        """
        Get all zones
        """
        return self.zones
    
    def populate_vehicles_from_config(self, config):
        """
        Populates vehicles in the simulation based on a configuration file.
        First checks if vehicles exist in database and match expected count,
        loads them if available, otherwise generates and saves them to database.
        """
        # Calculate expected number of vehicles
        dev_fraction = config.get("vehicle_generation", {}).get("dev_fraction", 1.0)
        expected_vehicles = round(config["vehicle_generation"]["total_num_vehicles"] * dev_fraction)
        
        # Check if vehicles exist in database and count matches
        if vehicles_exist(self.db_session):
            actual_count = get_vehicle_count(self.db_session)
            print(f"🔍 Database has {actual_count} vehicles, expected {expected_vehicles}")
            
            if actual_count == expected_vehicles:
                print("✅ Vehicle count matches, loading from DB...")
                self._load_vehicles_from_database()
                return
            else:
                print(f"⚠️  Vehicle count mismatch! Clearing database and regenerating...")
                # Clear vehicles and schedules from database
                clear_vehicles(self.db_session)
                clear_vehicle_schedules(self.db_session)
                self.db_session.commit()
        else:
            print("📥 No vehicles found in database, generating...")
        
        print("📥 No vehicles found in database, generating and saving to DB...")
        
        dev_fraction = config.get("vehicle_generation", {}).get("dev_fraction", 1.0)
        orig_total_vehicles = config["vehicle_generation"]["total_num_vehicles"]

        total_vehicles = round(orig_total_vehicles * dev_fraction)
        print(f"🚗 Total vehicles to generate: {total_vehicles}")
        
        
        orig_estimated_peak = self.estimate_required_vehicles(config)
        estimated_peak = round(orig_estimated_peak * dev_fraction)
        print(f"📊 Estimated required vehicles: {estimated_peak}")
        
        if estimated_peak > total_vehicles:
            print(f"❌ ERROR: Terminating the simulation since estimated required vehicles ({estimated_peak}) exceeds total vehicles ({total_vehicles}).")
            return False
        
        zone_alloc = config["vehicle_generation"]["zone_allocation"]
        vehicle_types = config["vehicle_generation"]["vehicle_types"]

        vehicle_id_counter = 0

        # Track per-zone assignments
        active_zone_ids = [zid for zid in zone_alloc if zid.lower() not in ("h", "stagnant")]
        num_zones = len(active_zone_ids)

        sum_vehicles = 0
        # Calculate total stagnant vehicles
        stagnant_per_zone = {}
        total_stagnant = 0
        if "stagnant" in zone_alloc:
            stagnant_pct = zone_alloc["stagnant"]["percentage"]
            total_stagnant = round((stagnant_pct / 100) * total_vehicles)
            base_stag = total_stagnant // num_zones
            extra_stag = total_stagnant % num_zones
            for i, zid in enumerate(active_zone_ids):
                stagnant_per_zone[zid] = base_stag + (1 if i < extra_stag else 0)
                sum_vehicles += stagnant_per_zone[zid]
        
        # Calculate total vehicles in other zones
        active_zone_vehicle_counts = {}
        for zid in zone_alloc:
            if zid.lower() == "stagnant":
                continue
            if zid.upper() == "H":
                continue
            percentage = zone_alloc[zid]["percentage"]
            num_zone_vehicles = round((percentage / 100) * total_vehicles)
            active_zone_vehicle_counts[zid] = num_zone_vehicles
            sum_vehicles += num_zone_vehicles
    
        # Allocate more vehicles to zones until total_vehicles is reached
        while total_vehicles > sum_vehicles:
            zone_id = random.choice(active_zone_ids)
            active_zone_vehicle_counts[zone_id] += 1
            sum_vehicles += 1
        
        print(f"🔍 Calculated vehicle distribution:")
        for zone_id, count in active_zone_vehicle_counts.items():
            print(f"  {zone_id}: {count} vehicles")
        print(f"🔍 Total calculated: {sum_vehicles} vehicles")
        
        # Create vehicles in each zone
        for zone_id, zone_cfg in tqdm(zone_alloc.items(), desc="🚗 Allocating vehicles by zone"):
            if zone_id.lower() == "stagnant":
                continue
            if zone_id.upper() == "H":
                continue  # Skip highway zone
                
            num_zone_vehicles = active_zone_vehicle_counts[zone_id] + stagnant_per_zone.get(zone_id, 0)
            type_distribution = zone_cfg["vehicle_type_distribution"]

            # Get eligible single lane roads in this zone
            zone = self.zones.get(zone_id)
            if not zone:
                print(f"⚠️ Zone {zone_id} not found, skipping...")
                continue
                
            eligible_roads = []
            for road_id in zone.edges:
                road = self.roads.get(road_id)
                if road and road.num_lanes == 1:
                    eligible_roads.append(road_id)
                    
            if not eligible_roads:
                print(f"⚠️ No eligible roads found in zone {zone_id}, skipping...")
                continue

            # Allocate vehicles across types
            type_allocations = {
                vtype: round((vperc / 100) * num_zone_vehicles)
                for vtype, vperc in type_distribution.items()
            }
            
            vehicle_specs = [
                (vtype, vehicle_types[vtype].copy())
                for vtype, count in type_allocations.items()
                for _ in range(count)
            ]
            random.shuffle(vehicle_specs)

            per_road = len(vehicle_specs) // len(eligible_roads)
            overflow = len(vehicle_specs) % len(eligible_roads)

            vehicle_iter = iter(vehicle_specs)

            for i, road_id in enumerate(tqdm(eligible_roads, desc=f"Zone {zone_id} roads")):
                vehicles_on_road = per_road + (1 if i < overflow else 0)
                road = self.roads.get(road_id)
                if not road:
                    continue
                    
                net_edge = self.net.getEdge(road_id)
                length = road.length
                spacing = length / (vehicles_on_road + 1)

                for j in range(vehicles_on_road):
                    if len(self.vehicles) >= total_vehicles:
                        break
                    try:
                        vtype, vcfg = next(vehicle_iter)
                    except StopIteration:
                        break

                    pos = (j + 1) * spacing
                    x, y = net_edge.getLane(0).getShape()[0]

                    vehicle = Vehicle(
                        vehicle_id=f"veh_{vehicle_id_counter}",
                        vehicle_type=vtype,
                        current_zone=zone_id,
                        current_edge=road_id,
                        current_position=pos,
                        current_x=x,
                        current_y=y,
                        length=vcfg["length"],
                        width=vcfg["width"],
                        height=vcfg["height"],
                        color=vcfg["color"],
                        status="parked",
                        is_stagnant=False
                    )
                    
                    # Initialize additional attributes needed for simulation
                    vehicle.scheduled = [False] * config["vehicle_generation"]["simulation_weeks"]
                    vehicle.destinations = {}

                    self.vehicles[vehicle.id] = vehicle
                    road.add_vehicle_and_update(vehicle)
                    zone.add_original_vehicle(vehicle.id)
                    zone.add_current_vehicle(vehicle.id)

                    self.assign_destinations(vehicle, self.zones, config["landmarks"])
                    vehicle_id_counter += 1

            # Randomly convert some vehicles in this zone to stagnant
            zone_vehicle_ids = list(zone.current_vehicles)
            if 'stagnant' in zone_alloc:
                num_to_convert = stagnant_per_zone.get(zone_id, 0)
                to_convert = random.sample(zone_vehicle_ids, min(num_to_convert, len(zone_vehicle_ids)))
                for vid in to_convert:
                    v = self.vehicles.get(vid)
                    if v:
                        v.is_stagnant = True
                        v.color = "white"
    
        print(f"🔍 Total vehicles created: {len(self.vehicles)}")
        print(f"✅ Zones loaded: {len(self.zones)}")
        for zid, zone in self.zones.items():
            print(f"📍 Zone {zid}: {len(zone.edges)} roads, {len(zone.junctions)} junctions, {len(zone.current_vehicles)} vehicles")
        
        # Save vehicles to database
        print("💾 Saving vehicles to database...")
        self._save_vehicles_to_database()
        
        return True
    
    def _load_vehicles_from_database(self):
        """Load vehicles from database into memory"""
        try:
            # Debug: Check total count first
            total_count = get_vehicle_count(self.db_session)
            print(f"🔍 Total vehicles in database: {total_count}")
            
            db_vehicles = get_all_vehicles(self.db_session)
            print(f"📥 Loading {len(db_vehicles)} vehicles from database...")
            
            for db_vehicle in db_vehicles:
                # Create Vehicle object from database data
                vehicle = Vehicle(
                    vehicle_id=db_vehicle.id,
                    vehicle_type=db_vehicle.vehicle_type,
                    current_zone=db_vehicle.current_zone,
                    current_edge=db_vehicle.current_edge,
                    current_position=db_vehicle.current_position,
                    current_x=db_vehicle.current_x,
                    current_y=db_vehicle.current_y,
                    speed=db_vehicle.speed,
                    status=db_vehicle.status,
                    scheduled=False  # Initialize as False, will be set to list later
                )
                
                # Initialize scheduled as a list for multi-week scheduling
                vehicle.scheduled = [False] * self.config["vehicle_generation"]["simulation_weeks"]
                
                # Load destinations if available
                if db_vehicle.destinations:
                    import json
                    try:
                        vehicle.destinations = json.loads(db_vehicle.destinations)
                    except json.JSONDecodeError:
                        vehicle.destinations = {}
                
                self.vehicles[db_vehicle.id] = vehicle
                
                # Add vehicle to its zone's current_vehicles list
                if vehicle.current_zone and vehicle.current_zone in self.zones:
                    self.zones[vehicle.current_zone].current_vehicles.add(vehicle.id)
            
            print(f"✅ Loaded {len(self.vehicles)} vehicles from database")
            
        except Exception as e:
            print(f"❌ Error loading vehicles from database: {e}")
            self.vehicles = {}
    
    def _save_vehicles_to_database(self):
        """Save vehicles to database"""
        try:
            print(f"💾 Saving {len(self.vehicles)} vehicles to database...")
            
            # Clear existing vehicles first
            clear_vehicles(self.db_session)
            
            # Save vehicles in batches
            batch_size = 1000
            vehicles_list = list(self.vehicles.values())
            
            for i in range(0, len(vehicles_list), batch_size):
                batch = vehicles_list[i:i + batch_size]
                
                for vehicle in batch:
                    # Prepare vehicle data for database
                    scheduled_value = getattr(vehicle, 'scheduled', False)
                    # Ensure scheduled is a boolean, not a list
                    if isinstance(scheduled_value, list):
                        scheduled_value = bool(scheduled_value[0]) if scheduled_value else False
                    elif not isinstance(scheduled_value, bool):
                        scheduled_value = bool(scheduled_value)
                    
                    vehicle_data = {
                        "id": vehicle.id,
                        "vehicle_type": vehicle.vehicle_type,
                        "current_zone": vehicle.current_zone,
                        "current_edge": vehicle.current_edge,
                        "current_position": vehicle.current_position,
                        "current_x": vehicle.current_x,
                        "current_y": vehicle.current_y,
                        "speed": getattr(vehicle, 'speed', 0.0),
                        "status": getattr(vehicle, 'status', 'parked'),
                        "scheduled": scheduled_value,
                        "destinations": json.dumps(getattr(vehicle, 'destinations', {}))
                    }
                    
                    try:
                        add_vehicle(self.db_session, vehicle_data)
                    except Exception as e:
                        # Skip if vehicle already exists and rollback the session
                        self.db_session.rollback()
                        pass
                
                print(f"💾 Saved batch {i//batch_size + 1}/{(len(vehicles_list) + batch_size - 1)//batch_size}")
            
            print(f"✅ Successfully saved {len(self.vehicles)} vehicles to database")
            
        except Exception as e:
            print(f"❌ Error saving vehicles to database: {e}")
            self.db_session.rollback()
    
    def assign_destinations(self, vehicle, zone_map, landmark_map):
        """
        Assign destination points to a vehicle for various activities
        """
        # Initialize destinations dictionary
        vehicle.destinations = {}
        
        # HOME
        vehicle.destinations["home"] = {
            "edge": vehicle.current_edge,
            "position": vehicle.current_position
        }

        # WORK (random edge in Zone B)
        zone_b_edges = [eid for eid in zone_map["B"].edges if self.roads.get(eid).num_lanes == 1]
        if zone_b_edges:
            work_edge = random.choice(zone_b_edges)
            vehicle.destinations["work"] = {
                "edge": work_edge,
                "position": random.uniform(1.0, self.roads.get(work_edge).length - 1.0)
            }

        # FRIEND 1: same zone, single-lane
        same_zone_edges = [eid for eid in zone_map[vehicle.current_zone].edges if self.roads.get(eid).num_lanes == 1]
        if same_zone_edges:
            friend1_edge = random.choice(same_zone_edges)
            vehicle.destinations["friend1"] = {
                "edge": friend1_edge,
                "position": random.uniform(1.0, self.roads.get(friend1_edge).length - 1.0)
            }

        # FRIEND 2 & 3: in other zones, single-lane only
        other_zones = [z for z in zone_map if z != vehicle.current_zone and z != "H"]
        for i in range(2, 4):
            if i - 2 < len(other_zones):
                other_zone_id = other_zones[i - 2]
                eligible_edges = [eid for eid in zone_map[other_zone_id].edges if self.roads.get(eid).num_lanes == 1]
                if eligible_edges:
                    other_edge = random.choice(eligible_edges)
                    vehicle.destinations[f"friend{i}"] = {
                        "edge": other_edge,
                        "position": random.uniform(1.0, self.roads.get(other_edge).length - 1.0)
                    }

        # PARKS 1–4 (Zone A) - use random edges from Zone A
        zone_a_edges = [eid for eid in zone_map["A"].edges if self.roads.get(eid).num_lanes == 1]
        for i in range(1, 5):
            if zone_a_edges:
                park_edge = random.choice(zone_a_edges)
                vehicle.destinations[f"park{i}"] = {
                    "edge": park_edge,
                    "position": random.uniform(1.0, self.roads.get(park_edge).length - 1.0)
                }

        # STADIUMS 1–2 (Zone C) - use random edges from Zone C
        zone_c_edges = [eid for eid in zone_map["C"].edges if self.roads.get(eid).num_lanes == 1]
        for i in range(1, 3):
            if zone_c_edges:
                stadium_edge = random.choice(zone_c_edges)
                vehicle.destinations[f"stadium{i}"] = {
                    "edge": stadium_edge,
                    "position": random.uniform(1.0, self.roads.get(stadium_edge).length - 1.0)
                }

        # RESTAURANTS by zone
        rest_map = {"A": "restaurantA", "B": "restaurantB", "C": "restaurantC"}
        for zone_id, label in rest_map.items():
            eligible = [eid for eid in zone_map[zone_id].edges if self.roads.get(eid).num_lanes == 1]
            if eligible:
                edge = random.choice(eligible)
                vehicle.destinations[label] = {
                    "edge": edge,
                    "position": random.uniform(1.0, self.roads.get(edge).length - 1.0)
                }
    
    def estimate_required_vehicles(self, config):
        """
        Estimate the required number of vehicles based on configuration
        """
        total = 0
        dev_fraction = config.get("vehicle_generation", {}).get("dev_fraction", 1.0)
        num_weeks = config["vehicle_generation"]["simulation_weeks"]

        for entry in config.get("weekday_schedule", []):
            vpm = entry.get("vpm_rate", 0.0)
            if vpm <= 0:
                continue
                
            interval = 60 / vpm

            start = self.convert_time_to_seconds(entry["start_time"])
            end = self.convert_time_to_seconds(entry["end_time"])
            duration = max(end - start, 0)

            num_dispatches = int(duration // interval)
            num_zones = len(entry.get("source_zones", []))
            num_days = len(entry.get("repeat_on_days", [1, 2, 3, 4, 5]))

            # Multiply by number of weeks
            total += num_dispatches * num_zones * num_days * num_weeks

        # Apply development fraction
        return int(total * dev_fraction)
    
    
    def debug_system_state(self):
        """
        Debug method to print current system state
        """
        print("\n" + "="*50)
        print("🐛 DEBUG: System State")
        print("="*50)
        print(f"📊 Junctions loaded: {len(self.junctions)}")
        print(f"🛣️  Roads loaded: {len(self.roads)}")
        print(f"🏘️  Zones loaded: {len(self.zones)}")
        print(f"🚗 Vehicles loaded: {len(self.vehicles)}")
        
        if self.zones:
            print("\n📍 Zone Details:")
            for zone_id, zone in self.zones.items():
                print(f"  Zone {zone_id}: {len(zone.edges)} edges, {len(zone.junctions)} junctions, {len(zone.current_vehicles)} vehicles")
        
        print(f"🗄️  Database session: {'Connected' if self.db_session else 'Not connected'}")
        print("="*50 + "\n")
    
    def debug_database_connection(self):
        """
        Debug database connection and tables
        """
        print("\n" + "="*50)
        print("🐛 DEBUG: Database Connection")
        print("="*50)
        try:
            # Test database connection
            from sqlalchemy import text
            result = self.db_session.execute(text("SELECT 1")).fetchone()
            print("✅ Database connection: OK")
            
            # Check table existence
            from sqlalchemy import inspect
            inspector = inspect(self.db_session.bind)
            tables = inspector.get_table_names()
            print(f"📋 Available tables: {tables}")
            
            # Check entity counts
            entity_status = check_entities_exist(self.db_session)
            print(f"📊 Entity counts: {entity_status}")
            
        except Exception as e:
            print(f"❌ Database connection error: {e}")
        print("="*50 + "\n")
    
    def clear_roads_and_zones(self):
        """
        Clears all roads and zones vehicles before dispatching.
        """
        print("🧹 Clearing roads and zones...")
        
        # Clear roads
        for road in self.roads.values():
            road.vehicles_on_road.clear()
            road.density = 0.0
            road.avg_speed = 0.0
        
        # Clear zones
        for zone in self.zones.values():
            zone.original_vehicles.clear()
            zone.current_vehicles.clear()
        
        print(f"✅ Cleared {len(self.roads)} roads and {len(self.zones)} zones")
    
    def schedule_from_config(self, config):
        """
        Schedule vehicles based on configuration - optimized to use database
        """
        print("📅 Scheduling vehicles from configuration...")
        
        # Check if schedule already exists in database and has expected number of vehicles
        if schedule_exists(self.db_session):
            # Calculate expected number of vehicles
            dev_fraction = config.get("vehicle_generation", {}).get("dev_fraction", 1.0)
            expected_vehicles = round(config["vehicle_generation"]["total_num_vehicles"] * dev_fraction)
            
            # Check if vehicle count matches expected
            actual_vehicles = get_vehicle_count(self.db_session)
            if actual_vehicles == expected_vehicles:
                print("✅ Vehicle schedule found in database, loading from DB...")
                self._load_schedule_from_database()
                return
            else:
                print(f"⚠️  Schedule exists but vehicle count mismatch ({actual_vehicles} vs {expected_vehicles}), regenerating...")
                clear_vehicle_schedules(self.db_session)
                self.db_session.commit()
        else:
            print("📝 No schedule found in database, creating new schedule...")
        
        print("📝 No schedule found in database, creating new schedule...")
        self._create_and_save_schedule(config)
    
    def _load_schedule_from_database(self):
        """
        Load vehicle schedule from database
        """
        print("📥 Loading vehicle schedule from database...")
        
        try:
            # Get all schedule entries from database
            schedule_entries = get_vehicle_schedules(self.db_session)
            
            # Group by step
            for entry in schedule_entries:
                step = entry.step
                if step not in self.schedule:
                    self.schedule[step] = []
                
                # Reconstruct the schedule entry format
                vehicle_id = entry.vehicle_id
                origin = entry.source_zone  # Using source_zone as origin for now
                destination = entry.destination_zone  # Using destination_zone as destination for now
                
                self.schedule[step].append((vehicle_id, origin, destination))
            
            print(f"✅ Loaded {len(schedule_entries)} schedule entries from database")
            print(f"📅 Total scheduled vehicles: {sum(len(v) for v in self.schedule.values())}")
            
        except Exception as e:
            print(f"❌ Error loading schedule from database: {e}")
            print("📝 Falling back to creating new schedule...")
            self._create_and_save_schedule(self.config)
    
    def _create_and_save_schedule(self, config):
        """
        Create new vehicle schedule and save to database
        """
        print("📝 Creating new vehicle schedule...")
        
        # Clear existing schedule from database
        clear_vehicle_schedules(self.db_session)
        
        schedule_entries = config.get("weekday_schedule", [])
        num_weeks = config["vehicle_generation"]["simulation_weeks"]
        dev_fraction = config.get("vehicle_generation", {}).get("dev_fraction", 1.0)
        seconds_in_day = 86400
        seconds_in_week = seconds_in_day * 7
        num_scheduled_vehicles = 0
        
        # Create a schedule for each week
        for week in tqdm(range(num_weeks), desc="Scheduling vehicles by week"):
            week_start = week * seconds_in_week
            num_weekly_vehicles = 0
            # Adjust the start and end times for the current week       
            for entry in tqdm(schedule_entries, desc=f"Week {week+1} entries", leave=False):
                print(f"📅 Scheduling vehicles for entry: {entry.get('name', 'Unnamed')}")
                start_sec = self.convert_time_to_seconds(entry["start_time"]) + week_start
                end_sec = self.convert_time_to_seconds(entry["end_time"]) + week_start
                vpm_rate = entry.get("vpm_rate", 0)
                vpm_rate = vpm_rate * dev_fraction
                source_zones = entry.get("source_zones", [])
                origin_keys = entry.get("origin", [])
                destination_keys = entry.get("destination", [])
                repeat_days = entry.get("repeat_on_days", [])

                # Compute interval between dispatches
                interval = max(60 // vpm_rate, 1)
                local_steps = list(range(start_sec, end_sec + 1, int(interval)))
                if len(local_steps) == 0:
                    local_steps = [start_sec]
                for day in repeat_days:
                    num_scheduled_vehicles_per_day = 0
                    base_step = (day - 1) * seconds_in_day
                    steps = [base_step + s for s in local_steps]

                    for zone_id in source_zones:
                        zone = self.zones.get(zone_id)
                        if zone is None:
                            continue
                        eligible = [
                            v for v in zone.current_vehicles
                            if not self.get_vehicle(v).scheduled[week]
                        ]
                        eligible = eligible[:int(len(eligible) * dev_fraction)]
                        steps_to_use = steps[:int(len(eligible))]
                        for step, veh_id in zip(steps_to_use, eligible):
                            vehicle = self.get_vehicle(veh_id)
                            vehicle.scheduled[week] = True

                            while True:
                                origin = random.choice(origin_keys)
                                dest = random.choice(destination_keys)
                                if origin != dest:
                                    break
                                else:
                                    print(f"⚠️  Origin {origin} and destination {dest} are the same. Retrying...")
            
                            # Add to in-memory schedule
                            self.add_to_schedule(step, [(veh_id, origin, dest)])
                            
                            # Save to database
                            schedule_data = {
                                "vehicle_id": veh_id,
                                "step": step,
                                "week": week + 1,
                                "day": day,
                                "entry_name": entry.get('name', 'Unnamed'),
                                "vpm_rate": vpm_rate,
                                "source_zone": zone_id,
                                "destination_zone": dest  # Using dest as destination_zone for now
                            }
                            add_vehicle_schedule(self.db_session, schedule_data)
                            
                            num_scheduled_vehicles += 1
                            num_weekly_vehicles += 1
                            num_scheduled_vehicles_per_day += 1
                    if num_scheduled_vehicles_per_day == 0:
                        print(f"⚠️  No vehicles scheduled for dispatch on day {day} in week {week + 1}.")
                        # Continue instead of exiting

                    print(f"📅 Week {week + 1} scheduled vehicles for day {day}: {num_scheduled_vehicles_per_day}")
            print(f"📅 Week {week + 1} scheduled vehicles: {num_weekly_vehicles}")
        print(f"📅 Total vehicles scheduled for dispatch: {num_scheduled_vehicles}")
        print("📅 All schedules created and saved to database.") 
        print(f"📅 Total scheduled vehicles: {sum(len(v) for v in self.schedule.values())}")
        print(f"📅 Total vehicles in simulation: {len(self.vehicles)}")
        
    
    def calculate_simulation_limit(self, config):
        """
        Calculate the total simulation time limit based on the configuration
        Allow for an additional 30 minutes for finalization
        """
        # Calculate the total simulation time limit based on the configuration
        # Allow for an additional 30 minutes for finalization
        extra_time = 1800  # 30 minutes in seconds
        num_weeks = config["vehicle_generation"]["simulation_weeks"]
        seconds_in_day = 86400
        seconds_in_week = seconds_in_day * 7
        return num_weeks * seconds_in_week + extra_time
    
    def run_simulation(self, sumo_binary="sumo", sumocfg_path=None):
        """
        Launch SUMO with TraCI and run the simulation for the calculated time limit
        """
        if sumocfg_path is None:
            sumocfg_path = self.sumo_config_path
            
        print(f"🚀 Starting SUMO simulation...")
        print(f"📁 SUMO config: {sumocfg_path}")
        
        simulation_limit = self.calculate_simulation_limit(self.config)
        print(f"⏱️  Simulation limit: {simulation_limit} steps")
        
        # Set simulation as running
        self.simulation_running = True
        
        # Launch SUMO with TraCI
        sumo_cmd = [sumo_binary, "-c", sumocfg_path, "--start"]
        limit = self.calculate_simulation_limit(self.config)
        
        try:
            traci.start(sumo_cmd)
            print("✅ SUMO TraCI connection established")
            
            # Run simulation steps
            from tqdm import tqdm
            for step in tqdm(range(limit), desc="Simulation Steps", unit="step"):
                if not self.simulation_running:
                    print("🛑 Simulation stopped by user")
                    break
                    
                traci.simulationStep()
                self.current_step = step
                
                # Update simulation progress
                if limit > 0:
                    simulation_progress = int((step / limit) * 100)
                
                # Update vehicle states using the database-backed update method
                self.update(step, traci)
                self.dispatch(step, traci)
                
                # Store current step for API access
                self.current_step = step
                
                # Optional: Add simulation monitoring/logging here
                if step % 1000 == 0:  # Log every 1000 steps
                    print(f"📊 Step {step}: {len(traci.vehicle.getIDList())} vehicles active")
            
            print("✅ Simulation completed successfully!")
            
        except Exception as e:
            print(f"❌ Simulation error: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            # Set simulation as not running
            self.simulation_running = False
            # Close TraCI connection
            try:
                traci.close()
                print("🔌 TraCI connection closed")
            except:
                pass
    
    def dispatch(self, current_step, traci):
        """
        Dispatches all vehicles scheduled for the given simulation step.
        """
        if current_step not in self.schedule:
            return
        
        curr_week = current_step // 604800

        for vehicle_id, origin_label, destination_label in self.schedule[current_step]:
            vehicle = self.get_vehicle(vehicle_id)
            if not vehicle or vehicle.status != "parked":
                continue  # Only dispatch parked vehicles
            
            # Check if vehicle has destinations data
            if not hasattr(vehicle, 'destinations') or not vehicle.destinations:
                print(f"⚠️  Vehicle {vehicle_id} has no destinations data, skipping")
                continue
                
            origin = vehicle.destinations.get(origin_label)
            if not origin:
                print(f"⚠️  Vehicle {vehicle_id} has no origin '{origin_label}', skipping")
                continue
            
            # set current vehicle properties
            vehicle.current_edge = origin["edge"]
            vehicle.current_position = float(origin["position"])
            vehicle.current_zone = self.roads.get(vehicle.current_edge).zone
            # set origin properties
            vehicle.origin_name = origin_label
            vehicle.origin_edge = origin["edge"]
            vehicle.origin_position = float(origin["position"])
            vehicle.origin_zone = vehicle.current_zone
            vehicle.origin_step = current_step+1
         
            destination = vehicle.destinations.get(destination_label)
            if not destination:
                print(f"⚠️  Vehicle {vehicle_id} has no destination '{destination_label}', skipping")
                continue
                
            vehicle.destination_name = destination_label
            vehicle.destination_edge = destination["edge"]
            vehicle.destination_position = float(destination["position"])
            vehicle.destination_zone = self.roads.get(vehicle.destination_edge).zone

            route_id = f"route_{vehicle_id}_to_{destination_label}_{curr_week}"

            try:
                route_result = traci.simulation.findRoute(vehicle.current_edge, destination["edge"])
                full_route_edges = route_result.edges
                traci.route.add(routeID=route_id, edges=full_route_edges)
                vehicle.route = list(full_route_edges)
                vehicle.route_left = list(full_route_edges)
                vehicle.route_length = round(sum(
                    self.roads.get(e).length for e in vehicle.route_left if self.roads.get(e)), 2)
                vehicle.route_length_left = vehicle.route_length

                traci.vehicle.add(
                                vehID=vehicle.id,
                                routeID=route_id,
                                typeID=vehicle.vehicle_type,
                                depart=vehicle.origin_step,
                                departPos=vehicle.current_position,
                                departSpeed=0,
                                departLane="0",
                            )
                if vehicle.is_stagnant:
                    traci.vehicle.setColor(vehicle.id, (255, 255, 255))  # White for stagnant vehicles
                vehicle.origin_x, vehicle.origin_y = traci.simulation.convert2D(vehicle.origin_edge, float(vehicle.origin_position), 0)
                vehicle.current_x, vehicle.current_y = vehicle.origin_x, vehicle.origin_y
                vehicle.destination_x, vehicle.destination_y = traci.simulation.convert2D(vehicle.destination_edge, float(vehicle.destination_position), 0)
                road = self.roads.get(vehicle.current_edge)
                if road:
                    road.add_vehicle_and_update(vehicle)
                else:
                    self.log.fatal(f"Road {vehicle.current_edge} not found in database. Cannot add vehicle {vehicle.id}.")
                    exit(1)
                traci.vehicle.subscribe(vehicle.id, [tc.VAR_ROAD_ID])
                self.vehicles_in_route.add(vehicle.id)
                self.log.info(f"[DISPATCHED] {vehicle.id} from {origin_label} to {destination_label} at step {vehicle.origin_step}={self.convert_seconds_to_time(vehicle.origin_step)} distance {vehicle.route_length}m.")
                vehicle.status = "in_route"
            except traci.TraCIException as e:
                print(f"[ERROR] Failed to dispatch {vehicle.id}: {e}")

        del self.schedule[current_step]

    def update(self, current_step, traci):
        """
        Update vehicle states during simulation - adapted to use database entities
        """
        for vid in traci.vehicle.getIDList():
            # Get vehicle from database instead of self.db.vehicles
            vehicle = self.get_vehicle(vid)
            if vehicle is not None and vehicle.status == "in_route":
                current_edge = traci.vehicle.getRoadID(vid)
                curr_road = self.roads.get(current_edge)  # Use self.roads instead of self.db.get_road()
                if curr_road is None:
                    continue
                # update vehicle dynamic features
                vehicle.current_position = traci.vehicle.getLanePosition(vid)
                vehicle.acceleration = traci.vehicle.getAcceleration(vid)
                vehicle.speed = traci.vehicle.getSpeed(vid)
                vehicle.current_lane = traci.vehicle.getLaneID(vid)
                vehicle.current_x, vehicle.current_y = traci.vehicle.getPosition(vid)
                vehicle.current_zone = curr_road.zone
                
                prev_road = self.roads.get(vehicle.current_edge)  # Use self.roads instead of self.db.get_road()
                prev_edge = vehicle.current_edge

                # only update vehicle in road for average road speed and density 
                if(current_edge == prev_edge):
                    curr_road.add_vehicle_and_update(vehicle)
                else:
                    # if vehicle changed road, update its state
                    print(f"Vehicle {vehicle.id} changed road from {vehicle.current_edge} to {current_edge}.")
                
                # remove vehicle from previous Road and add to current Road
                if prev_road is not None and prev_road != curr_road:
                    print(f"Vehicle {vehicle.id} is moving from {vehicle.current_edge} to {current_edge}.")
                    if vehicle.id in prev_road.vehicles_on_road.keys():
                        prev_road.remove_vehicle_and_update(vehicle)
                        curr_road.add_vehicle_and_update(vehicle)
                    else:
                        print(f"Previous road {vehicle.current_edge} not found in prev_road.vehicles_on_road.")
                
                # update vehicle route
                vehicle.current_edge = current_edge
                if vehicle.route and vehicle.current_edge in vehicle.route:
                    idx = vehicle.route.index(vehicle.current_edge)
                    vehicle.route_left = vehicle.route[idx:]
                    vehicle.route_length_left = round(sum(self.roads.get(e).length for e in vehicle.route_left if self.roads.get(e)), 2)
                
               
                if current_edge == vehicle.destination_edge:
                    vehicle.status = "parked"
                    vehicle.current_edge = vehicle.destination_edge
                    vehicle.current_position = vehicle.destination_position
                    vehicle.route_length_left = 0
                    vehicle.destination_step = current_step
                    self.vehicles_in_route.remove(vid)
                    curr_road.remove_vehicle_and_update(vehicle)
                    self.add_ground_truth_label(vehicle)
                    print(f"Vehicle {vehicle.id} arrived at destination {vehicle.destination_name} at {self.convert_seconds_to_time(current_step)} started {self.convert_seconds_to_time(vehicle.origin_step)} duration {self.convert_seconds_to_time(current_step - vehicle.origin_step)}")
                    if current_step - vehicle.origin_step > 2 * 60 * 60 :
                        print(f"Vehicle {vehicle.id} travel duration {self.convert_seconds_to_time(current_step - vehicle.origin_step)} exceeds top limit")
        if current_step % 300 == 0:
            print(f"step {current_step} time {self.convert_seconds_to_time(current_step)} vehicles in route: {len(self.vehicles_in_route)}")
    
    def get_vehicle(self, vehicle_id):
        """
        Get vehicle by ID from the vehicles dictionary
        """
        return self.vehicles.get(vehicle_id)
    
    def convert_seconds_to_time(self, seconds):
        """
        Converts a number of seconds into a time string formatted as WW:DD:HH:MM:SS.
        Handles both the new format and backward compatibility with HH:MM:SS.
        """
        if seconds < 86400:  # Less than a day, use HH:MM:SS format
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:  # More than a day, use WW:DD:HH:MM:SS format
            week = seconds // 604800
            day = (seconds % 604800) // 86400
            hour = (seconds % 86400) // 3600
            minute = (seconds % 3600) // 60
            second = seconds % 60
            return f"{week:02d}:{day:02d}:{hour:02d}:{minute:02d}:{second:02d}"
    
    def add_ground_truth_label(self, vehicle):
        trip = {
            "vehicle_id": vehicle.id,
            "origin_time_sec": vehicle.origin_step,
            "destination_time_sec": vehicle.destination_step,
            "origin_x": vehicle.origin_x,
            "origin_y": vehicle.origin_y,
            "destination_x": vehicle.destination_x,
            "destination_y": vehicle.destination_y,
            "origin_edge": vehicle.origin_edge,
            "destination_edge": vehicle.destination_edge,
            "route": vehicle.route,
            "initial_route_length": vehicle.route_length,
            "total_travel_time_seconds": (vehicle.destination_step - vehicle.origin_step)
        }
        self.ground_truth_labels.append(trip)
    
    def convert_time_to_seconds(self, time_str):
        """
        Converts a time string formatted as HH:MM into the number of seconds since midnight.
        Handles both HH:MM and HH:MM:SS formats for backward compatibility.
        """
        try:
            parts = time_str.split(":")
            if len(parts) == 2:
                hour, minute = map(int, parts)
                return hour * 3600 + minute * 60
            elif len(parts) == 3:
                hour, minute, second = map(int, parts)
                return hour * 3600 + minute * 60 + second
            else:
                # Fallback for single number (assume minutes)
                return int(time_str) * 60
        except (ValueError, AttributeError):
            print(f"⚠️  Warning: Invalid time format '{time_str}', using 0")
            return 0
    
    def add_to_schedule(self, step, vehicle_data):
        """
        Add vehicle to schedule at specific step
        """
        if step not in self.schedule:
            self.schedule[step] = []
        self.schedule[step].extend(vehicle_data)