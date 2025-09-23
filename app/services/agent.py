import logging
from app.services.qdrant_service import query_qdrant_for_context
from app.queries import add_message as save_message

logger = logging.getLogger(__name__)

async def get_agent_response(user: str, text: str) -> str:
    # 1. Guardar mensaje en DB
    await save_message(user, text, role="user")

    # 2. Buscar contexto en Qdrant
    context = await query_qdrant_for_context(text)

    # 3. Construir respuesta con Langroid
    # (esto depende de cómo lo configuraste, ejemplo básico:)
    reply = f"Tu mensaje fue: {text}. Contexto encontrado: {context}"

    # 4. Guardar respuesta en DB
    await save_message(user, reply, role="assistant")

    return reply


