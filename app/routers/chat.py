from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from app.services.agent import get_agent_response
from app.services.websocketService import manager
from app.services.userService import create_or_update_user  # ✅ nueva función
from app.database import get_connection  # asegúrate de tener esta utilidad

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    user_id: Optional[str] = Field(None, description="ID único del usuario (puede venir del frontend)")
    name: Optional[str] = Field(None, description="Nombre del usuario (opcional)")
    email: Optional[str] = Field(None, description="Email del usuario (opcional)")
    phone: Optional[str] = Field(None, description="Teléfono del usuario (opcional)")
    channel: Optional[str] = Field("web", description="Canal del mensaje (web, whatsapp, telegram, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales del usuario")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Respuesta del asistente")


@router.post("/", response_model=ChatResponse, summary="Chat con el asistente IZA")
async def chat_with_assistant(request: ChatRequest):
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

        user_id = request.user_id or "web_user"
        logger.info(f"💬 Chat request from {user_id}: {request.message}")

        # ✅ 1️⃣ Crear o actualizar usuario en MySQL antes de procesar el chat
        try:
            conn = get_connection()
            create_or_update_user(
                conn=conn,
                user_id=user_id,
                name=request.name,
                email=request.email,
                phone=request.phone,
                channel=request.channel,
                metadata=request.metadata,
            )
        except Exception as db_error:
            logger.warning(f"⚠️ No se pudo registrar/actualizar el usuario {user_id}: {db_error}")

        # ✅ 2️⃣ Notificar al WebSocket que hay un nuevo mensaje del usuario
        await manager.notify_new_message(
            user_id=user_id,
            chat_id=0,
            role="user",
            text=request.message.strip(),
            channel=request.channel
        )

        # ✅ 3️⃣ Obtener respuesta del agente (usa Redis + MySQL)
        reply = await get_agent_response(
            user_id=user_id,
            user_message=request.message.strip(),
            channel=request.channel
        )

        # ✅ 4️⃣ Notificar al WebSocket la respuesta del asistente
        await manager.notify_new_message(
            user_id=user_id,
            chat_id=0,
            role="assistant",
            text=reply,
            channel=request.channel
        )

        logger.info(f"✅ Chat completado para {user_id}")
        return ChatResponse(reply=reply)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"💥 Error en endpoint /chat: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor. Intenta nuevamente.")
