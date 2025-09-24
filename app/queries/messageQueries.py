from git import Optional
from app.database.database import get_connection
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def add_message(chat_id: int, role: str, text: str) -> int:
    """Añade un mensaje al chat y retorna su ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (chat_id, role, text) VALUES (%s, %s, %s)",
            (chat_id, role, text)
        )
        message_id = cursor.lastrowid
        
        # Actualizar timestamp del chat
        cursor.execute(
            "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (chat_id,)
        )
        
        logger.debug(f"Mensaje añadido: chat_id={chat_id}, role={role}, message_id={message_id}")
        return message_id
    finally:
        cursor.close()
        conn.close()

def get_messages_by_chat(chat_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene los mensajes de un chat"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM messages WHERE chat_id = %s ORDER BY timestamp ASC"
        params = [chat_id]
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
            
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_recent_messages_by_user(user_id: str, channel: str = "web", limit: int = 10) -> List[Dict[str, Any]]:
    """Obtiene los mensajes recientes de un usuario"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT m.* FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE c.user_id = %s AND c.channel = %s
        ORDER BY m.timestamp DESC
        LIMIT %s
        """
        cursor.execute(query, (user_id, channel, limit))
        messages = cursor.fetchall()
        return list(reversed(messages))  # Devolver en orden cronológico
    finally:
        cursor.close()
        conn.close()