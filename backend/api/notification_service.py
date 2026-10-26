from config import get_database_connection, close_database_connection
from flask_mail import Message
from app_init import mail
from flask import current_app

def create_notification(type_str, message):
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        # Get all active users
        cursor.execute("SELECT id, email FROM app_auth.users WHERE status = 'active'")
        users = cursor.fetchall()

        # Insert notification for each user and send email
        for user_id, email in users:
            cursor.execute(
                "INSERT INTO app_auth.notifications (user_id, message, type) VALUES (%s, %s, %s)",
                (user_id, message, type_str)
            )
            
            # Send Email
            try:
                if current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"):
                    msg = Message("SFA Notification - " + type_str.title(), recipients=[email])
                    msg.body = str(message)
                    mail.send(msg)
            except Exception as e:
                print(f"Failed to send email to {email}: {e}")

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Notification error: {e}")
    finally:
        cursor.close()
        close_database_connection(conn)
