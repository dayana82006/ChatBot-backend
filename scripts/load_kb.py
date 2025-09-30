import sys
import os
import asyncio
import uuid
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import upsert_documents, ensure_collection, get_collection_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base de conocimiento completa para Café Que Rico
KB_DOCUMENTS = [
    # ==================== PRODUCTOS Y VARIEDADES ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Café Que Rico Clásico: Blend suave 100% arábica colombiano, tueste medio. Notas de chocolate, caramelo y nuez. Ideal para método de preparación en prensa francesa o cafetera. Presentaciones: 250g ($25.000) y 500g ($45.000). Disponible en grano entero o molido (fino, medio, grueso).",
        "payload": {
            "title": "Café Que Rico Clásico",
            "source": "catalog",
            "lang": "es",
            "tags": ["productos", "clasico", "blend", "tueste-medio"],
            "category": "productos",
            "precio_min": 25000,
            "precio_max": 45000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Que Rico Premium Huila: Single-origin de la región de Huila, Colombia. Tueste medio-claro. Perfil de sabor: cítricos, frutas rojas, acidez brillante, cuerpo medio. Altitud: 1600-1800 msnm. Proceso lavado. Presentaciones: 250g ($38.000) y 500g ($70.000). Solo grano entero o molido medio.",
        "payload": {
            "title": "Café Premium Huila",
            "source": "catalog",
            "lang": "es",
            "tags": ["productos", "premium", "huila", "single-origin", "frutal"],
            "category": "productos",
            "precio_min": 38000,
            "precio_max": 70000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Que Rico Nariño Orgánico: Certificado orgánico internacional. Single-origin de Nariño. Tueste claro. Notas de flores, miel, cítricos dulces. Proceso natural. Sin químicos ni pesticidas. Presentaciones: 250g ($42.000) y 500g ($78.000). Disponible en grano entero o molido fino/medio.",
        "payload": {
            "title": "Café Nariño Orgánico",
            "source": "catalog",
            "lang": "es",
            "tags": ["productos", "organico", "narino", "certificado", "natural"],
            "category": "productos",
            "precio_min": 42000,
            "precio_max": 78000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Que Rico Tolima Intenso: Single-origin de Tolima. Tueste oscuro. Notas de chocolate amargo, frutos secos, cuerpo robusto. Ideal para espresso. Presentaciones: 250g ($35.000) y 500g ($65.000). Disponible en grano entero o molido fino para espresso.",
        "payload": {
            "title": "Café Tolima Intenso",
            "source": "catalog",
            "lang": "es",
            "tags": ["productos", "tolima", "intenso", "espresso", "tueste-oscuro"],
            "category": "productos",
            "precio_min": 35000,
            "precio_max": 65000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Que Rico Descafeinado: Proceso suizo de descafeinado (sin químicos). Blend suave, tueste medio. Conserva 98% del sabor original. Notas de caramelo y avellana. Presentaciones: 250g ($30.000) y 500g ($55.000). Solo molido medio.",
        "payload": {
            "title": "Café Descafeinado",
            "source": "catalog",
            "lang": "es",
            "tags": ["productos", "descafeinado", "sin-cafeina", "proceso-suizo"],
            "category": "productos",
            "precio_min": 30000,
            "precio_max": 55000
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Café Que Rico Edición Especial: Micro-lote limitado que cambia cada mes. Café de competencia o geishas especiales. Tueste personalizado. Precio: $95.000 por 250g. Solo 50 bolsas por mes. Disponible solo en grano entero. Incluye ficha de cata.",
        "payload": {
            "title": "Edición Especial Limitada",
            "source": "catalog",
            "lang": "es",
            "tags": ["productos", "especial", "limitado", "geisha", "competencia"],
            "category": "productos",
            "precio_min": 95000,
            "precio_max": 95000
        }
    },

    # ==================== PRECIOS Y PRESENTACIONES ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Lista de precios Café Que Rico: Clásico 250g $25.000 / 500g $45.000 | Premium Huila 250g $38.000 / 500g $70.000 | Nariño Orgánico 250g $42.000 / 500g $78.000 | Tolima Intenso 250g $35.000 / 500g $65.000 | Descafeinado 250g $30.000 / 500g $55.000 | Edición Especial 250g $95.000. Todos los precios en pesos colombianos (COP).",
        "payload": {
            "title": "Lista completa de precios",
            "source": "pricing",
            "lang": "es",
            "tags": ["precios", "lista", "costos"],
            "category": "precios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Tipos de molido disponibles: FINO (para espresso, cafetera italiana), MEDIO (para cafetera de goteo, V60), GRUESO (para prensa francesa, cold brew). El café viene en grano entero por defecto. Sin cargo adicional por moler.",
        "payload": {
            "title": "Tipos de molido",
            "source": "info",
            "lang": "es",
            "tags": ["molido", "preparacion", "granos"],
            "category": "productos"
        }
    },

    # ==================== PROMOCIONES Y DESCUENTOS ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Promoción 3x2: Compra 3 bolsas de cualquier café (pueden ser diferentes) y paga solo 2. La de menor valor es gratis. Válido todos los días. No acumulable con otros descuentos.",
        "payload": {
            "title": "Promoción 3x2",
            "source": "promotions",
            "lang": "es",
            "tags": ["promociones", "descuentos", "3x2", "oferta"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Descuento por volumen: 10% de descuento en compras superiores a $150.000 COP. 15% de descuento en compras superiores a $300.000 COP. Ideal para oficinas o grupos.",
        "payload": {
            "title": "Descuentos por volumen",
            "source": "promotions",
            "lang": "es",
            "tags": ["promociones", "descuentos", "volumen", "mayoreo"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Combo Cafetero: 1 bolsa de Clásico 500g + 1 bolsa de Premium Huila 250g + 1 prensa francesa = $95.000 (ahorro de $18.000). Perfecto para regalo o comenzar en el mundo del café de especialidad.",
        "payload": {
            "title": "Combo Cafetero",
            "source": "promotions",
            "lang": "es",
            "tags": ["promociones", "combo", "paquete", "regalo"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Programa de fidelidad: Por cada $100.000 en compras acumulas 1 punto. 5 puntos = 1 bolsa de café Clásico 250g gratis. 10 puntos = 1 bolsa Premium de tu elección gratis. Los puntos no expiran.",
        "payload": {
            "title": "Programa de fidelidad",
            "source": "promotions",
            "lang": "es",
            "tags": ["fidelidad", "puntos", "recompensas", "lealtad"],
            "category": "promociones"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Descuento del mes de octubre 2025: 20% de descuento en toda la línea orgánica Nariño. Código: OCTUBRE20. Válido hasta el 31 de octubre.",
        "payload": {
            "title": "Descuento octubre 2025",
            "source": "promotions",
            "lang": "es",
            "tags": ["promociones", "descuento-mes", "octubre", "organico"],
            "category": "promociones"
        }
    },

    # ==================== ENVÍOS Y ENTREGA ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Envíos en Bucaramanga y área metropolitana (Floridablanca, Girón, Piedecuesta): Entrega en 24-48 horas. Costo: $8.000 COP. GRATIS en pedidos superiores a $80.000 COP.",
        "payload": {
            "title": "Envíos Bucaramanga",
            "source": "shipping",
            "lang": "es",
            "tags": ["envios", "bucaramanga", "local", "rapido"],
            "category": "envios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Envíos nacionales Colombia: Cobertura en todas las ciudades principales (Bogotá, Medellín, Cali, Barranquilla, Cartagena, etc). Tiempo de entrega: 3-5 días hábiles. Costo: $15.000 COP. GRATIS en pedidos superiores a $120.000 COP. Usamos Servientrega y Coordinadora.",
        "payload": {
            "title": "Envíos nacionales",
            "source": "shipping",
            "lang": "es",
            "tags": ["envios", "nacional", "colombia", "servientrega"],
            "category": "envios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Recogida en tienda: Disponible sin costo en nuestra tienda ubicada en Calle 35 #15-20, Cabecera del Llano, Bucaramanga. Horario: Lunes a viernes 9:00 AM - 7:00 PM, sábados 10:00 AM - 5:00 PM. Pedido listo en 2-4 horas.",
        "payload": {
            "title": "Recogida en tienda",
            "source": "shipping",
            "lang": "es",
            "tags": ["recogida", "tienda-fisica", "bucaramanga", "cabecera"],
            "category": "envios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Seguimiento de pedido: Recibirás número de guía por WhatsApp o email 24 horas después del despacho. Puedes rastrear tu pedido en tiempo real en la página de la transportadora.",
        "payload": {
            "title": "Rastreo de pedidos",
            "source": "shipping",
            "lang": "es",
            "tags": ["envios", "rastreo", "seguimiento", "guia"],
            "category": "envios"
        }
    },

    # ==================== MÉTODOS DE PAGO ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Métodos de pago aceptados: Transferencia bancaria (Bancolombia, Davivienda, Nequi), Daviplata, Nequi, Tarjetas de crédito/débito (Visa, Mastercard, American Express), PSE, Efectivo (solo en recogida en tienda), Wompi (pasarela segura).",
        "payload": {
            "title": "Métodos de pago",
            "source": "payment",
            "lang": "es",
            "tags": ["pagos", "metodos", "transferencia", "tarjetas"],
            "category": "pagos"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Pago contra entrega: Disponible solo en Bucaramanga y área metropolitana. Recargo de $3.000 COP. Puedes pagar en efectivo o con datáfono al momento de recibir tu pedido.",
        "payload": {
            "title": "Pago contra entrega",
            "source": "payment",
            "lang": "es",
            "tags": ["pagos", "contraentrega", "efectivo", "datafono"],
            "category": "pagos"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Datos bancarios para transferencia: Banco Bancolombia, Cuenta de ahorros #12345678901, Titular: Café Que Rico SAS, NIT: 900.123.456-7. Enviar comprobante por WhatsApp al 300-123-4567.",
        "payload": {
            "title": "Datos bancarios",
            "source": "payment",
            "lang": "es",
            "tags": ["pagos", "transferencia", "bancolombia", "datos"],
            "category": "pagos"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Pago seguro con tarjeta: Procesamos pagos con Wompi, certificado PCI DSS. No almacenamos datos de tu tarjeta. Transacciones 100% seguras con verificación 3D Secure.",
        "payload": {
            "title": "Seguridad en pagos",
            "source": "payment",
            "lang": "es",
            "tags": ["pagos", "seguridad", "wompi", "tarjetas"],
            "category": "pagos"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Cuotas sin interés: Pagos con tarjeta de crédito aceptan cuotas sin interés: 3 cuotas en compras superiores a $90.000, 6 cuotas en compras superiores a $180.000. Aplica con bancos participantes.",
        "payload": {
            "title": "Cuotas sin interés",
            "source": "payment",
            "lang": "es",
            "tags": ["pagos", "cuotas", "credito", "sin-interes"],
            "category": "pagos"
        }
    },

    # ==================== PROCESO DE COMPRA ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Cómo hacer tu pedido: 1) Dime qué café quieres y la cantidad. 2) Elige el tipo de molido (o grano entero). 3) Confirma tu dirección de entrega. 4) Selecciona método de pago. 5) Te envío resumen y total. 6) Realizas el pago. 7) Confirmamos y despachamos. Simple y rápido.",
        "payload": {
            "title": "Proceso de compra",
            "source": "sales",
            "lang": "es",
            "tags": ["compra", "pedido", "proceso", "pasos"],
            "category": "ventas"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Canales de venta: Puedes comprar por WhatsApp (300-123-4567), página web (www.cafequerico.co), Instagram (@cafequerico), o hablando directamente conmigo, IZA, tu asistente virtual. Atención 24/7.",
        "payload": {
            "title": "Canales de venta",
            "source": "sales",
            "lang": "es",
            "tags": ["ventas", "canales", "whatsapp", "web"],
            "category": "ventas"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Tiempo de procesamiento: Pedidos recibidos antes de las 2:00 PM se despachan el mismo día. Pedidos después de las 2:00 PM se despachan al día siguiente hábil. No despachamos domingos ni festivos.",
        "payload": {
            "title": "Tiempo de procesamiento",
            "source": "sales",
            "lang": "es",
            "tags": ["ventas", "procesamiento", "despacho", "tiempos"],
            "category": "ventas"
        }
    },

    # ==================== GARANTÍAS Y DEVOLUCIONES ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Garantía de frescura: Todo nuestro café se tuesta máximo 7 días antes del envío. Garantizamos frescura por 3 meses desde la fecha de tueste (indicada en el empaque). Si no estás satisfecho con la frescura, cambio o reembolso 100%.",
        "payload": {
            "title": "Garantía de frescura",
            "source": "policy",
            "lang": "es",
            "tags": ["garantia", "frescura", "calidad", "tueste"],
            "category": "garantias"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Política de devolución: Tienes 7 días desde la recepción para devolver el producto si no quedaste satisfecho. Reembolso 100% o cambio por otro café. El café debe estar en empaque original sin abrir. Costo de envío de devolución corre por cuenta del cliente.",
        "payload": {
            "title": "Política de devolución",
            "source": "policy",
            "lang": "es",
            "tags": ["devolucion", "reembolso", "garantia", "7dias"],
            "category": "garantias"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Producto dañado o equivocado: Si recibes producto dañado o equivocado, contacta inmediatamente. Reposición sin costo y nosotros cubrimos el envío. Toma fotos del empaque y producto como evidencia.",
        "payload": {
            "title": "Producto dañado",
            "source": "policy",
            "lang": "es",
            "tags": ["garantia", "dañado", "reposicion", "error"],
            "category": "garantias"
        }
    },

    # ==================== INFORMACIÓN DE CONTACTO ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Contacto Café Que Rico: WhatsApp ventas: 300-123-4567 | Email: ventas@cafequerico.co | Soporte: soporte@cafequerico.co | Teléfono fijo: (7) 123-4567 | Dirección tienda: Calle 35 #15-20, Cabecera del Llano, Bucaramanga | Instagram: @cafequerico | Facebook: Café Que Rico",
        "payload": {
            "title": "Información de contacto",
            "source": "contact",
            "lang": "es",
            "tags": ["contacto", "whatsapp", "email", "telefono"],
            "category": "contacto"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Horarios de atención: Tienda física: Lunes a viernes 9:00 AM - 7:00 PM, sábados 10:00 AM - 5:00 PM, domingos cerrado | Atención WhatsApp y web: 24/7 con IZA (respuestas inmediatas) | Atención humana: Lunes a viernes 8:00 AM - 6:00 PM, sábados 9:00 AM - 1:00 PM",
        "payload": {
            "title": "Horarios de atención",
            "source": "contact",
            "lang": "es",
            "tags": ["horarios", "atencion", "disponibilidad"],
            "category": "contacto"
        }
    },

    # ==================== PREPARACIÓN Y CONSEJOS ====================
    {
        "id": str(uuid.uuid4()),
        "text": "Consejos de preparación: Prensa francesa: 30g café molido grueso por 500ml agua a 92-96°C, infusión 4 minutos | V60: 15g café molido medio por 250ml agua a 90-94°C, tiempo total 2:30-3:00 min | Espresso: 18-20g café molido fino, extracción 25-30 segundos, 40ml salida",
        "payload": {
            "title": "Guía de preparación",
            "source": "info",
            "lang": "es",
            "tags": ["preparacion", "metodos", "recetas", "barista"],
            "category": "educacion"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Conservación del café: Guardar en lugar fresco y seco, lejos de luz directa y olores fuertes. Usar recipiente hermético. No refrigerar ni congelar. Consumir preferiblemente dentro de 1 mes después de abrir el empaque para sabor óptimo.",
        "payload": {
            "title": "Conservación del café",
            "source": "info",
            "lang": "es",
            "tags": ["conservacion", "almacenamiento", "frescura"],
            "category": "educacion"
        }
    },

    # ==================== PREGUNTAS FRECUENTES ====================
    {
        "id": str(uuid.uuid4()),
        "text": "¿Hacen envíos internacionales? Actualmente solo enviamos dentro de Colombia. Estamos trabajando en expandir a países de Latinoamérica próximamente.",
        "payload": {
            "title": "Envíos internacionales",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "internacional", "envios"],
            "category": "faq"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Puedo cambiar o cancelar mi pedido? Sí, puedes cambiar o cancelar sin costo antes de que se despache. Una vez despachado, aplica política de devolución estándar.",
        "payload": {
            "title": "Cambios y cancelaciones",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "cancelacion", "cambios"],
            "category": "faq"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿El café es de comercio justo? Sí, trabajamos directamente con cooperativas de caficultores colombianos, pagando precio justo y premium por calidad. Parte de nuestras ganancias va al desarrollo de las comunidades cafeteras.",
        "payload": {
            "title": "Comercio justo",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "comercio-justo", "etico", "social"],
            "category": "faq"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Tienen suscripción mensual? Sí, plan de suscripción: recibe café fresco cada mes con 15% de descuento. Elige frecuencia (quincenal/mensual), tipo de café y cantidad. Cancela cuando quieras. Envío gratis en suscripciones.",
        "payload": {
            "title": "Suscripción mensual",
            "source": "faq",
            "lang": "es",
            "tags": ["faq", "suscripcion", "mensual", "recurrente"],
            "category": "faq"
        }
    }
]

async def load_knowledge_base():
    """Carga la base de conocimiento en Qdrant"""
    try:
        logger.info("Iniciando carga de base de conocimiento...")
        
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
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Cargando lote {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            await upsert_documents(batch)
        
        info_after = get_collection_info()
        logger.info(f"Info de colección después de cargar: {info_after}")
        
        logger.info(f"Base de conocimiento cargada exitosamente!")
        logger.info(f"   - {len(documents)} documentos cargados")
        logger.info(f"   - Colección: {info_after.get('name', 'N/A')}")
        logger.info(f"   - Total puntos: {info_after.get('points_count', 'N/A')}")
        
    except Exception as e:
        logger.exception(f"Error cargando base de conocimiento: {e}")
        raise

async def main():
    """Función principal"""
    logger.info("Script de carga de KB iniciando...")
    await load_knowledge_base()
    logger.info("Script completado exitosamente!")

if __name__ == "__main__":
    asyncio.run(main())