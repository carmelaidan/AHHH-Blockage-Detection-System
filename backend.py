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

def execute_query(sql, params=None, fetch=False):
    """Execute a database query and optionally fetch results."""
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
    """Initialize the water_levels table with geospatial support."""
    sql_postgis = "CREATE EXTENSION IF NOT EXISTS postgis;"
    execute_query(sql_postgis)
    
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
    """
    
    sql_indexes = """
    CREATE INDEX IF NOT EXISTS idx_location ON water_levels USING GIST(location);
    CREATE INDEX IF NOT EXISTS idx_recorded_at ON water_levels(recorded_at DESC);
    """
    
    execute_query(sql_create)
    execute_query(sql_alter)
    execute_query(sql_indexes)
    
    print("✅ PostGIS extension enabled!")
    print("✅ Table 'water_levels' with geospatial support is ready!")

def export_to_geojson(limit=100):
    """Export water level data as GeoJSON for QGIS."""
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

@app.route('/api/water-level', methods=['POST'])
def receive_data():
    """Receive water level data from ESP32 sensor."""
    try:
        data = request.get_json()
        sensor_id = data.get('sensor_id')
        water_level = data.get('water_level_cm')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not sensor_id or water_level is None:
            return jsonify({"error": "Missing sensor_id or water_level_cm"}), 400

        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                if latitude and longitude:
                    cur.execute("""
                        INSERT INTO water_levels 
                        (sensor_id, water_level_cm, latitude, longitude, location) 
                        VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326));
                    """, (sensor_id, water_level, latitude, longitude, longitude, latitude))
                else:
                    cur.execute("""
                        INSERT INTO water_levels (sensor_id, water_level_cm) 
                        VALUES (%s, %s);
                    """, (sensor_id, water_level))
                conn.commit()
        
        return jsonify({"status": "success", "message": "Data saved!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/water-level', methods=['GET'])
def get_data():
    """Get latest 10 water level readings."""
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, sensor_id, water_level_cm, latitude, longitude, recorded_at 
                    FROM water_levels ORDER BY recorded_at DESC LIMIT 10;
                """)
                rows = cur.fetchall()
        
        results = [{
            "id": row[0],
            "sensor_id": row[1],
            "water_level_cm": float(row[2]),
            "latitude": float(row[3]) if row[3] else None,
            "longitude": float(row[4]) if row[4] else None,
            "recorded_at": row[5].strftime("%Y-%m-%d %H:%M:%S")
        } for row in rows]
        
        return jsonify({"status": "success", "data": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/geojson', methods=['GET'])
def export_geojson():
    """Export sensor data as GeoJSON for QGIS."""
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
