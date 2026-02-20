"""
DATABASE - PostgreSQL Setup with PostGIS
Run this once to initialize the database table
"""

from backend import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
