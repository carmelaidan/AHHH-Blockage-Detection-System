import psycopg2
from config import DB_PARAMS

try:
    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            # Check total records
            cur.execute("SELECT COUNT(*) FROM water_levels;")
            total = cur.fetchone()[0]
            print(f"📊 Total records in database: {total}")
            
            # Check records with coordinates
            cur.execute("""
                SELECT COUNT(*) FROM water_levels 
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
            """)
            with_coords = cur.fetchone()[0]
            print(f"📍 Records with latitude/longitude: {with_coords}")
            
            # Show last 5 records
            print("\n📋 Last 5 records:")
            cur.execute("""
                SELECT id, sensor_id, water_level_cm, latitude, longitude, recorded_at
                FROM water_levels 
                ORDER BY recorded_at DESC 
                LIMIT 5;
            """)
            for row in cur.fetchall():
                print(f"  ID: {row[0]}, Sensor: {row[1]}, Level: {row[2]}, Lat: {row[3]}, Lon: {row[4]}, Time: {row[5]}")
            
except Exception as e:
    print(f"❌ Error: {e}")
