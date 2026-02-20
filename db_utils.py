import psycopg2
from config import DB_PARAMS

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

def enable_postgis():
    """Enable PostGIS extension for geospatial queries."""
    sql = "CREATE EXTENSION IF NOT EXISTS postgis;"
    if execute_query(sql):
        print("✅ PostGIS extension enabled!")

def init_db():
    """Initialize the water_levels table with geospatial support."""
    enable_postgis()
    
    # Create table if it doesn't exist
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
    
    # Add missing columns if they don't exist
    sql_alter = """
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS latitude NUMERIC(10, 6);
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS longitude NUMERIC(10, 6);
    ALTER TABLE water_levels ADD COLUMN IF NOT EXISTS location GEOMETRY(POINT, 4326);
    """
    
    # Create indexes
    sql_indexes = """
    CREATE INDEX IF NOT EXISTS idx_location ON water_levels USING GIST(location);
    CREATE INDEX IF NOT EXISTS idx_recorded_at ON water_levels(recorded_at DESC);
    """
    
    execute_query(sql_create)
    execute_query(sql_alter)
    execute_query(sql_indexes)
    
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
            geojson_data = result[0][0]
            return geojson_data
        return None
    except Exception as e:
        print(f"❌ GeoJSON export error: {e}")
        return None
