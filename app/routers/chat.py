from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.services.agent import get_agent_response

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    user_id: str = None  # opcional

class ChatResponse(BaseModel):
    reply: str

@router.post("/", response_model=ChatResponse, summary="Envía un mensaje al asistente por HTTP")
async def chat_with_assistant(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    logger.info(f"Chat incoming from {request.user_id}: {request.message}")
    reply = await get_agent_response(user_id=request.user_id or "web_user", user_message=request.message)
    return ChatResponse(reply=reply)
