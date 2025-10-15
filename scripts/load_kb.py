import sys
import os
import asyncio
import uuid
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import upsert_documents, ensure_collection, get_collection_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KB_DOCUMENTS = [
    # ==================== CATÁLOGO COMPLETO ====================
    {
         "id": str(uuid.uuid4()),
        "text": """📖 Catálogo Completo Café:

    🌟 LÍNEA PREMIUM SINGLE-ORIGIN:
    • ☕ Café Premium Huila: 250g $38.000 / 500g $70.000
    Tueste medio-claro, sabor frutal con notas cítricas y frutas rojas. Altitud 1600-1800 msnm.
    
    • 🌿 Café Nariño Orgánico (Certificado): 250g $42.000 / 500g $78.000
    Tueste claro, notas florales y miel. Proceso natural sin químicos.
    
    • 💪 Café Tolima Intenso: 250g $35.000 / 500g $65.000
    Tueste oscuro, ideal para espresso. Chocolate amargo y frutos secos.
    
    • 🌴 Café Sierra Nevada: 250g $36.000 / 500g $67.000
    Tueste medio, sabor dulce con panela y frutas tropicales.

    🏡 LÍNEA CLÁSICA:
    • ☕ Café Clásico: 250g $25.000 / 500g $45.000
    Blend suave 100% arábica. Notas de chocolate, caramelo y nuez.
    
    • 🌰 Café Antioquia Reserva Familiar: 250g $33.000 / 500g $60.000
    Blend de pequeños productores. Cacao, azúcar morena y nueces tostadas.
    
    • 😴 Café Descafeinado: 250g $30.000 / 500g $55.000
    Proceso suizo sin químicos. Conserva 98% del sabor original.

    💎 EDICIÓN LIMITADA:
    • ✨ Café Edición Especial: 250g $95.000
    Micro-lote mensual, solo 50 bolsas. Incluye ficha de cata.

    🧊 FORMATO LISTO PARA TOMAR:
    • 🧋 Cold Brew (Café Frío): 350ml $12.000 / 1L $30.000
    100% natural sin azúcar. Elaborado con café Huila.
    
    • ♻️ Cápsulas Nespresso: 10 unidades $22.000 / 30 unidades $60.000
    Compatibles, compostables y biodegradables.

    🍫 COMPLEMENTOS:
    • 🍫 Chocolate Artesanal: 100g $15.000
    70% cacao con granos de café molido. Hecho en Santander.

    📦 Todos los cafés disponibles en grano entero o molido (fino, medio, grueso).""",
            "payload": {
                "title": "Información de catalogo",
                "source": "catalog",
                "lang": "es",
                "tags": ["catalogo", "contacto", "whatsapp",  "telefono", "direccion"],
                "category": "contacto"
            }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "🕒 Horarios de atención Café Que Rico: Tienda física: lunes a viernes de 9:00 AM a 7:00 PM, sábados de 10:00 AM a 5:00 PM, domingos cerrado. 💬 Atención virtual con IZA (asistente automático): 24/7. 📞 Atención humana por WhatsApp y teléfono: lunes a viernes de 8:00 AM a 6:00 PM, sábados de 9:00 AM a 1:00 PM.",
        "payload": {
            "title": "Horarios de Atención",
            "source": "contact",
            "lang": "es",
            "tags": ["horarios", "atencion", "disponibilidad"],
            "category": "contacto"
        }
    },

    # ==================== 🧠 PREPARACIÓN Y CONSEJOS ====================
    {
        "id": str(uuid.uuid4()),
        "text": "📋 Guía de preparación de café: ☕ PRENSA FRANCESA: 30g de café molido grueso por cada 500ml de agua a 92-96°C, ⏳ tiempo de infusión 4 minutos. 🔹 V60 O CHEMEX: 15g de café molido medio por cada 250ml de agua a 90-94°C, tiempo total de preparación 2:30 a 3:00 minutos. ⚡ ESPRESSO: 18-20g de café molido fino, extracción 25-30 segundos. 💧 CAFETERA DE GOTEO: 60g de café molido medio por litro de agua.",
        "payload": {
            "title": "Guía de Preparación",
            "source": "info",
            "lang": "es",
            "tags": ["preparacion", "metodos", "recetas", "barista"],
            "category": "educacion"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "🧺 Consejos de conservación del café: Guarda el café en un lugar fresco 🌬️ y seco, alejado de la luz ☀️ y olores fuertes. Usa un recipiente hermético 🔒. ❌ No refrigeres ni congeles. Consume dentro del primer mes para mejor sabor.",
        "payload": {
            "title": "Conservación del Café",
            "source": "info",
            "lang": "es",
            "tags": ["conservacion", "almacenamiento", "frescura", "cuidados"],
            "category": "educacion"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "🍰 Recomendaciones de maridaje: El Café Clásico combina bien con pan dulce 🍩 y postres de chocolate 🍫. El Premium Huila es ideal con frutas frescas 🍓. El Tolima Intenso acompaña chocolate amargo 🍪. El Nariño Orgánico va perfecto con miel 🍯. Nuestro chocolate artesanal es el maridaje ideal para cualquier café ☕.",
        "payload": {
            "title": "Maridaje con Café",
            "source": "info",
            "lang": "es",
            "tags": ["maridaje", "acompañamiento", "postres"],
            "category": "educacion"
        }
    },

    # ==================== ❓ PREGUNTAS FRECUENTES ====================
    {
        "id": str(uuid.uuid4()),
        "text": "🌍 ¿Hacen envíos internacionales? Actualmente Café Que Rico solo realiza envíos dentro de 🇨🇴 Colombia. Estamos trabajando para expandirnos a Latinoamérica 🌎 próximamente.",
        "payload": {
            "title": "Envíos Internacionales",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "internacional", "envios", "exterior"],
            "category": "faq"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "♻️ ¿Puedo cambiar o cancelar mi pedido? Sí, siempre que no haya sido despachado 📦. Si ya fue enviado, aplica nuestra política de devolución estándar de 7 días 📅. Contáctanos por WhatsApp 📱 o teléfono.",
        "payload": {
            "title": "Cambios y Cancelaciones",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "cancelacion", "cambios", "modificar"],
            "category": "faq"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "🤝 ¿El café de Que Rico es de comercio justo? ¡Sí! Trabajamos con pequeños productores 👩‍🌾👨‍🌾, pagando precio justo 💰 y apoyando educación y desarrollo local 📚🏡.",
        "payload": {
            "title": "Comercio Justo",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "comercio-justo", "etico", "social", "sostenible"],
            "category": "faq"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "🕰️ ¿Cuánto tiempo dura el café después de abierto? Mantiene su mejor sabor durante 1 mes si lo guardas correctamente 🔒. Después puede perder aroma, pero sigue siendo consumible ☕.",
        "payload": {
            "title": "Duración del Café",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "duracion", "caducidad", "frescura"],
            "category": "faq"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "👋 ¿Qué café me recomiendan si soy principiante? Prueba el Café Clásico o el Sierra Nevada 🌄. Son suaves y equilibrados. También puedes probar el Combo Cafetero 🎁 con prensa francesa y guía de preparación.",
        "payload": {
            "title": "Recomendación para Principiantes",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "principiante", "recomendacion", "basico"],
            "category": "faq"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Ofrecen café para empresas u oficinas? Sí, ofrecemos servicio especial para empresas y oficinas con descuentos por volumen (10% en compras sobre $150.000 y 15% sobre $300.000). Podemos crear planes personalizados de suministro mensual con facturación y entrega programada. Contacta a nuestro equipo comercial para más información y cotizaciones especiales.",
        "payload": {
            "title": "Café para Empresas",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "empresas", "oficinas", "corporativo", "volumen"],
            "category": "faq"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Tienen café en grano para máquinas superautomáticas? Sí, todos nuestros cafés están disponibles en grano entero, perfectos para máquinas superautomáticas. Te recomendamos especialmente el Café Clásico o el Tolima Intenso si prefieres espressos más robustos. El grano entero mantiene mejor la frescura y las máquinas superautomáticas muelen justo antes de preparar, garantizando el mejor sabor.",
        "payload": {
            "title": "Café para Máquinas Automáticas",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "maquinas", "automaticas", "grano"],
            "category": "faq"
        }
    },
    # ==================== PRODUCTOS INDIVIDUALES DETALLADOS ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Café Clásico Que Rico: Blend suave 100% arábica colombiano con tueste medio. Perfil de sabor equilibrado con notas de chocolate, caramelo y nuez. Ideal para prensa francesa o cafetera de filtro. Cuerpo medio y acidez suave. Precio: 250g $25.000 / 500g $45.000. Disponible en grano entero, molido fino, medio o grueso.",
        "payload": {
            "title": "Café Clásico",
            "source": "products",
            "lang": "es",
            "tags": ["clasico", "blend", "chocolate", "tueste-medio"],
            "category": "productos",
            "precio_min": 25000,
            "precio_max": 45000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Premium Huila Que Rico: Single-origin de la región de Huila, Colombia. Tueste medio-claro para resaltar sus cualidades. Perfil frutal con notas de cítricos, frutas rojas y acidez brillante. Cuerpo medio. Cultivado entre 1600-1800 msnm, proceso lavado. Precio: 250g $38.000 / 500g $70.000. Disponible en grano entero o molido medio.",
        "payload": {
            "title": "Café Premium Huila",
            "source": "products",
            "lang": "es",
            "tags": ["huila", "premium", "frutal", "single-origin"],
            "category": "productos",
            "precio_min": 38000,
            "precio_max": 70000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Nariño Orgánico Que Rico: Certificado orgánico internacional. Single-origin de Nariño con tueste claro. Perfil delicado con notas florales, miel y cítricos dulces. Proceso natural sin químicos ni pesticidas. Ideal para métodos de preparación suaves. Precio: 250g $42.000 / 500g $78.000. Disponible en grano entero, molido fino o medio.",
        "payload": {
            "title": "Café Nariño Orgánico",
            "source": "products",
            "lang": "es",
            "tags": ["narino", "organico", "certificado", "flores"],
            "category": "productos",
            "precio_min": 42000,
            "precio_max": 78000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Tolima Intenso Que Rico: Single-origin de Tolima con tueste oscuro. Perfil robusto con notas de chocolate amargo y frutos secos. Cuerpo fuerte, ideal para espresso y métodos de presión. Excelente crema y persistencia. Precio: 250g $35.000 / 500g $65.000. Disponible en grano entero o molido fino para espresso.",
        "payload": {
            "title": "Café Tolima Intenso",
            "source": "products",
            "lang": "es",
            "tags": ["tolima", "intenso", "espresso", "chocolate"],
            "category": "productos",
            "precio_min": 35000,
            "precio_max": 65000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Sierra Nevada Que Rico: Origen Sierra Nevada de Santa Marta, 100% arábica. Tueste medio que resalta su dulzor natural. Sabor a panela, frutas tropicales y final limpio. Cultivado a 1500 msnm, proceso lavado. Precio: 250g $36.000 / 500g $67.000. Disponible en grano entero o molido medio.",
        "payload": {
            "title": "Café Sierra Nevada",
            "source": "products",
            "lang": "es",
            "tags": ["sierra-nevada", "dulce", "panela", "tropical"],
            "category": "productos",
            "precio_min": 36000,
            "precio_max": 67000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Antioquia Reserva Familiar Que Rico: Blend especial de pequeños productores de Antioquia. Tueste medio-oscuro. Perfil de cacao, azúcar morena y nueces tostadas. Cuerpo cremoso y persistente. Apoya a familias caficultoras locales. Precio: 250g $33.000 / 500g $60.000. Disponible en grano entero o molido fino.",
        "payload": {
            "title": "Café Antioquia Reserva",
            "source": "products",
            "lang": "es",
            "tags": ["antioquia", "blend", "cacao", "cremoso"],
            "category": "productos",
            "precio_min": 33000,
            "precio_max": 60000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Descafeinado Que Rico: Proceso suizo de descafeinado sin químicos. Blend suave con tueste medio que conserva 98% del sabor original. Notas de caramelo y avellana. Perfecto para disfrutar en cualquier momento sin afectar el sueño. Precio: 250g $30.000 / 500g $55.000. Solo disponible molido medio.",
        "payload": {
            "title": "Café Descafeinado",
            "source": "products",
            "lang": "es",
            "tags": ["descafeinado", "sin-cafeina", "suizo"],
            "category": "productos",
            "precio_min": 30000,
            "precio_max": 55000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Edición Especial Que Rico: Micro-lote limitado que cambia mensualmente. Incluye cafés de competencia, variedades geisha y perfiles únicos. Tueste personalizado según el perfil del grano. Solo 50 bolsas por mes. Incluye ficha técnica de cata con información del origen, perfil sensorial y sugerencias de preparación. Precio: 250g $95.000. Solo en grano entero.",
        "payload": {
            "title": "Edición Especial Limitada",
            "source": "products",
            "lang": "es",
            "tags": ["especial", "limitado", "geisha", "competencia"],
            "category": "productos",
            "precio_min": 95000,
            "precio_max": 95000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Cold Brew Que Rico (Café Frío Listo): Café frío listo para tomar, 100% natural sin azúcar añadida. Elaborado con café Premium Huila de tueste medio mediante proceso de extracción en frío de 12 horas. Perfil suave con notas de chocolate, frutas y vainilla. Mantener refrigerado. Consumir dentro de 7 días después de abrir. Precio: 350ml $12.000 / 1L $30.000.",
        "payload": {
            "title": "Cold Brew",
            "source": "products",
            "lang": "es",
            "tags": ["cold-brew", "frio", "listo", "natural"],
            "category": "productos",
            "precio_min": 12000,
            "precio_max": 30000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Cápsulas Café Que Rico para Nespresso: Cápsulas compatibles con máquinas Nespresso. Mezcla especial de café colombiano tueste medio con notas de chocolate y caramelo. Intensidad media-alta. 100% compostables y biodegradables, amigables con el medio ambiente. Precio: Caja de 10 cápsulas $22.000 / Caja de 30 cápsulas $60.000.",
        "payload": {
            "title": "Cápsulas Nespresso",
            "source": "products",
            "lang": "es",
            "tags": ["capsulas", "nespresso", "compostable", "compatible"],
            "category": "productos",
            "precio_min": 22000,
            "precio_max": 60000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Chocolate Artesanal Que Rico: Tableta de chocolate 70% cacao con granos de café molido. Elaboración artesanal en Santander. Ingredientes: cacao, azúcar, manteca de cacao y café molido. Maridaje perfecto para acompañar tu café. Peso: 100g. Precio: $15.000.",
        "payload": {
            "title": "Chocolate Artesanal",
            "source": "products",
            "lang": "es",
            "tags": ["chocolate", "artesanal", "cacao", "santander"],
            "category": "productos",
            "precio_min": 15000,
            "precio_max": 15000
        }
    },

    # ==================== OPCIONES DE MOLIDO ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Tipos de molido disponibles en Café Que Rico: MOLIDO FINO (ideal para máquinas espresso y cafeteras italianas tipo moka), MOLIDO MEDIO (perfecto para cafeteras de goteo, V60, Chemex y métodos de vertido), MOLIDO GRUESO (recomendado para prensa francesa y cold brew). También disponible en GRANO ENTERO para quienes prefieren moler en casa. El servicio de molido no tiene costo adicional.",
        "payload": {
            "title": "Tipos de molido",
            "source": "info",
            "lang": "es",
            "tags": ["molido", "preparacion", "fino", "medio", "grueso"],
            "category": "productos"
        }
    },

    # ==================== PROMOCIONES ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Promoción 3x2 Café Que Rico: Compra 3 bolsas de café de cualquier variedad (pueden ser diferentes) y paga solo 2. La bolsa de menor valor es gratis. Válida todos los días sin excepción. No acumulable con otros descuentos. Aplica para compras en tienda, web y WhatsApp.",
        "payload": {
            "title": "Promoción 3x2",
            "source": "promotions",
            "lang": "es",
            "tags": ["3x2", "promocion", "descuento", "oferta"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Descuentos por volumen Café Que Rico: 10% de descuento en compras superiores a $150.000 COP. 15% de descuento en compras superiores a $300.000 COP. Ideal para oficinas, empresas o grupos. Los descuentos se aplican automáticamente al total de la compra. Acumulable con envío gratis pero no con otras promociones.",
        "payload": {
            "title": "Descuentos por volumen",
            "source": "promotions",
            "lang": "es",
            "tags": ["descuento", "volumen", "mayoreo", "empresas"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Combo Cafetero Que Rico: Incluye 1 bolsa Café Clásico 500g, 1 bolsa Premium Huila 250g y 1 prensa francesa de vidrio. Todo por $95.000 (ahorro de $18.000 comparado con compra individual). Perfecto para regalar o para quien está empezando en el mundo del café de especialidad. Incluye guía básica de preparación.",
        "payload": {
            "title": "Combo Cafetero",
            "source": "promotions",
            "lang": "es",
            "tags": ["combo", "paquete", "regalo", "prensa"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Programa de Fidelidad Café Que Rico: Acumula 1 punto por cada $100.000 en compras. Canjea 5 puntos por 1 bolsa de Café Clásico 250g gratis. Canjea 10 puntos por 1 bolsa Premium de tu elección gratis. Los puntos no expiran nunca. Consulta tu saldo de puntos en cualquier momento por WhatsApp o en tienda.",
        "payload": {
            "title": "Programa de Fidelidad",
            "source": "promotions",
            "lang": "es",
            "tags": ["fidelidad", "puntos", "recompensas", "lealtad"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Promoción del mes de octubre 2025: 20% de descuento en toda la línea orgánica (Café Nariño Orgánico en todas sus presentaciones). Usa el código OCTUBRE20 al hacer tu pedido. Válido hasta el 31 de octubre de 2025. Aplica en compras por web, WhatsApp y tienda física.",
        "payload": {
            "title": "Promoción Octubre 2025",
            "source": "promotions",
            "lang": "es",
            "tags": ["promocion-mes", "octubre", "organico", "codigo"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Suscripción mensual Café Que Rico: Recibe café fresco cada mes con 15% de descuento permanente. Elige la frecuencia (quincenal o mensual), tipo de café preferido y cantidad. Envío totalmente gratis en todas las entregas. Puedes pausar o cancelar cuando quieras sin penalización. Ideal para no quedarte sin café en casa.",
        "payload": {
            "title": "Suscripción Mensual",
            "source": "promotions",
            "lang": "es",
            "tags": ["suscripcion", "mensual", "descuento", "recurrente"],
            "category": "promociones"
        }
    },

     # ==================== 🚚 ENVÍOS ====================
    {
        "id": str(uuid.uuid4()),
        "text": "🚚 Política de envíos Café Que Rico: Realizamos entregas en toda Colombia 🇨🇴. Envíos gratuitos a partir de $100.000 💸. Entregas en 2 a 5 días hábiles 📦. Usamos transportadoras certificadas como Servientrega y Coordinadora. También puedes recoger tu pedido directamente en nuestra tienda física 🏬.",
        "payload": {
            "title": "Política de Envíos",
            "source": "shipping",
            "lang": "es",
            "tags": ["envios", "domicilio", "tienda", "servientrega", "plazos"],
            "category": "envios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "📦 Rastreo de pedido: Una vez despachado tu pedido, recibirás un número de guía 🔢 por correo electrónico 📧 o WhatsApp 📱. Puedes rastrearlo en tiempo real en la página de la transportadora 🚛.",
        "payload": {
            "title": "Rastreo de Pedido",
            "source": "shipping",
            "lang": "es",
            "tags": ["rastreo", "envio", "seguimiento", "pedido"],
            "category": "envios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "📬 Envíos en Bucaramanga y área metropolitana: Entregas el mismo día 🕒 si el pedido se realiza antes de las 2:00 PM. Después de esa hora, se programa para el siguiente día hábil. Entregas por mensajería local en bicicleta 🚴‍♂️ o moto 🛵.",
        "payload": {
            "title": "Envíos Locales Bucaramanga",
            "source": "shipping",
            "lang": "es",
            "tags": ["bucaramanga", "envios", "local", "mismo dia"],
            "category": "envios"
        }
    },

    # ==================== 💳 PAGOS ====================
    {
        "id": str(uuid.uuid4()),
        "text": "💳 Métodos de pago disponibles: Aceptamos transferencias bancarias 🏦, PSE 💻, Nequi 📱, Daviplata 💰, tarjetas de crédito 💳 y pagos en efectivo contra entrega 💵 (solo Bucaramanga). Los pagos son procesados de forma segura 🔒.",
        "payload": {
            "title": "Métodos de Pago",
            "source": "payments",
            "lang": "es",
            "tags": ["pagos", "pse", "nequi", "daviplata", "efectivo"],
            "category": "pagos"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "🔐 Seguridad en pagos: Todos los pagos se procesan mediante plataformas certificadas y seguras 🔒. No almacenamos datos bancarios 🧾. Puedes confiar plenamente en la seguridad de nuestras transacciones 🛡️.",
        "payload": {
            "title": "Seguridad en Pagos",
            "source": "payments",
            "lang": "es",
            "tags": ["seguridad", "pagos", "datos", "confianza"],
            "category": "pagos"
        }
    },

    # ==================== 💸 PROMOCIONES ====================
    {
        "id": str(uuid.uuid4()),
        "text": "🎁 Promociones vigentes Café Que Rico: 💥 Combo Cafetero: prensa francesa + 250g de café clásico $55.000. ☕ Llévate 3 bolsas de 250g y paga solo 2. 🌿 Envío gratis en compras superiores a $100.000. 🧊 10% de descuento en Cold Brew por lanzamiento.",
        "payload": {
            "title": "Promociones Vigentes",
            "source": "promos",
            "lang": "es",
            "tags": ["promociones", "descuento", "combo", "envio gratis"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "🎉 Programa de fidelidad: Cada compra suma puntos ☕. Por cada $10.000 acumulas 1 punto ⭐. Con 10 puntos obtienes un 15% de descuento en tu siguiente compra. Puedes consultar tus puntos desde tu cuenta 💻 o escribiendo a WhatsApp 📱.",
        "payload": {
            "title": "Programa de Fidelidad",
            "source": "promos",
            "lang": "es",
            "tags": ["fidelidad", "puntos", "beneficios", "descuento"],
            "category": "promociones"
        }
    },

    # ==================== 🧾 POLÍTICAS ====================
    {
        "id": str(uuid.uuid4()),
        "text": "📜 Política de devoluciones: Aceptamos devoluciones dentro de los 7 días posteriores a la entrega 🗓️ si el producto presenta defectos o errores en el pedido. El café abierto o consumido no aplica para devolución 🚫. Para iniciar el proceso, comunícate con soporte técnico 💬.",
        "payload": {
            "title": "Política de Devoluciones",
            "source": "policy",
            "lang": "es",
            "tags": ["devoluciones", "reembolso", "politica", "pedido"],
            "category": "politicas"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "🔒 Política de privacidad: Café Que Rico protege tus datos personales 🛡️. No compartimos información con terceros y cumplimos con la Ley 1581 de 2012 sobre protección de datos personales en Colombia 📘.",
        "payload": {
            "title": "Política de Privacidad",
            "source": "policy",
            "lang": "es",
            "tags": ["privacidad", "datos", "seguridad", "colombia"],
            "category": "politicas"
        }
    },

    # ==================== 📱 CONTACTO ====================
    {
        "id": str(uuid.uuid4()),
        "text": "📞 Contacto Café Que Rico: WhatsApp: +57 316 555 9087 📱 | Teléfono: (607) 635 4488 ☎️ | Email: contacto@caferico.co ✉️ | Dirección: Calle 36 #23-45, Bucaramanga 🏬 | Instagram: @cafericocol ☕.",
        "payload": {
            "title": "Información de Contacto",
            "source": "contact",
            "lang": "es",
            "tags": ["contacto", "whatsapp", "telefono", "direccion", "instagram"],
            "category": "contacto"
        }
    },
]


async def load_knowledge_base():
    """Carga la base de conocimiento en Qdrant"""
    try:
        logger.info("Iniciando carga de base de conocimiento optimizada...")
        
        ensure_collection()
        
        info = get_collection_info()
        logger.info(f"Info de colección antes de cargar: {info}")
        
        documents = []
        for item in KB_DOCUMENTS:
            doc = {
                "id": item["id"],
                "text": item["text"],
                "payload": item["payload"]
            }
            documents.append(doc)
        
        batch_size = 10
        total_batches = (len(documents) - 1) // batch_size + 1
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = i // batch_size + 1
            logger.info(f"Cargando lote {batch_num}/{total_batches} ({len(batch)} documentos)")
            await upsert_documents(batch)
        
        info_after = get_collection_info()
        logger.info(f"Info de colección después de cargar: {info_after}")
        
        logger.info(f"✅ Base de conocimiento cargada exitosamente!")
        logger.info(f"   📦 Total documentos: {len(documents)}")
        logger.info(f"   🗂️  Colección: {info_after.get('name', 'N/A')}")
        logger.info(f"   📊 Puntos en Qdrant: {info_after.get('points_count', 'N/A')}")
        
    except Exception as e:
        logger.exception(f"❌ Error cargando base de conocimiento: {e}")
        raise

async def main():
    """Función principal"""
    logger.info("🚀 Script de carga de KB iniciando...")
    await load_knowledge_base()
    logger.info("🎉 Script completado exitosamente!")

if __name__ == "__main__":
    asyncio.run(main())

    