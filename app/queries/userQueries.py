from app.database.database import get_connection
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_or_create_user(user_id: str, channel: str = "web") -> bool:
    """Crea un usuario si no existe en la base de datos"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()

        if not existing:
            cursor.execute(
                """
                INSERT INTO users (user_id, channel, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, channel, datetime.utcnow(), datetime.utcnow())
            )
            conn.commit()
            logger.info(f"🆕 Nuevo usuario creado: {user_id} ({channel})")
            return True  # Nuevo usuario creado

        return False  # Ya existía

    except Exception as e:
        logger.error(f"❌ Error en get_or_create_user: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
