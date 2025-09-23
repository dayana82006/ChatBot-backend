# app/routers/whatsapp.py
from fastapi import APIRouter, Request, HTTPException, Response
import logging
from app.services.whatsappService import send_whatsapp_message
from app.queries.messageQueries import add_message
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# 👉 Verificación del webhook
@router.get("/whatsapp/webhook", summary="Verificación del webhook de WhatsApp")
async def verify_whatsapp_webhook(request: Request):
    """
    Endpoint para verificación del webhook: WhatsApp envía hub.mode, hub.verify_token, hub.challenge.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully!")
        return Response(content=challenge or "", media_type="text/plain")
    else:
        raise HTTPException(status_code=403, detail="Verification failed")

# 👉 Recepción de mensajes
@router.post("/whatsapp/webhook", summary="Recepción de mensajes de WhatsApp")
async def whatsapp_webhook_handler(request: Request):
    """
    Endpoint para recibir mensajes entrantes de WhatsApp via Meta Graph API.
    Guarda el mensaje en DB y responde automáticamente.
    """
    payload = await request.json()
    logger.info(f"Received WhatsApp webhook payload: {payload}")

    try:
        # 📌 Extraer info del payload
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ignored"}

        message = messages[0]
        from_number = message["from"]  # número del usuario
        text = message.get("text", {}).get("body", "")

        # 📌 Guardar mensaje en DB
        chat_id = value.get("metadata", {}).get("phone_number_id")
        add_message(chat_id=chat_id, role="user", text=text)

        # 📌 Preparar respuesta (aquí podrías llamar a tu agente IA)
        reply_text = f"Echo: {text}"

        # 📌 Enviar respuesta a WhatsApp
        send_whatsapp_message(to=from_number, message=reply_text)

        return {"status": "sent", "reply": reply_text}

    except Exception as e:
        logger.exception("Error processing incoming WhatsApp message")
        raise HTTPException(status_code=500, detail=str(e))
