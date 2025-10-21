# app/services/sessionManager.py
from app.services.redisServices import sync_user_session

async def initialize_user_session(user_id: str, channel: str = "web"):
    """
    Inicializa sesión del usuario verificando Redis y MySQL.
    Devuelve el diccionario con la sesión completa.
    """
    session_data = await sync_user_session(user_id, channel)
    return session_data
