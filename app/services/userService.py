import logging
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

def create_or_update_user(
    conn,
    user_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    channel: str = "web",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Crea un usuario si no existe o actualiza sus datos si ya existe.
    """
    try:
        cursor = conn.cursor(dictionary=True)

        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()

        metadata_json = json.dumps(metadata) if metadata else None

        if existing:
            # Actualizar datos si ya existe
            cursor.execute("""
                UPDATE users
                SET name = COALESCE(%s, name),
                    email = COALESCE(%s, email),
                    phone = COALESCE(%s, phone),
                    channel = COALESCE(%s, channel),
                    metadata = COALESCE(%s, metadata)
                WHERE user_id = %s
            """, (name, email, phone, channel, metadata_json, user_id))
            logger.info(f"🔄 Usuario actualizado: {user_id}")
        else:
            # Crear nuevo usuario
            cursor.execute("""
                INSERT INTO users (user_id, name, email, phone, channel, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, name, email, phone, channel, metadata_json))
            logger.info(f"🆕 Usuario creado: {user_id}")

        conn.commit()
        cursor.close()
    except Exception as e:
        logger.exception(f"💥 Error en create_or_update_user: {e}")
