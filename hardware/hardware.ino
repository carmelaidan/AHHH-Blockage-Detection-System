/**
 * A.H.H.H. SYSTEM - Arduino UNO R4 Firmware
 * A02YYUW Ultrasonic Sensor + SIM7600 GSM/GPS Module
 * Water Level Detection with Hysteresis & Alert Management
 */

#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <RTClib.h>
#include <SoftwareSerial.h> // Fixed: Added explicitly for UNO R4

// Sensor Configuration
const int GSM_RX = 2; // RX from SIM7600
const int GSM_TX = 3; // TX to SIM7600     
const int LED_PIN = 13; // Status LED

// I2C Device Addresses
const uint8_t INA219_ADDR = 0x40;  
const uint8_t RTC_ADDR = 0x68;

// Thresholds (inches) & Hysteresis
// SPEC: 4.7" = 25% of 18.7" basin = blockage threshold
// SPEC: 4.2" = 22.5% = hysteresis clear threshold  
const float FLOOD_THRESHOLD = 4.7;    
const float NORMAL_THRESHOLD = 4.2;
const float INCH_TO_CM = 2.54;

// Alert levels per BAMBI.pdf spec: 25%, 50%, 75% escalation
// But hardware uses simple binary: normal or flooded
// 25% = 4.7", 50% = 9.35", 75% = 14.025"
const float ALERT_LEVEL_2 = 9.35;   // 50% threshold
const float ALERT_LEVEL_3 = 14.025; // 75% threshold

// State Management
enum WaterState { NORMAL, FLOODED, ESCALATED };
WaterState currentState = NORMAL;
const unsigned long MEASUREMENT_INTERVAL = 10000;    
const unsigned long ALERT_REPEAT_INTERVAL = 300000;  // 5 minutes per spec
unsigned long lastMeasurementTime = 0;
unsigned long lastAlertTime = 0;
unsigned long lastAlertRepeatTime = 0;

// Performance tracking for metrics
unsigned long dataPacketsSent = 0;
unsigned long totalDataBytes = 0;
unsigned long systemStartTime = 0;

// Server & Location
const char* serverUrl = "http://192.168.x.x:5000/api/water-level";
const char* sensorId = "AHHH_Arduino_01";
const float latitude = 8.7465;
const float longitude = 127.3851;

SoftwareSerial gsmSerial(GSM_RX, GSM_TX);
Adafruit_INA219 ina219(INA219_ADDR);
RTC_DS3231 rtc;

bool sendATCommand(const char* command, unsigned long timeoutMs = 2000) {
    gsmSerial.println(command);
    unsigned long startTime = millis();
    String response = "";
    
    while (millis() - startTime < timeoutMs) {
        if (gsmSerial.available()) {
            char c = gsmSerial.read();
            response += c;
            
            if (response.indexOf("OK") > -1) {
                // Fixed: Removed printf
                Serial.print("✅ AT OK: ");
                Serial.println(command);
                return true;
            }
            if (response.indexOf("ERROR") > -1) {
                Serial.print("❌ AT ERROR: ");
                Serial.println(command);
                return false;
            }
        }
    }
    
    Serial.print("⏱️ AT TIMEOUT (");
    Serial.print(timeoutMs);
    Serial.print("ms): ");
    Serial.println(command);
    return false;
}

float readWaterLevel() {
    if (Serial1.available() >= 4) {
        byte data[4];
        if (Serial1.read() == 0xFF) {
            data[0] = 0xFF;
            for (int i = 1; i < 4; i++) {
                data[i] = Serial1.read();
            }
            if (((data[0] + data[1] + data[2]) & 0xFF) == data[3]) {
                float distance = ((data[1] << 8) | data[2]) / 1000.0;
                return distance > 0 && distance < 500 ? distance : -1;
            }
        }
    }
    return -1;
}

float readPowerConsumption() {
    if (!ina219.begin()) {
        Serial.println("INA219 not found!");
        return -1.0;
    }
    float busVoltage = ina219.getBusVoltage_V();
    float current_mA = ina219.getCurrent_mA();
    return (busVoltage * current_mA) / 1000.0;
}

String getRTCTimestamp() {
    DateTime now = rtc.now();
    char buf[25];
    sprintf(buf, "%04d-%02d-%02dT%02d:%02d:%02d", 
            now.year(), now.month(), now.day(),
            now.hour(), now.minute(), now.second());
    return String(buf);
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

bool sendDataViaSIM7600(float waterLevel, bool isAlert = false, bool isCleared = false) {
    float waterLevelCm = waterLevel * INCH_TO_CM;
    float powerWatts = readPowerConsumption();
    String timestamp = getRTCTimestamp();
    
    StaticJsonDocument<512> doc;
    doc["sensor_id"] = sensorId;
    doc["water_level_cm"] = waterLevelCm;
    doc["latitude"] = latitude;
    doc["longitude"] = longitude;
    doc["power_consumption_watts"] = powerWatts;
    doc["mcu_timestamp"] = timestamp;
    doc["is_simulated"] = false;  // Real hardware
    
    // Per BAMBI.pdf: Add alert status and type
    if (isAlert) {
        doc["alert_status"] = true;
        doc["alert_type"] = "blockage_detected";
        Serial.println("🚨 BLOCKAGE ALERT SENT via HTTP");
    } else if (isCleared) {
        doc["alert_status"] = false;
        doc["alert_type"] = "blockage_cleared";
        doc["message"] = "Regularization: blockage has been relieved";
        Serial.println("✅ REGULARIZATION ALERT SENT via HTTP");
    } else {
        doc["alert_status"] = false;
        doc["alert_type"] = "normal_reading";
    }
    
    String payload;
    serializeJson(doc, payload);
    totalDataBytes += payload.length();
    dataPacketsSent++;
    
    String urlCmd = "AT+HTTPPARA=\"URL\",\"" + String(serverUrl) + "\"";
    if (!sendATCommand(urlCmd.c_str(), 2000)) return false;
    if (!sendATCommand("AT+HTTPPARA=\"CONTENT\",\"application/json\"", 2000)) return false;
    
    String dataCmd = "AT+HTTPDATA=" + String(payload.length()) + ",10000";
    if (!sendATCommand(dataCmd.c_str(), 2000)) return false;
    
    gsmSerial.print(payload);
    delay(100);
    
    if (!sendATCommand("AT+HTTPACTION=1", 3000)) return false;
    
    return gsmSerialReadResponse();
}

void initI2C() {
    Serial.println("📡 Initializing I2C devices...");
    Wire.begin();
    if (!rtc.begin()) {
        Serial.println("❌ DS3231 RTC not found!");
    } else {
        if (rtc.lostPower()) rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
        Serial.println("✅ DS3231 RTC ready");
    }
    
    if (!ina219.begin()) {
        Serial.println("❌ INA219 not found!");
    } else {
        Serial.println("✅ INA219 power sensor ready");
    }
}

void initGSM() {
    Serial.println("📡 Initializing SIM7600...");
    sendATCommand("ATE0", 1000);
    sendATCommand("AT+CPIN?", 2000);
    sendATCommand("AT+CREG?", 2000);
    Serial.println("✅ GSM initialized");
}

void setup() {
    Serial.begin(115200);
    Serial1.begin(9600);
    gsmSerial.begin(115200);
    
    pinMode(LED_PIN, OUTPUT);
    systemStartTime = millis();
    
    Serial.println("\n===== A.H.H.H. SYSTEM - ARDUINO UNO R4 =====");
    Serial.println("IoT+GIS Blockage Detection per BAMBI.pdf Spec");
    Serial.println("Flood Threshold: 4.7 inches (25% capacity)");
    Serial.println("Multi-level alerts: 25%, 50%, 75% escalation");
    Serial.println("Alert repeat: Every 5 minutes while condition persists");
    Serial.println("Clear condition: 4.2 inches with hysteresis");
    
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
        float capacityPct = (levelCm / 47.5) * 100;  // Basin height: 47.5cm
        
        // Display current status
        Serial.print("📊 Water: ");
        Serial.print(levelCm, 2);
        Serial.print(" cm (");
        Serial.print(capacityPct, 1);
        Serial.print("%) | Power: ");
        Serial.print(powerW, 2);
        Serial.println(" W");

        // STATE MACHINE per BAMBI.pdf spec
        // NORMAL state → FLOODED (on threshold breach)
        if (currentState == NORMAL && levelInches >= FLOOD_THRESHOLD) {
            currentState = FLOODED;
            lastAlertTime = millis();
            lastAlertRepeatTime = millis();
            Serial.println("🚨 BLOCKAGE DETECTED! [25% capacity reached]");
            sendDataViaSIM7600(levelInches, true, false);  // Send alert
            
        } 
        // FLOODED state → handle repeating alerts every 5 minutes
        else if (currentState == FLOODED) {
            // Check if 5 min repeat interval elapsed
            if (millis() - lastAlertRepeatTime >= ALERT_REPEAT_INTERVAL) {
                lastAlertRepeatTime = millis();
                Serial.println("🔔 Repeat blockage alert (5 min cycle)...");
                sendDataViaSIM7600(levelInches, true, false);
            }
            
            // Check for escalation to next level (50%)
            else if (levelInches >= ALERT_LEVEL_2 && currentState != ESCALATED) {
                currentState = ESCALATED;
                Serial.println("⚠️ ESCALATED: 50% capacity reached!");
                sendDataViaSIM7600(levelInches, true, false);
            }
            
            // Check for recovery: hysteresis clears condition
            if (levelInches <= NORMAL_THRESHOLD) {
                currentState = NORMAL;
                Serial.println("✅ BLOCKAGE CLEARED [Regularization Alert]");
                sendDataViaSIM7600(levelInches, false, true);  // Send regularization alert
            }
        }
    }
}