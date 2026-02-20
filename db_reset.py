import psycopg2
from config import DB_PARAMS

try:
    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            # Drop the old table if it exists
            cur.execute("DROP TABLE IF EXISTS water_levels CASCADE;")
            conn.commit()
    print("✅ Old table dropped successfully!")
    
    # Now reinitialize
    from db_utils import init_db
    init_db()
    
except Exception as e:
    print(f"❌ Error: {e}")
