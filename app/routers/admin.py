# backend/app/routers/admin.py
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatSummary(BaseModel):
    user_id: str
    channel: str
    last_message: str
    updated_at: datetime.datetime
    count: int

class ChatListResponse(BaseModel):
    items: List[ChatSummary]
    page: int
    total: int

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    text: str
    ts: datetime.datetime

class ChatDetailResponse(BaseModel):
    user_id: str
    channel: str
    messages: List[ChatMessage]


@router.get("/chats", response_model=ChatListResponse, summary="Lista de chats de usuarios")
async def list_chats(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    channel: Optional[str] = Query(None, regex="^(web|wa|tg)$")
):
    """
    Endpoint para obtener un listado paginado y filtrado de los chats de usuarios.
    Actualmente es un stub.
    """
    logger.info(f"Admin: Listing chats - page={page}, limit={limit}, search={search}, channel={channel}")
    # TODO: Implementar la lógica para consultar los chats desde la DB (SQLite/PostgreSQL)
    # y aplicar paginación, búsqueda y filtro.
    
    # Datos de prueba para el stub
    dummy_chats = [
        ChatSummary(user_id="user_web_1", channel="web", last_message="Necesito información sobre precios.", updated_at=datetime.datetime.now(), count=5),
        ChatSummary(user_id="+573001234567", channel="wa", last_message="Hola IZA, cómo estás?", updated_at=datetime.datetime.now() - datetime.timedelta(hours=1), count=3),
        ChatSummary(user_id="telegram_user_42", channel="tg", last_message="Quiero saber sobre el producto X.", updated_at=datetime.datetime.now() - datetime.timedelta(days=1), count=10),
    ]

    filtered_chats = dummy_chats
    if search:
        filtered_chats = [c for c in filtered_chats if search.lower() in c.user_id.lower() or search.lower() in c.last_message.lower()]
    if channel:
        filtered_chats = [c for c in filtered_chats if c.channel == channel]

    total_items = len(filtered_chats)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_chats = filtered_chats[start_index:end_index]

    return ChatListResponse(items=paginated_chats, page=page, total=total_items)

@router.get("/chats/{user_id}", response_model=ChatDetailResponse, summary="Detalle de un chat específico")
async def get_chat_detail(user_id: str):
    """
    Endpoint para obtener el historial completo de mensajes de un chat específico.
    Actualmente es un stub.
    """
    logger.info(f"Admin: Getting chat detail for user_id={user_id}")
    # TODO: Implementar la lógica para consultar los mensajes de un chat desde la DB.

    # Datos de prueba para el stub
    if user_id == "user_web_1":
        messages = [
            ChatMessage(role="user", text="Hola, quisiera saber más sobre sus servicios.", ts=datetime.datetime.now() - datetime.timedelta(minutes=10)),
            ChatMessage(role="assistant", text="¡Claro! Con gusto te ayudo. ¿Qué tipo de servicio te interesa?", ts=datetime.datetime.now() - datetime.timedelta(minutes=9)),
            ChatMessage(role="user", text="Necesito información sobre precios.", ts=datetime.datetime.now() - datetime.timedelta(minutes=5)),
        ]
        return ChatDetailResponse(user_id=user_id, channel="web", messages=messages)
    elif user_id == "+573001234567":
        messages = [
            ChatMessage(role="user", text="Hola IZA, cómo estás?", ts=datetime.datetime.now() - datetime.timedelta(hours=1)),
            ChatMessage(role="assistant", text="¡Hola! Estoy muy bien, listo para ayudarte. ¿En qué puedo asistirte hoy?", ts=datetime.datetime.now() - datetime.timedelta(hours=1, minutes=-1)),
        ]
        return ChatDetailResponse(user_id=user_id, channel="wa", messages=messages)
    
    raise HTTPException(status_code=404, detail="Chat not found")