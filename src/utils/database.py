import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()


DB_CONFIG = {
    "host": os.getenv("SUPABASE_DB_HOST"),
    "port": os.getenv("SUPABASE_DB_PORT", "5432"),
    "database": os.getenv("SUPABASE_DB_NAME", "postgres"),
    "user": os.getenv("SUPABASE_DB_USER"),
    "password": os.getenv("SUPABASE_DB_PASSWORD"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)