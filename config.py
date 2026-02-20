import os
from dotenv import load_dotenv

# Load the database password from the hidden .env file
load_dotenv()

DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "host": "127.0.0.1",
    "port": "5432"
}

# The URL where our Flask API is listening
# Make sure there are no spaces in the variable name 'API_URL'
API_URL = "http://127.0.0.1:5000/api/water-level"