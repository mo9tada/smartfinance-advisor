from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Message
import datetime
import random
import string
from config import get_database_connection, close_database_connection
from app_init import bcrypt, mail  # Assuming we initialize these in a common file

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def get_db():
    return get_database_connection()

@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    phone = data.get("phone")
    role = data.get("role", "viewer")

    if not all([first_name, last_name, email]):
        return jsonify(msg="Missing required fields"), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM app_auth.users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify(msg="Email already exists"), 400

        cursor.execute(
            "INSERT INTO app_auth.users (first_name, last_name, email, phone, role, status) VALUES (%s, %s, %s, %s, %s, 'pending')",
            (first_name, last_name, email, phone, role)
        )
        conn.commit()
        return jsonify(msg="Registration submitted, awaiting admin approval"), 201
    except Exception as e:
        return jsonify(msg=str(e)), 500
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    matricule = data.get("matricule")
    password = data.get("password")

    if not all([matricule, password]):
        return jsonify(msg="Missing matricule or password"), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, password_hash, role, first_name, last_name, status FROM app_auth.users WHERE matricule = %s", (matricule,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify(msg="Invalid credentials"), 401
        
        user_id, pw_hash, role, first_name, last_name, status = user

        if status != "active":
            return jsonify(msg=f"Account is {status}"), 403

        if bcrypt.check_password_hash(pw_hash, password):
            access_token = create_access_token(identity=str(user_id), additional_claims={
                "role": role,
                "matricule": matricule,
                "full_name": f"{first_name} {last_name}"
            })
            cursor.execute("UPDATE app_auth.users SET last_login = NOW() WHERE id = %s", (user_id,))
            conn.commit()
            return jsonify(access_token=access_token, user={
                "id": user_id,
                "full_name": f"{first_name} {last_name}",
                "role": role,
                "matricule": matricule
            }), 200
        else:
            return jsonify(msg="Invalid credentials"), 401
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify(msg="Email is required"), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM app_auth.users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            # Prevent user enumeration? Or just return success.
            return jsonify(msg="Verification code sent if email exists"), 200

        code = ''.join(random.choices(string.digits, k=6))
        expires = datetime.datetime.now() + datetime.timedelta(minutes=10)
        
        cursor.execute(
            "UPDATE app_auth.users SET reset_code = %s, reset_code_expires_at = %s WHERE email = %s",
            (code, expires, email)
        )

        # Send email
        if not current_app.config.get("MAIL_USERNAME") or not current_app.config.get("MAIL_PASSWORD"):
            raise RuntimeError("SMTP credentials are missing. Configure MAIL_USERNAME and MAIL_PASSWORD in .env.")

        msg = Message("Password Reset Code", recipients=[email])
        msg.body = f"Your verification code is: {code}. It expires in 10 minutes."
        mail.send(msg)

        conn.commit()

        return jsonify(msg="Verification code sent to your email"), 200
    except Exception as e:
        conn.rollback()
        return jsonify(msg=f"Could not send reset code email: {str(e)}"), 500
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/verify-reset-code", methods=["POST"])
def verify_code():
    data = request.get_json()
    email = data.get("email")
    code = data.get("code")

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM app_auth.users WHERE email = %s AND reset_code = %s AND reset_code_expires_at > NOW()",
            (email, code)
        )
        if cursor.fetchone():
            return jsonify(valid=True), 200
        else:
            return jsonify(valid=False, msg="Invalid or expired code"), 400
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    code = data.get("code")
    new_password = data.get("new_password")

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM app_auth.users WHERE email = %s AND reset_code = %s AND reset_code_expires_at > NOW()",
            (email, code)
        )
        if not cursor.fetchone():
            return jsonify(msg="Invalid or expired code"), 400

        pw_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        cursor.execute(
            "UPDATE app_auth.users SET password_hash = %s, reset_code = NULL, reset_code_expires_at = NULL WHERE email = %s",
            (pw_hash, email)
        )
        conn.commit()
        return jsonify(msg="Password updated successfully"), 200
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, first_name, last_name, role, matricule, email FROM app_auth.users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            uid, fname, lname, role, matricule, email = user
            return jsonify(user={
                "id": uid,
                "full_name": f"{fname} {lname}",
                "role": role,
                "matricule": matricule,
                "email": email
            }), 200
        return jsonify(msg="User not found"), 404
    finally:
        cursor.close()
        close_database_connection(conn)
