"""
BACKEND - Flask REST API + Database Operations
Receives sensor data, stores in PostgreSQL, exports as GeoJSON
"""

from flask import Flask, request, jsonify
import psycopg2
import json
from config import DB_PARAMS

app = Flask(__name__)

# ============= DATABASE OPERATIONS =============
# All the SQL stuff happens here - inserting data, pulling it back out, etc.

def execute_query(sql, params=None, fetch=False):
    """Run any SQL query - useful to keep this centralized so we don't repeat code"""  
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                if fetch:
                    return cur.fetchall()
                conn.commit()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def init_db():
    """Set up the database tables and PostGIS for map stuff - run this once at startup"""
    # First, enable PostGIS extension for geospatial queries (maps, coordinates, etc)
    sql_postgis = "CREATE EXTENSION IF NOT EXISTS postgis;"
    execute_query(sql_postgis)
    
    # Create the main table - stores every sensor reading with location coordinates
    # location column uses PostGIS POINT to store lat/lon as a single geometry for faster queries
    sql_create = """
    CREATE TABLE IF NOT EXISTS water_levels (
        id SERIAL PRIMARY KEY,
        sensor_id VARCHAR(50) NOT NULL,
        water_level_cm NUMERIC(5, 2) NOT NULL,
        latitude NUMERIC(10, 6),
        longitude NUMERIC(10, 6),
        location GEOMETRY(POINT, 4326),
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    sql_alter = """
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS latitude NUMERIC(10, 6);
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS longitude NUMERIC(10, 6);
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS location GEOMETRY(POINT, 4326);
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS power_consumption_watts FLOAT;
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS is_simulated BOOLEAN DEFAULT FALSE;
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS alert_status BOOLEAN DEFAULT FALSE;
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS alert_type VARCHAR(50);
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS capacity_percentage NUMERIC(5, 2);
    """
    
    # Indexes speed up searches - one for location-based queries, one for time-based sorting
    sql_indexes = """
    CREATE INDEX IF NOT EXISTS idx_location ON water_levels USING GIST(location);
    CREATE INDEX IF NOT EXISTS idx_recorded_at ON water_levels(recorded_at DESC);
    """
    
    # Run all the setup commands
    execute_query(sql_create)
    execute_query(sql_alter)
    execute_query(sql_indexes)
    
    print("✅ PostGIS extension enabled!")
    print("✅ Table 'water_levels' with geospatial support is ready!")

def export_to_geojson(limit=100):
    """Convert sensor data to GeoJSON format - useful for QGIS and mapping tools"""
    # Using PostgreSQL's json_build_object to structure the data as proper GeoJSON
    # This returns coordinates and properties in the format QGIS expects
    sql = f"""
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', COALESCE(json_agg(
            json_build_object(
                'type', 'Feature',
                'geometry', json_build_object(
                    'type', 'Point',
                    'coordinates', ARRAY[longitude, latitude]
                ),
                'properties', json_build_object(
                    'id', id,
                    'sensor_id', sensor_id,
                    'water_level_cm', water_level_cm,
                    'recorded_at', TO_CHAR(recorded_at, 'YYYY-MM-DD HH24:MI:SS')
                )
            ) ORDER BY recorded_at DESC
        ), '[]'::json)
    ) FROM water_levels 
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL 
    LIMIT {limit};
    """
    try:
        result = execute_query(sql, fetch=True)
        if result and len(result) > 0 and result[0][0]:
            return result[0][0]
        return None
    except Exception as e:
        print(f"❌ GeoJSON export error: {e}")
        return None

# ============= API ENDPOINTS =============
# These are the web endpoints that sensors and the frontend talk to

@app.route('/api/water-level', methods=['POST'])
def receive_data():
    """Accept incoming sensor data per BAMBI.pdf spec and store in database"""
    try:
        data = request.get_json()
        sensor_id = data.get('sensor_id')
        water_level = data.get('water_level_cm')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        power_consumption = data.get('power_consumption_watts', 0.0)
        mcu_timestamp = data.get('mcu_timestamp')
        is_simulated = data.get('is_simulated', False)
        alert_status = data.get('alert_status', False)
        alert_type = data.get('alert_type', 'normal_reading')
        
        if not sensor_id or water_level is None:
            return jsonify({"error": "Missing sensor_id or water_level_cm"}), 400
        
        # Calculate capacity percentage (47.5cm basin height per BAMBI.pdf)
        BASIN_HEIGHT_CM = 47.5
        capacity_pct = (water_level / BASIN_HEIGHT_CM) * 100
        
        # Validate alert type
        valid_alert_types = ['normal_reading', 'blockage_detected', 'blockage_cleared']
        if alert_type not in valid_alert_types:
            alert_type = 'normal_reading'

        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                if latitude and longitude:
                    cur.execute("""
                        INSERT INTO water_levels 
                        (sensor_id, water_level_cm, latitude, longitude, location, power_consumption_watts, 
                         is_simulated, alert_status, alert_type, capacity_percentage, recorded_at) 
                        VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, %s, %s, %s);
                    """, (sensor_id, water_level, latitude, longitude, longitude, latitude, 
                          power_consumption, is_simulated, alert_status, alert_type, capacity_pct, mcu_timestamp))
                else:
                    cur.execute("""
                        INSERT INTO water_levels (sensor_id, water_level_cm, power_consumption_watts, is_simulated, alert_status, alert_type, capacity_percentage, recorded_at) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """, (sensor_id, water_level, power_consumption, is_simulated, alert_status, alert_type, capacity_pct, mcu_timestamp))
                conn.commit()
        
        if alert_status:
            print(f"🚨 ALERT LOGGED: {sensor_id} | Type: {alert_type} | Level: {water_level}cm ({capacity_pct:.1f}%)")
        
        return jsonify({"status": "success", "message": "Data saved!", "capacity_percentage": capacity_pct}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/water-level', methods=['GET'])
def get_data():
    """Fetch sensor readings for dashboard with alert tracking per BAMBI.pdf spec
    
    Query parameters:
    - limit: Number of recent readings (default: 100, max: 1000)
    - source: 'real' (hardware), 'simulated' (simulator), 'all' (default)
    - alerts_only: 'true' to show only alerting readings
    """
    try:
        limit = request.args.get('limit', default=100, type=int)
        limit = max(10, min(limit, 1000))
        source = request.args.get('source', default='all').lower()
        alerts_only = request.args.get('alerts_only', default='false').lower() == 'true'
        
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                if alerts_only:
                    cur.execute("""
                        SELECT id, sensor_id, water_level_cm, latitude, longitude, power_consumption_watts, 
                               alert_status, alert_type, capacity_percentage, recorded_at
                        FROM water_levels WHERE alert_status = TRUE 
                        ORDER BY recorded_at DESC LIMIT %s;
                    """, (limit,))
                elif source == 'real':
                    cur.execute("""
                        SELECT id, sensor_id, water_level_cm, latitude, longitude, power_consumption_watts, 
                               alert_status, alert_type, capacity_percentage, recorded_at 
                        FROM water_levels WHERE is_simulated = FALSE 
                        ORDER BY recorded_at DESC LIMIT %s;
                    """, (limit,))
                elif source == 'simulated':
                    cur.execute("""
                        SELECT id, sensor_id, water_level_cm, latitude, longitude, power_consumption_watts, 
                               alert_status, alert_type, capacity_percentage, recorded_at 
                        FROM water_levels WHERE is_simulated = TRUE 
                        ORDER BY recorded_at DESC LIMIT %s;
                    """, (limit,))
                else:
                    cur.execute("""
                        SELECT id, sensor_id, water_level_cm, latitude, longitude, power_consumption_watts, 
                               alert_status, alert_type, capacity_percentage, recorded_at 
                        FROM water_levels ORDER BY recorded_at DESC LIMIT %s;
                    """, (limit,))
                rows = cur.fetchall()
        
        results = [{
            "id": row[0],
            "sensor_id": row[1],
            "water_level_cm": float(row[2]),
            "latitude": float(row[3]) if row[3] else None,
            "longitude": float(row[4]) if row[4] else None,
            "power_consumption_watts": float(row[5]) if row[5] else 0.0,
            "alert_status": row[6] if row[6] is not None else False,
            "alert_type": row[7] if row[7] else "normal_reading",
            "capacity_percentage": float(row[8]) if row[8] else 0.0,
            "recorded_at": row[9].strftime("%Y-%m-%d %H:%M:%S")
        } for row in rows]
        
        return jsonify({"status": "success", "data": results, "count": len(results)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/geojson', methods=['GET'])
def export_geojson():
    """Let users download all sensor data in GeoJSON format"""
    try:
        geojson_data = export_to_geojson(limit=100)
        if geojson_data:
            return jsonify(geojson_data), 200
        else:
            return jsonify({"error": "No geospatial data available."}), 404
    except Exception as e:
        return jsonify({"error": f"Export error: {str(e)}"}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
