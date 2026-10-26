# Helper script to run database migrations
import os
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from config import get_database_connection, close_database_connection, DB_HOST, DB_USER, DB_NAME, DB_PORT

def run_migration(sql_file):
    try:
        print(f"Connecting to {DB_NAME} on {DB_HOST}:{DB_PORT} as {DB_USER}...")
        conn = get_database_connection()
        cursor = conn.cursor()
        
        with open(sql_file, 'r') as f:
            sql = f.read()
            
        print(f"Executing migration from {sql_file}...")
        cursor.execute(sql)
        conn.commit()
        
        print("Migration successful!")
        cursor.close()
        close_database_connection(conn)
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <sql_file>")
        sys.exit(1)
        
    run_migration(sys.argv[1])
