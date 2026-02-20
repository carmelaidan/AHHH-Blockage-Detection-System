import psycopg2
from config import DB_PARAMS

try:
    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            # Update all records to have coordinates
            cur.execute("""
                UPDATE water_levels 
                SET latitude = 8.7465, longitude = 127.3851
                WHERE latitude IS NULL OR longitude IS NULL;
            """)
            conn.commit()
            print(f"✅ Updated {cur.rowcount} records with coordinates!")
            
except Exception as e:
    print(f"❌ Error: {e}")
