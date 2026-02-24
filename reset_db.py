"""
Reset Database - Completely clear water_levels table for fresh hardware test
Run once: python reset_db.py
"""

import psycopg2
from config import DB_PARAMS

try:
    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE water_levels RESTART IDENTITY;")
            conn.commit()
    print("✅ Database reset! water_levels table is now empty and ready for real hardware data.")
except Exception as e:
    print(f"❌ Error: {e}")
