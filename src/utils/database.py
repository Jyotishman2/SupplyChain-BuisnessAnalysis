import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "nexamart",
    "user": "postgres",
    "password": "123456789"
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)