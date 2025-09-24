import sys
import os
import asyncio
import uuid
import logging

# Añadir el directorio raíz al path para importar módulos de la app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import upsert_documents, ensure_collection, get_collection_info

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base de conocimiento mejorada para IZA - Café
KB_DOCUMENTS = [
    {
        "id": str(uuid.uuid4()),
        "text": "¿Qué tipos de café vende IZA?",
        "payload": {
            "title": "Tipos de café disponibles",
            "source": "faq",
            "lang": "es",
            "tags": ["productos", "cafe", "tipos"],
            "category": "productos"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "IZA ofrece café arábica especial 100% colombiano, incluyendo blends premium y granos de origen single-origin de regiones como Huila, Nariño y Tolima. También tenemos opciones de tueste claro, medio y oscuro.",
        "payload": {
            "title": "Catálogo de productos IZA",
            "source": "catalog",
            "lang": "es",
            "tags": ["productos", "cafe", "arabica", "colombia"],
            "category": "productos"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Cuánto cuesta el café de IZA?",
        "payload": {
            "title": "Precios del café",
            "source": "faq",
            "lang": "es",
            "tags": ["precios", "costos"],
            "category": "precios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Los precios de IZA van desde $25.000 COP por bolsa de 250g para nuestro blend clásico, hasta $45.000 COP por bolsas premium de 500g de single-origin. Ofrecemos descuentos por compras de 3 o más bolsas.",
        "payload": {
            "title": "Lista de precios IZA 2024",
            "source": "pricing",
            "lang": "es",
            "tags": ["precios", "descuentos", "promociones"],
            "category": "precios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Cómo es el envío del café?",
        "payload": {
            "title": "Información de envíos",
            "source": "faq",
            "lang": "es",
            "tags": ["envios", "logistica"],
            "category": "envios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Realizamos entregas en Bucaramanga y área metropolitana en 24-48 horas. Para otras ciudades de Colombia, el tiempo de envío es de 3-5 días hábiles. El envío es GRATIS para pedidos superiores a $80.000 COP.",
        "payload": {
            "title": "Política de envíos IZA",
            "source": "shipping",
            "lang": "es",
            "tags": ["envios", "tiempos", "gratis", "bucaramanga"],
            "category": "envios"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Cómo puedo hacer un pedido?",
        "payload": {
            "title": "Cómo hacer pedidos",
            "source": "faq",
            "lang": "es",
            "tags": ["pedidos", "compras"],
            "category": "ventas"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Puedes hacer tu pedido por WhatsApp al 300-123-4567, por nuestro sitio web www.izacafe.co, o escribiéndome directamente aquí. Aceptamos pagos por transferencia, Nequi, Daviplata y tarjetas de crédito.",
        "payload": {
            "title": "Canales de venta y métodos de pago",
            "source": "sales",
            "lang": "es",
            "tags": ["pedidos", "whatsapp", "pagos", "transferencia"],
            "category": "ventas"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Qué garantía tiene el café?",
        "payload": {
            "title": "Garantía del producto",
            "source": "faq",
            "lang": "es",
            "tags": ["garantia", "calidad"],
            "category": "servicio"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Garantizamos la frescura de nuestro café. Si no estás completamente satisfecho, puedes devolver el producto dentro de los 7 días posteriores a la compra para un reembolso completo o cambio.",
        "payload": {
            "title": "Política de garantía y devoluciones",
            "source": "policy",
            "lang": "es",
            "tags": ["garantia", "devolucion", "satisfaccion"],
            "category": "servicio"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Tienen café orgánico?",
        "payload": {
            "title": "Café orgánico",
            "source": "faq",
            "lang": "es",
            "tags": ["organico", "certificado"],
            "category": "productos"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Sí, tenemos una línea de café 100% orgánico certificado de la región de Nariño. Este café especial cuesta $38.000 COP por bolsa de 250g y viene con certificación orgánica internacional.",
        "payload": {
            "title": "Línea de café orgánico IZA",
            "source": "organic",
            "lang": "es",
            "tags": ["organico", "certificado", "narino", "especial"],
            "category": "productos"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "¿Cómo contactar soporte?",
        "payload": {
            "title": "Contactar soporte",
            "source": "faq",
            "lang": "es",
            "tags": ["soporte", "contacto"],
            "category": "servicio"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Para soporte técnico o consultas especiales, puedes escribir a soporte@izacafe.co o llamar al (7) 123-4567 de lunes a viernes de 8:00 AM a 6:00 PM. También puedes hablar conmigo, IZA, y te ayudo con la mayoría de consultas.",
        "payload": {
            "title": "Información de contacto y soporte",
            "source": "contact",
            "lang": "es",
            "tags": ["soporte", "email", "telefono", "horarios"],
            "category": "servicio"
        }
    }
]

async def load_knowledge_base():
    """Carga la base de conocimiento en Qdrant"""
    try:
        logger.info("🔄 Iniciando carga de base de conocimiento...")
        
        # Asegurar que la colección existe
        ensure_collection()
        
        # Obtener info de la colección
        info = get_collection_info()
        logger.info(f"📊 Info de colección antes de cargar: {info}")
        
        # Preparar documentos
        documents = []
        for item in KB_DOCUMENTS:
            doc = {
                "id": item["id"],
                "text": item["text"],
                "payload": item["payload"]
            }
            documents.append(doc)
        
        # Cargar documentos en lotes
        batch_size = 5
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"📥 Cargando lote {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            await upsert_documents(batch)
        
        # Verificar carga
        info_after = get_collection_info()
        logger.info(f"📊 Info de colección después de cargar: {info_after}")
        
        logger.info(f"✅ Base de conocimiento cargada exitosamente!")
        logger.info(f"   - {len(documents)} documentos cargados")
        logger.info(f"   - Colección: {info_after.get('name', 'N/A')}")
        logger.info(f"   - Total puntos: {info_after.get('points_count', 'N/A')}")
        
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