from app.queries.chatQueries import create_chat, get_chat
from app.queries.messageQueries import add_message, get_messages_by_chat

# Crear chat
chat_id = create_chat("user_123")
print("Nuevo chat:", chat_id)

# Obtener chat
chat = get_chat(chat_id)
print("Chat:", chat)

# Agregar mensajes
msg1 = add_message(chat_id, "user", "Hola asistente")
msg2 = add_message(chat_id, "assistant", "Hola usuario, ¿cómo estás?")
print("Mensajes agregados:", msg1, msg2)

# Consultar mensajes
messages = get_messages_by_chat(chat_id)
print("Mensajes:", messages)
