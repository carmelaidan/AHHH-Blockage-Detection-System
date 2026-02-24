import os
from dotenv import load_dotenv

# Load database credentials from .env (keep passwords out of version control!)
load_dotenv()

DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "host": "127.0.0.1",
    "port": "5432"
}

# Flask API endpoint - sensors and frontend talk to this
API_URL = "http://127.0.0.1:5000/api/water-level"