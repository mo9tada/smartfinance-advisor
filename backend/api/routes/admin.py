from flask import Blueprint, request, jsonify, current_app
import string
import random
from flask_mail import Message
from config import get_database_connection, close_database_connection
from api.decorators import admin_required
from app_init import bcrypt, mail

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

def get_db():
    return get_database_connection()

@bp.route("/users/pending", methods=["GET"])
@admin_required()
def get_pending():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, first_name, last_name, email, phone, role, created_at FROM app_auth.users WHERE status = 'pending'")
        rows = cursor.fetchall()
        users = []
        for r in rows:
            users.append({
                "id": r[0], "first_name": r[1], "last_name": r[2], "email": r[3],
                "phone": r[4], "role": r[5], "created_at": r[6]
            })
        return jsonify(users), 200
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/users/accept/<int:user_id>", methods=["POST"])
@admin_required()
def accept_user(user_id):
    matricule = f"SFA-{user_id:04d}"
    temp_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    pw_hash = bcrypt.generate_password_hash(temp_pw).decode('utf-8')

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT email FROM app_auth.users WHERE id = %s", (user_id,))
        res = cursor.fetchone()
        if not res:
            return jsonify(msg="User not found"), 404
        email = res[0]

        cursor.execute(
            "UPDATE app_auth.users SET matricule = %s, password_hash = %s, status = 'active' WHERE id = %s",
            (matricule, pw_hash, user_id)
        )

        # Send email
        if not current_app.config.get("MAIL_USERNAME") or not current_app.config.get("MAIL_PASSWORD"):
            raise RuntimeError("SMTP credentials are missing. Configure MAIL_USERNAME and MAIL_PASSWORD in .env.")

        msg = Message("Account Approved - Smart Finance Advisor", recipients=[email])
        msg.body = f"Your account has been approved.\nMatricule: {matricule}\nTemporary Password: {temp_pw}\nPlease login and change your password."
        mail.send(msg)

        conn.commit()

        return jsonify(msg="User accepted and credentials sent by email"), 200
    except Exception as e:
        conn.rollback()
        return jsonify(msg=f"Could not send credentials email: {str(e)}"), 500
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/users/reject/<int:user_id>", methods=["POST"])
@admin_required()
def reject_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE app_auth.users SET status = 'deleted' WHERE id = %s", (user_id,))
        conn.commit()
        return jsonify(msg="User rejected"), 200
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/users/active", methods=["GET"])
@admin_required()
def get_active():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, first_name, last_name, email, phone, role, matricule, created_at, last_login FROM app_auth.users WHERE status = 'active'")
        rows = cursor.fetchall()
        users = []
        for r in rows:
            users.append({
                "id": r[0], "full_name": f"{r[1]} {r[2]}", "email": r[3], "phone": r[4],
                "role": r[5], "matricule": r[6], "created_at": r[7], "last_login": r[8]
            })
        return jsonify(users), 200
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required()
def update_user(user_id):
    data = request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    phone = data.get("phone")
    role = data.get("role")

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE app_auth.users SET first_name=%s, last_name=%s, email=%s, phone=%s, role=%s WHERE id=%s",
            (first_name, last_name, email, phone, role, user_id)
        )
        conn.commit()
        return jsonify(msg="User updated successfully"), 200
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required()
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE app_auth.users SET status = 'deleted' WHERE id = %s", (user_id,))
        conn.commit()
        return jsonify(msg="User account deleted"), 200
    finally:
        cursor.close()
        close_database_connection(conn)
