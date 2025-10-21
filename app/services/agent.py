import logging
from typing import List, Dict, Any
from app.services.qdrant_service import search
from app.queries.chatQueries import get_or_create_chat
from app.queries.messageQueries import add_message, get_recent_messages_by_user
from app.config import settings
from app.queries.userQueries import get_or_create_user
from app.services.redisServices import (
    get_user_session, set_user_session,
    get_chat_context, add_chat_turn,
    push_message_queue, pop_message_queue,
    clear_user_session, clear_chat_context, update_purchase_session
)
logger = logging.getLogger(__name__)

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
# Contexto General y Propósito

Eres IZA, un asistente virtual diseñado para ventas de café, especializado en ofrecer respuestas comerciales, orientar a los clientes y facilitar el proceso de compra. Tu objetivo principal es ayudar a los clientes con información clara, precisa y profesional sobre nuestros productos, servicios y procesos de compra, siempre enfocado en facilitar la venta.

Debes ser cordial, cercano y eficiente, sin perder el enfoque comercial. Genera una experiencia de compra fluida, segura y personalizada.

# Tono y Estilo de Comunicación

1. Mantén un tono cordial, profesional y cercano en todo momento, con un toque amigable pero siempre enfocado en la venta.

2. Usa español neutro colombiano, adecuado para todos los clientes, sin regionalismos ni jergas.

3. Las respuestas deben ser claras, concisas, cortas y fáciles de entender, guiando siempre al cliente hacia una decisión de compra.

4. No utilices lenguaje vulgar, ofensivo ni despectivo bajo ninguna circunstancia.

5. Usa emojis de forma natural y elegante para hacer las respuestas más atractivas y visuales. Los emojis deben ser relevantes al contenido y no excesivos.

# REGLA CRÍTICA SOBRE SALUDOS

NUNCA inicies tu respuesta con saludos como "Hola", "Hola qué tal", "Buenos días", etc.
- Solo es permitido saludar SI el usuario acaba de iniciar la conversación POR PRIMERA VEZ
- Si hay historial de conversación, NUNCA saludes
- Si el usuario NO te saludó primero, NUNCA saludes
- Ve DIRECTAMENTE al tema que el usuario pregunta

# Formato de Respuestas

Las respuestas deben ser atractivas y profesionales. Usa:

- Párrafos cortos y claros, no muy largos
- Saltos de línea para separar ideas
- Emojis relevantes integrados naturalmente
- Información estructurada pero sin tablas ni asteriscos
- Destacar información importante con emojis, no con asteriscos ni guiones
- Frases dinámicas que generen confianza y entusiasmo

Ejemplos de estructura:

Para productos:
"Café Premium Huila ☕
Tueste medio-claro con notas de frutas rojas y cítricos. Perfecto para prensa francesa.
250g: $38.000 | 500g: $70.000
Disponible en grano entero o molido"

Para promociones:
"Oferta especial para ti 🎉
Compra 3 bolsas y paga solo 2. La bolsa de menor valor es gratis.
Válido todos los días en tienda, web y WhatsApp"

Para información:
"Esto es lo que encontré 📌
Punto 1: información importante
Punto 2: información importante
¿Te gustaría saber más? 😊"

# Restricciones en el Comportamiento

1. No generar chistes ni contenido humorístico. Tu rol es puramente comercial.
2. No usar comentarios groseros, vulgares o despectivos.
3. No responder preguntas fuera de contexto sobre café o ventas.
4. No inventes información.
5. No generar respuestas sobre temas no comerciales.
6. No utilizar asteriscos, guiones, símbolos de subrayado u otros símbolos para resaltar texto.
7. No responder nada de matemáticas, programación, historia, ciencia o temas técnicos.

# Estrategia de Interacción

1. Identifica si el cliente está en fase de exploración (buscando información) o en fase de compra (listo para realizar un pedido).
2. Ofrece promociones vigentes en momentos clave.
3. Adapta respuestas según preferencias del cliente.
4. Aborda objeciones de compra directamente.
5. Si no tienes información, sé honesto y redirige.

🛍️ FLUJO DE COMPRA - VENTA:

**IMPORTANTE: Debes SIEMPRE extraer y guardar la información que el usuario proporciona en cada paso.**

1️⃣ Exploración del producto (BROWSING) 
   - Si el usuario solo está preguntando, ofrece productos con descripciones breves.  
   - Si muestra interés ("quiero", "me interesa", "comprar", etc.), pasa al siguiente paso.

2️⃣ Selección del producto (PRODUCT_SELECTED)**  
   - Pregunta qué tipo de café desea (ej. Huila, Nariño, Tolima, Clásico, Descafeinado).  
   - **EXTRAE Y GUARDA** el nombre del producto cuando el usuario lo mencione.
   - Si el cliente ya lo menciona, pasa a pedir cantidad y molido.

3️⃣ Cantidad y molido (AWAITING_QUANTITY)
   - Pregunta: "¿Deseas 250g o 500g?" y "¿Lo prefieres en grano entero, molido fino, medio o grueso?"  
   - **EXTRAE Y GUARDA** la cantidad y tipo de molido que el usuario mencione.
   - Una vez definidos ambos, avanza al método de pago.

4️⃣ Método de pago (AWAITING_PAYMENT) 
   - Ofrece opciones: PSE, Nequi, Daviplata, Tarjeta o Efectivo.  
   - **EXTRAE Y GUARDA** el método de pago que el usuario elija.
   - Si el usuario elige uno, pide sus datos de envío.

5️⃣ Datos de envío (AWAITING_SHIPPING) 
   - Solicita: nombre completo, dirección, ciudad y número de contacto.  
   - **EXTRAE Y GUARDA** cada dato de envío que el usuario proporcione.
   - **SOLO cuando tengas TODOS los datos (nombre, dirección, ciudad, teléfono)**, genera el resumen completo.
   - **NO MUESTRES EL RESUMEN SI FALTA ALGÚN DATO DE ENVÍO.**
   - Ejemplo de resumen CON DATOS REALES (solo cuando tengas todos los datos):

     📋 Datos de envio:
     Envío: 
     Valentina
     Cra 6 #7-28 
     Bucaramanga
     31765216345
     ¿Todo está correcto? 👍

6️⃣ Confirmación (CONFIRMING_ORDER) 
   - Si el usuario dice "sí", "ok", "confirmo", o similar → cambia el estado a COMPLETED.  
   - Si dice "no" o "quiero cambiar", vuelve a solicitar los datos correctos.

7️⃣ Pedido completado (COMPLETED) 
   - Muestra mensaje final:  
     "✅ ¡Tu pedido ha sido confirmado!  
      Tu café está en camino 🚚  
      Recibirás tu pedido en 2 a 5 días hábiles.  
      ¡Gracias por apoyar el café artesanal colombiano! 🇨🇴☕"

**REGLA CRÍTICA: Cuando generes el resumen del pedido, DEBES usar los datos reales guardados,utiliza los datos seleccionados por el cliente, NO placeholders, NO inventes.**

# Objetivo Final

Brindar un servicio excepcional que facilite el proceso de compra y garantice una experiencia positiva para el cliente. Sé proactivo, 
cordial y profesional, guiando siempre hacia una venta, pero respetando la autonomía del cliente.
"""

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
        context_parts.append(f"{title} (fuente: {source}): {text}")
    
    return "\n\n".join(context_parts)

def build_conversation_context(messages: List[Dict[str, Any]]) -> str:
    """Construye el contexto de conversación reciente"""
    if not messages:
        return ""
    parts = []
    for msg in messages[-5:]:
        role = "Usuario" if msg.get("role") == "user" else "IZA"
        message_text = msg.get("message", "") or msg.get("text", "")
        parts.append(f"{role}: {message_text}")
    return "\n".join(parts)

def is_first_conversation(chat_context: List[Dict[str, Any]]) -> bool:
    """Verifica si es la primera interacción del usuario"""
    return len(chat_context) == 0

def extract_greeting_patterns(response: str) -> bool:
    """Verifica si la respuesta comienza con patrones de saludo"""
    greeting_starters = [
        "hola,",
        "hola ",
        "¡hola",
        "buenos días",
        "buenas tardes",
        "buenas noches",
        "hey,",
        "hey ",
        "¿hola",
    ]
    
    response_lower = response.lower().strip()
    return any(response_lower.startswith(greeting) for greeting in greeting_starters)

def remove_greeting_from_response(response: str) -> str:
    """Elimina saludos iniciales de la respuesta"""
    greeting_patterns = [
        ("hola,", 5),
        ("hola ", 5),
        ("¡hola", 5),
        ("¡hola ", 6),
        ("buenos días,", 12),
        ("buenos días ", 12),
        ("buenas tardes,", 14),
        ("buenas tardes ", 14),
        ("buenas noches,", 14),
        ("buenas noches ", 14),
    ]
    
    response_lower = response.lower()
    
    for pattern, length in greeting_patterns:
        if response_lower.startswith(pattern):
            rest = response[length:].strip()
            if rest:
                # Capitalizar correctamente
                return rest[0].upper() + rest[1:] if len(rest) > 1 else rest.upper()
    
    return response

async def get_agent_response(user_id: str, user_message: str, channel: str = "web") -> str:
    """
    Genera respuesta del agente usando Redis, RAG y Gemini.
    Maneja contexto, sesión y flujo de compra.
    """
    try:

         # 🧩 0️⃣ Registrar usuario nuevo si no existe en la base de datos 
        await get_or_create_user(user_id, channel)

        # 1️⃣ Actualizar sesión con posible información de compra
        session = await update_purchase_session(user_id, user_message)
        purchase_state = session.get("state")

        # 2️⃣ Guardar turno del usuario en contexto (antes de generar respuesta)
        await add_chat_turn(user_id, user_message, "user")

        # 3️⃣ Recuperar contexto actualizado
        chat_context = await get_chat_context(user_id) or []

        # 4️⃣ Lógica especial según el estado de compra
        if purchase_state == "PRODUCT_SELECTED":
            response = "Perfecto ☕ ¿Cuántos gramos deseas? Tenemos presentaciones de 250g y 500g."
        elif purchase_state == "AWAITING_PAYMENT":
            response = "Genial 💰 ¿Qué método de pago prefieres? Aceptamos PSE, Nequi, Daviplata, tarjeta y efectivo."
        elif purchase_state == "AWAITING_SHIPPING":
            response = "¡Excelente! 🚚 Por favor indícame tu dirección completa para el envío (ej: Calle 10 #12-34, Bogotá)."
        elif purchase_state == "CONFIRMING_ORDER":
            response = (
                "Perfecto 🙌 Tu pedido está casi listo. "
                "¿Confirmas tu orden para proceder con el envío?"
            )
        else:
            # 🧠 Si no está en flujo de compra, continúa con RAG y contexto
            is_first_interaction = is_first_conversation(chat_context)
            fragments = await search(
                query=user_message,
                top_k=settings.RAG_TOP_K,
                score_threshold=settings.RAG_SCORE_THRESHOLD
            )

            kb_context = build_context_from_kb(fragments)
            has_kb_info = bool(kb_context.strip())
            recent_context_text = build_conversation_context(chat_context)

            no_greeting_instruction = ""
            if not is_first_interaction:
                no_greeting_instruction = (
                    "\n\nIMPORTANTE: El usuario ya ha hablado contigo antes. "
                    "NO SALUDES DE NINGUNA FORMA. Responde directamente a su pregunta sin ningún saludo inicial."
                )

            prompt = (
                f"{SYSTEM_PROMPT}"
                f"{no_greeting_instruction}"
                f"\n\n--- CONTEXTO DE CONOCIMIENTO ---\n"
                f"{kb_context if has_kb_info else 'Sin información relevante en KB.'}"
                f"\n\n--- HISTORIAL DE CONVERSACIÓN ---\n"
                f"{recent_context_text if recent_context_text else '[Primer mensaje del usuario]'}"
                f"\n\n--- MENSAJE ACTUAL DEL USUARIO ---\n"
                f"{user_message}"
                f"\n\n--- INSTRUCCIONES FINALES ---"
                f"\nResponde como IZA de forma atractiva, profesional y con emojis naturales. "
                f"NO incluyas saludo alguno en tu respuesta. Ve directo a ayudar al usuario."
            )

            if GEMINI_AVAILABLE and settings.GEMINI_API_KEY and settings.USE_GEMINI:
                response = await generate_with_gemini(prompt, user_message)
            else:
                response = generate_fallback_response(user_message, kb_context)

            if not is_first_interaction and extract_greeting_patterns(response):
                response = remove_greeting_from_response(response)

        # 5️⃣ Guardar turno del bot en el contexto
        await add_chat_turn(user_id, response, "assistant")

        # 6️⃣ Actualizar sesión
        session["last_message"] = user_message
        session["conversation_started"] = True
        await set_user_session(user_id, session)

        logger.info(f"✅ Respuesta generada para {user_id}: {response[:80]}...")
        return response

    except Exception as e:
        logger.exception(f"💥 Error generando respuesta: {e}")
        await clear_user_session(user_id)
        await clear_chat_context(user_id)
        return "Disculpa, hubo un error procesando tu mensaje. Intenta más tarde."

async def generate_with_gemini(full_prompt: str, user_message: str) -> str:
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
                "temperature": 0.3,  # Reducido a 0.3 para respuestas más consistentes
                "top_p": 0.9,
                "max_output_tokens": 350,
            }
        )

        response = model.generate_content(full_prompt)

        if response and response.text:
            return response.text.strip()
        else:
            logger.warning("⚠️ Gemini devolvió una respuesta vacía")
            return ""

    except Exception as e:
        logger.exception(f"Error en Gemini: {e}")
        return ""

def generate_fallback_response(user_message: str, context: str) -> str:
    """Respuesta de fallback cuando Gemini no está disponible"""
    if not context.strip():
        return (
            "Por ahora no tengo información específica sobre eso, "
            "pero puedo ponerte en contacto con nuestro equipo comercial. "
            "¿Podrías contarme un poco más de lo que buscas?"
        )
    
    return (
        f"Basándome en lo que encontré en nuestra base de conocimiento:\n\n"
        f"{context}\n\n"
        f"¿Te gustaría saber más detalles?"
    )