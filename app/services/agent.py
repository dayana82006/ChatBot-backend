import logging
from typing import List, Dict, Any, Optional
from app.services.qdrant_service import search
from app.queries.chatQueries import get_or_create_chat
from app.queries.messageQueries import add_message, get_recent_messages_by_user
from app.config import settings

logger = logging.getLogger(__name__)

# Intentar importar Langroid
try:
    import langroid as lr
    from langroid.language_models.openai_gpt import OpenAIGPT, OpenAIGPTConfig
    LANGROID_AVAILABLE = True
    logger.info("Langroid disponible")
except ImportError as e:
    LANGROID_AVAILABLE = False
    logger.warning(f"Langroid no disponible: {e}")

SYSTEM_PROMPT = """
Eres IZA, el asistente comercial de ventas de café de la marca IZA. 

IDENTIDAD Y PERSONALIDAD:
- Eres cordial, cercano y usas un tono profesional pero amigable (estilo colombiano)
- Eres breve, claro y orientado a resolver dudas y facilitar ventas
- Siempre mantienes un enfoque comercial sin ser agresivo

REGLAS DE COMPORTAMIENTO:
1. Usa ÚNICAMENTE información de los fragmentos de conocimiento proporcionados
2. Si no tienes información suficiente, admítelo con transparencia y ofrece alternativas
3. Haz preguntas aclaratorias cuando falte información para ayudar mejor al cliente
4. Sugiere siempre un próximo paso orientado a la venta (ej: pedir contacto, recomendar productos)
5. NO inventes datos, precios o información que no esté en el contexto
6. Si el cliente pide hablar con un humano, proporciona información de contacto

ESTILO DE COMUNICACIÓN:
- Saluda de manera amigable pero profesional
- Usa español neutro con toque colombiano
- Sé conciso pero completo en las respuestas
- Termina con una pregunta o sugerencia de acción cuando sea apropiado
"""

def build_context_from_kb(fragments: List[Dict[str, Any]]) -> str:
    """Construye el contexto a partir de los fragmentos recuperados"""
    if not fragments:
        return "No se encontró información relevante en la base de conocimiento."
    
    context_parts = []
    for i, fragment in enumerate(fragments, 1):
        payload = fragment.get("payload", {})
        text = payload.get("text", "")
        title = payload.get("title", f"Fragmento {i}")
        source = payload.get("source", "kb")
        
        context_parts.append(f"**{title}** (fuente: {source}):\n{text}")
    
    return "\n\n".join(context_parts)

def build_conversation_context(messages: List[Dict[str, Any]]) -> str:
    """Construye el contexto de conversación reciente"""
    if not messages:
        return ""
    
    context_parts = []
    for msg in messages[-5:]:  # Solo los últimos 5 mensajes
        role = "Usuario" if msg["role"] == "user" else "IZA"
        context_parts.append(f"{role}: {msg['text']}")
    
    return "\n".join(context_parts)

async def get_agent_response(user_id: str, user_message: str, channel: str = "web") -> str:
    """
    Genera respuesta del agente usando RAG y Langroid
    """
    try:
        # 1. Buscar información relevante en Qdrant
        logger.info(f"Buscando información para: {user_message}")
        fragments = await search(
            query=user_message,
            top_k=settings.RAG_TOP_K,
            score_threshold=settings.RAG_SCORE_THRESHOLD
        )
        
        # 2. Construir contexto de conocimiento
        kb_context = build_context_from_kb(fragments)
        
        # 3. Obtener historial de conversación reciente
        recent_messages = get_recent_messages_by_user(user_id, channel, limit=5)
        conversation_context = build_conversation_context(recent_messages)
        
        # 4. Construir prompt completo
        prompt_parts = [
            SYSTEM_PROMPT,
            "\n--- CONTEXTO DE CONOCIMIENTO ---",
            kb_context,
        ]
        
        if conversation_context:
            prompt_parts.extend([
                "\n--- HISTORIAL DE CONVERSACIÓN RECIENTE ---",
                conversation_context,
            ])
        
        prompt_parts.extend([
            f"\n--- MENSAJE ACTUAL DEL USUARIO ---",
            f"Usuario: {user_message}",
            "\n--- INSTRUCCIONES FINALES ---",
            "Responde como IZA basándote en el contexto proporcionado. Si no tienes información suficiente, sé transparente y ofrece alternativas de contacto o preguntas aclaratorias."
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        # 5. Generar respuesta
        if LANGROID_AVAILABLE and settings.OPENAI_API_KEY:
            response = await generate_with_langroid(full_prompt)
        else:
            response = generate_fallback_response(user_message, kb_context)
        
        # 6. Guardar la conversación en base de datos
        chat_id = get_or_create_chat(user_id, channel)
        add_message(chat_id, "user", user_message)
        add_message(chat_id, "assistant", response)
        
        logger.info(f"Respuesta generada para {user_id}: {response[:100]}...")
        return response
        
    except Exception as e:
        logger.exception(f"Error generando respuesta del agente: {e}")
        return "Disculpa, en este momento tengo dificultades técnicas. ¿Podrías intentar nuevamente en unos momentos?"

async def generate_with_langroid(prompt: str) -> str:
    """Genera respuesta usando Langroid"""
    try:
        # Configurar el modelo OpenAI
        config = OpenAIGPTConfig(
            api_key=settings.OPENAI_API_KEY,
            chat_model=settings.LLM_MODEL_NAME,
            chat_context_length=4000,
            temperature=0.7,
            max_output_tokens=300
        )
        
        # Crear el modelo LLM
        llm = OpenAIGPT(config)
        
        # Crear agente de chat
        agent = lr.ChatAgent(
            config=lr.ChatAgentConfig(
                name="IZA",
                system_message=prompt,
                llm=config,
            )
        )
        
        # Generar respuesta
        response = agent.llm_response("")
        return response.content if hasattr(response, 'content') else str(response)
        
    except Exception as e:
        logger.exception(f"Error con Langroid: {e}")
        return generate_fallback_response("", "")

def generate_fallback_response(user_message: str, context: str) -> str:
    """Respuesta de fallback cuando Langroid no está disponible"""
    if not context or context == "No se encontró información relevante en la base de conocimiento.":
        return (
            "¡Hola! Soy IZA, tu asistente comercial de café. "
            "En este momento no tengo información específica sobre tu consulta, "
            "pero estaré encantada de conectarte con nuestro equipo de ventas. "
            "¿Podrías contarme más detalles sobre lo que necesitas?"
        )
    
    return (
        f"¡Hola! Soy IZA, encontré esta información que puede ayudarte:\n\n"
        f"{context}\n\n"
        f"¿Te gustaría saber algo más específico sobre nuestros cafés?"
    )