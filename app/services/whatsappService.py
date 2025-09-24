import logging
import httpx
from typing import Dict, Any
from app.services.agent import get_agent_response
from app.config import settings

logger = logging.getLogger(__name__)

# Configuración WhatsApp
WHATSAPP_TOKEN = settings.WHATSAPP_TOKEN
GRAPH_URL = settings.GRAPH_URL

async def process_whatsapp_message(payload: Dict[str, Any]) -> str:
    """
    Procesa mensajes entrantes de WhatsApp y genera respuestas.
    """
    try:
        # Validar estructura del payload
        if not payload.get("entry"):
            logger.debug("No entry in payload")
            return "no_entry"

        entry = payload["entry"][0]
        changes = entry.get("changes", [])
        
        if not changes:
            logger.debug("No changes in payload")
            return "no_changes"
            
        value = changes[0].get("value", {})
        messages = value.get("messages", [])

        if not messages:
            logger.debug("No messages in payload (status update or other event)")
            return "no_message"

        # Procesar primer mensaje
        message = messages[0]
        from_number = message.get("from")
        message_id = message.get("id")
        
        # Extraer texto del mensaje
        text = ""
        if "text" in message:
            text = message["text"].get("body", "")
        elif "button" in message:
            text = message["button"].get("text", "")
        else:
            text = "Mensaje no soportado"

        logger.info(f"📱 WhatsApp mensaje de {from_number}: {text}")

        # Generar respuesta usando el agente
        reply_text = await get_agent_response(
            user_id=from_number, 
            user_message=text, 
            channel="whatsapp"
        )

        # Enviar respuesta
        await send_whatsapp_message(to=from_number, message=reply_text)
        
        logger.info(f"✅ Respuesta enviada a {from_number}")
        return reply_text

    except Exception as e:
        logger.exception("Error procesando mensaje de WhatsApp")
        # Intentar enviar mensaje de error al usuario si es posible
        if 'from_number' in locals():
            try:
                await send_whatsapp_message(
                    to=from_number, 
                    message="Disculpa, tengo problemas técnicos. Intenta nuevamente en unos momentos."
                )
            except:
                pass
        raise

async def send_whatsapp_message(to: str, message: str):
    """
    Envía un mensaje de texto a través de la WhatsApp Graph API.
    """
    if not WHATSAPP_TOKEN or not GRAPH_URL:
        logger.error("WhatsApp no configurado correctamente")
        raise ValueError("WhatsApp credentials not configured")

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GRAPH_URL, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Mensaje WhatsApp enviado a {to}")
            else:
                logger.error(f"❌ Error enviando mensaje WhatsApp: {response.status_code} - {response.text}")
                response.raise_for_status()
                
    except httpx.TimeoutException:
        logger.error("Timeout enviando mensaje de WhatsApp")
        raise
    except Exception as e:
        logger.exception(f"Error enviando mensaje de WhatsApp: {e}")
        raise

def validate_whatsapp_config() -> bool:
    """Valida que la configuración de WhatsApp esté completa"""
    required_vars = [
        settings.WHATSAPP_TOKEN,
        settings.WHATSAPP_PHONE_ID,
        settings.WHATSAPP_VERIFY_TOKEN
    ]
    
    if all(required_vars):
        logger.info("✅ Configuración de WhatsApp completa")
        return True
    else:
        logger.warning("⚠️ Configuración de WhatsApp incompleta")
        return False