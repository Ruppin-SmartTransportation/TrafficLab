from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import os
import time
import json

from services.sumo_service import SUMOSimulation
from models.database import SessionLocal, Journey, get_db
from sqlalchemy.orm import Session

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
async def complete_journey(vehicle_id: str, actual_duration: float):
    """Complete a journey and save results"""
    try:
        # Get vehicle data from simulation
        vehicle_data = sumo_simulation.user_defined_vehicles.get(vehicle_id)
        if not vehicle_data:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Calculate metrics
        current_time = sumo_simulation.current_step
        end_time_string = sumo_simulation.get_simulation_time()
        
        # Get prediction data
        prediction = vehicle_data.get('prediction', {})
        predicted_eta = prediction.get('predicted_eta', 0)
        start_time = vehicle_data.get('start_time', 0)
        
        # Calculate predicted duration (ETA - start_time)
        predicted_duration = predicted_eta - start_time
        
        # Calculate actual duration (current_time - start_time)
        actual_duration_calculated = current_time - start_time
        
        # Use the provided actual_duration if it's reasonable, otherwise use calculated
        if actual_duration > 0 and abs(actual_duration - actual_duration_calculated) < 60:  # Within 1 minute
            final_actual_duration = actual_duration
        else:
            final_actual_duration = actual_duration_calculated
        
        # Calculate error as difference between predicted and actual duration
        absolute_error = abs(predicted_duration - final_actual_duration)
        accuracy = max(0, 100 - (absolute_error / final_actual_duration) * 100) if final_actual_duration > 0 else 0
        
        # Update vehicle data
        vehicle_data['end_time'] = current_time
        vehicle_data['end_time_string'] = end_time_string
        vehicle_data['actual_duration'] = final_actual_duration
        vehicle_data['absolute_error'] = absolute_error
        vehicle_data['accuracy'] = accuracy
        vehicle_data['status'] = 'finished'
        
        print(f"✅ Journey {vehicle_id} completed")
        
        return {
            "vehicle_id": vehicle_id,
            "predicted_eta": predicted_eta,
            "actual_duration": final_actual_duration,
            "absolute_error": absolute_error,
            "accuracy": accuracy,
            "distance": vehicle_data.get('travel_distance', 0)
        }
        
    except Exception as e:
        print(f"❌ API: Error completing journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Database endpoints removed - using in-memory only

@app.get("/api/simulation/results")
async def get_simulation_results(limit: int = 10):
    """Get recent simulation results"""
    try:
        finished_vehicles = sumo_simulation.get_finished_vehicles()
        # Convert to the format expected by frontend
        results = []
        for vehicle in finished_vehicles[:limit]:
            result = {
                "vehicle_id": vehicle.get("id", ""),
                "start_time": vehicle.get("start_time", 0),
                "start_time_string": vehicle.get("start_time_string", "00:00:00"),
                "distance": vehicle.get("travel_distance", 0),
                "predicted_eta": vehicle.get("prediction", {}).get("predicted_eta", 0),
                "status": "finished",
                "end_time": vehicle.get("end_time", 0),
                "end_time_string": vehicle.get("end_time_string", "00:00:00"),
                "actual_duration": vehicle.get("actual_duration", 0),
                "absolute_error": vehicle.get("absolute_error", 0),
                "accuracy": vehicle.get("accuracy", 0)
            }
            results.append(result)
        
        return {"results": results}
    except Exception as e:
        print(f"❌ API: Error getting simulation results: {e}")
        return {"results": []}

# Journey API endpoints

@app.post("/api/journeys/save")
async def save_journey(journey_data: dict, db: Session = Depends(get_db)):
    """Save a journey to the database"""
    try:
        from models.database import create_journey
        
        # Create the journey in the database
        journey = create_journey(db, journey_data)
        
        return {
            "success": True,
            "message": "Journey saved successfully",
            "journey_id": journey.id,
            "journey_number": journey.journey_number
        }
    except Exception as e:
        print(f"❌ API: Error saving journey: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save journey: {str(e)}")

@app.get("/api/journeys/recent")
async def get_recent_journeys(limit: int = 20, db: Session = Depends(get_db)):
    """Get recent journeys from the database"""
    try:
        from models.database import get_recent_journeys
        
        journeys = get_recent_journeys(db, limit)
        
        return {
            "success": True,
            "journeys": journeys,
            "count": len(journeys)
        }
    except Exception as e:
        print(f"❌ API: Error getting recent journeys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent journeys: {str(e)}")

@app.delete("/api/journeys/delete-last")
async def delete_last_journey(db: Session = Depends(get_db)):
    """Delete the last journey (highest journey number)"""
    try:
        from models.database import delete_last_journey
        
        deleted_journey = delete_last_journey(db)
        
        if deleted_journey:
            return {
                "success": True,
                "message": "Last journey deleted successfully",
                "deleted_journey_number": deleted_journey.journey_number
            }
        else:
            return {
                "success": False,
                "message": "No journeys found to delete"
            }
    except Exception as e:
        print(f"❌ API: Error deleting last journey: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete last journey: {str(e)}")

@app.delete("/api/journeys/delete-all")
async def delete_all_journeys(db: Session = Depends(get_db)):
    """Delete all journeys from the database"""
    try:
        from models.database import clear_journeys, get_journey_count
        
        # Get count before deletion
        count_before = get_journey_count(db)
        
        # Clear all journeys
        clear_journeys(db)
        
        return {
            "success": True,
            "message": f"All {count_before} journeys deleted successfully",
            "deleted_count": count_before
        }
    except Exception as e:
        print(f"❌ API: Error deleting all journeys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete all journeys: {str(e)}")

@app.get("/api/journeys/count")
async def get_journey_count(db: Session = Depends(get_db)):
    """Get total number of journeys in the database"""
    try:
        from models.database import get_journey_count
        
        count = get_journey_count(db)
        
        return {
            "success": True,
            "count": count
        }
    except Exception as e:
        print(f"❌ API: Error getting journey count: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get journey count: {str(e)}")

@app.get("/api/journeys/statistics")
async def get_journey_statistics(db: Session = Depends(get_db)):
    """Get journey statistics including MAE, RMSE, MAPE"""
    try:
        from models.database import get_journey_statistics
        
        stats = get_journey_statistics(db)
        
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        print(f"❌ API: Error getting journey statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get journey statistics: {str(e)}")

@app.get("/api/simulation/vehicles/finished")
async def get_finished_vehicles():
    """Get finished user-defined vehicles"""
    try:
        finished_vehicles = sumo_simulation.get_finished_vehicles()
        return {"finished_vehicles": finished_vehicles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulation/vehicles/finished/clear")
async def clear_finished_vehicles():
    """Clear all finished vehicles"""
    try:
        sumo_simulation.clear_finished_vehicles()
        return {"message": "Finished vehicles cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/simulation/vehicles/{vehicle_id}/prediction")
async def get_vehicle_prediction(vehicle_id: str):
    """Get ETA prediction for a specific vehicle"""
    try:
        prediction = sumo_simulation.get_vehicle_prediction(vehicle_id)
        if prediction:
            return {"prediction": prediction}
        else:
            return {"prediction": None, "message": "Vehicle not found or no prediction available"}
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
        
        # Get vehicle data for response
        vehicle_data = sumo_simulation.user_defined_vehicles.get(vehicle_id, {})
        prediction = vehicle_data.get('prediction', {}).get('predicted_eta', 0)
        print(f"✅ API: Vehicle {vehicle_id} added to simulation")
        print(f"🕐 Start time: {vehicle_data.get('start_time', 0)}, Start time string: {vehicle_data.get('start_time_string', 'N/A')}")
        
        return {
            "vehicle_id": vehicle_id, 
            "status": "started",
            "start_time": vehicle_data.get('start_time', 0),
            "start_time_string": vehicle_data.get('start_time_string', '00:00:00'),
            "distance": vehicle_data.get('travel_distance', 0),
            "predicted_eta": prediction
        }
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
            
            # Get the full vehicle data including prediction
            vehicle_data = sumo_simulation.user_defined_vehicles.get(vehicle_id, {})
            
            return {
                "vehicle_id": vehicle_id, 
                "status": "started",
                "start_time": vehicle_data.get('start_time', 0),
                "distance": vehicle_data.get('travel_distance', 0),
                "predicted_eta": vehicle_data.get('prediction', {}).get('predicted_eta', 0),
                "route_edges": journey_request.route_edges
            }
            
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
