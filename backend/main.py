from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import os
import time
import json

from services.sumo_service import SUMOSimulation

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
async def calculate_route_by_edges(
    start_edge: str,
    end_edge: str
):
    """Calculate route between two edges using SUMO"""
    try:
        route_data = sumo_simulation.calculate_route_by_edges(start_edge, end_edge)
        return route_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
