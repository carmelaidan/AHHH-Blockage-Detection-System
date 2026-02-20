# 🌊 Automated Hydro-Hazard Helper
**A Local Flood-Monitoring System for Grade 12 Research**

## 📋 Project Overview
The **Automated Hydro-Hazard Helper** is an IoT-based system designed to monitor water levels in real-time using ultrasonic sensing. It provides a localized solution for flood detection, storing data in a PostgreSQL database with PostGIS support and visualizing it through a live web dashboard with interactive mapping.

## 🛠️ Tech Stack
* **Hardware:** ESP32 + HC-SR04 Ultrasonic Sensor
* **Firmware:** Arduino C++ with WiFi & HTTP support
* **Backend:** Python Flask (REST API)
* **Database:** PostgreSQL (with PostGIS for spatial analysis)
* **Frontend:** Python Streamlit with Plotly & Folium maps
* **Spatial Export:** GeoJSON for QGIS integration
* **Version Control:** Git & GitHub

## 🏗️ System Architecture
1. **Hardware:** ESP32 with HC-SR04 sensor measures water distance and sends it to Flask API via Wi-Fi
2. **API (Backend):** Flask server receives data and saves it to PostgreSQL with geospatial coordinates
3. **Database:** PostGIS-enabled PostgreSQL stores historical data with timestamps and locations
4. **Dashboard:** Streamlit displays real-time metrics, trend charts, alerts, and interactive maps
5. **QGIS Export:** GeoJSON endpoint for spatial analysis and mapping

## 🚀 Quick Start

### Prerequisites
* PostgreSQL (with PostGIS extension)
* Python 3.8+
* Arduino IDE (for ESP32 firmware upload)
* ESP32 Dev Board + HC-SR04 Sensor (for real hardware)

### Backend Installation
```bash
# Clone repository
git clone <your-repo-url>
cd Hydro-Hazard-Helper

# Install Python dependencies
pip install -r requirements.txt

# Create .env file with your database password
echo "DB_PASSWORD=1546985" > .env
```

### Running the System (Simulator Mode - No Hardware Needed)

**Terminal 1 - Initialize Database:**
```bash
python setup_db.py
```

**Terminal 2 - Start Flask API:**
```bash
python app.py
```

**Terminal 3 - Run Dashboard:**
```bash
streamlit run dashboard.py
```

**Terminal 4 - Simulate Sensor Data:**
```bash
# Run once to send test data
python sim_esp32.py

# Or run 5 times to simulate 5 readings
for ($i=1; $i -le 5; $i++) { python sim_esp32.py; Start-Sleep -Seconds 2 }
```

### With Real Hardware

See **[HARDWARE_TESTING_GUIDE.md](./HARDWARE_TESTING_GUIDE.md)** for:
- ✅ Complete wiring diagram
- ✅ ESP32 firmware upload instructions
- ✅ 5-phase testing procedure
- ✅ Troubleshooting guide
- ✅ Production deployment checklist

### Simulator vs Real Hardware

See **[SIMULATOR_VS_HARDWARE.md](./SIMULATOR_VS_HARDWARE.md)** to understand:
- ✅ Why simulator validates your entire backend
- ✅ What happens when you switch to real hardware
- ✅ Confidence levels at each phase
- ✅ Code compatibility between simulator and real data

## 📊 Dashboard Features

### Real-Time Metrics
* Latest water level, average, peak, and minimum readings
* Visual alerts color-coded by status (Normal/Warning/Danger)
* Automatic threshold triggers

### Interactive Map
* OpenStreetMap-based visualization of sensor locations
* Color-coded markers:
  - 🟢 **Green:** Normal (< 50 cm)
  - 🟠 **Orange:** Warning (50-70 cm)
  - 🔴 **Red:** Danger (≥ 70 cm)
* Clickable popups with sensor details and readings
* Circle markers scaled by water level magnitude
* Real-time location tracking for multiple sensors

### Visualizations
* **Trend Charts:** Interactive water level timeline with alert thresholds
* **Distribution Charts:** Average water levels per sensor
* **Statistics:** Total readings, duration, and active sensor count

### Data Management
* CSV export for offline analysis
* GeoJSON export for QGIS spatial analysis
* Real-time data table with all sensor readings
* Manual refresh button for live updates

## 🗺️ QGIS Integration
Export sensor data as GeoJSON:
```bash
python qgis_export.py
```
Then open the generated `water_levels.geojson` in QGIS to visualize sensor locations on a detailed map.

## ⚠️ Alert Thresholds
- 🟢 **Normal:** < 50 cm
- 🟠 **Warning:** 50-70 cm
- 🔴 **Danger:** ≥ 70 cm

Adjust these in `dashboard.py` lines 16-17.

## 📁 Project Structure
```
Hydro-Hazard-Helper/
├── app.py                           # Flask API server
├── dashboard.py                     # Streamlit dashboard with maps
├── db_utils.py                     # Database utilities
├── config.py                       # Configuration & secrets
├── sim_esp32.py                    # Sensor simulator (demo)
├── qgis_export.py                  # QGIS export utility
├── setup_db.py                     # Database initialization
├── esp32_firmware.ino              # Arduino firmware for ESP32
├── requirements.txt                # Python dependencies
├── .env                            # Database credentials (git-ignored)
├── README.md                       # This file
├── HARDWARE_TESTING_GUIDE.md       # Complete hardware setup guide
├── SIMULATOR_VS_HARDWARE.md        # Why simulator validates backend
└── ESP32_SETUP_GUIDE.md           # Detailed ESP32 instructions
```

## 🔐 Security Notes
* **Never commit `.env` to GitHub** - it contains passwords
* Use environment variables for all sensitive data
* Change default PostgreSQL password in production
* Update Wi-Fi credentials in ESP32 firmware before uploading
* Restrict API access in production environment

## 📝 License
This is a Grade 12 Research project. Use responsibly.