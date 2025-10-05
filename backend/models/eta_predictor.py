import torch
import torch.nn as nn
import numpy as np
from typing import List, Tuple

class ETAPredictor(nn.Module):
    """
    Simple neural network for ETA prediction based on:
    - Distance
    - Current speed
    - Traffic density
    - Time of day
    """
    
    def __init__(self, input_size: int = 4, hidden_size: int = 64, output_size: int = 1):
        super(ETAPredictor, self).__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, output_size)
        )
        
    def forward(self, x):
        return self.network(x)
    
    def predict_eta(self, distance: float, current_speed: float, 
                   traffic_density: float, time_of_day: float) -> float:
        """
        Predict ETA in seconds
        
        Args:
            distance: Distance in meters
            current_speed: Current speed in m/s
            traffic_density: Traffic density (0-1)
            time_of_day: Time of day as fraction (0-1)
        """
        # Normalize inputs
        inputs = torch.tensor([
            distance / 1000.0,  # Convert to km
            current_speed / 30.0,  # Normalize speed
            traffic_density,
            time_of_day
        ], dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            prediction = self.forward(inputs)
            # Convert back to seconds
            return max(1.0, prediction.item() * 3600)  # Minimum 1 second

def create_trained_model() -> ETAPredictor:
    """
    Create a pre-trained ETA prediction model
    In a real scenario, this would be trained on historical data
    """
    model = ETAPredictor()
    
    # Simple heuristic-based "training" for demo purposes
    # In reality, this would be trained on real traffic data
    model.eval()
    
    return model

def calculate_traffic_density(vehicles: List[dict], road_length: float) -> float:
    """
    Calculate traffic density based on number of vehicles on road
    
    Args:
        vehicles: List of vehicle dictionaries with position info
        road_length: Length of the road segment in meters
    
    Returns:
        Traffic density (0-1)
    """
    if road_length <= 0:
        return 0.0
    
    # Count vehicles on the road
    vehicle_count = len(vehicles)
    
    # Calculate density (vehicles per km)
    density = (vehicle_count * 1000) / road_length
    
    # Normalize to 0-1 range (assuming max 50 vehicles per km)
    return min(1.0, density / 50.0)

def get_time_of_day_fraction() -> float:
    """
    Get current time of day as a fraction (0-1)
    """
    import datetime
    now = datetime.datetime.now()
    total_seconds = now.hour * 3600 + now.minute * 60 + now.second
    return total_seconds / 86400.0  # 86400 seconds in a day
