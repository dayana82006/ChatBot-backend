import logging
from typing import List, Dict, Any
from app.services.qdrant_service import search
from app.queries.chatQueries import get_or_create_chat
from app.queries.messageQueries import add_message, get_recent_messages_by_user
from app.config import settings
from app.services.redisServices import (
    get_user_session, set_user_session,
    get_chat_context, add_chat_turn,
    push_message_queue, pop_message_queue,
    clear_user_session, clear_chat_context
)
from app.services.UserServices import get_or_create_user


logger = logging.getLogger(__name__)

# Intentar importar Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("✅ Gemini API configurada correctamente")
except ImportError as e:
    GEMINI_AVAILABLE = False
    logger.warning(f"⚠️ Gemini no disponible: {e}")

SYSTEM_PROMPT = """
# **Contexto General y Propósito**
Eres IZA, un asistente virtual diseñado para ventas de café , especializado en ofrecer respuestas comerciales,
 orientar a los clientes y facilitar el proceso de compra. Tu objetivo principal es ayudar a los clientes con información clara,
 precisa y profesional sobre nuestros productos, servicios y procesos de compra, siempre enfocado en facilitar la venta. Debes ser cordial, 
 cercano y eficiente, sin perder el enfoque comercial.
Recuerda siempre: Debes generar una experiencia de compra fluida, segura y personalizada, manteniendo el enfoque comercial en todo momento.

# **Tono y Estilo de Comunicación**
1. Mantén un tono **cordial, profesional y cercano** en todo momento, con un toque amigable pero siempre enfocado en la venta.
2. Usa un **español neutro colombiano**, adecuado para todos los clientes, sin regionalismos ni jergas.
3. Las respuestas deben ser **claras, concisas, cortas y fáciles de entender**, guiando siempre al cliente hacia una decisión de compra.
4. No utilices lenguaje vulgar, ofensivo ni despectivo bajo ninguna circunstancia.

# **Restricciones en el Comportamiento**
1. **No generar chistes ni contenido humorístico**. Tu rol es puramente comercial y orientado a la atención al cliente en temas relacionados con café.
2. **No usar comentarios groseros, vulgares o despectivos**. Mantén siempre un tono profesional y respetuoso.
3. **No responder preguntas fuera de contexto**. Si un cliente te pregunta algo no relacionado con café o ventas, dile educadamente que no puedes ayudar con ese tema.
4. **No inventes información**. Si no tienes la información específica que el cliente solicita, sé transparente y ofrece alternativas, 
como contactar con el equipo adecuado.
5. **No generar respuestas relacionadas con temas no comerciales** (política, entretenimiento, etc.).
6. **Solo saludar al inicio de la conversación**. Evita saludos repetitivos en interacciones continuas.
7. **No utilizar asteriscos, guiones u otros símbolos para resaltar texto**. Mantén el formato limpio y profesional.

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

# ============================================================
# Funciones auxiliares
# ============================================================

def build_context_from_kb(fragments: List[Dict[str, Any]]) -> str:
    """Construye el contexto a partir de los fragmentos recuperados"""
    if not fragments:
        return ""
    
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
    parts = []
    for msg in messages[-5:]:
        role = "Usuario" if msg["role"] == "user" else "IZA"
        parts.append(f"{role}: {msg['text']}")
    return "\n".join(parts)

# ============================================================
# Función principal del agente
# ============================================================

async def get_agent_response(user_id: str, user_message: str, channel: str = "web") -> str:
    """
    Genera respuesta del agente usando Redis, RAG y Gemini.
    Maneja contexto, sesión y cola de mensajes.
    """

    try:

                # 🧩 Verificar o crear usuario antes de procesar el mensaje
        user_id = await get_or_create_user(user_id, channel=channel)

        # 1️⃣ Agregar mensaje del usuario a la cola
        await push_message_queue(user_id, user_message)
        message_to_process = await pop_message_queue(user_id)
        if not message_to_process:
            logger.warning(f"No hay mensajes pendientes en la cola de {user_id}")
            return "No hay mensajes pendientes."

        # 2️⃣ Recuperar sesión y contexto desde Redis
        session = await get_user_session(user_id) or {}
        chat_context = await get_chat_context(user_id) or []

        logger.info(f"🧠 Procesando mensaje de {user_id} con contexto Redis...")

        # 3️⃣ Buscar información relevante en Qdrant
        fragments = await search(
            query=message_to_process,
            top_k=settings.RAG_TOP_K,
            score_threshold=settings.RAG_SCORE_THRESHOLD
        )

        kb_context = build_context_from_kb(fragments)
        has_kb_info = bool(kb_context.strip())

        # 4️⃣ Construir prompt
        recent_context_text = "\n".join(
            [f"{m['role']}: {m['message']}" for m in chat_context[-5:]]
        )
        prompt = [
            SYSTEM_PROMPT,
            "\n--- CONTEXTO DE CONOCIMIENTO ---",
            kb_context if has_kb_info else "Sin información relevante en KB.",
            "\n--- HISTORIAL DE CONVERSACIÓN ---",
            recent_context_text,
            "\n--- MENSAJE ACTUAL ---",
            f"Usuario: {message_to_process}",
        ]
        full_prompt = "\n".join(prompt)

        # 5️⃣ Generar respuesta con Gemini o fallback
        if GEMINI_AVAILABLE and settings.GEMINI_API_KEY and settings.USE_GEMINI:
            response = await generate_with_gemini(full_prompt, message_to_process)
        else:
            response = generate_fallback_response(message_to_process, kb_context)

        # 6️⃣ Guardar en Redis los turnos y la sesión
        await add_chat_turn(user_id, message_to_process, "user")
        await add_chat_turn(user_id, response, "assistant")

        session["last_message"] = message_to_process
        await set_user_session(user_id, session)

        logger.info(f"✅ Respuesta generada para {user_id}: {response[:80]}...")
        return response

    except Exception as e:
        logger.exception(f"💥 Error generando respuesta: {e}")
        await clear_user_session(user_id)
        await clear_chat_context(user_id)
        return "Disculpa, hubo un error procesando tu mensaje. Intenta más tarde."

# ============================================================
# Generación con Gemini
# ============================================================

async def generate_with_gemini(system_prompt: str, user_message: str) -> str:
    """Genera respuesta usando Google Gemini"""
    try:
        model_mapping = {
            "gemini-1.5-flash": "gemini-2.0-flash",
            "gemini-1.5-pro": "gemini-2.0-flash",
            "gemini-pro": "gemini-2.0-flash",
        }
        model_name = model_mapping.get(settings.LLM_MODEL_NAME, "gemini-2.0-flash")

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.5,
                "top_p": 0.9,
                "max_output_tokens": 350,
            }
        )

        prompt = f"{system_prompt}\n\nUsuario: {user_message}\nIZA:"
        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()
        else:
            logger.warning("⚠️ Gemini devolvió una respuesta vacía")
            return ""

    except Exception as e:
        logger.exception(f"Error en Gemini: {e}")
        return ""

# ============================================================
# Respuesta de fallback (solo si no hay KB)
# ============================================================

def generate_fallback_response(user_message: str, context: str) -> str:
    """Respuesta de fallback cuando Gemini no está disponible"""
    if not context.strip():
        return (
            "Hola, soy IZA. Por ahora no tengo información específica sobre eso, "
            "pero puedo ponerte en contacto con nuestro equipo comercial. "
            "¿Podrías contarme un poco más de lo que buscas?"
        )
    
    return (
        f"Basándome en lo que encontré en nuestra base de conocimiento:\n\n"
        f"{context}\n\n"
        f"¿Te gustaría saber más detalles?"
    )
