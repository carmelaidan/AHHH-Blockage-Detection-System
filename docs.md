# 🌊 Hydro-Hazard Helper - Complete Documentation

## Project Overview
IoT-based flood monitoring system using ESP32, HC-SR04 sensor, Flask API, PostgreSQL, and Streamlit dashboard with QGIS integration.

## System Architecture
```
ESP32 Sensor → Flask Backend → PostgreSQL Database → Streamlit Frontend
  (hardware.ino)  (backend.py)   (database.py)    (frontend.py)
```

## Quick Start

### 1. Initialize Database (First Time Only)
```powershell
python database.py
```

### 2. Start Backend API (Terminal 1)
```powershell
python backend.py
```

### 3. Start Frontend Dashboard (Terminal 2)
```powershell
streamlit run frontend.py
```

### 4. Test with Simulator (Terminal 3)
```powershell
python simulator.py
# Run 5-10 times to generate test data
```

## 5 Core Files

| File | Purpose |
|------|---------|
| **backend.py** | Flask REST API + PostgreSQL database operations |
| **frontend.py** | Streamlit web dashboard with maps & charts |
| **database.py** | Database initialization script |
| **hardware.ino** | ESP32 firmware for HC-SR04 sensor |
| **docs.md** | Complete documentation (this file) |

## Supporting Files

- **simulator.py** - Test data generator
- **config.py** - Configuration & API URL
- **.env** - Database credentials
- **README.md** - Quick reference
- **requirements.txt** - Python dependencies
- **.gitignore** - Git configuration

## Features

✅ Real-time water level monitoring
✅ Interactive map with sensor locations
✅ Trend charts and statistics
✅ Color-coded alerts (Normal/Warning/Danger)
✅ CSV & GeoJSON export
✅ QGIS integration

## Alert Thresholds
- 🟢 Normal: < 50 cm
- 🟠 Warning: 50-70 cm
- 🔴 Danger: ≥ 70 cm

## Hardware Setup

### Components
- ESP32 Development Board
- HC-SR04 Ultrasonic Sensor
- 4x Jumper Wires
- 1kΩ + 2kΩ Resistors (voltage divider)

### Wiring
```
HC-SR04 VCC → ESP32 5V
HC-SR04 GND → ESP32 GND
HC-SR04 TRIG → ESP32 GPIO5
HC-SR04 ECHO → ESP32 GPIO18 (via voltage divider)
```

### Firmware Upload
1. Open hardware.ino in Arduino IDE
2. Update WiFi credentials and server IP
3. Select "ESP32 Dev Module" board
4. Click Upload

## Testing Phases

**Phase 1:** Database
```powershell
python database.py
```

**Phase 2:** Backend
```powershell
python backend.py
```

**Phase 3:** Frontend
```powershell
streamlit run frontend.py
```

**Phase 4:** Simulator
```powershell
python simulator.py
```

**Phase 5:** Verification
- Open http://localhost:8501
- Should see real-time metrics, map, and charts

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to backend" | Run `python backend.py` in Terminal 1 |
| No data showing | Run `python simulator.py` multiple times |
| Database error | Run `python database.py` to reinitialize |
| Import error | Run `pip install -r requirements.txt` |

## For Your Thesis

**Files to Present:**
1. **backend.py** - Flask API and database
2. **frontend.py** - Dashboard visualization
3. **hardware.ino** - ESP32 sensor code
4. **docs.md** - Documentation

**Files Not Required:**
- simulator.py, config.py, requirements.txt (supporting only)

---

Your professional IoT flood monitoring system is ready! 🌊
