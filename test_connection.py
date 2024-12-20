import psycopg2

DATABASE_CONFIG = {
    "host": "aqueduct.c78eqesmgw14.us-east-2.rds.amazonaws.com",
    "dbname": "postgres",
    "user": "aqueduct_admin",
    "password": "StrongPassword123!"
}

try:
    conn = psycopg2.connect(**DATABASE_CONFIG)
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
