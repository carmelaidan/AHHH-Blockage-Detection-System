"""
SIMULATOR - Test Data Generator
Use this to test the system without hardware - simulates sensor readings
Run multiple times to generate test data (python simulator.py)
"""

import requests
from config import API_URL
import random
from datetime import datetime

# Generate a fake water level reading and send it to the API
try:
    water_level = round(random.uniform(20, 60), 1)  # Random level between 20-60 cm
    power_consumption = round(random.uniform(0.3, 1.2), 2)  # Random power 0.3-1.2W
    mcu_timestamp = datetime.utcnow().isoformat() + "Z"  # ISO 8601 UTC format
    
    # Send to the backend like a real sensor would
    response = requests.post(API_URL, json={
        "sensor_id": "Ternate_Sensor_02",
        "water_level_cm": water_level,
        "latitude": 8.7465,
        "longitude": 127.3851,
        "power_consumption_watts": power_consumption,
        "mcu_timestamp": mcu_timestamp,
        "is_simulated": True
    }, timeout=5)
    
    if response.status_code == 201:
        print(f"✅ Success! Level: {water_level}cm | Power: {power_consumption}W | Time: {mcu_timestamp}")
    else:
        print(f"⚠️ Error {response.status_code}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
