import os
import secrets
import sys
from pathlib import Path
from flask_bcrypt import Bcrypt
from flask import Flask

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from config import get_database_connection, close_database_connection

def seed_admin():
    # Setup bcrypt without a full app if possible, but easier to just mock an app
    app = Flask(__name__)
    bcrypt = Bcrypt(app)
    
    first_name = "Admin"
    last_name = "User"
    email = os.getenv("SEED_ADMIN_EMAIL", "admin@sfa.com")
    matricule = os.getenv("SEED_ADMIN_MATRICULE", "SFA-0001")
    # Use the configured password, or generate a strong one and show it once.
    password = os.getenv("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(16)
    role = "administrator"
    
    print(f"Seeding admin user: {email} / {matricule}")
    
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM app_auth.users WHERE email = %s OR matricule = %s", (email, matricule))
        if cursor.fetchone():
            print("Admin user already exists!")
            return

        cursor.execute(
            """INSERT INTO app_auth.users (first_name, last_name, email, role, matricule, password_hash, status) 
               VALUES (%s, %s, %s, %s, %s, %s, 'active')""",
            (first_name, last_name, email, role, matricule, password_hash)
        )
        conn.commit()
        print(f"Successfully created administrator account!")
        print(f"Matricule: {matricule}")
        print(f"Password: {password}")
        
    except Exception as e:
        print(f"Error seeding admin: {e}")
        conn.rollback()
    finally:
        cursor.close()
        close_database_connection(conn)

if __name__ == "__main__":
    seed_admin()
