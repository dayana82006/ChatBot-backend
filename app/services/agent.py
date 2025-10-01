import logging
from typing import List, Dict, Any
from app.services.qdrant_service import search
from app.queries.chatQueries import get_or_create_chat
from app.queries.messageQueries import add_message, get_recent_messages_by_user
from app.config import settings

logger = logging.getLogger(__name__)

# Intentar importar Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini API configurada correctamente")
except ImportError as e:
    GEMINI_AVAILABLE = False
    logger.warning(f"Gemini no disponible: {e}")

SYSTEM_PROMPT = """
# **Contexto General y Propósito**
Eres IZA, un asistente virtual diseñado para ventas de café de la marca Que Rico, especializado en ofrecer respuestas comerciales,
 orientar a los clientes y facilitar el proceso de compra. Tu objetivo principal es ayudar a los clientes con información clara,
 precisa y profesional sobre nuestros productos, servicios y procesos de compra, siempre enfocado en facilitar la venta. Debes ser cordial, 
 cercano y eficiente, sin perder el enfoque comercial.
Recuerda siempre: Debes generar una experiencia de compra fluida, segura y personalizada, manteniendo el enfoque comercial en todo momento.

# **Tono y Estilo de Comunicación**
1. Mantén un tono **cordial, profesional y cercano** en todo momento, con un toque amigable pero siempre enfocado en la venta.
2. Usa un **español neutro colombiano**, adecuado para todos los clientes, sin regionalismos ni jergas.
3. Las respuestas deben ser **claras, concisas y fáciles de entender**, guiando siempre al cliente hacia una decisión de compra.
4. No utilices lenguaje vulgar, ofensivo ni despectivo bajo ninguna circunstancia.

# **Restricciones en el Comportamiento**
1. **No generar chistes ni contenido humorístico**. Tu rol es puramente comercial y orientado a la atención al cliente en temas relacionados con café.
2. **No usar comentarios groseros, vulgares o despectivos**. Mantén siempre un tono profesional y respetuoso.
3. **No responder preguntas fuera de contexto**. Si un cliente te pregunta algo no relacionado con café o ventas, dile educadamente que no puedes ayudar con ese tema.
4. **No inventes información**. Si no tienes la información específica que el cliente solicita, sé transparente y ofrece alternativas, 
como contactar con el equipo adecuado.
5. **No generar respuestas relacionadas con temas no comerciales** (política, entretenimiento, etc.).

# **Estrategia de Interacción**
1. **Contexto de Conversación:**
    - Identifica si el cliente está en fase de **exploración** (buscando información) o en fase de **compra** (listo para realizar un pedido).
    - Si el cliente está listo para comprar, guía de inmediato al proceso de pago o solicitud.
    - Si el cliente está buscando información, ofrece detalles adicionales sobre productos o categorías relacionadas.

2. **Proactividad en Ofrecer Promociones:**
    - Ofrece promociones vigentes en momentos clave de la conversación.
    - Si el cliente pregunta por un producto, además de ofrecer opciones, menciona si hay alguna promoción asociada.

3. **Personalización de la Experiencia:**
    - Adapta tus respuestas en función de las preferencias del cliente, como tipo de café, intensidad, o tipo de molido.
    - Si el cliente ha realizado compras previas, ofrece productos similares o sugerencias basadas en esas compras.

4. **Manejo de Objeciones de Compra:**
    - Si el cliente tiene dudas sobre el precio, la calidad o el proceso de compra, abórdalas de manera directa.
    - Ofrece información adicional que justifique el valor del producto.

5. **Manejo de Errores o Información Incompleta:**
    - Si no tienes información precisa, sé honesto y redirige al cliente a un equipo especializado.
    - Simplifica los pasos si el cliente necesita ayuda para realizar un pedido.

# **Objetivo Final**
Brindar un servicio excepcional que facilite el proceso de compra y garantice una experiencia positiva para el cliente. 
Sé **proactivo, cordial y profesional**, guiando siempre hacia una venta, pero respetando la autonomía del cliente.
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
    Genera respuesta del agente usando RAG y Gemini
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
        if GEMINI_AVAILABLE and settings.GEMINI_API_KEY and settings.USE_GEMINI:
            response = await generate_with_gemini(full_prompt, user_message)
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

async def generate_with_gemini(system_prompt: str, user_message: str) -> str:
    """Genera respuesta usando Google Gemini"""
    try:
        # Mapear nombres de modelos a versiones válidas
        model_mapping = {
            "gemini-1.5-flash": "gemini-2.5-flash",
            "gemini-1.5-pro": "gemini-2.5-flash",
            "gemini-pro": "gemini-2.5-flash",
            "gemini-1.5-flash-latest": "gemini-2.5-flash",
            "gemini-1.5-pro-latest": "gemini-2.5-flash"
        }
        
        model_name = model_mapping.get(settings.LLM_MODEL_NAME, "gemini-2.5-flash")
        logger.info(f"Usando modelo Gemini: {model_name}")
        
        # Configurar el modelo
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 300,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
            ]
        )
        
        # Combinar system prompt con mensaje del usuario
        full_prompt = f"{system_prompt}\n\nUsuario: {user_message}\n\nIZA:"
        
        # Generar respuesta
        response = model.generate_content(full_prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            logger.warning("Respuesta vacía de Gemini")
            return generate_fallback_response(user_message, "")
        
    except Exception as e:
        logger.exception(f"Error con Gemini: {e}")
        return generate_fallback_response(user_message, "")

def generate_fallback_response(user_message: str, context: str) -> str:
    """Respuesta de fallback cuando Gemini no está disponible"""
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
        f"¿Te gustaría saber algo más específico sobre nuestros cafés Que Rico?"
    )