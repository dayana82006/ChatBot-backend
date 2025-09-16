# backend/app/routers/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/", response_model=ChatResponse, summary="Envía un mensaje al asistente por HTTP")
async def chat_with_assistant(request: ChatRequest):
    """
    Endpoint para enviar un mensaje de texto al asistente comercial y recibir una respuesta.
    Actualmente es un stub, la lógica real del agente y RAG se integrará en fases posteriores.
    """
    logger.info(f"Received chat message: {request.message}")
    # TODO: Integrar con la lógica del agente Langroid y RAG
    # Por ahora, una respuesta de prueba
    if not request.message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    reply_message = f"Hola, recibí tu mensaje: '{request.message}'. Todavía estoy aprendiendo, pero pronto podré ayudarte como IZA."
    
    return ChatResponse(reply=reply_message)