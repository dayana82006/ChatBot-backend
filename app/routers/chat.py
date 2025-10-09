from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging
from app.services.agent import get_agent_response
from app.services.websocketService import manager
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    user_id: Optional[str] = Field(None, description="ID del usuario (opcional)")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Respuesta del asistente")

@router.post("/", response_model=ChatResponse, summary="Chat con el asistente IZA")
async def chat_with_assistant(request: ChatRequest):
    try:
        # Validación adicional
        if not request.message.strip():
            raise HTTPException(
                status_code=400, 
                detail="El mensaje no puede estar vacío."
            )

        user_id = request.user_id or "web_user"
        logger.info(f"💬 Chat request from {user_id}: {request.message}")

        await manager.notify_new_message(
            user_id=user_id,
            chat_id=0,  # Puedes obtener el chat_id real si lo guardas en BD
            role="user",
            text=request.message.strip(),
            channel="web"
        )

        # Generar respuesta usando el agente
        reply = await get_agent_response(
            user_id=user_id,
            user_message=request.message.strip(),
            channel="web"
        )

        # 🔥 NOTIFICAR RESPUESTA DEL ASISTENTE POR WEBSOCKET
        await manager.notify_new_message(
            user_id=user_id,
            chat_id=0,
            role="assistant",
            text=reply,
            channel="web"
        )

        logger.info(f"✅ Chat response generated for {user_id}")
        return ChatResponse(reply=reply)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor. Intenta nuevamente."
        )