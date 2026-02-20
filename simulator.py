"""
SIMULATOR - Test Data Generator
Simulates ESP32 sensor for testing without hardware
"""

import requests
from config import API_URL
import random

try:
    water_level = round(random.uniform(20, 60), 1)
    
    response = requests.post(API_URL, json={
        "sensor_id": "Ternate_Sensor_02",
        "water_level_cm": water_level,
        "latitude": 8.7465,
        "longitude": 127.3851
    }, timeout=5)
    
    if response.status_code == 201:
        print(f"✅ Success! Water level: {water_level} cm")
    else:
        print(f"⚠️ Error {response.status_code}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
