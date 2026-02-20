import requests
from config import API_URL
import random

try:
    # Simulate varying water levels (between 20-60 cm)
    water_level = round(random.uniform(20, 60), 1)
    
    response = requests.post(API_URL, json={
        "sensor_id": "Ternate_Sensor_02",
        "water_level_cm": water_level,
        "latitude": 8.7465,      # Ternate, Philippines
        "longitude": 127.3851
    }, timeout=5)
    
    if response.status_code == 201:
        print(f"✅ Success! Water level: {water_level} cm - {response.json()}")
    else:
        print(f"⚠️ Error {response.status_code}: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"❌ Connection failed: {e}")