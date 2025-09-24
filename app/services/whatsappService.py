import logging
import httpx
from typing import Dict, Any
from app.services.agent import get_agent_response
from app.queries import add_message
import os

logger = logging.getLogger(__name__)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "YOUR_WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "YOUR_PHONE_NUMBER_ID")
GRAPH_API_VERSION = os.getenv("WHATSAPP_GRAPH_VERSION", "v17.0")
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_PHONE_ID}/messages"

async def process_whatsapp_message(payload: Dict[str, Any]) -> str:
    """
    Parsea el payload de Meta y procesa el primer mensaje encontrado.
    """
    try:
        entry = payload.get("entry", [])
        if not entry:
            logger.debug("No entry in payload")
            return "no_entry"

        change = entry[0].get("changes", [])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            logger.debug("No messages in payload (maybe an event we don't handle)")
            return "no_message"

        message = messages[0]
        from_number = message.get("from")
        message_id = message.get("id")
        # Puede venir como "text": {"body": "hola"} u otros tipos (image, button, etc.)
        text = None
        if "text" in message:
            text = message["text"].get("body")
        elif "button" in message:
            text = message["button"].get("text")
        else:
            # si quieres manejar imágenes/otros tipos, implementa aquí
            text = ""

        logger.info(f"Incoming message from {from_number}: {text} (id: {message_id})")

        # Guardar mensaje de usuario en DB (asíncrono)
        await add_message(user_id=from_number, role="user", content=text)

        # Obtener respuesta del agente (aquí integrarás Langroid/Qdrant)
        reply_text = await get_agent_response(user_id=from_number, user_message=text)

        # Guardar respuesta del asistente en DB
        await add_message(user_id=from_number, role="assistant", content=reply_text)

        # Enviar la respuesta via Graph API
        await send_whatsapp_message(to=from_number, message=reply_text)

        return reply_text
    except Exception as e:
        logger.exception("Error in process_whatsapp_message")
        raise

async def send_whatsapp_message(to: str, message: str):
    """
    Envía un texto simple por la Graph API.
    """
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

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GRAPH_URL, headers=headers, json=payload)
        logger.info(f"WhatsApp send response: {resp.status_code} {resp.text}")
        resp.raise_for_status()
