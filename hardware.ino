/**
 * AHHH SYSTEM - Arduino UNO R4 Firmware
 * A02YYUW Ultrasonic Sensor + SIM7600 GSM/GPS Module
 * Water Level Detection with Hysteresis & Alert Management
 */

#include <ArduinoJson.h>

// Sensor Configuration
const int GSM_RX = 2;     // RX from SIM7600
const int GSM_TX = 3;     // TX to SIM7600
const int LED_PIN = 13;   // Status LED

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

// Send HTTP POST via SIM7600 AT commands
bool sendDataViaSIM7600(float waterLevel) {
    float waterLevelCm = waterLevel * INCH_TO_CM;
    
    // Create JSON payload
    StaticJsonDocument<256> doc;
    doc["sensor_id"] = sensorId;
    doc["water_level_cm"] = waterLevelCm;
    doc["latitude"] = latitude;
    doc["longitude"] = longitude;
    
    String payload;
    serializeJson(doc, payload);
    
    // AT command for HTTP POST
    gsmSerial.print("AT+HTTPPARA=\"URL\",\"");
    gsmSerial.print(serverUrl);
    gsmSerial.println("\"");
    delay(500);
    
    gsmSerial.print("AT+HTTPPARA=\"CONTENT\",\"application/json\"");
    gsmSerial.println();
    delay(500);
    
    gsmSerial.print("AT+HTTPDATA=");
    gsmSerial.print(payload.length());
    gsmSerial.println(",10000");
    delay(500);
    
    gsmSerial.print(payload);
    gsmSerial.println();
    delay(1000);
    
    gsmSerial.println("AT+HTTPACTION=1");  // POST
    delay(2000);
    
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

void initGSM() {
    Serial.println("📡 Initializing SIM7600...");
    gsmSerial.println("ATE0");  // Disable echo
    delay(1000);
    gsmSerial.println("AT+CPIN?");  // Check SIM
    delay(1000);
    gsmSerial.println("AT+CREG?");  // Check registration
    delay(2000);
    Serial.println("✅ GSM initialized");
}

void setup() {
    Serial.begin(115200);
    Serial1.begin(9600);
    gsmSerial.begin(115200);
    
    pinMode(LED_PIN, OUTPUT);
    
    Serial.println("\n===== AHHH SYSTEM - ARDUINO UNO R4 =====");
    Serial.println("Water Level Detection with Hysteresis");
    Serial.println("Flood Threshold: 4.7 inches");
    Serial.println("Normal Threshold: 4.2 inches");
    
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
        Serial.printf("📊 Water Level: %.2f inches (%.2f cm)\n", levelInches, levelCm);
        
        // State Machine with Hysteresis
        if (currentState == NORMAL && levelInches >= FLOOD_THRESHOLD) {
            currentState = FLOODED;
            lastAlertTime = millis();
            Serial.println("🚨 FLOOD DETECTED! Sending alert...");
            sendDataViaSIM7600(levelInches);
            
        } else if (currentState == FLOODED) {
            // Send repeating alerts every 5 minutes while flooded
            if (millis() - lastAlertTime >= ALERT_REPEAT_INTERVAL) {
                lastAlertTime = millis();
                Serial.println("🔔 Sending repeat alert (5-minute interval)...");
                sendDataViaSIM7600(levelInches);
            }
            
            // Clear state when water drops below normal threshold
            if (levelInches <= NORMAL_THRESHOLD) {
                currentState = NORMAL;
                Serial.println("✅ Flood cleared! Sending regularization alert...");
                sendDataViaSIM7600(levelInches);
            }
        } else {
            // Normal state - no alert needed
            Serial.println("✅ Normal water level");
        }
    }
    
    delay(100);
}
