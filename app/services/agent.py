# app/services/agent.py
import logging
from typing import List
from app.services.qdrant_service import search
from app.config import settings

logger = logging.getLogger(__name__)

# Si usas Langroid:
try:
    import langroid as lr
    import langroid.language_models as lm
    LANGROID_AVAILABLE = True
except Exception as e:
    LANGROID_AVAILABLE = False
    logger.warning("Langroid no disponible: %s", e)

# Prompt base / system
SYSTEM_PROMPT = """
Eres IZA, el asistente comercial de ventas de café de la marca IZA.
Eres cordial, cercano (tono colombiano), breve y enfocado en vender y ayudar.
Sigue estas reglas:
- Usa información tomada de los fragmentos provistos. Cita la fuente si aplica.
- Si no hay evidencia suficiente, di con transparencia que no tienes la info y ofrece alternativas.
- Haz una pregunta aclaratoria si falta info para cerrar la venta.
- Tono: amable, entusiasta pero profesional.
"""

def build_context_message(kb_fragments: List[dict]) -> str:
    parts = []
    for i, f in enumerate(kb_fragments):
        payload = f.get("payload", {})
        title = payload.get("title", f"fragmento_{i}")
        text = payload.get("text", "") or f.get("payload", {}).get("text", "") or ""
        # En Qdrant guardamos el texto como payload o en el id; mejor incluir h.payload["text"] si lo guardaste ahí.
        # Para seguridad, use payload['title'] y h.payload si está.
        parts.append(f"Fragmento {i+1} (titulo: {title}): {f.get('payload', {}).get('text', '') or f.get('payload', '') or ''}")
    return "\n".join(parts)
async def get_agent_response(user_id: str, user_message: str) -> str:
    # 1) Recuperar top-k
    top_k = settings.RAG_TOP_K
    fragments = await search(
        user_message,
        top_k=top_k,
        score_threshold=settings.RAG_SCORE_THRESHOLD,
    )

    # build context
    context_texts = []
    for f in fragments:
        p = f.get("payload", {})
        maybe_text = p.get("text") or p.get("content") or p.get("title") or ""
        context_texts.append(f"- {maybe_text} (source: {p.get('source', 'kb')})")

    context_block = "\n".join(context_texts) if context_texts else "Sin contexto relevante encontrado."

    # 2) Formar prompt final
    full_prompt = f"""{SYSTEM_PROMPT}

Contexto recuperado:
{context_block}

Usuario: {user_message}

Instrucciones: Responde en español, con estilo amistoso colombiano, orientado a la venta. Sé breve y sugiere un siguiente paso (ej: pedir dirección, preguntar cuántos paquetes). Si no hay info en el contexto, admite no saber y propone alternativas.
"""

    # 3) Generar respuesta con Langroid (si está disponible)
    if LANGROID_AVAILABLE:
        model_name = settings.LLM_MODEL_NAME or "gpt-3.5-turbo"
        llm = (
            lm.OpenAIChat(model=model_name, openai_api_key=settings.OPENAI_API_KEY)
            if settings.OPENAI_API_KEY
            else lm.OpenAIChat(model=model_name)
        )
        chat_agent = lr.ChatAgent(llm=llm)
        response = chat_agent.run(full_prompt)
        return response

    # Fallback
    reply = (
        "Hola! Puedo ayudarte con nuestros cafés. "
        "Encontré esto: "
        + (context_block if context_texts else "No hay información relevante en la KB.")
        + " ¿Quieres que te recomiende un café para empezar?"
    )
    return reply

