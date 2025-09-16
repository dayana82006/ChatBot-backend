# backend/app/routers/whatsapp.py
from fastapi import APIRouter, Request, HTTPException, Response
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/webhook", summary="Verificación del webhook de WhatsApp")
async def verify_whatsapp_webhook(request: Request):
    """
    Endpoint para la verificación del webhook de WhatsApp Cloud API.
    Meta enviará una solicitud GET con parámetros específicos para validar el webhook.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == "YOUR_WHATSAPP_VERIFY_TOKEN": # Reemplazar con settings.WHATSAPP_VERIFY_TOKEN
            logger.info("WhatsApp webhook verified successfully!")
            return Response(content=challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Verification failed")
    raise HTTPException(status_code=400, detail="Missing hub.mode or hub.verify_token")

@router.post("/webhook", summary="Recepción de mensajes de WhatsApp")
async def whatsapp_webhook_handler(request: Request):
    """
    Endpoint para recibir mensajes entrantes de WhatsApp.
    Aquí se procesarán los mensajes y se enviarán respuestas.
    """
    payload = await request.json()
    logger.info(f"Received WhatsApp webhook payload: {payload}")
    # TODO: Implementar la lógica para procesar mensajes y responder
    # Esto incluirá parsear el payload de Meta, extraer el mensaje,
    # llamar al agente y enviar la respuesta usando la Graph API.
    return {"status": "sent"}