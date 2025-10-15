import logging
import httpx
from typing import Dict, Any
from app.services.agent import get_agent_response
from app.config import settings
from app.services.websocketService import manager

logger = logging.getLogger(__name__)

WHATSAPP_TOKEN = settings.WHATSAPP_TOKEN
GRAPH_URL = settings.GRAPH_URL

async def process_whatsapp_message(payload: Dict[str, Any]) -> str:
    try:
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

        message = messages[0]
        from_number = message.get("from")
        message_id = message.get("id")

        text = ""
        if "text" in message:
            text = message["text"].get("body", "")
        elif "button" in message:
            text = message["button"].get("text", "")
        else:
            text = "Mensaje no soportado"

        logger.info(f"📱 WhatsApp mensaje de {from_number}: {text}")

        # 🔥 NOTIFICAR MENSAJE DEL USUARIO POR WEBSOCKET
        await manager.notify_new_message(
            user_id=from_number,
            chat_id=0,
            role="user",
            text=text,
            channel="web"
        )
        logger.debug(f"📡 Mensaje de usuario notificado via WebSocket")

        # Generar respuesta del agente
        reply_text = await get_agent_response(
            user_id=from_number,
            user_message=text,
            channel="web"
        )

        # Enviar respuesta por WhatsApp
        await send_whatsapp_message(to=from_number, message=reply_text)

        # 🔥 NOTIFICAR RESPUESTA DEL ASISTENTE POR WEBSOCKET
        await manager.notify_new_message(
            user_id=from_number,
            chat_id=0,
            role="assistant",
            text=reply_text,
            channel="web"
        )
        logger.debug(f"📡 Respuesta del asistente notificada via WebSocket")

        logger.info(f"✅ Respuesta enviada a {from_number}")
        return reply_text

    except Exception as e:
        logger.exception("Error procesando mensaje de WhatsApp")
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