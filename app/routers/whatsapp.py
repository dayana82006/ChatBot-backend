from fastapi import APIRouter, Request, HTTPException, Response
import logging
from app.services.whatsappService import process_whatsapp_message, validate_whatsapp_config
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/webhook", summary="Verificación del webhook de WhatsApp")
async def verify_whatsapp_webhook(request: Request):
    """
    Endpoint para verificación del webhook de WhatsApp.
    Meta envía hub.mode, hub.verify_token, hub.challenge.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info(f"WhatsApp webhook verification: mode={mode}, token_match={token == settings.WHATSAPP_VERIFY_TOKEN}")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ WhatsApp webhook verificado exitosamente")
        return Response(content=challenge, media_type="text/plain")
    else:
        logger.warning("❌ WhatsApp webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook", summary="Recepción de mensajes de WhatsApp")
async def whatsapp_webhook_handler(request: Request):
    """
    Endpoint para recibir mensajes entrantes de WhatsApp via Meta Graph API.
    Procesa el mensaje y responde automáticamente usando el agente IZA.
    """
    try:
        # Validar configuración
        if not validate_whatsapp_config():
            raise HTTPException(
                status_code=500,
                detail="WhatsApp not properly configured"
            )

        payload = await request.json()
        logger.debug(f"WhatsApp webhook payload: {payload}")

        # Procesar mensaje
        result = await process_whatsapp_message(payload)

        if result in ["no_entry", "no_changes", "no_message"]:
            logger.debug(f"WhatsApp webhook ignored: {result}")
            return {"status": "ignored", "reason": result}

        return {"status": "sent", "reply": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing WhatsApp webhook")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", summary="Estado de configuración de WhatsApp")
async def whatsapp_status():
    """Endpoint para verificar el estado de la configuración de WhatsApp"""
    config_status = validate_whatsapp_config()
    
    return {
        "configured": config_status,
        "webhook_url": f"{settings.PUBLIC_BASE_URL}/whatsapp/webhook" if hasattr(settings, 'PUBLIC_BASE_URL') and settings.PUBLIC_BASE_URL else None,
        "phone_id": settings.WHATSAPP_PHONE_ID,
        "verify_token_set": bool(settings.WHATSAPP_VERIFY_TOKEN)
    }