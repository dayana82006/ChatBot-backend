from app.database.database import get_connection

def create_chat(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chats (user_id) VALUES (%s)", (user_id,))
    conn.commit()
    chat_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return chat_id

def get_chat(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chats WHERE id = %s", (chat_id,))
    chat = cursor.fetchone()
    cursor.close()
    conn.close()
    return chat
