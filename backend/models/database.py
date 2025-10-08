from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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

def delete_last_journey(db: Session):
    """Delete the last journey (highest journey number)"""
    try:
        last_journey = db.query(Journey).order_by(Journey.journey_number.desc()).first()
        if last_journey:
            db.delete(last_journey)
            db.commit()
            return last_journey
        return None
    except Exception as e:
        print(f"Error deleting last journey: {e}")
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