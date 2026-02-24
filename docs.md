# 🌊 A.H.H.H. Blockage Detection System - Complete Documentation

## Project Overview
IoT-based storm drain blockage detection using Arduino UNO R4, SIM7600 GSM/GPS module, A02YYUW ultrasonic sensor, Flask API, PostgreSQL, and Streamlit dashboard with QGIS integration.

## System Architecture
```
Arduino UNO R4 + SIM7600 → Flask Backend → PostgreSQL Database → Streamlit Frontend
      (hardware.ino)        (backend.py)     [initialized]      (frontend.py)
```
Database automatically initializes when backend.py starts.

## Quick Start

Database initializes automatically when backend starts - no manual setup needed!

### 1. Start Backend API (Terminal 1)
```powershell
python backend.py
```

### 2. Start Frontend Dashboard (Terminal 2)
```powershell
streamlit run frontend.py
```

### 3. Test with Simulator (Terminal 3)
```powershell
python simulator.py
# Run 5-10 times to generate test data
```

## 4 Core Files

| File | Purpose |
|------|----------|
| **backend.py** | Flask REST API + PostgreSQL database operations (includes auto-init) |
| **frontend.py** | Streamlit web dashboard with maps & charts |
| **hardware.ino** | Arduino UNO R4 firmware for SIM7600 + A02YYUW sensor |
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
- Arduino UNO R4 WiFi Board
- SIM7600 GSM/GPS Module (Serial1)
- A02YYUW Ultrasonic Sensor (UART, Serial1 shared via demux)
- INA219 DC Current/Power Sensor (I2C: SDA=A4, SCL=A5)
- DS3231 Real-Time Clock (I2C: SDA=A4, SCL=A5)
- 4x Jumper Wires + I2C Pull-up Resistors (4.7kΩ)

### Pin Configuration
```
SIM7600:  RX→Pin2 (GSM_RX), TX→Pin3 (GSM_TX)
A02YYUW:  UART output → Serial1
INA219:   SDA→A4, SCL→A5 (I2C Address 0x40)
DS3231:   SDA→A4, SCL→A5 (I2C Address 0x68)
LED:      Pin13 for status indication
```

### Firmware Upload
1. Open hardware.ino in Arduino IDE
2. Update server IP and sensor location coordinates
3. Select "Arduino UNO R4 WiFi" board
4. Click Upload

## Testing Phases

**Phase 1:** Backend (Database auto-initializes)
```powershell
python backend.py
```

**Phase 2:** Frontend
```powershell
streamlit run frontend.py
```

**Phase 3:** Simulator
```powershell
python simulator.py
```

**Phase 4:** Verification
- Open http://localhost:8501
- Should see real-time metrics, map, and charts

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to backend" | Run `python backend.py` in Terminal 1 |
| No data showing | Run `python simulator.py` multiple times |
| Database error | Restart `python backend.py` to reinitialize |
| Import error | Run `pip install -r requirements.txt` |

## For Your Thesis

**Files to Present:**
1. **backend.py** - Flask API and PostgreSQL integration
2. **frontend.py** - A.H.H.H. Dashboard visualization
3. **hardware.ino** - Arduino UNO R4 sensor & SIM7600 code
4. **docs.md** - Complete documentation

**Files Not Required:**
- simulator.py, config.py, requirements.txt (supporting only)

---

Your professional IoT flood monitoring system is ready! 🌊
