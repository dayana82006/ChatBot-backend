import logging
from typing import List, Dict, Any, Optional
from app.services.qdrant_service import search
from app.queries.chatQueries import get_or_create_chat
from app.queries.messageQueries import add_message
from app.config import settings
from app.services.redisServices import (
    get_user_session, set_user_session,
    get_chat_context, add_chat_turn,
    push_message_queue, pop_message_queue,
    clear_user_session, clear_chat_context
)
from app.queries.orderService import (
    get_or_create_pending_order,
    add_or_update_order_detail,
    update_order_status,
    get_order_summary
)

logger = logging.getLogger(__name__)

# ======================================================
# Configuración de Gemini
# ======================================================
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("✅ Gemini API configurada correctamente")
except ImportError as e:
    GEMINI_AVAILABLE = False
    logger.warning(f"⚠️ Gemini no disponible: {e}")

# ======================================================
# Prompt base del sistema
# ======================================================

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


# ======================================================
# Funciones auxiliares
# ======================================================

def detect_intent(text: str) -> str:
    """Detecta intención general del usuario"""
    text = text.lower()
    if any(k in text for k in ["pedido", "ordenar", "comprar", "quiero café", "hacer pedido"]):
        return "hacer_pedido"
    if any(k in text for k in ["confirmo", "sí", "ok", "confirmar"]):
        return "confirmar_pedido"
    if any(k in text for k in ["huila", "nariño", "tolima", "clásico", "descafeinado"]):
        return "seleccionar_producto"
    if any(k in text for k in ["unidad", "bolsa", "quiero", "libras", "cantidad"]):
        return "seleccionar_cantidad"
    return "general"

def extraer_numero(text: str) -> int:
    import re
    m = re.search(r"\d+", text)
    return int(m.group()) if m else 1

def obtener_producto_desde_texto(text: str):
    productos = {
        "huila": (1, 18000),
        "nariño": (2, 19000),
        "tolima": (3, 18500),
        "clásico": (4, 15000),
        "descafeinado": (5, 20000)
    }
    for k, v in productos.items():
        if k in text:
            return v
    return None

def generar_resumen(detalles: List[Dict[str, Any]]) -> str:
    texto = "📋 Resumen de tu pedido:\n\n"
    total = 0
    for d in detalles:
        subtotal = d["cantidad"] * float(d["precio_unitario"])
        texto += f"- Producto #{d['producto_id']}: {d['cantidad']} x ${d['precio_unitario']} = ${subtotal}\n"
        total += subtotal
    texto += f"\n💰 Total: ${total}\n¿Deseas confirmar tu pedido? (sí / no)"
    return texto

    # otras funciones auxiliares

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


# ======================================================
# 🛒 FLUJO DE PEDIDO
# ======================================================

def handle_order_flow(user_id: str, intent: str, user_message: str) -> str:
    """
    Controla el flujo completo de pedidos paso a paso.
    """
    pedido_id = get_or_create_pending_order(user_id)

    if intent == "hacer_pedido":
        update_order_status(pedido_id, "BROWSING")
        return "Perfecto ☕ ¿Qué tipo de café deseas? Tenemos Huila, Nariño, Tolima, Clásico y Descafeinado."

    elif intent == "seleccionar_producto":
        producto = obtener_producto_desde_texto(user_message)
        if producto:
            producto_id, precio = producto
            add_or_update_order_detail(pedido_id, producto_id, cantidad=1, precio_unitario=precio)
            update_order_status(pedido_id, "AWAITING_QUANTITY")
            return f"Excelente elección 😋 ¿Cuántas unidades deseas?"
        else:
            return "No entendí qué tipo de café deseas. ¿Podrías repetirlo?"

    elif intent == "seleccionar_cantidad":
        cantidad = extraer_numero(user_message)
        add_or_update_order_detail(pedido_id, producto_id=None, cantidad=cantidad, precio_unitario=None)       
        update_order_status(pedido_id, "AWAITING_CONFIRMATION")
        return f"Perfecto, has pedido {cantidad} unidades. ¿Deseas ver el resumen antes de confirmar?"

    elif intent == "confirmar_pedido":
        update_order_status(pedido_id, "COMPLETED")
        detalles = get_order_summary(pedido_id)
        return generar_resumen(detalles) + "\n\n✅ ¡Tu pedido ha sido confirmado! 🚚"

    else:
        return "Puedo ayudarte con tu pedido ☕. ¿Deseas comenzar?"


# ======================================================
# Lógica principal
# ======================================================
async def get_agent_response(
    user_id: str,
    user_message: str,
    channel: str = "web",
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
    ) -> str:
    try:
        # 1️⃣ Agregar mensaje del usuario
        await push_message_queue(user_id, user_message)
        message_to_process = await pop_message_queue(user_id) or user_message

        # 2️⃣ Recuperar sesión y contexto
        session = await get_user_session(user_id) or {}
        chat_context = await get_chat_context(user_id) or []

        logger.info(f"🧠 Procesando mensaje de {user_id} con contexto Redis...")

        # 3️⃣ Determinar si es la primera conversación
        is_first_interaction = is_first_conversation(chat_context)
        logger.info(f"Primera interacción: {is_first_interaction}")

        # 4️⃣ Buscar información en Qdrant
        fragments = await search(
            query=message_to_process,
            top_k=settings.RAG_TOP_K,
            score_threshold=settings.RAG_SCORE_THRESHOLD
 )
        kb_context = build_context_from_kb(fragments)
        has_kb_info = bool(kb_context.strip())

        # 5️⃣ Construir contexto conversacional
        recent_context_text = build_conversation_context(chat_context)

        # 6️⃣ Evitar saludos innecesarios
        no_greeting_instruction = ""
        if not is_first_interaction:
            no_greeting_instruction = (
                "\n\nIMPORTANTE: El usuario ya ha hablado contigo antes. "
                "NO SALUDES DE NINGUNA FORMA. Responde directamente sin saludo."
            )

        # 7️⃣ Construir prompt
        prompt = (
            f"{SYSTEM_PROMPT}"
            f"{no_greeting_instruction}"
            f"\n\n--- CONTEXTO DE CONOCIMIENTO ---\n"
            f"{kb_context if has_kb_info else 'Sin información relevante en KB.'}"
            f"\n\n--- HISTORIAL DE CONVERSACIÓN ---\n"
            f"{recent_context_text if recent_context_text else '[Primer mensaje del usuario]'}"
            f"\n\n--- MENSAJE ACTUAL DEL USUARIO ---\n"
            f"{message_to_process}"
          )

        # 🔍 Detectar intención
        intent = detect_intent(user_message)

            # 🛒 Manejar flujo de pedido
        if intent in ["hacer_pedido", "seleccionar_producto", "seleccionar_cantidad", "confirmar_pedido"]:
            order_response = handle_order_flow(user_id, intent, user_message)
            await add_chat_turn(user_id, order_response, "assistant")
            return order_response


        # 8️⃣ Generar respuesta (Gemini o fallback)
        if GEMINI_AVAILABLE and settings.GEMINI_API_KEY and settings.USE_GEMINI:
            response = await generate_with_gemini(prompt, message_to_process)
        else:
            response = generate_fallback_response(message_to_process, kb_context)

        # 9️⃣ Limpiar saludos
        if not is_first_interaction and extract_greeting_patterns(response):
            response = remove_greeting_from_response(response)

        # 🔟 Guardar en MySQL
        try:
            chat_id = get_or_create_chat(
                user_id=user_id,
                channel=channel,
                name=name,
                email=email,
                phone=phone
            )
            add_message(chat_id, "user", user_message)
            add_message(chat_id, "assistant", response)
        except Exception as db_error:
            logger.error(f"❌ Error guardando en MySQL: {db_error}")

        # 1️⃣1️⃣ Guardar en Redis
        await add_chat_turn(user_id, user_message, "user")
        await add_chat_turn(user_id, response, "assistant")
        session["last_message"] = user_message
        session["conversation_started"] = True
        await set_user_session(user_id, session)

        logger.info(f"✅ Respuesta generada para {user_id}")
        return response

    except Exception as e:
        logger.exception(f"💥 Error generando respuesta: {e}")
        if "corrupt" in str(e).lower() or "decode" in str(e).lower():
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

        response =  model.generate_content(full_prompt)

        if response and response.text:
            return response.text.strip()
        else:
            logger.warning("⚠️ Gemini devolvió una respuesta vacía")
            return ""

    except Exception as e:
        logger.exception(f"Error en Gemini: {e}")
        return ""

def generate_fallback_response(user_message: str, context: str) -> str:
    if not context.strip():
        return (
            "Puedo ayudarte con tu pedido ☕. "
            "Cuéntame qué tipo de café buscas: Huila, Nariño, Tolima, Clásico o Descafeinado. "
            "Te guiaré paso a paso para realizar tu compra fácilmente. 🚀"
        )
    
    return (
        f"Esto es lo que encontré sobre eso 📖\n\n{context}\n\n"
        "¿Te gustaría que te ayude a elegir el café ideal para ti? ☕"
    )
