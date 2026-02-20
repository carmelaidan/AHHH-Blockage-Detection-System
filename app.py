from flask import Flask, request, jsonify
import psycopg2
import json
from config import DB_PARAMS
from db_utils import export_to_geojson

app = Flask(__name__)

@app.route('/api/water-level', methods=['POST'])
def receive_data():
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
            return jsonify({"error": "No geospatial data available. Ensure sensors have latitude/longitude."}), 404
    except Exception as e:
        return jsonify({"error": f"GeoJSON export error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)