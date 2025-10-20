# app/services/redisServices.py
import json
import logging
import redis.asyncio as redis
from app.config import settings

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


async def update_purchase_session(user_id: str, user_message: str):
    session = await get_user_session(user_id) or {}
    message_lower = user_message.lower()

    # Detectar tipo de café
    if any(x in message_lower for x in ["huila", "nariño", "tolima", "clásico", "descafeinado"]):
        session["product"] = user_message
        session["state"] = "PRODUCT_SELECTED"

    # Detectar cantidad
    elif any(x in message_lower for x in ["250", "500"]):
        session["quantity"] = user_message
        session["state"] = "AWAITING_PAYMENT"

    # Detectar método de pago
    elif any(x in message_lower for x in ["pse", "nequi", "daviplata", "tarjeta", "efectivo"]):
        session["payment"] = user_message
        session["state"] = "AWAITING_SHIPPING"

    # Detectar datos de envío
    elif any(x in message_lower for x in ["cra", "cll", "calle", "avenida"]) or len(message_lower.split()) > 3:
        session.setdefault("shipping_data", []).append(user_message)
        if len(session["shipping_data"]) >= 4:
            session["state"] = "CONFIRMING_ORDER"

    await set_user_session(user_id, session)
    return session


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
