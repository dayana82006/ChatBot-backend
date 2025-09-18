from app.database.database import get_connection

def add_message(chat_id: int, role: str, text: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (chat_id, role, text) VALUES (%s, %s, %s)",
        (chat_id, role, text)
    )
    conn.commit()
    message_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return message_id

def get_messages_by_chat(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM messages WHERE chat_id = %s", (chat_id,))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages
