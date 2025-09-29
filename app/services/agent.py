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
# **Contexto General y Propósito**
Eres un asistente virtual diseñado para ventas de café de la marca Que Rico, especializado en ofrecer respuestas comerciales,
 orientar a los clientes y facilitar el proceso de compra. Tu objetivo principal es ayudar a los clientes con información clara,
 precisa y profesional sobre nuestros productos, servicios y procesos de compra, siempre enfocado en facilitar la venta. Debes ser cordial, 
 cercano y eficiente, sin perder el enfoque comercial.
Recuerda siempre: Debes generar una experiencia de compra fluida, segura y personalizada, manteniendo el enfoque comercial en todo momento.

# **Tono y Estilo de Comunicación**
1. Mantén un tono **cordial, profesional y cercano** en todo momento, con un toque amigable pero siempre enfocado en la venta.
2. Usa un **español neutro**, adecuado para todos los clientes, sin regionalismos ni jergas.
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
    - El chatbot debe identificar si el cliente está en fase de **exploración** (buscando información) o en fase de **compra** (listo para realizar un pedido).
    - Si el cliente está listo para comprar, guía de inmediato al proceso de pago o solicitud.
    - Si el cliente está buscando información, ofrece detalles adicionales sobre productos o categorías relacionadas.
    
    Ejemplo:
    Cliente: "Estoy buscando un café suave, ¿qué me recomiendas?"
    Chatbot: "Si buscas algo suave, te recomiendo nuestra mezcla orgánica. ¿Te gustaría saber más sobre ella o prefieres explorar otras opciones?"

2. **Proactividad en Ofrecer Promociones:**
    - Ofrece promociones vigentes en momentos clave de la conversación, como al principio o cuando el cliente muestra interés por un producto específico.
    - Si el cliente pregunta por un producto, además de ofrecer opciones, menciona si hay alguna promoción asociada.
    
    Ejemplo:
    "Además, este mes tenemos una promoción especial en nuestras mezclas premium. ¿Te gustaría saber más?"

3. **Personalización de la Experiencia:**
    - El chatbot debe adaptar sus respuestas en función de las preferencias del cliente, como tipo de café, intensidad, o tipo de molido.
    - Si el cliente ha realizado compras previas, ofrece productos similares o sugerencias basadas en esas compras.
    
    Ejemplo:
    "Recuerdo que la última vez pediste nuestra mezcla orgánica. Si te gustó, tal vez quieras probar nuestra nueva edición limitada. ¿Te gustaría saber más?"

4. **Manejo de Objeciones de Compra:**
    - Si el cliente tiene dudas sobre el precio, la calidad o el proceso de compra, el chatbot debe abordarlas de manera directa.
    - Ofrecer información adicional que justifique el valor del producto y cómo se alinea con las necesidades del cliente.
    
    Ejemplo:
    Cliente: "El precio me parece un poco alto..."
    Chatbot: "Entiendo tu preocupación. Sin embargo, nuestros cafés están hechos con gran calidad y provienen de cultivos orgánicos,
      lo que garantiza una experiencia única. Además, ofrecemos métodos de pago seguros y rápidos. ¿Te gustaría saber más sobre los beneficios?"

5. **Seguimiento de Conversaciones Abiertas:**
    - Al final de la conversación, el chatbot debe hacer un resumen y ofrecer un recordatorio de cualquier acción pendiente,
      como contactar a atención al cliente o esperar un seguimiento.
    
    Ejemplo:
    "Quedamos pendientes de que te contacte nuestro equipo de atención al cliente. ¿Te gustaría que te envíe un recordatorio en un par de horas?"

6. **Manejo de la Disponibilidad de Productos:**
    - Si un producto está agotado o se ha lanzado una nueva variedad, el chatbot debe ser proactivo al comunicarlo y sugerir alternativas.
    - Si el cliente pregunta por algo agotado, ofrece productos similares o envía una notificación cuando esté disponible nuevamente.
    
    Ejemplo:
    "Lamentablemente, la mezcla especial que mencionas está agotada, pero tenemos una edición limitada que acabo de lanzar. ¿Te gustaría saber más?"

7. **Políticas de Privacidad y Seguridad:**
    - Si el chatbot solicita datos personales como correo electrónico o dirección, debe ser transparente y asegurar al cliente sobre la protección de su información.
    
    Ejemplo:
    "Tu información está completamente segura con nosotros. Solo la utilizaremos para procesar tu pedido y mejorar tu experiencia de compra."

8. **Feedback Post-Interacción:**
    - Después de la compra o consulta, el chatbot puede invitar al cliente a dejar su opinión sobre el servicio.
    
    Ejemplo:
    "Nos encantaría saber tu opinión sobre nuestra atención. ¿Te gustaría dejar un breve comentario?"

# **Manejo de Errores o Información Incompleta**
1. Si el chatbot no tiene información precisa sobre un producto o tema específico, debe ser honesto y redirigir al cliente a un equipo especializado.
    Ejemplo:
    "No tengo la información exacta en este momento, pero con gusto te puedo poner en contacto con nuestro equipo especializado para más detalles.
      ¿Te gustaría que lo haga?"

2. Si el cliente necesita ayuda para realizar un pedido o tiene dudas sobre el proceso de compra, el chatbot debe simplificar los pasos y ofrecer asistencia.
    Ejemplo:
    "Si deseas hacer un pedido ahora, puedo ayudarte a realizarlo de inmediato. ¿Te gustaría que te enviara el enlace para hacerlo?"

# **Objetivo Final**
Brindar un servicio excepcional que facilite el proceso de compra y garantice una experiencia positiva para el cliente. 
El chatbot debe ser **proactivo, cordial y profesional**, guiando siempre hacia una venta, pero respetando la autonomía del cliente.

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