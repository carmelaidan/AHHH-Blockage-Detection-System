# ESP32 Firmware Installation Guide

## 🛠️ Hardware Requirements
- **ESP32 Development Board** (e.g., NodeMCU-32S, DOIT DevKit v1)
- **HC-SR04 Ultrasonic Sensor** (water level detector)
- **USB Cable** (USB-A to Micro-USB)
- **Jumper Wires**
- **5V Power Supply** (for the sensor)

## 📋 Pin Connections

### HC-SR04 Sensor to ESP32
| HC-SR04 Pin | ESP32 Pin | Description |
|-------------|-----------|-------------|
| VCC | 5V | Power supply |
| GND | GND | Ground |
| TRIG | GPIO5 (D5) | Trigger signal |
| ECHO | GPIO18 (D18) | Echo receive |

### Wiring Diagram
```
HC-SR04              ESP32
├─ VCC ──────────→ 5V
├─ GND ──────────→ GND
├─ TRIG ─────────→ GPIO5
└─ ECHO ─────────→ GPIO18 (with 1kΩ + 2kΩ voltage divider for 5V→3.3V)
```

**⚠️ Important:** The ESP32 GPIO accepts 3.3V max. Use a voltage divider for the ECHO pin:
- 1kΩ resistor from ECHO to GPIO18
- 2kΩ resistor from GPIO18 to GND

## 📥 Software Installation

### Step 1: Install Arduino IDE
1. Download from https://www.arduino.cc/en/software
2. Install and launch the IDE

### Step 2: Add ESP32 Board Support
1. Go to **File → Preferences**
2. In "Additional Boards Manager URLs", paste:
   ```
   https://dl.espressif.com/dl/package_esp32_index.json
   ```
3. Click **Tools → Board Manager**
4. Search for "ESP32" and install **ESP32 by Espressif Systems**

### Step 3: Install Required Libraries
1. Go to **Sketch → Include Library → Manage Libraries**
2. Search and install:
   - **WiFi** (built-in, no install needed)
   - **HTTPClient** (built-in, no install needed)
   - **ArduinoJson** by Benoit Blanchon (search and install)

### Step 4: Configure Firmware
Open `esp32_firmware.ino` and update these values:

```cpp
const char* ssid = "YOUR_WIFI_SSID";           // Your Wi-Fi network name
const char* password = "YOUR_WIFI_PASSWORD";   // Your Wi-Fi password
const char* serverUrl = "http://192.168.x.x:5000/api/water-level";  // Your PC's IP
const char* sensorId = "ESP32_Sensor_01";      // Unique sensor name
const float latitude = 8.7465;                 // Your location latitude
const float longitude = 127.3851;              // Your location longitude
```

**To find your PC's IP address:**
- **Windows:** Open Command Prompt and type `ipconfig` (look for "IPv4 Address")
- **Mac/Linux:** Open Terminal and type `ifconfig` (look for "inet")

### Step 5: Select Board and Port
1. Go to **Tools → Board** and select **ESP32 Dev Module**
2. Go to **Tools → Port** and select your USB port (e.g., COM3, /dev/ttyUSB0)
3. Set **Tools → Upload Speed** to **115200**

### Step 6: Upload Firmware
1. Click the **Upload** button (→ arrow icon)
2. Wait for "Uploading..." message
3. When complete, you'll see "Done uploading"

### Step 7: Monitor Serial Output
1. Go to **Tools → Serial Monitor**
2. Set baud rate to **115200**
3. You should see:
   ```
   ===== HYDRO-HAZARD HELPER - ESP32 FIRMWARE =====
   Initializing system...
   📡 Connecting to Wi-Fi...
   ✅ Connected to Wi-Fi!
   IP Address: 192.168.1.100
   RSSI: -55 dBm
   ✅ Setup complete! Ready to measure water levels.
   ```

## ✅ Testing the System

### Test 1: Verify Sensor Reading
1. Dip the HC-SR04 sensor into water
2. Check the Serial Monitor for distance readings
3. Values should change as you move the sensor

### Test 2: Verify Data Transmission
1. Ensure Flask API is running (`python app.py`)
2. Check Serial Monitor for "✅ Data successfully sent to server!"
3. Open the dashboard (Streamlit) to see new readings

### Test 3: Troubleshooting

**Problem:** Serial Monitor shows "❌ Failed to connect to Wi-Fi"
- **Solution:** Check Wi-Fi SSID and password in the firmware
- Ensure the router is 2.4GHz (ESP32 doesn't support 5GHz)

**Problem:** "Server error: HTTP 0" in Serial Monitor
- **Solution:** Verify the server URL is correct (use your PC's IP address)
- Ensure Flask API is running on port 5000
- Check firewall settings allow port 5000

**Problem:** Water level readings are unstable
- **Solution:** Add a small delay between readings
- Ensure HC-SR04 has stable power supply
- Check sensor isn't exposed to ultrasonic interference

## 📊 Data Flow
```
ESP32 Sensor
    ↓ (Reads every 10 seconds)
Flask API (http://192.168.x.x:5000)
    ↓ (HTTP POST)
PostgreSQL Database
    ↓ (Stores with timestamp & location)
Streamlit Dashboard
    ↓ (Fetches and displays)
Your Browser
```

## 🔧 Advanced Configuration

### Change Measurement Interval
Edit this line in the firmware:
```cpp
const unsigned long MEASUREMENT_INTERVAL = 10000;  // milliseconds
```
- 5000 = every 5 seconds
- 30000 = every 30 seconds
- 60000 = every 1 minute

### Adjust Sensor Sensitivity
The sensor automatically rejects measurements outside 2-400 cm. To change:
```cpp
if (distance < 2 || distance > 400) {  // Modify these values
    return -1;
}
```

### Change LED Pin
If you want to use a different LED:
```cpp
const int LED_PIN = 2;  // Change to your desired GPIO
```

## 📚 Additional Resources
- [ESP32 Pinout](https://randomnweb.com/esp32-pinout/)
- [HC-SR04 Datasheet](https://cdn.sparkfun.com/assets/b/e/4/b/e/25642-HC-SR04_ultrasonic_sensor.pdf)
- [Arduino JSON Library Docs](https://arduinojson.org/)

---

**Happy monitoring! 🌊**
