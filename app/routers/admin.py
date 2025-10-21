from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime
import logging
from app.queries.chatQueries import get_all_chats_with_summary
from app.queries.messageQueries import get_messages_by_chat
from app.queries.chatQueries import get_chat_by_user
from app.services.redisServices import get_chat_context 

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)

# Modelos Pydantic
class ChatSummary(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    channel: str = Field(..., description="Canal (web, whatsapp, telegram)")
    last_message: Optional[str] = Field(None, description="Último mensaje")
    updated_at: datetime.datetime = Field(..., description="Última actualización")
    count: int = Field(..., description="Número total de mensajes")

class ChatListResponse(BaseModel):
    items: List[ChatSummary] = Field(..., description="Lista de chats")
    page: int = Field(..., description="Página actual")
    total: int = Field(..., description="Total de elementos")

class ChatMessage(BaseModel):
    role: str = Field(..., description="Rol (user o assistant)")
    text: str = Field(..., description="Contenido del mensaje")
    ts: datetime.datetime = Field(..., description="Timestamp del mensaje", alias="timestamp")

class ChatDetailResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    channel: str = Field(..., description="Canal de comunicación")
    messages: List[ChatMessage] = Field(..., description="Lista de mensajes")

# ✅ Nuevo endpoint: lista todos los chats con sus mensajes
@router.get("/chats/", summary="Lista todos los chats con sus mensajes")
async def list_all_chats_with_messages():
    """
    Obtiene todos los chats con todos sus mensajes (sin paginación).
    """
    try:
        logger.info("Admin: Listing all chats with messages")

        # Traer todos los chats (sin paginación, límite alto para traerlos todos)
        result = get_all_chats_with_summary(page=1, limit=10000)

        chats_with_messages = []
        for chat in result["items"]:
            # Traer mensajes de cada chat
            messages = get_messages_by_chat(chat["id"])
            msg_list = [
                {
                    "id": msg["id"],
                    "role": msg["role"],
                    "text": msg["text"],
                    "timestamp": msg["timestamp"]
                }
                for msg in messages
            ]

            chats_with_messages.append({
                "id": chat["id"],
                "user_id": chat["user_id"],
                "channel": chat["channel"] or "web",
                "created_at": chat["created_at"],
                "updated_at": chat["updated_at"],
                "messages": msg_list
            })

        return {
            "total": result["total"],
            "items": chats_with_messages
        }

    except Exception as e:
        logger.exception(f"Error listing all chats with messages: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")



@router.get("/chats/{user_id}", response_model=ChatDetailResponse, summary="Detalle de chat específico")
async def get_chat_detail(
    user_id: str,
    channel: str = Query("web", description="Canal del chat")
):
    """
    Obtiene el historial completo de mensajes de un chat específico desde Redis.
    
    - **user_id**: ID del usuario
    - **channel**: Canal de comunicación (web, whatsapp, telegram)
    """
    try:
        logger.info(f"Admin: Getting chat detail for user_id={user_id}, channel={channel}")

        # 🔹 Obtenemos los mensajes del contexto de Redis
        chat_context = await get_chat_context(user_id)

        if not chat_context:
            raise HTTPException(
                status_code=404,
                detail=f"No hay mensajes guardados en Redis para user_id={user_id}"
            )

        # 🔹 Convertimos los mensajes al modelo ChatMessage
        chat_messages = []
        for item in chat_context:
            chat_messages.append(
                ChatMessage(
                    role=item.get("role", "user"),
                    text=item.get("message", ""),
                    timestamp=datetime.datetime.now()  # Redis no guarda timestamp
                )
            )

        # 🔹 Devolvemos la respuesta compatible con el frontend
        return ChatDetailResponse(
            user_id=user_id,
            channel=channel,
            messages=chat_messages
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting chat detail: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/stats", summary="Estadísticas generales")
async def get_admin_stats():
    """
    Obtiene estadísticas generales del sistema.
    """
    try:
        # Obtener estadísticas básicas
        all_chats = get_all_chats_with_summary(page=1, limit=1000)  # Obtener todos para contar
        
        stats = {
            "total_chats": all_chats["total"],
            "channels": {
                "web": len([c for c in all_chats["items"] if c.get("channel", "web") == "web"]),
                "whatsapp": len([c for c in all_chats["items"] if c.get("channel") == "whatsapp"]),
                "telegram": len([c for c in all_chats["items"] if c.get("channel") == "telegram"])
            },
            "total_messages": sum(c.get("count", 0) for c in all_chats["items"]),
            "last_activity": max(
                (c.get("updated_at") for c in all_chats["items"] if c.get("updated_at")),
                default=None
            )
        }
        
        return stats
        
    except Exception as e:
        logger.exception(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")