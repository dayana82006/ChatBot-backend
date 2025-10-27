from app.database.database import get_connection
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def create_chat(user_id: str, channel: str = "web") -> int:
    """Crea un nuevo chat y retorna su ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO chats (user_id, channel) VALUES (%s, %s)", 
            (user_id, channel)
        )
        chat_id = cursor.lastrowid
        logger.info(f"Chat creado: ID={chat_id}, user_id={user_id}, channel={channel}")
        return chat_id
    finally:
        cursor.close()
        conn.close()

def get_chat_by_user(user_id: str, channel: str = "web") -> Optional[Dict[str, Any]]:
    """Obtiene el chat más reciente de un usuario"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM chats WHERE user_id = %s AND channel = %s ORDER BY updated_at DESC LIMIT 1", 
            (user_id, channel)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def get_chat(chat_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un chat por ID"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM chats WHERE id = %s", (chat_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def get_or_create_chat(
    user_id: str,
    channel: str = "web",
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> int:
    """
    Obtiene el chat existente o crea uno nuevo, y crea el usuario si no existe.
    Si se proveen datos opcionales (nombre, email, teléfono), se guardan o actualizan.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1️⃣ Verificar si el usuario existe
        cursor.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            # Crear usuario nuevo con la información disponible
            cursor.execute(
                """
                INSERT INTO users (user_id, name, email, phone, channel)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, name, email, phone, channel)
            )
            conn.commit()
            logger.info(f"🧍 Usuario creado automáticamente: {user_id}")
        else:
            # Si el usuario ya existe, actualizar sus datos si llegan nuevos
            updates = []
            params = {}
            if name:
                updates.append("name = %(name)s")
                params["name"] = name
            if email:
                updates.append("email = %(email)s")
                params["email"] = email
            if updates:
                params["user_id"] = user_id
                update_sql = f"UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = %(user_id)s"
                cursor.execute(update_sql, params)
                conn.commit()
                logger.info(f"🔄 Usuario actualizado: {user_id}")

        # 2️⃣ Buscar chat existente del usuario en ese canal
        cursor.execute(
            """
            SELECT id FROM chats 
            WHERE user_id = %s AND channel = %s 
            ORDER BY updated_at DESC LIMIT 1
            """,
            (user_id, channel)
        )
        chat = cursor.fetchone()

        if chat:
            logger.debug(f"💬 Chat existente encontrado: {chat['id']} para usuario {user_id}")
            return chat["id"]

        # 3️⃣ Crear nuevo chat
        cursor.execute(
            "INSERT INTO chats (user_id, channel) VALUES (%s, %s)",
            (user_id, channel)
        )
        conn.commit()
        chat_id = cursor.lastrowid
        logger.info(f"💬 Nuevo chat creado: chat_id={chat_id}, user_id={user_id}, channel={channel}")

        return chat_id

    except Exception as e:
        logger.error(f"❌ Error en get_or_create_chat: {e}")
        raise
    finally:
        cursor.close()
        conn.close()



def get_all_chats_with_summary(
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """Obtiene todos los chats con resumen para el panel admin"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        where_clauses = []
        params = {}

        if search:
            where_clauses.append("c.user_id LIKE %(search)s")
            params["search"] = f"%{search}%"
        if channel:
            where_clauses.append("c.channel = %(channel)s")
            params["channel"] = channel

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Query para los chats resumidos
        query = f"""
            SELECT 
                c.id,
                c.user_id,
                c.channel,
                c.created_at,
                c.updated_at,
                COUNT(m.id) as count,
                (
                    SELECT m2.text 
                    FROM messages m2 
                    WHERE m2.chat_id = c.id 
                    ORDER BY m2.timestamp DESC 
                    LIMIT 1
                ) as last_message
            FROM chats c
            LEFT JOIN messages m ON c.id = m.chat_id
            {where_sql}
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        params["limit"] = limit
        params["offset"] = (page - 1) * limit

        cursor.execute(query, params)
        items = cursor.fetchall()

        # Query para contar el total
        count_query = f"""
            SELECT COUNT(*) as total
            FROM chats c
            {where_sql}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]

        return {
            "items": items,
            "page": page,
            "total": total
        }

    finally:
        cursor.close()
        conn.close()