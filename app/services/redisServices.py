# app/services/redisServices.py
import json
import logging
import redis.asyncio as redis
from app.config import settings
from app.database.database import get_connection
from app.queries.chatQueries import get_or_create_chat
from app.queries.userQueries import get_user_by_id, create_user
from app import redis_client




logger = logging.getLogger(__name__)
redis_client = None

async def init_redis():
    global redis_client
    try:
        redis_client = await redis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Conexión con Redis establecida (async)")
    except Exception as e:
        logger.error(f"❌ Error al conectar con Redis: {e}")
        redis_client = None

async def close_redis():
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
            logger.info("🔌 Conexión con Redis cerrada correctamente")
        except Exception as e:
            logger.warning(f"⚠️ Error al cerrar Redis: {e}")
        redis_client = None

# ==== CACHE ====
async def set_cache(key: str, value: dict, expire: int = settings.CACHE_EXPIRE):
    if redis_client:
        await redis_client.setex(key, expire, json.dumps(value))

async def get_cache(key: str):
    if redis_client:
        data = await redis_client.get(key)
        return json.loads(data) if data else None

# ==== SESIONES ====
async def set_user_session(user_id: str, data: dict, expire: int = settings.SESSION_EXPIRE):
    if redis_client:
        await redis_client.setex(f"session:{user_id}", expire, json.dumps(data))

async def get_user_session(user_id: str):
    if redis_client:
        data = await redis_client.get(f"session:{user_id}")
        return json.loads(data) if data else {}

async def clear_user_session(user_id: str):
    if redis_client:
        await redis_client.delete(f"session:{user_id}")

# ==== SINCRONIZACIÓN REDIS <-> MYSQL ====
async def sync_user_session(user_id: str, channel: str = "web"):
    """
    Verifica si el usuario tiene sesión activa en Redis,
    si no, la busca o crea en la base de datos.
    """
    # 1️⃣ Buscar en Redis
    session = await get_user_session(user_id)
    if session:
        logger.info(f"Sesión encontrada en Redis: {user_id}")
        return session

    logger.info(f"No se encontró sesión en Redis para {user_id}, buscando en BD...")

    # 2️⃣ Buscar usuario en base de datos
    user = get_user_by_id(user_id)
    if not user:
        logger.info(f"Usuario {user_id} no existe, creando...")
        user = create_user(user_id, channel=channel)

    # 3️⃣ Buscar chat existente o crear uno nuevo
    chat_id = get_or_create_chat(user_id, channel)

    # 4️⃣ Crear sesión base
    session_data = {
        "user_id": user_id,
        "chat_id": chat_id,
        "channel": channel,
        "context": []
    }

    # 5️⃣ Guardar sesión en Redis
    await set_user_session(user_id, session_data)
    logger.info(f"Sesión creada y guardada en Redis para {user_id}")
    return session_data


async def clear_user_session(user_id: str):
    if redis_client:
        await redis_client.delete(f"session:{user_id}")

# ==== CONTEXTO DE CHAT ====
async def add_chat_turn(user_id: str, message: str, role: str):
    if redis_client:
        key = f"context:{user_id}"
        entry = json.dumps({"role": role, "message": message})
        await redis_client.rpush(key, entry)
        await redis_client.ltrim(key, -settings.MAX_CHAT_TURNS, -1)
        await redis_client.expire(key, settings.SESSION_EXPIRE)

async def get_chat_context(user_id: str):
    if redis_client:
        key = f"context:{user_id}"
        data = await redis_client.lrange(key, 0, -1)
        return [json.loads(item) for item in data]
    return []

async def clear_chat_context(user_id: str):
    if redis_client:
        await redis_client.delete(f"context:{user_id}")

# ==== COLA DE MENSAJES ====
async def push_message_queue(user_id: str, message: str):
    if redis_client:
        await redis_client.rpush(f"queue:{user_id}", message)

async def pop_message_queue(user_id: str):
    if redis_client:
        return await redis_client.lpop(f"queue:{user_id}")
