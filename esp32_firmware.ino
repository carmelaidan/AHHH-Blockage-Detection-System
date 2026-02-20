#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ===== WIFI CONFIGURATION =====
const char* ssid = "YOUR_WIFI_SSID";           // Change to your Wi-Fi network name
const char* password = "YOUR_WIFI_PASSWORD";   // Change to your Wi-Fi password

// ===== SENSOR CONFIGURATION =====
const int TRIG_PIN = 5;    // GPIO5 (D5) - HC-SR04 Trigger Pin
const int ECHO_PIN = 18;   // GPIO18 (D18) - HC-SR04 Echo Pin
const int LED_PIN = 2;     // GPIO2 (D2) - Built-in LED for status

// ===== SERVER CONFIGURATION =====
const char* serverUrl = "http://192.168.x.x:5000/api/water-level";  // Change IP to your PC
const char* sensorId = "ESP32_Sensor_01";     // Unique sensor identifier
const float latitude = 8.7465;                 // Your location latitude
const float longitude = 127.3851;              // Your location longitude

// ===== TIMING CONFIGURATION =====
const unsigned long MEASUREMENT_INTERVAL = 10000;  // Take reading every 10 seconds
const unsigned long WIFI_TIMEOUT = 20000;          // Wi-Fi connection timeout
unsigned long lastMeasurementTime = 0;

// ===== FUNCTION PROTOTYPES =====
float measureWaterLevel();
void sendDataToServer(float waterLevel);
void connectToWiFi();
void blinkLED(int count, int delayMs);

void setup() {
    // Initialize serial communication for debugging
    Serial.begin(115200);
    delay(2000);  // Wait for serial monitor to connect
    
    Serial.println("\n\n===== HYDRO-HAZARD HELPER - ESP32 FIRMWARE =====");
    Serial.println("Initializing system...");
    
    // Configure pins
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    pinMode(LED_PIN, OUTPUT);
    
    // Blink LED 3 times to indicate startup
    blinkLED(3, 200);
    
    // Connect to Wi-Fi
    connectToWiFi();
    
    Serial.println("✅ Setup complete! Ready to measure water levels.");
}

void loop() {
    // Check if it's time to take a measurement
    if (millis() - lastMeasurementTime >= MEASUREMENT_INTERVAL) {
        lastMeasurementTime = millis();
        
        // Measure water level
        float waterLevel = measureWaterLevel();
        
        if (waterLevel >= 0) {  // Valid measurement
            Serial.printf("\n📊 Water Level: %.2f cm\n", waterLevel);
            
            // Blink once to indicate measurement
            digitalWrite(LED_PIN, HIGH);
            delay(100);
            digitalWrite(LED_PIN, LOW);
            
            // Send data to server
            sendDataToServer(waterLevel);
        } else {
            Serial.println("❌ Failed to read sensor. Retrying...");
        }
    }
    
    // Check Wi-Fi connection every 10 seconds
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ Wi-Fi disconnected! Reconnecting...");
        connectToWiFi();
    }
    
    delay(100);  // Small delay to prevent watchdog timeout
}

/**
 * Measure water level using HC-SR04 ultrasonic sensor.
 * Returns distance in centimeters, or -1 if measurement failed.
 */
float measureWaterLevel() {
    // Trigger the sensor
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    
    // Measure the echo time
    unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // Timeout after 30ms
    
    // Calculate distance: speed of sound is ~343 m/s = 0.0343 cm/µs
    // Distance = (time in µs × 0.0343) / 2
    if (duration == 0) {
        return -1;  // No echo received, measurement failed
    }
    
    float distance = (duration * 0.0343) / 2;
    
    // HC-SR04 typical range: 2-400 cm. Reject outliers.
    if (distance < 2 || distance > 400) {
        return -1;
    }
    
    return distance;
}

/**
 * Send water level data to Flask API via HTTP POST.
 */
void sendDataToServer(float waterLevel) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("❌ Wi-Fi not connected. Cannot send data.");
        return;
    }
    
    HTTPClient http;
    
    // Construct the URL
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");
    
    // Create JSON payload
    DynamicJsonDocument doc(256);
    doc["sensor_id"] = sensorId;
    doc["water_level_cm"] = waterLevel;
    doc["latitude"] = latitude;
    doc["longitude"] = longitude;
    
    // Serialize JSON to string
    String jsonPayload;
    serializeJson(doc, jsonPayload);
    
    Serial.print("📤 Sending: ");
    Serial.println(jsonPayload);
    
    // Send POST request
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode == 201) {
        Serial.println("✅ Data successfully sent to server!");
        blinkLED(2, 150);
    } else {
        Serial.printf("⚠️ Server error: HTTP %d\n", httpResponseCode);
        Serial.println("Response: " + http.getString());
    }
    
    http.end();
}

/**
 * Connect ESP32 to Wi-Fi network.
 */
void connectToWiFi() {
    Serial.println("\n📡 Connecting to Wi-Fi...");
    Serial.printf("SSID: %s\n", ssid);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    unsigned long startTime = millis();
    
    // Wait for connection with timeout
    while (WiFi.status() != WL_CONNECTED && millis() - startTime < WIFI_TIMEOUT) {
        delay(500);
        Serial.print(".");
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✅ Connected to Wi-Fi!");
        Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
        blinkLED(3, 100);
    } else {
        Serial.println("\n❌ Failed to connect to Wi-Fi. Check credentials and try again.");
        blinkLED(5, 200);
    }
}

/**
 * Utility function to blink LED for status indication.
 */
void blinkLED(int count, int delayMs) {
    for (int i = 0; i < count; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(delayMs);
        digitalWrite(LED_PIN, LOW);
        delay(delayMs);
    }
}
