import os
from dotenv import load_dotenv

load_dotenv() # This clever line loads the variables from .env

DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"), # This is the secure way!
    "host": "127.0.0.1",
    "port": "5432"
}