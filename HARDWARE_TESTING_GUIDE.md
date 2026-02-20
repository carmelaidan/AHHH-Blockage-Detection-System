# 🛠️ Hardware Setup & Testing Guide

## Part 1: Hardware Assembly

### 1.1 Required Components
- ESP32 Development Board (NodeMCU-32S or DOIT DevKit v1)
- HC-SR04 Ultrasonic Sensor
- USB Cable (USB-A to Micro-USB)
- 4x Jumper Wires (Female-Female)
- 1kΩ Resistor (for voltage divider)
- 2kΩ Resistor (for voltage divider)
- Breadboard (optional but recommended)
- 5V Power Supply (optional, for standalone operation)

### 1.2 Wiring Diagram

```
HC-SR04 Sensor              ESP32 Board
├─ VCC (5V) ────────────→ 5V Pin
├─ GND ─────────────────→ GND Pin
├─ TRIG (GPIO) ─────────→ GPIO5 (D5)
└─ ECHO (GPIO) ─────────→ GPIO18 (D18) via Voltage Divider
                         
Voltage Divider (for ECHO pin - protects 3.3V GPIO from 5V signal):
    HC-SR04 ECHO ──[1kΩ]──→ GPIO18 ──[2kΩ]──→ GND
```

### 1.3 Step-by-Step Wiring

1. **Power Connections:**
   - HC-SR04 VCC → ESP32 5V Pin
   - HC-SR04 GND → ESP32 GND Pin

2. **Signal Connections (Trigger):**
   - HC-SR04 TRIG → ESP32 GPIO5 (D5)

3. **Signal Connections (Echo with Voltage Divider):**
   - HC-SR04 ECHO → 1kΩ Resistor → GPIO18 (D18)
   - GPIO18 → 2kΩ Resistor → GND

**⚠️ Critical:** Always use the voltage divider on ECHO pin. Connecting 5V directly to GPIO18 will damage the ESP32!

---

## Part 2: Software Preparation

### 2.1 Pre-Hardware Checklist
Before connecting hardware, verify your backend is working:

```powershell
# Terminal 1 - Test Database
python db_test.py
# Expected: ✅ Successfully connected to PostgreSQL!

# Terminal 2 - Initialize Database
python setup_db.py
# Expected: ✅ PostGIS extension enabled!
#           ✅ Table 'water_levels' with geospatial support is ready!

# Terminal 3 - Start Flask API
python app.py
# Expected: * Running on http://0.0.0.0:5000
```

### 2.2 Verify Simulator Works
```powershell
# Terminal 4 - Run Simulator
python sim_esp32.py
# Expected: ✅ Success! {'status': 'success', 'message': 'Data saved!'}
```

### 2.3 Verify Dashboard
Open browser and go to `http://localhost:8501`
- Should see data from simulator
- Map should show Ternate, Philippines coordinates

**If simulator works, your backend is 100% ready for real hardware!**

---

## Part 3: ESP32 Firmware Upload

### 3.1 Configure Firmware

Open `esp32_firmware.ino` and update these 4 variables:

```cpp
const char* ssid = "YOUR_WIFI_SSID";           // Your Wi-Fi network name
const char* password = "YOUR_WIFI_PASSWORD";   // Your Wi-Fi password
const char* serverUrl = "http://192.168.x.x:5000/api/water-level";  // Your PC's IP
const float latitude = 8.7465;                 // Your sensor location latitude
const float longitude = 127.3851;              // Your sensor location longitude
```

**Finding Your PC's IP Address:**
```powershell
# Run this in PowerShell to find your IP
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.1.100)
```

Example:
```cpp
const char* serverUrl = "http://192.168.1.100:5000/api/water-level";
```

### 3.2 Upload Firmware

1. Open `esp32_firmware.ino` in Arduino IDE
2. Go to **Tools → Board** → Select **ESP32 Dev Module**
3. Go to **Tools → Port** → Select your USB port
4. Go to **Tools → Upload Speed** → Set to **115200**
5. Click **Upload** (→ button)
6. Wait for "Done uploading" message

### 3.3 Test Serial Connection

1. Go to **Tools → Serial Monitor**
2. Set baud rate to **115200**
3. You should see:
   ```
   ===== HYDRO-HAZARD HELPER - ESP32 FIRMWARE =====
   Initializing system...
   📡 Connecting to Wi-Fi...
   ...
   ✅ Connected to Wi-Fi!
   IP Address: 192.168.x.x
   RSSI: -55 dBm
   ✅ Setup complete! Ready to measure water levels.
   ```

---

## Part 4: Hardware Testing (5 Phases)

### Phase 1: Serial Output Verification ✅

**Objective:** Verify ESP32 is reading sensor correctly

**Setup:**
1. Keep Flask API running (`python app.py`)
2. Open Arduino Serial Monitor
3. Watch for continuous sensor readings

**Expected Output (every 10 seconds):**
```
📊 Water Level: 15.43 cm
📊 Water Level: 15.45 cm
📊 Water Level: 15.44 cm
```

**Troubleshooting:**
- No output? Check USB cable and board selection
- Garbage text? Check baud rate is 115200
- Constant errors? Check HC-SR04 wiring

---

### Phase 2: Wi-Fi Connectivity ✅

**Objective:** Verify ESP32 connects to your network

**Check Serial Output for:**
```
📡 Connecting to Wi-Fi...
✅ Connected to Wi-Fi!
IP Address: 192.168.1.x
RSSI: -45 dBm
```

**Troubleshooting:**
- "Failed to connect to Wi-Fi"?
  - Verify SSID and password in firmware
  - Ensure 2.4GHz Wi-Fi (ESP32 doesn't support 5GHz)
  - Try moving ESP32 closer to router

- High RSSI (worse than -70)?
  - Move ESP32 closer to router for better signal

---

### Phase 3: API Communication ✅

**Objective:** Verify ESP32 sends data to Flask

**Check Serial Output for:**
```
📤 Sending: {"sensor_id":"ESP32_Sensor_01","water_level_cm":15.43,"latitude":8.7465,"longitude":127.3851}
✅ Data successfully sent to server!
```

**Troubleshooting:**
- "Server error: HTTP 0"?
  - Verify serverUrl IP is correct
  - Check Flask API is running (`python app.py`)
  - Check firewall allows port 5000

- "Connection failed"?
  - Verify Wi-Fi is connected (Phase 2)
  - Check PC and ESP32 are on same network

---

### Phase 4: Database Verification ✅

**Objective:** Verify data appears in PostgreSQL

**Run this command:**
```powershell
python insert_test.py
```

**Check Database directly:**
```powershell
# Connect to PostgreSQL
psql -U postgres -d postgres

# Run this SQL query
SELECT sensor_id, water_level_cm, latitude, longitude, recorded_at 
FROM water_levels 
ORDER BY recorded_at DESC LIMIT 5;
```

**Expected Output:**
```
     sensor_id     | water_level_cm | latitude  | longitude  |     recorded_at
─────────────────────┼────────────────┼───────────┼────────────┼──────────────────────
 ESP32_Sensor_01    |          15.43 |  8.746500 | 127.385100 | 2024-01-15 10:30:45
 ESP32_Sensor_01    |          15.44 |  8.746500 | 127.385100 | 2024-01-15 10:30:55
```

---

### Phase 5: Dashboard Visualization ✅

**Objective:** Verify real-time data appears on dashboard

**Steps:**
1. Open `http://localhost:8501` in browser
2. Click **🔄 Refresh Data** button
3. Verify:
   - ✅ Latest Reading shows your sensor data
   - ✅ Trend chart updates with new points
   - ✅ Map shows sensor location with marker
   - ✅ Water level metric updates

**Dashboard Checklist:**
- [ ] Metrics show real ESP32 data (not simulator data)
- [ ] Trend chart shows water level changing
- [ ] Map shows correct location
- [ ] Recent Readings table shows ESP32_Sensor_01
- [ ] CSV export contains real data

---

## Part 5: Real-World Validation Tests

### Test 1: Sensor Accuracy ✓

**Procedure:**
1. Place HC-SR04 15cm above water surface
2. Check Serial Monitor shows ~15.0 cm
3. Place 25cm above water, check shows ~25.0 cm
4. Compare with measuring tape

**Acceptance Criteria:**
- Reading should match physical measurement within ±1 cm
- No fluctuation > 2 cm between consecutive readings

---

### Test 2: Data Reliability ✓

**Procedure:**
1. Let ESP32 run for 1 hour continuously
2. Check database for data gaps

```powershell
python insert_test.py  # Check for 6+ readings every 10 seconds
```

**Acceptance Criteria:**
- 360+ readings in 1 hour (6 per minute)
- No missing data points
- All timestamps in order

---

### Test 3: Alert System ✓

**Procedure:**
1. Simulate high water by covering sensor partially
2. Get readings above 50 cm in Serial Monitor
3. Open dashboard and verify:
   - [ ] Yellow warning appears (≥50 cm)
   - [ ] Map marker turns orange
   - [ ] Status metric shows 🟠 WARNING

4. Cover sensor more to get ≥70 cm
5. Verify:
   - [ ] Red danger alert appears
   - [ ] Map marker turns red
   - [ ] Status metric shows 🔴 DANGER

**Acceptance Criteria:**
- Alerts trigger at correct thresholds
- Color coding matches levels
- No false positives

---

### Test 4: Multiple Sensors ✓

**Procedure:**
1. Set up 2nd ESP32 with different location:
   ```cpp
   const char* sensorId = "ESP32_Sensor_02";
   const float latitude = 8.7500;
   const float longitude = 127.3900;
   ```
2. Upload firmware to 2nd board
3. Both should send data simultaneously

**Acceptance Criteria:**
- Dashboard shows both sensors
- Map shows 2 markers at different locations
- Statistics show "Active Sensors: 2"
- Distribution chart shows both sensors

---

## Part 6: Troubleshooting Reference

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| No Serial output | USB not connected | Check USB cable, try different port |
| Garbage text | Wrong baud rate | Set to 115200 in Serial Monitor |
| Wi-Fi fails | Wrong credentials | Update SSID/password in firmware |
| Can't reach server | Wrong IP address | Run `ipconfig` to find your PC IP |
| Sensor reads 0 cm | No power to sensor | Check VCC connection |
| Inconsistent readings | Wire loose | Resolder connections, use breadboard |
| API timeout | Firewall blocking | Allow port 5000 in Windows Firewall |
| Data in DB but not dashboard | Cached data | Clear browser cache, `st.rerun()` |

---

## Part 7: Production Checklist

Before deploying as final project:

- [ ] All 5 testing phases passed
- [ ] 1+ hour reliability test successful
- [ ] Multiple sensors working together
- [ ] Alert system triggers correctly
- [ ] Dashboard displays all data
- [ ] CSV export contains correct data
- [ ] QGIS GeoJSON export works
- [ ] No errors in Serial Monitor after 1 hour
- [ ] Wi-Fi reconnects automatically if disconnected
- [ ] Database backup created

---

## Next Steps

After successful hardware testing:

1. **Optimize Thresholds:** Adjust ALERT_THRESHOLD and DANGER_THRESHOLD based on your flood risk
2. **Deploy Dashboard:** Move to public network for remote monitoring
3. **Add Notifications:** Implement email/SMS alerts for high water
4. **Expand Coverage:** Add more sensors at different locations
5. **Archive Data:** Set up automated database backups

---

**Your complete IoT flood monitoring system is production-ready! 🌊**
