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

# Global variable for SUMO simulation
sumo_simulation = None

@app.on_event("startup")    
async def startup_event():
    global sumo_simulation
    print("🚀 Initializing TrafficLab System...")
    
    # Initialize database first
    try:
        print("🗄️ Initializing database...")
        from models.database import create_tables
        create_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        raise
    
    # Initialize SUMO simulation during startup, not at import time
    sumo_config_path = os.path.join(os.path.dirname(__file__), "sumo", "urban_three_zones.sumocfg")
    sim_config_path = os.path.join(os.path.dirname(__file__), "sumo", "sim.config.json")
    
    try:
        sumo_simulation = SUMOSimulation(sumo_config_path, sim_config_path)
        # Debug system state after initialization
        sumo_simulation.debug_system_state()
        print("✅ System initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    global sumo_simulation
    if sumo_simulation:
        try:
            sumo_simulation.stop_simulation()
            print("✅ Simulation stopped gracefully")
        except Exception as e:
            print(f"⚠️ Error stopping simulation: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    if sumo_simulation is None:
        return {"status": "unhealthy", "message": "System not initialized"}
    
    try:
        # Check database connectivity
        from models.database import get_db
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        # Check if simulation is responsive
        status = sumo_simulation.get_simulation_status()
        return {
            "status": "healthy", 
            "simulation": status,
            "database": "connected"
        }
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}

@app.get("/")
async def root():
    return {"message": "SmartTransportation Lab API is running!"}


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
        from models.database import get_recent_journeys, get_journey_count
        
        journeys = get_recent_journeys(db, limit)
        total_count = get_journey_count(db)
        
        return {
            "success": True,
            "journeys": journeys,
            "count": len(journeys),
            "total_count": total_count
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

@app.get("/api/journeys/plot-data/duration-vs-mae")
async def get_duration_vs_mae_data(db: Session = Depends(get_db)):
    """Get data for Trip Duration vs MAE scatter plot"""
    try:
        from models.database import get_duration_vs_mae_plot_data
        
        plot_data = get_duration_vs_mae_plot_data(db)
        
        return {
            "success": True,
            "plot_data": plot_data
        }
    except Exception as e:
        print(f"❌ API: Error getting duration vs MAE plot data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get plot data: {str(e)}")

@app.get("/api/journeys/plot-data/distance-vs-mae")
async def get_distance_vs_mae_data(db: Session = Depends(get_db)):
    """Get data for Trip Distance vs MAE scatter plot"""
    try:
        from models.database import get_distance_vs_mae_plot_data
        
        plot_data = get_distance_vs_mae_plot_data(db)
        
        return {
            "success": True,
            "plot_data": plot_data
        }
    except Exception as e:
        print(f"❌ API: Error getting distance vs MAE plot data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get plot data: {str(e)}")

@app.get("/api/journeys/plot-image/duration-vs-mae")
async def get_duration_vs_mae_plot_image(db: Session = Depends(get_db)):
    """Generate matplotlib plot image for Trip Duration vs MAE scatter plot"""
    try:
        from models.database import get_duration_vs_mae_plot_data
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        import io
        import base64
        
        # Get plot data
        plot_data = get_duration_vs_mae_plot_data(db)
        
        if not plot_data.get('data_points'):
            return {
                "success": False,
                "message": "No data available for plotting"
            }
        
        # Create matplotlib figure
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Define colors for categories
        colors = {
            'short': '#3b82f6',    # Blue
            'medium': '#f59e0b',   # Orange
            'long': '#10b981'      # Green
        }
        
        # Plot data points by category
        for category, color in colors.items():
            category_points = [p for p in plot_data['data_points'] if p['category'] == category]
            if category_points:
                x_vals = [p['x'] for p in category_points]
                y_vals = [p['y'] for p in category_points]
                
                # Convert duration from seconds to minutes for display
                x_vals_minutes = [x / 60 for x in x_vals]
                
                ax.scatter(x_vals_minutes, y_vals, 
                          c=color, 
                          label=plot_data['categories'][category]['label'],
                          alpha=0.7, 
                          s=60,
                          edgecolors='white',
                          linewidth=0.5)
        
        # Set axis labels and title
        ax.set_xlabel('Trip Duration (minutes)', fontsize=14, color='white')
        ax.set_ylabel('MAE (seconds)', fontsize=14, color='white')
        ax.set_title('Trip Duration vs MAE Scatter Plot', fontsize=16, color='white', pad=20)
        
        # Set axis ranges
        ax.set_xlim(0, 80)  # 0 to 80 minutes
        ax.set_ylim(0, 200)  # 0 to 200 seconds
        
        # Set grid
        ax.grid(True, alpha=0.3, color='gray')
        ax.set_facecolor('black')
        
        # Set legend
        ax.legend(loc='upper right', framealpha=0.8)
        
        # Set tick colors
        ax.tick_params(colors='white')
        
        # Convert to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='black', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return {
            "success": True,
            "image": f"data:image/png;base64,{image_base64}",
            "total_points": len(plot_data['data_points'])
        }
        
    except Exception as e:
        print(f"❌ API: Error generating matplotlib plot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate plot: {str(e)}")

@app.get("/api/journeys/plot-image/distance-vs-mae")
async def get_distance_vs_mae_plot_image(db: Session = Depends(get_db)):
    """Generate matplotlib plot image for Trip Distance vs MAE scatter plot"""
    try:
        from models.database import get_distance_vs_mae_plot_data
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        import io
        import base64
        
        # Get plot data
        plot_data = get_distance_vs_mae_plot_data(db)
        
        if not plot_data.get('data_points'):
            return {
                "success": False,
                "message": "No data available for plotting"
            }
        
        # Create matplotlib figure
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Define colors for categories
        colors = {
            'short': '#3b82f6',    # Blue
            'medium': '#f59e0b',   # Orange
            'long': '#10b981'      # Green
        }
        
        # Plot data points by category
        for category, color in colors.items():
            category_points = [p for p in plot_data['data_points'] if p['category'] == category]
            if category_points:
                x_vals = [p['x'] for p in category_points]
                y_vals = [p['y'] for p in category_points]
                
                # Convert distance from meters to kilometers for display
                x_vals_km = [x / 1000 for x in x_vals]
                
                ax.scatter(x_vals_km, y_vals, 
                          c=color, 
                          label=plot_data['categories'][category]['label'],
                          alpha=0.7, 
                          s=60,
                          edgecolors='white',
                          linewidth=0.5)
        
        # Set axis labels and title
        ax.set_xlabel('Trip Distance (km)', fontsize=14, color='white')
        ax.set_ylabel('MAE (seconds)', fontsize=14, color='white')
        ax.set_title('Trip Distance vs MAE Scatter Plot', fontsize=16, color='white', pad=20)
        
        # Set axis ranges
        ax.set_xlim(0, 20)  # 0 to 20 kilometers
        ax.set_ylim(0, 200)  # 0 to 200 seconds
        
        # Set grid
        ax.grid(True, alpha=0.3, color='gray')
        ax.set_facecolor('black')
        
        # Set legend
        ax.legend(loc='upper right', framealpha=0.8)
        
        # Set tick colors
        ax.tick_params(colors='white')
        
        # Convert to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='black', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return {
            "success": True,
            "image": f"data:image/png;base64,{image_base64}",
            "total_points": len(plot_data['data_points'])
        }
        
    except Exception as e:
        print(f"❌ API: Error generating matplotlib plot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate plot: {str(e)}")

@app.get("/api/journeys/plot-data/mae-by-time")
async def get_mae_by_time_data(db: Session = Depends(get_db)):
    """Get data for MAE by Time of Day bar chart"""
    try:
        from models.database import get_mae_by_time_plot_data
        
        plot_data = get_mae_by_time_plot_data(db)
        
        return {
            "success": True,
            "plot_data": plot_data
        }
    except Exception as e:
        print(f"❌ API: Error getting MAE by time plot data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get plot data: {str(e)}")

@app.get("/api/journeys/plot-image/mae-by-time")
async def get_mae_by_time_plot_image(db: Session = Depends(get_db)):
    """Generate matplotlib plot image for MAE by Time of Day bar chart"""
    try:
        from models.database import get_mae_by_time_plot_data
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        import io
        import base64
        
        # Get plot data
        plot_data = get_mae_by_time_plot_data(db)
        
        if not plot_data.get('data_points'):
            return {
                "success": False,
                "message": "No data available for plotting"
            }
        
        # Create matplotlib figure
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Extract data for plotting
        hours = [point['hour'] for point in plot_data['data_points']]
        mae_values = [point['mae'] for point in plot_data['data_points']]
        counts = [point['count'] for point in plot_data['data_points']]
        
        # Create bar chart
        bars = ax.bar(hours, mae_values, 
                     color='#3b82f6', 
                     alpha=0.8,
                     edgecolor='white',
                     linewidth=0.5)
        
        # Add count labels on top of bars (only for bars with data)
        for i, (bar, count) in enumerate(zip(bars, counts)):
            if count > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'n={count}', 
                       ha='center', va='bottom',
                       fontsize=8, color='white')
        
        # Set axis labels and title
        ax.set_xlabel('Hour of Day', fontsize=14, color='white')
        ax.set_ylabel('Average MAE (seconds)', fontsize=14, color='white')
        ax.set_title('MAE by Time of Day', fontsize=16, color='white', pad=20)
        
        # Set x-axis to show all hours
        ax.set_xticks(range(0, 24))
        ax.set_xticklabels([f'{h:02d}:00' for h in range(24)], rotation=45)
        
        # Set y-axis range
        max_mae = max(mae_values) if mae_values else 0
        ax.set_ylim(0, max_mae * 1.1 if max_mae > 0 else 10)
        
        # Set grid
        ax.grid(True, alpha=0.3, color='gray', axis='y')
        ax.set_facecolor('black')
        
        # Set tick colors
        ax.tick_params(colors='white')
        
        # Convert to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                   facecolor='black', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return {
            "success": True,
            "image": f"data:image/png;base64,{image_base64}",
            "total_points": len(plot_data['data_points'])
        }
        
    except Exception as e:
        print(f"❌ API: Error generating matplotlib plot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate plot: {str(e)}")

@app.get("/api/journeys/plot-data/duration-histogram/{category}")
async def get_duration_histogram_data(category: str, db: Session = Depends(get_db)):
    """Get data for Trip Duration vs MAE Histogram"""
    try:
        from models.database import get_duration_histogram_plot_data
        
        plot_data = get_duration_histogram_plot_data(db, category)
        
        return {
            "success": True,
            "plot_data": plot_data
        }
    except Exception as e:
        print(f"❌ API: Error getting duration histogram plot data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get plot data: {str(e)}")

@app.get("/api/journeys/plot-image/duration-histogram/{category}")
async def get_duration_histogram_plot_image(category: str, db: Session = Depends(get_db)):
    """Generate matplotlib plot image for Trip Duration vs MAE Histogram"""
    try:
        from models.database import get_duration_histogram_plot_data
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        import io
        import base64
        import numpy as np
        
        # Get plot data
        plot_data = get_duration_histogram_plot_data(db, category)
        
        if not plot_data.get('data_points'):
            return {
                "success": False,
                "message": "No data available for plotting"
            }
        
        # Create matplotlib figure
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Extract data for plotting
        bin_centers = [point['bin_center'] for point in plot_data['data_points']]
        counts = [point['count'] for point in plot_data['data_points']]
        bin_edges = plot_data['bins']
        
        # Create histogram
        bars = ax.bar(bin_centers, counts, 
                     width=np.diff(bin_edges)[0] * 0.8,  # 80% width for spacing
                     color='#3b82f6', 
                     alpha=0.8,
                     edgecolor='white',
                     linewidth=0.5)
        
        # Set axis labels and title
        ax.set_xlabel('MAE (seconds)', fontsize=14, color='white')
        ax.set_ylabel('Frequency', fontsize=14, color='white')
        ax.set_title(f'Trip Duration vs MAE Histogram - {category.title()}', fontsize=16, color='white', pad=20)
        
        # Set x-axis range
        ax.set_xlim(0, max(bin_centers) * 1.1 if bin_centers else 10)
        
        # Set y-axis range
        max_count = max(counts) if counts else 1
        ax.set_ylim(0, max_count * 1.1)
        
        # Set grid
        ax.grid(True, alpha=0.3, color='gray', axis='y')
        ax.set_facecolor('black')
        
        # Set tick colors
        ax.tick_params(colors='white')
        
        # Add statistics text
        total_journeys = plot_data['total_journeys']
        mae_values = plot_data.get('mae_values', [])
        if mae_values:
            mean_mae = np.mean(mae_values)
            std_mae = np.std(mae_values)
            ax.text(0.02, 0.98, f'Total Journeys: {total_journeys}\nMean MAE: {mean_mae:.1f}s\nStd MAE: {std_mae:.1f}s', 
                   transform=ax.transAxes, fontsize=10, color='white',
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
        
        # Convert to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                   facecolor='black', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return {
            "success": True,
            "image": f"data:image/png;base64,{image_base64}",
            "total_points": len(plot_data['data_points']),
            "total_journeys": total_journeys
        }
        
    except Exception as e:
        print(f"❌ API: Error generating matplotlib plot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate plot: {str(e)}")

@app.get("/api/journeys/plot-data/distance-histogram/{category}")
async def get_distance_histogram_data(category: str, db: Session = Depends(get_db)):
    """Get data for Trip Distance vs MAE Histogram"""
    try:
        from models.database import get_distance_histogram_plot_data
        
        plot_data = get_distance_histogram_plot_data(db, category)
        
        return {
            "success": True,
            "plot_data": plot_data
        }
    except Exception as e:
        print(f"❌ API: Error getting distance histogram plot data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get plot data: {str(e)}")

@app.get("/api/journeys/plot-image/distance-histogram/{category}")
async def get_distance_histogram_plot_image(category: str, db: Session = Depends(get_db)):
    """Generate matplotlib plot image for Trip Distance vs MAE Histogram"""
    try:
        from models.database import get_distance_histogram_plot_data
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        import io
        import base64
        import numpy as np
        
        # Get plot data
        plot_data = get_distance_histogram_plot_data(db, category)
        
        if not plot_data.get('data_points'):
            return {
                "success": False,
                "message": "No data available for plotting"
            }
        
        # Create matplotlib figure
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Extract data for plotting
        bin_centers = [point['bin_center'] for point in plot_data['data_points']]
        counts = [point['count'] for point in plot_data['data_points']]
        bin_edges = plot_data['bins']
        
        # Create histogram
        bars = ax.bar(bin_centers, counts, 
                     width=np.diff(bin_edges)[0] * 0.8,  # 80% width for spacing
                     color='#10b981',  # Green color for distance histograms
                     alpha=0.8,
                     edgecolor='white',
                     linewidth=0.5)
        
        # Set axis labels and title
        ax.set_xlabel('MAE (seconds)', fontsize=14, color='white')
        ax.set_ylabel('Frequency', fontsize=14, color='white')
        ax.set_title(f'Trip Distance vs MAE Histogram - {category.title()}', fontsize=16, color='white', pad=20)
        
        # Set x-axis range
        ax.set_xlim(0, max(bin_centers) * 1.1 if bin_centers else 10)
        
        # Set y-axis range
        max_count = max(counts) if counts else 1
        ax.set_ylim(0, max_count * 1.1)
        
        # Set grid
        ax.grid(True, alpha=0.3, color='gray', axis='y')
        ax.set_facecolor('black')
        
        # Set tick colors
        ax.tick_params(colors='white')
        
        # Add statistics text
        total_journeys = plot_data['total_journeys']
        mae_values = plot_data.get('mae_values', [])
        if mae_values:
            mean_mae = np.mean(mae_values)
            std_mae = np.std(mae_values)
            ax.text(0.02, 0.98, f'Total Journeys: {total_journeys}\nMean MAE: {mean_mae:.1f}s\nStd MAE: {std_mae:.1f}s', 
                   transform=ax.transAxes, fontsize=10, color='white',
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
        
        # Convert to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                   facecolor='black', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return {
            "success": True,
            "image": f"data:image/png;base64,{image_base64}",
            "total_points": len(plot_data['data_points']),
            "total_journeys": total_journeys
        }
        
    except Exception as e:
        print(f"❌ API: Error generating matplotlib plot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate plot: {str(e)}")

@app.post("/api/admin/seed-data")
async def seed_random_journeys(db: Session = Depends(get_db)):
    """
    HIDDEN COMMAND: Seed database with 100 random journeys from labels.json
    Simulates realistic ETA predictions with duration-based error patterns
    """
    try:
        import json
        import random
        import numpy as np
        from datetime import datetime, timedelta
        from models.database import Journey
        
        print("🌱 Starting data seeding process...")
        
        # Load labels.json
        labels_file = "labels.json"
        if not os.path.exists(labels_file):
            raise HTTPException(status_code=404, detail="labels.json file not found")
        
        print("📖 Loading labels.json...")
        with open(labels_file, 'r') as f:
            all_journeys = json.load(f)
        
        print(f"📊 Loaded {len(all_journeys)} total journeys from labels.json")
        
        # Select 100 random journeys
        selected_journeys = random.sample(all_journeys, min(100, len(all_journeys)))
        print(f"🎲 Selected {len(selected_journeys)} random journeys")
        
        # Get next journey number
        last_journey = db.query(Journey).order_by(Journey.journey_number.desc()).first()
        next_journey_number = (last_journey.journey_number + 1) if last_journey else 1
        
        # Error parameters by duration bin
        error_params = {
            'short': {'mae': 24.05, 'std': 12.0},    # < 278 seconds
            'medium': {'mae': 38.31, 'std': 19.0},   # 278-609 seconds  
            'long': {'mae': 76.90, 'std': 38.0}      # > 609 seconds
        }
        
        inserted_count = 0
        error_stats = {'short': [], 'medium': [], 'long': []}
        
        for i, journey_data in enumerate(selected_journeys):
            try:
                # Extract data from labels.json
                vehicle_id = journey_data['vehicle_id']
                actual_duration = journey_data['total_travel_time_seconds']
                distance = journey_data['initial_route_length']
                origin_edge = journey_data['origin_edge']
                destination_edge = journey_data['destination_edge']
                route_edges = journey_data['route']
                
                # Determine duration bin and error parameters
                if actual_duration < 278:
                    bin_name = 'short'
                elif actual_duration <= 609:
                    bin_name = 'medium'
                else:
                    bin_name = 'long'
                
                error_config = error_params[bin_name]
                
                # Generate realistic prediction error
                # Use normal distribution with mean=0, std based on MAE
                error_seconds = np.random.normal(0, error_config['std'])
                
                # Ensure error is proportional to duration (longer trips can have larger errors)
                error_scale = min(1.0, actual_duration / 600.0)  # Scale up to 10 minutes
                error_seconds *= error_scale
                
                # Calculate predicted duration
                predicted_duration = actual_duration + error_seconds
                predicted_duration = max(1, int(predicted_duration))  # Ensure positive
                
                # Calculate actual error for statistics
                actual_error = abs(predicted_duration - actual_duration)
                error_stats[bin_name].append(actual_error)
                
                # Generate simulation timestamps (simulation steps, not Unix timestamps)
                # Simulation runs for 24 hours (0 to 86400 seconds)
                # Use random simulation steps across the full day
                start_step = random.randint(0, 86400)  # Random time across all 24 hours
                end_step = start_step + actual_duration
                predicted_eta = start_step + predicted_duration
                
                # Convert simulation steps to time strings (HH:MM:SS format)
                def simulation_step_to_time_string(step):
                    hours = step // 3600
                    minutes = (step % 3600) // 60
                    seconds = step % 60
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                start_time_string = simulation_step_to_time_string(start_step)
                end_time_string = simulation_step_to_time_string(end_step)
                
                # Create journey record
                journey = Journey(
                    journey_number=next_journey_number + i,
                    vehicle_id=vehicle_id,
                    start_edge=origin_edge,
                    end_edge=destination_edge,
                    route_edges=json.dumps(route_edges),
                    start_time=start_step,
                    start_time_string=start_time_string,
                    end_time=end_step,
                    end_time_string=end_time_string,
                    distance=distance,
                    predicted_eta=predicted_eta,
                    actual_duration=actual_duration,
                    absolute_error=actual_error,
                    accuracy=max(0, 100 * (1 - actual_error / actual_duration)) if actual_duration > 0 else 0,
                    status="finished"
                )
                
                db.add(journey)
                inserted_count += 1
                
                if (i + 1) % 20 == 0:
                    print(f"📝 Processed {i + 1}/{len(selected_journeys)} journeys...")
                    
            except Exception as e:
                print(f"⚠️ Error processing journey {i}: {e}")
                continue
        
        # Commit all changes
        db.commit()
        print(f"✅ Successfully inserted {inserted_count} journeys into database")
        
        # Calculate actual error statistics
        stats_summary = {}
        for bin_name, errors in error_stats.items():
            if errors:
                stats_summary[bin_name] = {
                    'count': len(errors),
                    'avg_mae': round(np.mean(errors), 2),
                    'target_mae': error_params[bin_name]['mae'],
                    'duration_range': '< 278s' if bin_name == 'short' else '278-609s' if bin_name == 'medium' else '> 609s'
                }
        
        print("📊 Error Statistics:")
        for bin_name, stats in stats_summary.items():
            print(f"  {bin_name.capitalize()}: {stats['count']} trips, MAE {stats['avg_mae']}s (target: {stats['target_mae']}s)")
        
        return {
            "success": True,
            "message": f"Successfully seeded {inserted_count} random journeys",
            "inserted_count": inserted_count,
            "error_statistics": stats_summary,
            "next_journey_number": next_journey_number + inserted_count
        }
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to seed data: {str(e)}")

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
