from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import os
import json

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/trafficlab")

# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

class SimulationResult(Base):
    """
    Database model for storing simulation results
    """
    __tablename__ = "simulation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, nullable=False)
    start_edge = Column(String, nullable=False)
    destination_edge = Column(String, nullable=False)
    predicted_eta = Column(Float, nullable=False)
    actual_duration = Column(Float, nullable=False)
    route_length = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    accuracy = Column(Float, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "start_edge": self.start_edge,
            "destination_edge": self.destination_edge,
            "predicted_eta": self.predicted_eta,
            "actual_duration": self.actual_duration,
            "route_length": self.route_length,
            "timestamp": self.timestamp.isoformat(),
            "accuracy": self.accuracy
        }

class JunctionDB(Base):
    """
    Database model for storing junction entities
    """
    __tablename__ = "junctions"
    
    id = Column(String, primary_key=True, index=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    type = Column(String, nullable=False, default="priority")
    zone = Column(String, nullable=True)
    node_type = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    incoming_roads = relationship("RoadDB", foreign_keys="RoadDB.to_junction", back_populates="to_junction_rel")
    outgoing_roads = relationship("RoadDB", foreign_keys="RoadDB.from_junction", back_populates="from_junction_rel")
    
    def to_dict(self):
        return {
            "id": self.id,
            "node_type": self.node_type,
            "x": self.x,
            "y": self.y,
            "type": self.type,
            "zone": self.zone,
            "incoming": [road.id for road in self.incoming_roads],
            "outgoing": [road.id for road in self.outgoing_roads]
        }

class RoadDB(Base):
    """
    Database model for storing road entities
    """
    __tablename__ = "roads"
    
    id = Column(String, primary_key=True, index=True)
    from_junction = Column(String, ForeignKey("junctions.id"), nullable=False)
    to_junction = Column(String, ForeignKey("junctions.id"), nullable=False)
    speed = Column(Float, nullable=False, default=13.89)
    length = Column(Float, nullable=False, default=100.0)
    num_lanes = Column(Integer, nullable=False, default=1)
    zone = Column(String, nullable=True)
    density = Column(Float, nullable=False, default=0.0)
    avg_speed = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    from_junction_rel = relationship("JunctionDB", foreign_keys=[from_junction], back_populates="outgoing_roads")
    to_junction_rel = relationship("JunctionDB", foreign_keys=[to_junction], back_populates="incoming_roads")
    
    def to_dict(self):
        return {
            "id": self.id,
            "from": self.from_junction,
            "to": self.to_junction,
            "speed": self.speed,
            "length": self.length,
            "num_lanes": self.num_lanes,
            "zone": self.zone,
            "density": self.density,
            "avg_speed": self.avg_speed,
            "vehicles_on_road": []  # This would need to be populated from a separate table if needed
        }

class ZoneDB(Base):
    """
    Database model for storing zone entities
    """
    __tablename__ = "zones"
    
    id = Column(String, primary_key=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "edges": [],  # This would need to be populated from relationships
            "junctions": [],  # This would need to be populated from relationships
            "original_vehicles": [],  # This would need to be populated from relationships
            "current_vehicles": []  # This would need to be populated from relationships
        }

class ZoneEdge(Base):
    """
    Junction table for zone-edge relationships
    """
    __tablename__ = "zone_edges"
    
    zone_id = Column(String, ForeignKey("zones.id"), primary_key=True)
    road_id = Column(String, ForeignKey("roads.id"), primary_key=True)

class ZoneJunction(Base):
    """
    Junction table for zone-junction relationships
    """
    __tablename__ = "zone_junctions"
    
    zone_id = Column(String, ForeignKey("zones.id"), primary_key=True)
    junction_id = Column(String, ForeignKey("junctions.id"), primary_key=True)

class VehicleSchedule(Base):
    """
    Database model for storing vehicle schedule data
    """
    __tablename__ = "vehicle_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, nullable=False, index=True)
    step = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    entry_name = Column(String, nullable=False)
    vpm_rate = Column(Float, nullable=False)
    source_zone = Column(String, nullable=False)
    destination_zone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "step": self.step,
            "week": self.week,
            "day": self.day,
            "entry_name": self.entry_name,
            "vpm_rate": self.vpm_rate,
            "source_zone": self.source_zone,
            "destination_zone": self.destination_zone,
            "created_at": self.created_at.isoformat()
        }

class VehicleDB(Base):
    """
    Database model for storing vehicle data
    """
    __tablename__ = "vehicles"
    
    id = Column(String, primary_key=True, index=True)
    vehicle_type = Column(String, nullable=False)
    current_zone = Column(String, nullable=False)
    current_edge = Column(String, nullable=False)
    current_position = Column(Float, nullable=False)
    current_x = Column(Float, nullable=False)
    current_y = Column(Float, nullable=False)
    speed = Column(Float, default=0.0)
    status = Column(String, default="parked")
    scheduled = Column(Boolean, default=False)
    destinations = Column(Text)  # JSON string of destinations
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_type": self.vehicle_type,
            "current_zone": self.current_zone,
            "current_edge": self.current_edge,
            "current_position": self.current_position,
            "current_x": self.current_x,
            "current_y": self.current_y,
            "speed": self.speed,
            "status": self.status,
            "scheduled": self.scheduled,
            "destinations": self.destinations,
            "created_at": self.created_at.isoformat()
        }

class Journey(Base):
    """
    Database model for storing journey data
    """
    __tablename__ = "journeys"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    journey_number = Column(Integer, nullable=False, unique=True, index=True)
    vehicle_id = Column(String, nullable=False, index=True)
    start_edge = Column(String, nullable=False)
    end_edge = Column(String, nullable=False)
    route_edges = Column(Text)  # JSON string of route edges
    start_time = Column(Integer, nullable=False)  # Simulation step when journey started
    start_time_string = Column(String, nullable=False)  # Human readable start time
    end_time = Column(Integer, nullable=True)  # Simulation step when journey ended
    end_time_string = Column(String, nullable=True)  # Human readable end time
    distance = Column(Float, nullable=False)  # Total distance in meters
    predicted_eta = Column(Integer, nullable=False)  # Predicted ETA in seconds
    actual_duration = Column(Integer, nullable=True)  # Actual duration in seconds
    absolute_error = Column(Integer, nullable=True)  # Absolute error in seconds
    accuracy = Column(Float, nullable=True)  # Accuracy percentage
    status = Column(String, nullable=False, default="running")  # running, finished, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "journey_number": self.journey_number,
            "vehicle_id": self.vehicle_id,
            "start_edge": self.start_edge,
            "end_edge": self.end_edge,
            "route_edges": json.loads(self.route_edges) if self.route_edges else [],
            "start_time": self.start_time,
            "start_time_string": self.start_time_string,
            "end_time": self.end_time,
            "end_time_string": self.end_time_string,
            "distance": self.distance,
            "predicted_eta": self.predicted_eta,
            "actual_duration": self.actual_duration,
            "absolute_error": self.absolute_error,
            "accuracy": self.accuracy,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

def create_database():
    """Create the database if it doesn't exist"""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from urllib.parse import urlparse
    
    try:
        # Parse the DATABASE_URL to get connection details
        db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/trafficlab")
        parsed_url = urlparse(db_url)
        
        # Connect to PostgreSQL server (not to the specific database)
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            user=parsed_url.username,
            password=parsed_url.password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create cursor
        cursor = conn.cursor()
        
        # Get database name from URL
        db_name = parsed_url.path[1:] if parsed_url.path else 'trafficlab'
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';")
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f'CREATE DATABASE {db_name};')
            print(f'✅ Database {db_name} created successfully')
        else:
            print(f'✅ Database {db_name} already exists')
        
        # Close connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ Error creating database: {e}')
        raise

def create_tables():
    """Create all database tables"""
    # First ensure the database exists
    create_database()
    
    # Then create the tables
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_simulation_result(db: Session, result_data: dict):
    """Save simulation result to database"""
    result = SimulationResult(**result_data)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

def get_recent_results(db: Session, limit: int = 10):
    """Get recent simulation results"""
    return db.query(SimulationResult).order_by(SimulationResult.timestamp.desc()).limit(limit).all()

def get_statistics(db: Session):
    """Get simulation statistics"""
    results = db.query(SimulationResult).all()
    
    if not results:
        return {
            "total_runs": 0,
            "average_accuracy": 0,
            "average_predicted_eta": 0,
            "average_actual_duration": 0,
            "average_route_length": 0
        }
    
    total_runs = len(results)
    accuracies = [r.accuracy for r in results if r.accuracy is not None]
    predicted_etas = [r.predicted_eta for r in results]
    actual_durations = [r.actual_duration for r in results]
    route_lengths = [r.route_length for r in results]
    
    return {
        "total_runs": total_runs,
        "average_accuracy": sum(accuracies) / len(accuracies) if accuracies else 0,
        "average_predicted_eta": sum(predicted_etas) / len(predicted_etas),
        "average_actual_duration": sum(actual_durations) / len(actual_durations),
        "average_route_length": sum(route_lengths) / len(route_lengths)
    }

# Entity CRUD operations

def add_junction(db: Session, junction_data: dict):
    """Add a junction to the database"""
    junction = JunctionDB(**junction_data)
    db.add(junction)
    db.commit()
    db.refresh(junction)
    return junction

def get_junction(db: Session, junction_id: str):
    """Get a junction by ID"""
    return db.query(JunctionDB).filter(JunctionDB.id == junction_id).first()

def get_all_junctions(db: Session):
    """Get all junctions"""
    return db.query(JunctionDB).all()

def update_junction(db: Session, junction_id: str, junction_data: dict):
    """Update a junction"""
    junction = db.query(JunctionDB).filter(JunctionDB.id == junction_id).first()
    if junction:
        for key, value in junction_data.items():
            setattr(junction, key, value)
        db.commit()
        db.refresh(junction)
    return junction

def delete_junction(db: Session, junction_id: str):
    """Delete a junction"""
    junction = db.query(JunctionDB).filter(JunctionDB.id == junction_id).first()
    if junction:
        db.delete(junction)
        db.commit()
    return junction

def add_road(db: Session, road_data: dict):
    """Add a road to the database"""
    road = RoadDB(**road_data)
    db.add(road)
    db.commit()
    db.refresh(road)
    return road

def get_road(db: Session, road_id: str):
    """Get a road by ID"""
    return db.query(RoadDB).filter(RoadDB.id == road_id).first()

def get_all_roads(db: Session):
    """Get all roads"""
    return db.query(RoadDB).all()

def update_road(db: Session, road_id: str, road_data: dict):
    """Update a road"""
    road = db.query(RoadDB).filter(RoadDB.id == road_id).first()
    if road:
        for key, value in road_data.items():
            setattr(road, key, value)
        db.commit()
        db.refresh(road)
    return road

def delete_road(db: Session, road_id: str):
    """Delete a road"""
    road = db.query(RoadDB).filter(RoadDB.id == road_id).first()
    if road:
        db.delete(road)
        db.commit()
    return road

def add_zone(db: Session, zone_data: dict):
    """Add a zone to the database"""
    zone = ZoneDB(**zone_data)
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone

def get_zone(db: Session, zone_id: str):
    """Get a zone by ID"""
    return db.query(ZoneDB).filter(ZoneDB.id == zone_id).first()

def get_all_zones(db: Session):
    """Get all zones"""
    return db.query(ZoneDB).all()

def update_zone(db: Session, zone_id: str, zone_data: dict):
    """Update a zone"""
    zone = db.query(ZoneDB).filter(ZoneDB.id == zone_id).first()
    if zone:
        for key, value in zone_data.items():
            setattr(zone, key, value)
        db.commit()
        db.refresh(zone)
    return zone

def delete_zone(db: Session, zone_id: str):
    """Delete a zone"""
    zone = db.query(ZoneDB).filter(ZoneDB.id == zone_id).first()
    if zone:
        db.delete(zone)
        db.commit()
    return zone

def add_zone_edge(db: Session, zone_id: str, road_id: str):
    """Add a road to a zone"""
    zone_edge = ZoneEdge(zone_id=zone_id, road_id=road_id)
    db.add(zone_edge)
    db.commit()
    return zone_edge

def add_zone_junction(db: Session, zone_id: str, junction_id: str):
    """Add a junction to a zone"""
    zone_junction = ZoneJunction(zone_id=zone_id, junction_id=junction_id)
    db.add(zone_junction)
    db.commit()
    return zone_junction

def get_zone_edges(db: Session, zone_id: str):
    """Get all roads in a zone"""
    return db.query(RoadDB).join(ZoneEdge).filter(ZoneEdge.zone_id == zone_id).all()

def get_zone_junctions(db: Session, zone_id: str):
    """Get all junctions in a zone"""
    return db.query(JunctionDB).join(ZoneJunction).filter(ZoneJunction.zone_id == zone_id).all()

def check_entities_exist(db: Session):
    """Check if entities exist in the database"""
    junction_count = db.query(JunctionDB).count()
    road_count = db.query(RoadDB).count()
    zone_count = db.query(ZoneDB).count()
    
    return {
        "junctions_exist": junction_count > 0,
        "roads_exist": road_count > 0,
        "zones_exist": zone_count > 0,
        "junction_count": junction_count,
        "road_count": road_count,
        "zone_count": zone_count
    }

# Vehicle Schedule CRUD operations

def add_vehicle_schedule(db: Session, schedule_data: dict):
    """Add a vehicle schedule entry to the database"""
    schedule = VehicleSchedule(**schedule_data)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

def get_vehicle_schedules(db: Session, step: int = None, week: int = None, day: int = None):
    """Get vehicle schedules with optional filters"""
    query = db.query(VehicleSchedule)
    
    if step is not None:
        query = query.filter(VehicleSchedule.step == step)
    if week is not None:
        query = query.filter(VehicleSchedule.week == week)
    if day is not None:
        query = query.filter(VehicleSchedule.day == day)
    
    return query.all()

def get_vehicle_schedule_by_step(db: Session, step: int):
    """Get all vehicle schedules for a specific step"""
    return db.query(VehicleSchedule).filter(VehicleSchedule.step == step).all()

def clear_vehicle_schedules(db: Session):
    """Clear all vehicle schedules from the database"""
    db.query(VehicleSchedule).delete()
    db.commit()

def get_schedule_count(db: Session):
    """Get the total number of scheduled vehicles"""
    return db.query(VehicleSchedule).count()

def schedule_exists(db: Session):
    """Check if vehicle schedules exist in the database"""
    return db.query(VehicleSchedule).count() > 0

# Vehicle CRUD functions
def add_vehicle(db: Session, vehicle_data: dict):
    """Add a vehicle to the database"""
    vehicle = VehicleDB(**vehicle_data)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle

def get_all_vehicles(db: Session):
    """Get all vehicles from database"""
    return db.query(VehicleDB).all()

def get_vehicle_count(db: Session):
    """Get count of vehicles in database"""
    return db.query(VehicleDB).count()

def clear_vehicles(db: Session):
    """Clear all vehicles from database"""
    db.query(VehicleDB).delete()
    db.commit()

def vehicles_exist(db: Session):
    """Check if vehicles exist in database"""
    return db.query(VehicleDB).count() > 0

def get_recent_results(db: Session, limit: int = 10):
    """Get recent simulation results"""
    try:
        results = db.query(SimulationResult).order_by(SimulationResult.timestamp.desc()).limit(limit).all()
        return [result.to_dict() for result in results]
    except Exception as e:
        print(f"Error getting recent results: {e}")
        return []

def get_statistics(db: Session):
    """Get simulation statistics"""
    try:
        total_results = db.query(SimulationResult).count()
        if total_results == 0:
            return {
                "total_simulations": 0,
                "average_accuracy": 0,
                "average_duration": 0,
                "success_rate": 0
            }
        
        # Calculate statistics
        results = db.query(SimulationResult).all()
        accuracies = [r.accuracy for r in results if r.accuracy is not None]
        durations = [r.actual_duration for r in results if r.actual_duration is not None]
        
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        avg_duration = sum(durations) / len(durations) if durations else 0
        success_rate = len([r for r in results if r.accuracy and r.accuracy > 0.8]) / total_results * 100
        
        return {
            "total_simulations": total_results,
            "average_accuracy": round(avg_accuracy, 2),
            "average_duration": round(avg_duration, 2),
            "success_rate": round(success_rate, 2)
        }
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {
            "total_simulations": 0,
            "average_accuracy": 0,
            "average_duration": 0,
            "success_rate": 0
        }

# Journey CRUD operations

def get_next_journey_number(db: Session):
    """Get the next journey number for continuous numbering"""
    try:
        last_journey = db.query(Journey).order_by(Journey.journey_number.desc()).first()
        if last_journey:
            return last_journey.journey_number + 1
        return 1
    except Exception as e:
        print(f"Error getting next journey number: {e}")
        return 1

def create_journey(db: Session, journey_data: dict):
    """Create a new journey in the database"""
    try:
        # Get the next journey number
        journey_number = get_next_journey_number(db)
        journey_data['journey_number'] = journey_number
        
        # Convert route_edges to JSON string if it's a list
        if 'route_edges' in journey_data and isinstance(journey_data['route_edges'], list):
            journey_data['route_edges'] = json.dumps(journey_data['route_edges'])
        
        journey = Journey(**journey_data)
        db.add(journey)
        db.commit()
        db.refresh(journey)
        return journey
    except Exception as e:
        print(f"Error creating journey: {e}")
        db.rollback()
        raise

def get_journey(db: Session, journey_id: int):
    """Get a journey by ID"""
    try:
        return db.query(Journey).filter(Journey.id == journey_id).first()
    except Exception as e:
        print(f"Error getting journey: {e}")
        return None

def get_journey_by_number(db: Session, journey_number: int):
    """Get a journey by journey number"""
    try:
        return db.query(Journey).filter(Journey.journey_number == journey_number).first()
    except Exception as e:
        print(f"Error getting journey by number: {e}")
        return None

def get_journey_by_vehicle_id(db: Session, vehicle_id: str):
    """Get a journey by vehicle ID"""
    try:
        return db.query(Journey).filter(Journey.vehicle_id == vehicle_id).first()
    except Exception as e:
        print(f"Error getting journey by vehicle ID: {e}")
        return None

def update_journey(db: Session, journey_id: int, journey_data: dict):
    """Update a journey"""
    try:
        journey = db.query(Journey).filter(Journey.id == journey_id).first()
        if journey:
            # Convert route_edges to JSON string if it's a list
            if 'route_edges' in journey_data and isinstance(journey_data['route_edges'], list):
                journey_data['route_edges'] = json.dumps(journey_data['route_edges'])
            
            for key, value in journey_data.items():
                setattr(journey, key, value)
            db.commit()
            db.refresh(journey)
        return journey
    except Exception as e:
        print(f"Error updating journey: {e}")
        db.rollback()
        raise

def get_recent_journeys(db: Session, limit: int = 20):
    """Get recent journeys ordered by journey number (descending)"""
    try:
        journeys = db.query(Journey).order_by(Journey.journey_number.desc()).limit(limit).all()
        return [journey.to_dict() for journey in journeys]
    except Exception as e:
        print(f"Error getting recent journeys: {e}")
        return []

def get_journey_count(db: Session):
    """Get total number of journeys"""
    try:
        return db.query(Journey).count()
    except Exception as e:
        print(f"Error getting journey count: {e}")
        return 0

def delete_journey(db: Session, journey_id: int):
    """Delete a journey"""
    try:
        journey = db.query(Journey).filter(Journey.id == journey_id).first()
        if journey:
            db.delete(journey)
            db.commit()
        return journey
    except Exception as e:
        print(f"Error deleting journey: {e}")
        db.rollback()
        raise

def clear_journeys(db: Session):
    """Clear all journeys from database"""
    try:
        db.query(Journey).delete()
        db.commit()
    except Exception as e:
        print(f"Error clearing journeys: {e}")
        db.rollback()
        raise