from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime
import logging
from app.queries.chatQueries import get_all_chats_with_summary
from app.queries.messageQueries import get_messages_by_chat
from app.queries.chatQueries import get_chat_by_user

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

@router.get("/chats", response_model=ChatListResponse, summary="Lista paginada de chats")
async def list_chats(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Elementos por página"),
    search: Optional[str] = Query(None, description="Búsqueda por user_id o contenido"),
    channel: Optional[str] = Query(None, description="Filtrar por canal")
):
    """
    Obtiene una lista paginada de todos los chats de usuarios.
    
    Soporta:
    - **Paginación**: page y limit
    - **Búsqueda**: por user_id o contenido del último mensaje
    - **Filtrado**: por canal (web, whatsapp, telegram)
    """
    try:
        logger.info(f"Admin: Listing chats - page={page}, limit={limit}, search={search}, channel={channel}")
        
        # Obtener chats de la base de datos
        result = get_all_chats_with_summary(
            page=page,
            limit=limit,
            search=search,
            channel=channel
        )
        
        # Convertir a objetos Pydantic
        chat_summaries = []
        for item in result["items"]:
            summary = ChatSummary(
                user_id=item["user_id"],
                channel=item["channel"] or "web",
                last_message=item["last_message"] or "Sin mensajes",
                updated_at=item["updated_at"],
                count=item["count"] or 0
            )
            chat_summaries.append(summary)
        
        return ChatListResponse(
            items=chat_summaries,
            page=result["page"],
            total=result["total"]
        )
        
    except Exception as e:
        logger.exception(f"Error listing chats: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/chats/{user_id}", response_model=ChatDetailResponse, summary="Detalle de chat específico")
async def get_chat_detail(
    user_id: str,
    channel: str = Query("web", description="Canal del chat")
):
    """
    Obtiene el historial completo de mensajes de un chat específico.
    
    - **user_id**: ID del usuario
    - **channel**: Canal de comunicación (web, whatsapp, telegram)
    """
    try:
        logger.info(f"Admin: Getting chat detail for user_id={user_id}, channel={channel}")
        
        # Buscar el chat
        chat = get_chat_by_user(user_id, channel)
        if not chat:
            raise HTTPException(
                status_code=404, 
                detail=f"Chat no encontrado para user_id={user_id}, channel={channel}"
            )
        
        # Obtener mensajes del chat
        messages = get_messages_by_chat(chat["id"])
        
        # Convertir mensajes a objetos Pydantic
        chat_messages = []
        for msg in messages:
            chat_message = ChatMessage(
                role=msg["role"],
                text=msg["text"],
                timestamp=msg["timestamp"]
            )
            chat_messages.append(chat_message)
        
        return ChatDetailResponse(
            user_id=user_id,
            channel=chat["channel"] or "web",
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