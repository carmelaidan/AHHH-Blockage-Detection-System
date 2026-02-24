"""
SIMULATOR - Test Data Generator per BAMBI.pdf validation
Generates realistic test data to demonstrate A.H.H.H. system performance
Run multiple times: python simulator.py
"""

import requests
from config import API_URL
import random
from datetime import datetime

# Simulate realistic water level patterns in catch basin (47.5cm height)
# Normal readings: 20-35cm (mostly), Blockage readings: 35-55cm (occasional)
should_trigger_blockage = random.random() < 0.35  # 35% chance of blockage reading
if should_trigger_blockage:
    water_level = round(random.uniform(35, 55), 1)  # High levels trigger blockage
else:
    water_level = round(random.uniform(20, 35), 1)  # Normal background levels

power_consumption = round(random.uniform(0.3, 1.2), 2)
mcu_timestamp = datetime.utcnow().isoformat() + "Z"

# Per BAMBI.pdf: Determine alert status based on thresholds (25%, 50%, 75%)
BASIN_HEIGHT = 47.5
capacity_pct = (water_level / BASIN_HEIGHT) * 100
alert_triggered = capacity_pct >= 25  # 25% = 11.875cm blockage threshold
alert_type = "normal_reading"

if alert_triggered:
    if capacity_pct >= 75:
        alert_type = "blockage_escalated_critical"
    elif capacity_pct >= 50:
        alert_type = "blockage_escalated"
    else:
        alert_type = "blockage_detected"

try:
    response = requests.post(API_URL, json={
        "sensor_id": "Ternate_Sensor_02",
        "water_level_cm": water_level,
        "latitude": 8.7465,
        "longitude": 127.3851,
        "power_consumption_watts": power_consumption,
        "mcu_timestamp": mcu_timestamp,
        "is_simulated": True,
        "alert_status": alert_triggered,
        "alert_type": alert_type
    }, timeout=5)
    
    if response.status_code == 201:
        status_emoji = "🚨" if alert_triggered else "✓"
        print(f"{status_emoji} OK | Level: {water_level}cm ({capacity_pct:.1f}%) | Alert: {alert_type}")
    else:
        print(f"⚠️ Error {response.status_code}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
