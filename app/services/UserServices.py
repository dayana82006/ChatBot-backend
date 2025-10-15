# app/services/userService.py
import logging
from app.services.redisServices import get_user_session, set_user_session
from app.database import db  # tu conexión a MySQL (usa tu librería o método)
logger = logging.getLogger(__name__)

async def get_or_create_user(user_id: str, name: str = None, phone: str = None, channel: str = "web"):
    """
    Busca el usuario en Redis, luego en MySQL, y lo crea si no existe.
    """
    # 1️⃣ Buscar en Redis
    session = await get_user_session(user_id)
    if session:
        logger.info(f"🟢 Sesión encontrada en Redis para {user_id}")
        return session

    # 2️⃣ Buscar en la base de datos
    user = await db.fetch_one("SELECT * FROM users WHERE user_id = :user_id", {"user_id": user_id})
    if user:
        logger.info(f"📦 Usuario existente en BD: {user_id}")
        await set_user_session(user_id, dict(user))
        return dict(user)

    # 3️⃣ Crear nuevo usuario
    logger.info(f"🆕 Nuevo usuario detectado: {user_id}, creando en BD...")
    insert_query = """
        INSERT INTO users (user_id, name, phone, channel)
        VALUES (:user_id, :name, :phone, :channel)
    """
    await db.execute(insert_query, {
        "user_id": user_id,
        "name": name or "Cliente nuevo",
        "phone": phone or user_id,
        "channel": channel
    })

    # Volver a consultarlo para devolver datos completos
    new_user = await db.fetch_one("SELECT * FROM users WHERE user_id = :user_id", {"user_id": user_id})

    # 4️⃣ Guardar sesión en Redis
    await set_user_session(user_id, dict(new_user))
    return dict(new_user)
