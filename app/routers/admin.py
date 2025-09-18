# backend/app/routers/admin.py
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatSummary(BaseModel):
    user_id: str
    last_message: str
    updated_at: datetime.datetime
    count: int

class ChatListResponse(BaseModel):
    items: List[ChatSummary]
    page: int
    total: int

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    text: str
    ts: datetime.datetime

class ChatDetailResponse(BaseModel):
    user_id: str
    messages: List[ChatMessage]

@router.get("/chats", response_model=ChatListResponse, summary="Lista de chats de usuarios")
async def list_chats(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
):
    """
    Endpoint para obtener un listado paginado y filtrado de los chats de usuarios (solo WhatsApp).
    """
    logger.info(f"Admin: Listing chats - page={page}, limit={limit}, search={search}")
    
    dummy_chats = [
        ChatSummary(user_id="+573001234567", last_message="Hola IZA, cómo estás?", updated_at=datetime.datetime.now(), count=3),
        ChatSummary(user_id="+573001111111", last_message="Quiero saber más del servicio", updated_at=datetime.datetime.now() - datetime.timedelta(minutes=30), count=5),
        ChatSummary(user_id="+573002222222", last_message="¿Cuánto cuesta?", updated_at=datetime.datetime.now() - datetime.timedelta(hours=1), count=2),
    ]

    filtered_chats = dummy_chats
    if search:
        filtered_chats = [
            c for c in filtered_chats
            if search.lower() in c.user_id.lower() or search.lower() in c.last_message.lower()
        ]

    total_items = len(filtered_chats)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_chats = filtered_chats[start_index:end_index]

    return ChatListResponse(items=paginated_chats, page=page, total=total_items)

@router.get("/chats/{user_id}", response_model=ChatDetailResponse, summary="Detalle de un chat específico")
async def get_chat_detail(user_id: str):
    """
    Endpoint para obtener el historial completo de mensajes de un chat específico (solo WhatsApp).
    """
    logger.info(f"Admin: Getting chat detail for user_id={user_id}")

    if user_id == "+573001234567":
        messages = [
            ChatMessage(role="user", text="Hola IZA, cómo estás?", ts=datetime.datetime.now() - datetime.timedelta(hours=1)),
            ChatMessage(role="assistant", text="¡Hola! Estoy muy bien, listo para ayudarte. ¿En qué puedo asistirte hoy?", ts=datetime.datetime.now() - datetime.timedelta(hours=1, minutes=-1)),
        ]
        return ChatDetailResponse(user_id=user_id, messages=messages)

    raise HTTPException(status_code=404, detail="Chat not found")
