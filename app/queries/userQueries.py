# app/queries/userQueries.py
from app.database.database import get_connection
from typing import Optional, Dict, Any

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def create_user(user_id: str, name: str = None, channel: str = "web") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "INSERT INTO users (user_id, name, channel) VALUES (%s, %s, %s)",
            (user_id, name, channel)
        )
        conn.commit()
        return {"user_id": user_id, "name": name, "channel": channel}
    finally:
        cursor.close()
        conn.close()
