from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import os
import time
import json

from services.sumo_service import SUMOSimulation

class RouteRequest(BaseModel):
    start_edge: str
    end_edge: str

app = FastAPI(title="SmartTransportation Lab API", version="1.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SUMO simulation
sumo_config_path = os.path.join(os.path.dirname(__file__), "sumo", "urban_three_zones.sumocfg")
sim_config_path = os.path.join(os.path.dirname(__file__), "sumo", "sim.config.json")

print("🚀 Initializing TrafficLab System...")
sumo_simulation = SUMOSimulation(sumo_config_path, sim_config_path)

# Debug system state after initialization
sumo_simulation.debug_system_state()

@app.on_event("startup")    
async def startup_event():
    print("✅ System initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    sumo_simulation.stop_simulation()

@app.get("/")
async def root():
    return {"message": "SmartTransportation Lab API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/simulation/status")
async def get_simulation_status():
    """Get current simulation status"""
    return sumo_simulation.get_simulation_status()

@app.post("/api/simulation/start")
async def start_simulation():
    """Start the simulation"""
    try:
        import traci
        sumo_simulation.start_endless_simulation(traci)
        return {"message": "Simulation started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/simulation/data-status")
async def get_data_status():
    """Get data loading status"""
    try:
        return {
            "data_loaded": sumo_simulation.is_data_loaded(),
            "junctions_count": len(sumo_simulation.junctions),
            "roads_count": len(sumo_simulation.roads),
            "zones_count": len(sumo_simulation.zones),
            "vehicles_count": len(sumo_simulation.vehicles),
            "schedule_count": sum(len(v) for v in sumo_simulation.schedule.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/simulation/vehicles/active")
async def get_active_vehicles():
    """Get all active vehicles with their positions from TraCI"""
    try:
        vehicles = sumo_simulation.get_active_vehicles()
        return vehicles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/simulation/vehicles/stagnant")
async def get_stagnant_vehicles():
    """Get currently stagnant vehicles"""
    try:
        stagnant_vehicles = sumo_simulation.get_stagnant_vehicles()
        return {"stagnant_vehicles": stagnant_vehicles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulation/start")
async def start_simulation():
    """Start the SUMO simulation"""
    try:
        if sumo_simulation.simulation_running:
            return {"message": "Simulation already running", "status": "running"}
        
        # Start simulation in background thread
        import threading
        simulation_thread = threading.Thread(target=sumo_simulation.run_simulation)
        simulation_thread.daemon = True
        simulation_thread.start()
        
        return {"message": "Simulation started", "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulation/stop")
async def stop_simulation():
    """Stop the SUMO simulation"""
    try:
        sumo_simulation.simulation_running = False
        return {"message": "Simulation stopped", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulation/start-journey")
async def start_journey(
    start: Dict[str, float],
    end: Dict[str, float]
):
    """Start a new journey with ETA prediction"""
    try:
        start_coords = (start["x"], start["y"])
        end_coords = (end["x"], end["y"])
        
        # Create a simple route (in real implementation, this would use SUMO routing)
        route = ["edge1", "edge2", "edge3", "edge4", "edge5"]
        
        # Add vehicle to simulation
        vehicle_id = sumo_simulation.add_vehicle(route)
        if not vehicle_id:
            raise HTTPException(status_code=400, detail="Failed to add vehicle")
        
        # Predict ETA
        predicted_eta = sumo_simulation.predict_eta(vehicle_id, end_coords)
        
        # Calculate distance
        distance = sumo_simulation.get_route_distance(start_coords, end_coords)
        
        return {
            "vehicle_id": vehicle_id,
            "predicted_eta": predicted_eta,
            "distance": distance,
            "start": start_coords,
            "end": end_coords
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/simulation/vehicle/{vehicle_id}/position")
async def get_vehicle_position(vehicle_id: str):
    """Get current vehicle position"""
    position = sumo_simulation.get_vehicle_position(vehicle_id)
    speed = sumo_simulation.get_vehicle_speed(vehicle_id)
    
    return {
        "vehicle_id": vehicle_id,
        "position": position,
        "speed": speed
    }

@app.post("/api/simulation/complete-journey")
async def complete_journey(
    vehicle_id: str,
    actual_duration: float
):
    """Complete a journey and save results"""
    try:
        # Get vehicle data
        vehicles = sumo_simulation.get_all_vehicles()
        vehicle = next((v for v in vehicles if v["id"] == vehicle_id), None)
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # For demo purposes, use simple coordinates
        start_coords = (0, 0)
        end_coords = (1000, 0)
        distance = 1000.0
        
        # Return result without database saving
        return {
            "vehicle_id": vehicle_id,
            "start": start_coords,
            "end": end_coords,
            "predicted_eta": vehicle.get("predicted_eta", 0),
            "actual_duration": actual_duration,
            "distance": distance
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Database endpoints removed - using in-memory only

@app.get("/api/simulation/results")
async def get_simulation_results(limit: int = 10):
    """Get recent simulation results"""
    # Return empty results since we don't have database
    return {"results": []}

@app.get("/api/simulation/vehicles/finished")
async def get_finished_vehicles():
    """Get finished user-defined vehicles"""
    try:
        finished_vehicles = sumo_simulation.get_finished_vehicles()
        return {"finished_vehicles": finished_vehicles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/simulation/statistics")
async def get_simulation_statistics():
    """Get simulation statistics"""
    # Return basic statistics from the simulation
    return {
        "total_vehicles": len(sumo_simulation.get_all_vehicles()),
        "vehicles_in_route": len(sumo_simulation.vehicles_in_route),
        "junctions_count": len(sumo_simulation.junctions),
        "roads_count": len(sumo_simulation.roads),
        "zones_count": len(sumo_simulation.zones)
    }

@app.get("/api/trips/current")
async def get_current_trips():
    """Get trips for the current step"""
    trips = sumo_simulation.get_trips_for_current_step()
    return {
        "trips": trips,
        "step": sumo_simulation.current_step,
        "count": len(trips)
    }

@app.post("/api/trips/next")
async def next_trips_step():
    """Move to next step and get trips"""
    trips = sumo_simulation.next_step()
    return {
        "trips": trips,
        "step": sumo_simulation.current_step,
        "count": len(trips)
    }

@app.post("/api/trips/play")
async def start_trips_playback():
    """Start trips playback"""
    sumo_simulation.start_trips_playback()
    return {"message": "Trips playback started"}

@app.post("/api/trips/stop")
async def stop_trips_playback():
    """Stop trips playback"""
    sumo_simulation.stop_trips_playback()
    return {"message": "Trips playback stopped"}

@app.get("/api/trips/status")
async def get_trips_status():
    """Get trips playback status"""
    return sumo_simulation.get_playback_status()

@app.get("/api/network/data")
async def get_network_data():
    """Get SUMO network data for visualization"""
    try:
        network_data = sumo_simulation.get_network_data()
        return network_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulation/calculate-route")
async def calculate_route(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float
):
    """Calculate route between two points using SUMO"""
    try:
        route_data = sumo_simulation.calculate_route(
            (start_x, start_y), 
            (end_x, end_y)
        )
        return route_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulation/calculate-route-by-edges")
async def calculate_route_by_edges(request: RouteRequest):
    """Calculate route between two edges using SUMO"""
    try:
        print(f"🛣️ API: Calculating route from {request.start_edge} to {request.end_edge}")
        route_data = sumo_simulation.calculate_route_by_edges(request.start_edge, request.end_edge)
        print(f"✅ API: Route calculation result: {route_data}")
        return route_data
    except Exception as e:
        print(f"❌ API: Route calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class JourneyRequest(BaseModel):
    start_edge: str
    end_edge: str
    route_edges: List[str]
    
    class Config:
        # Allow extra fields
        extra = "allow"

@app.post("/api/simulation/start-journey")
async def start_journey(request: JourneyRequest):
    """Add a vehicle to the simulation for the calculated journey"""
    try:
        print(f"🚗 API: Starting journey from {request.start_edge} to {request.end_edge}")
        print(f"🛣️ API: Route edges: {request.route_edges}")
        print(f"🔍 API: Route edges type: {type(request.route_edges)}")
        print(f"🔍 API: Route edges length: {len(request.route_edges) if request.route_edges else 'None'}")
        
        # Add vehicle to simulation
        vehicle_id = sumo_simulation.add_journey_vehicle(
            request.start_edge, 
            request.end_edge, 
            request.route_edges
        )
        
        print(f"✅ API: Vehicle {vehicle_id} added to simulation")
        return {"vehicle_id": vehicle_id, "status": "started"}
    except Exception as e:
        print(f"❌ API: Journey start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulation/start-journey-manual")
async def start_journey_manual(request: dict):
    """Manual endpoint to test Pydantic validation manually"""
    try:
        print(f"🔍 MANUAL: Raw request: {request}")
        print(f"🔍 MANUAL: Request type: {type(request)}")
        
        # Try to create the Pydantic model manually
        try:
            journey_request = JourneyRequest(**request)
            print(f"✅ MANUAL: Pydantic model created successfully")
            print(f"🔍 MANUAL: start_edge: {journey_request.start_edge}")
            print(f"🔍 MANUAL: end_edge: {journey_request.end_edge}")
            print(f"🔍 MANUAL: route_edges: {journey_request.route_edges}")
            print(f"🔍 MANUAL: route_edges type: {type(journey_request.route_edges)}")
            
            # Add vehicle to simulation
            vehicle_id = sumo_simulation.add_journey_vehicle(
                journey_request.start_edge, 
                journey_request.end_edge, 
                journey_request.route_edges
            )
            
            print(f"✅ MANUAL: Vehicle {vehicle_id} added to simulation")
            return {"vehicle_id": vehicle_id, "status": "started"}
            
        except Exception as validation_error:
            print(f"❌ MANUAL: Pydantic validation failed: {validation_error}")
            print(f"❌ MANUAL: Error type: {type(validation_error)}")
            return {"status": "validation_failed", "error": str(validation_error)}
            
    except Exception as e:
        print(f"❌ MANUAL: General error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulation/start-journey-validation")
async def start_journey_validation(request: dict):
    """Debug endpoint to test Pydantic validation"""
    try:
        print(f"🔍 VALIDATION: Raw request: {request}")
        print(f"🔍 VALIDATION: Request type: {type(request)}")
        
        # Try to create the Pydantic model
        try:
            journey_request = JourneyRequest(**request)
            print(f"✅ VALIDATION: Pydantic model created successfully")
            print(f"🔍 VALIDATION: start_edge: {journey_request.start_edge}")
            print(f"🔍 VALIDATION: end_edge: {journey_request.end_edge}")
            print(f"🔍 VALIDATION: route_edges: {journey_request.route_edges}")
            print(f"🔍 VALIDATION: route_edges type: {type(journey_request.route_edges)}")
            return {"status": "validation_success", "data": journey_request.dict()}
        except Exception as validation_error:
            print(f"❌ VALIDATION: Pydantic validation failed: {validation_error}")
            print(f"❌ VALIDATION: Error type: {type(validation_error)}")
            return {"status": "validation_failed", "error": str(validation_error)}
            
    except Exception as e:
        print(f"❌ VALIDATION: General error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulation/start-journey-raw")
async def start_journey_raw(request: dict):
    """Raw endpoint without Pydantic validation to test data"""
    try:
        print(f"🔍 RAW: Starting journey from {request.get('start_edge')} to {request.get('end_edge')}")
        print(f"🔍 RAW: Route edges: {request.get('route_edges')}")
        print(f"🔍 RAW: Route edges type: {type(request.get('route_edges'))}")
        print(f"🔍 RAW: Route edges length: {len(request.get('route_edges')) if request.get('route_edges') else 'None'}")
        
        # Validate manually
        start_edge = request.get('start_edge')
        end_edge = request.get('end_edge')
        route_edges = request.get('route_edges')
        
        if not start_edge or not isinstance(start_edge, str):
            raise HTTPException(status_code=422, detail="Invalid start_edge")
        if not end_edge or not isinstance(end_edge, str):
            raise HTTPException(status_code=422, detail="Invalid end_edge")
        if not route_edges or not isinstance(route_edges, list):
            raise HTTPException(status_code=422, detail="Invalid route_edges")
        
        # Add vehicle to simulation
        vehicle_id = sumo_simulation.add_journey_vehicle(
            start_edge, 
            end_edge, 
            route_edges
        )
        
        print(f"✅ RAW: Vehicle {vehicle_id} added to simulation")
        return {"vehicle_id": vehicle_id, "status": "started"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ RAW: Journey start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulation/start-journey-debug")
async def start_journey_debug(request: dict):
    """Debug endpoint to see raw request data"""
    try:
        print(f"🔍 DEBUG: Raw request data: {request}")
        print(f"🔍 DEBUG: Request type: {type(request)}")
        print(f"🔍 DEBUG: Request keys: {list(request.keys()) if isinstance(request, dict) else 'Not a dict'}")
        
        if 'route_edges' in request:
            print(f"🔍 DEBUG: Route edges: {request['route_edges']}")
            print(f"🔍 DEBUG: Route edges type: {type(request['route_edges'])}")
            print(f"🔍 DEBUG: Route edges is list: {isinstance(request['route_edges'], list)}")
        
        return {"debug": "Request received", "data": request}
    except Exception as e:
        print(f"❌ DEBUG: Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
