from app.database import database  # o el motor que uses
from datetime import datetime

async def get_or_create_user(user_id: str, channel: str = "web"):
    query_check = "SELECT id FROM users WHERE user_id = :user_id"
    existing = await database.fetch_one(query_check, {"user_id": user_id})

    if not existing:
        query_insert = """
            INSERT INTO users (user_id, channel, created_at, updated_at)
            VALUES (:user_id, :channel, :created_at, :updated_at)
        """
        values = {
            "user_id": user_id,
            "channel": channel,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await database.execute(query_insert, values)
        return True  # Nuevo usuario creado
    return False  # Ya existía
