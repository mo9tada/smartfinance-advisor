from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import get_database_connection, close_database_connection

bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

def get_db():
    return get_database_connection()

@bp.route("/", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, message, type, is_read, created_at FROM app_auth.notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 50",
            (user_id,)
        )
        rows = cursor.fetchall()
        notifications = []
        for r in rows:
            notifications.append({
                "id": r[0],
                "message": r[1],
                "type": r[2],
                "is_read": r[3],
                "created_at": r[4].isoformat() if r[4] else None
            })
        return jsonify(notifications), 200
    finally:
        cursor.close()
        close_database_connection(conn)

@bp.route("/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(notification_id):
    user_id = get_jwt_identity()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE app_auth.notifications SET is_read = TRUE WHERE id = %s AND user_id = %s",
            (notification_id, user_id)
        )
        conn.commit()
        return jsonify(msg="Notification marked as read"), 200
    finally:
        cursor.close()
        close_database_connection(conn)
