import os
import time
import threading
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional
from models.eta_predictor import ETAPredictor, calculate_traffic_density, get_time_of_day_fraction
from models.entities import Junction, Road, Zone, Vehicle

import json
import random
from sumolib import net as sumo_net
import traci
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
        
        # Step 3: Load schedule
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

    def read_zones_and_roads_from_sumo(self):
        """
        Read zones and roads from SUMO network file
        """
        print("📥 Loading entities from SUMO network...")
        self._load_entities_from_sumo()

    def _load_entities_from_sumo(self):
        """
        Load entities from SUMO network into memory
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
                num_lanes=edge.getLaneNumber(),
                zone=zone_id
            )
            self.roads[road.id] = road
            zone_objects[zone_id].add_edge(road.id)

            # Update junction connections
            from_junction = self.junctions.get(road.from_junction)
            to_junction = self.junctions.get(road.to_junction)
            if from_junction:
                from_junction.add_outgoing(road.id)
            if to_junction:
                to_junction.add_incoming(road.id)

        # 3. Store zones
        for zone in zone_objects.values():
            self.zones[zone.id] = zone
        
        print(f"✅ Successfully loaded {len(self.junctions)} junctions, {len(self.roads)} roads, {len(self.zones)} zones")

    def populate_vehicles_from_config(self, config):
        """
        Populates vehicles in the simulation based on a configuration file.
        """
        print("🚗 Generating vehicles from configuration...")
        
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
                road = self.roads[road_id]
                net_edge = self.net.getEdge(road_id)
                
                for j in range(vehicles_on_road):
                    try:
                        vtype, vcfg = next(vehicle_iter)
                    except StopIteration:
                        break
                    
                    spacing = road.length / (vehicles_on_road + 1)
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
        
        print(f"✅ Generated {len(self.vehicles)} vehicles")
        return True

    def assign_destinations(self, vehicle, zone_map, landmark_map):
        """
        Assign destinations to a vehicle based on zone and landmark configuration
        """
        vehicle.destinations = {}
        
        # Get vehicle's current zone
        current_zone = vehicle.current_zone
        
        # Find all possible destination zones (exclude current zone)
        possible_zones = [zid for zid in zone_map.keys() if zid != current_zone]
        
        if not possible_zones:
            return
        
        # Assign destinations for different trip types
        for trip_type, landmarks in landmark_map.items():
            if not landmarks:
                continue
                
            # Filter landmarks that are in possible destination zones
            available_landmarks = []
            for landmark_id, landmark_info in landmarks.items():
                landmark_zone = landmark_info.get('zone', '').upper()
                if landmark_zone in possible_zones:
                    available_landmarks.append((landmark_id, landmark_info))
            
            if available_landmarks:
                # Randomly select a destination landmark for this trip type
                landmark_id, landmark_info = random.choice(available_landmarks)
                vehicle.destinations[trip_type] = {
                    'landmark_id': landmark_id,
                    'zone': landmark_info['zone'].upper(),
                    'x': landmark_info['x'],
                    'y': landmark_info['y']
                }

    def schedule_from_config(self, config):
        """
        Schedule vehicles based on configuration
        """
        print("📅 Scheduling vehicles from configuration...")
        self._create_schedule(config)

    def _create_schedule(self, config):
        """
        Create vehicle schedule from configuration
        """
        print("📝 Creating new vehicle schedule...")
        
        # Clear existing schedule
        self.schedule = {}
        
        # Get simulation parameters
        simulation_weeks = config["vehicle_generation"]["simulation_weeks"]
        dev_fraction = config.get("vehicle_generation", {}).get("dev_fraction", 1.0)
        
        # Process each week
        for week in tqdm(range(1, simulation_weeks + 1), desc="Scheduling vehicles by week"):
            week_schedule = {}
            
            # Process each schedule entry
            for entry in tqdm(config.get("weekday_schedule", []), desc=f"Week {week} entries"):
                entry_name = entry.get("name", "Unknown")
                vpm = entry.get("vpm_rate", 0.0)
                
                if vpm <= 0:
                    continue
                
                # Calculate dispatch interval
                interval = 60 / vpm  # seconds between dispatches
                
                # Get time range
                start_time = self.convert_time_to_seconds(entry["start_time"])
                end_time = self.convert_time_to_seconds(entry["end_time"])
                duration = max(end_time - start_time, 0)
                
                # Calculate number of dispatches
                num_dispatches = int(duration // interval)
                
                # Get source and destination zones
                source_zones = entry.get("source_zones", [])
                destination_zones = entry.get("destination_zones", [])
                repeat_days = entry.get("repeat_on_days", [1, 2, 3, 4, 5])  # Default to weekdays
                
                # Generate dispatch times
                local_steps = []
                for i in range(num_dispatches):
                    step_time = start_time + (i * interval)
                    local_steps.append(step_time)
                
                # Process each day
                seconds_in_day = 24 * 60 * 60
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
                            if not self.get_vehicle(v).scheduled[week-1]
                        ]
                        eligible = eligible[:int(len(eligible) * dev_fraction)]
                        steps_to_use = steps[:int(len(eligible))]
                        for step, veh_id in zip(steps_to_use, eligible):
                            vehicle = self.get_vehicle(veh_id)
                            vehicle.scheduled[week-1] = True

                            while True:
                                origin = random.choice(list(vehicle.destinations.keys()))
                                destination = random.choice(list(vehicle.destinations.keys()))
                                if origin != destination:
                                    break

                            if step not in week_schedule:
                                week_schedule[step] = []
                            
                            week_schedule[step].append({
                                'vehicle_id': veh_id,
                                'origin': origin,
                                'destination': destination,
                                'zone': zone_id
                            })
                            num_scheduled_vehicles_per_day += 1
                    
                    print(f"📅 Week {week} scheduled vehicles for day {day}: {num_scheduled_vehicles_per_day}")
            
            self.schedule[week] = week_schedule
        
        # Calculate total scheduled vehicles
        total_scheduled = sum(len(day_schedule) for week_schedule in self.schedule.values() for day_schedule in week_schedule.values())
        print(f"📅 Total scheduled vehicles: {total_scheduled}")

    def clear_roads_and_zones(self):
        """
        Clear vehicle data from roads and zones
        """
        print("🧹 Clearing roads and zones...")
        
        # Clear all roads
        for road in self.roads.values():
            road.vehicles.clear()
            road.density = 0.0
            road.avg_speed = road.speed
        
        # Clear all zones
        for zone in self.zones.values():
            zone.original_vehicles.clear()
            zone.current_vehicles.clear()
        
        print(f"✅ Cleared {len(self.roads)} roads and {len(self.zones)} zones")

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

    def convert_time_to_seconds(self, time_str):
        """
        Convert time string (HH:MM or HH:MM:SS) to seconds
        """
        try:
            parts = time_str.split(':')
            if len(parts) == 2:  # HH:MM
                hours, minutes = map(int, parts)
                return hours * 3600 + minutes * 60
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            else:
                raise ValueError(f"Invalid time format: {time_str}")
        except (ValueError, AttributeError):
            print(f"⚠️  Invalid time format: {time_str}, using 0")
            return 0

    def convert_seconds_to_time(self, seconds):
        """
        Convert seconds to time string (HH:MM:SS or WW:DD:HH:MM:SS for longer durations)
        """
        if seconds < 86400:  # Less than a day
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:  # More than a day
            weeks = seconds // (7 * 24 * 3600)
            days = (seconds % (7 * 24 * 3600)) // (24 * 3600)
            hours = (seconds % (24 * 3600)) // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{weeks:02d}:{days:02d}:{hours:02d}:{minutes:02d}:{secs:02d}"

    def get_vehicle(self, vehicle_id):
        """
        Get vehicle by ID
        """
        return self.vehicles.get(vehicle_id)

    def get_all_vehicles(self):
        """
        Get all vehicles
        """
        return list(self.vehicles.values())

    def get_zones(self):
        """
        Get all zones
        """
        return self.zones

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

    def run_simulation(self):
        """
        Run the SUMO simulation
        """
        try:
            print("🚀 Starting SUMO simulation...")
            self.simulation_running = True
            
            # This is a placeholder - in a real implementation, you would:
            # 1. Launch SUMO with TraCI
            # 2. Step through the simulation
            # 3. Update vehicle positions and states
            # 4. Handle vehicle dispatch based on schedule
            
            print("✅ Simulation completed (placeholder)")
            self.simulation_running = False
            
        except Exception as e:
            print(f"❌ Simulation error: {e}")
            self.simulation_running = False

    def stop_simulation(self):
        """
        Stop the SUMO simulation
        """
        self.simulation_running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=5)
        print("🛑 Simulation stopped")

    def get_simulation_status(self):
        """
        Get current simulation status
        """
        return {
            "is_running": self.simulation_running,
            "vehicles": len(self.vehicles),
            "vehicles_in_route": len(self.vehicles_in_route),
            "current_step": self.current_step,
            "data_loaded": self.data_loaded
        }

    def get_active_vehicles(self):
        """
        Get currently active vehicles
        """
        return [
            {
                "id": vehicle.id,
                "type": vehicle.vehicle_type,
                "zone": vehicle.current_zone,
                "x": vehicle.current_x,
                "y": vehicle.current_y,
                "speed": vehicle.speed,
                "status": vehicle.status
            }
            for vehicle in self.vehicles.values()
            if vehicle.status in ["driving", "parked"]
        ]

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
        
        print("\n📍 Zone Details:")
        for zone_id, zone in self.zones.items():
            print(f"  Zone {zone_id}: {len(zone.edges)} edges, {len(zone.junctions)} junctions, {len(zone.current_vehicles)} vehicles")
        
        print(f"\n🗄️  Database session: Not using database")
        print("="*50)
