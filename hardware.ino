/**
 * A.H.H.H. SYSTEM - Arduino UNO R4 Firmware
 * A02YYUW Ultrasonic Sensor + SIM7600 GSM/GPS Module
 * Water Level Detection with Hysteresis & Alert Management
 */

#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <RTClib.h>

// Sensor Configuration
const int GSM_RX = 2;     // RX from SIM7600
const int GSM_TX = 3;     // TX to SIM7600
const int LED_PIN = 13;   // Status LED

// I2C Device Addresses
const uint8_t INA219_ADDR = 0x40;  // Default INA219 I2C address
const uint8_t RTC_ADDR = 0x68;     // DS3231 I2C address

// Thresholds (inches) & Hysteresis
const float FLOOD_THRESHOLD = 4.7;    // Trigger alert
const float NORMAL_THRESHOLD = 4.2;   // Reset alert
const float INCH_TO_CM = 2.54;

// State Management
enum WaterState { NORMAL, FLOODED };
WaterState currentState = NORMAL;

// Alert Timing
const unsigned long MEASUREMENT_INTERVAL = 10000;    // 10 seconds between readings
const unsigned long ALERT_REPEAT_INTERVAL = 300000;  // 5 minutes between alerts
unsigned long lastMeasurementTime = 0;
unsigned long lastAlertTime = 0;

// Server & Location
const char* serverUrl = "http://192.168.x.x:5000/api/water-level";
const char* sensorId = "AHHH_Arduino_01";
const float latitude = 8.7465;   // Update with basin location
const float longitude = 127.3851;

SoftwareSerial gsmSerial(GSM_RX, GSM_TX);
Adafruit_INA219 ina219(INA219_ADDR);
RTC_DS3231 rtc;

/**
 * Send AT command and wait for response (OK/ERROR/TIMEOUT)
 * This replaces blind delay() calls - prevents dropped packets when network is slow
 * 
 * Returns: true if OK received, false if ERROR or timeout
 */
bool sendATCommand(const char* command, unsigned long timeoutMs = 2000) {
    gsmSerial.println(command);
    
    unsigned long startTime = millis();
    String response = "";
    
    // Wait for response within timeout
    while (millis() - startTime < timeoutMs) {
        if (gsmSerial.available()) {
            char c = gsmSerial.read();
            response += c;
            
            // Check for OK or ERROR
            if (response.indexOf("OK") > -1) {
                Serial.printf("✅ AT OK: %s\n", command);
                return true;
            }
            if (response.indexOf("ERROR") > -1) {
                Serial.printf("❌ AT ERROR: %s\n", command);
                return false;
            }
        }
    }
    
    // Timeout - waited too long for response (network lag)
    Serial.printf("⏱️ AT TIMEOUT (%lums): %s\n", timeoutMs, command);
    return false;
}

// Read A02YYUW ultrasonic sensor via UART (Serial1)
float readWaterLevel() {
    if (Serial1.available() >= 4) {
        byte data[4];
        if (Serial1.read() == 0xFF) {
            data[0] = 0xFF;
            for (int i = 1; i < 4; i++) {
                data[i] = Serial1.read();
            }
            // Checksum validation
            if ((data[0] + data[1] + data[2]) & 0xFF == data[3]) {
                float distance = ((data[1] << 8) | data[2]) / 1000.0;  // mm to inches
                return distance > 0 && distance < 500 ? distance : -1;
            }
        }
    }
    return -1;
}

// Read power consumption from INA219 sensor
float readPowerConsumption() {
    if (!ina219.begin()) {
        Serial.println("INA219 not found!");
        return -1.0;
    }
    float busVoltage = ina219.getBusVoltage_V();
    float current_mA = ina219.getCurrent_mA();
    return (busVoltage * current_mA) / 1000.0;  // Return watts
}

// Get ISO 8601 timestamp from DS3231 RTC
String getRTCTimestamp() {
    DateTime now = rtc.now();
    char buf[25];
    sprintf(buf, "%04d-%02d-%02dT%02d:%02d:%02d", 
            now.year(), now.month(), now.day(),
            now.hour(), now.minute(), now.second());
    return String(buf);
}

// Send HTTP POST via SIM7600 AT commands
bool sendDataViaSIM7600(float waterLevel) {
    float waterLevelCm = waterLevel * INCH_TO_CM;
    float powerWatts = readPowerConsumption();
    String timestamp = getRTCTimestamp();
    
    // Create JSON payload (512 bytes for extended fields)
    StaticJsonDocument<512> doc;
    doc["sensor_id"] = sensorId;
    doc["water_level_cm"] = waterLevelCm;
    doc["latitude"] = latitude;
    doc["longitude"] = longitude;
    doc["power_consumption_watts"] = powerWatts;
    doc["mcu_timestamp"] = timestamp;
    
    String payload;
    serializeJson(doc, payload);
    
    // Set URL parameter - wait for each step to complete before proceeding
    String urlCmd = "AT+HTTPPARA=\"URL\",\"" + String(serverUrl) + "\"";
    if (!sendATCommand(urlCmd.c_str(), 2000)) {
        Serial.println("Failed to set URL");
        return false;
    }
    
    // Set content type header
    if (!sendATCommand("AT+HTTPPARA=\"CONTENT\",\"application/json\"", 2000)) {
        Serial.println("Failed to set content type");
        return false;
    }
    
    // Prepare HTTP data - tell SIM7600 payload size and timeout
    String dataCmd = "AT+HTTPDATA=" + String(payload.length()) + ",10000";
    if (!sendATCommand(dataCmd.c_str(), 2000)) {
        Serial.println("Failed to set HTTP data size");
        return false;
    }
    
    // Send the actual JSON payload
    gsmSerial.print(payload);
    delay(100);
    
    // Execute POST request
    if (!sendATCommand("AT+HTTPACTION=1", 3000)) {
        Serial.println("Failed to execute HTTP POST");
        return false;
    }
    
    // Check response code
    return gsmSerialReadResponse();
}

bool gsmSerialReadResponse() {
    unsigned long timeout = millis() + 5000;
    while (millis() < timeout) {
        if (gsmSerial.available()) {
            String response = gsmSerial.readStringUntil('\n');
            if (response.indexOf("200") > -1 || response.indexOf("201") > -1) {
                digitalWrite(LED_PIN, HIGH);
                delay(100);
                digitalWrite(LED_PIN, LOW);
                return true;
            }
        }
    }
    return false;
}

void initI2C() {
    Serial.println("📡 Initializing I2C devices...");
    Wire.begin();
    
    // Initialize RTC
    if (!rtc.begin()) {
        Serial.println("❌ DS3231 RTC not found!");
    } else {
        if (rtc.lostPower()) {
            rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
        }
        Serial.println("✅ DS3231 RTC ready");
    }
    
    // Initialize INA219
    if (!ina219.begin()) {
        Serial.println("❌ INA219 not found!");
    } else {
        Serial.println("✅ INA219 power sensor ready");
    }
}

void initGSM() {
    Serial.println("📡 Initializing SIM7600...");
    
    // Disable echo for cleaner responses
    sendATCommand("ATE0", 1000);
    
    // Check if SIM card is present and readable
    sendATCommand("AT+CPIN?", 2000);
    
    // Check network registration status
    sendATCommand("AT+CREG?", 2000);
    
    Serial.println("✅ GSM initialized");
}

void setup() {
    Serial.begin(115200);
    Serial1.begin(9600);
    gsmSerial.begin(115200);
    
    pinMode(LED_PIN, OUTPUT);
    
    Serial.println("\n===== A.H.H.H. SYSTEM - ARDUINO UNO R4 =====");
    Serial.println("Blockage Detection with Power Monitoring");
    Serial.println("Flood Threshold: 4.7 inches | Normal: 4.2 inches");
    
    initI2C();
    initGSM();
}

void loop() {
    if (millis() - lastMeasurementTime >= MEASUREMENT_INTERVAL) {
        lastMeasurementTime = millis();
        
        float levelInches = readWaterLevel();
        if (levelInches < 0) {
            Serial.println("❌ Sensor read failed");
            return;
        }
        
        float levelCm = levelInches * INCH_TO_CM;
        float powerW = readPowerConsumption();
        Serial.printf("📊 Water: %.2f cm | Power: %.2f W\n", levelCm, powerW);
        
        // State Machine with Hysteresis
        if (currentState == NORMAL && levelInches >= FLOOD_THRESHOLD) {
            currentState = FLOODED;
            lastAlertTime = millis();
            Serial.println("🚨 BLOCKAGE DETECTED!");
            sendDataViaSIM7600(levelInches);
            
        } else if (currentState == FLOODED) {
            // Send repeating alerts every 5 minutes while flooded
            if (millis() - lastAlertTime >= ALERT_REPEAT_INTERVAL) {
                lastAlertTime = millis();
                Serial.println("🔔 Repeat alert...");
                sendDataViaSIM7600(levelInches);
            }
            
            // Clear state when water drops below normal threshold
            if (levelInches <= NORMAL_THRESHOLD) {
                currentState = NORMAL;
                Serial.println("✅ Blockage cleared");
                sendDataViaSIM7600(levelInches);
            }
        }
    }
}
