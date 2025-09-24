from app.services.qdrant_service import upsert_documents, ensure_collection
import uuid
import datetime
import os

# Ejemplo de KB mínima (reemplaza por tus FAQs reales)
KB = [
    {
        "id": str(uuid.uuid4()),
        "text": "¿Qué tipos de café vende IZA?",
        "payload": {"title": "Tipos de café", "source": "faq", "lang": "es", "tags": ["productos","cafe"]}
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Ofrecemos café arábica especial, blends y granos de origen single-origin de Colombia.",
        "payload": {"title": "Descripción producto", "source": "faq", "lang": "es", "tags": ["productos","cafe", "descripcion"]}
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Tiempo de envío: entregas en Bucaramanga y próximas ciudades en 48-72 horas.",
        "payload": {"title": "Envios", "source": "faq", "lang": "es", "tags": ["envios","logistica"]}
    }
]

def main():
    ensure_collection()
    docs = []
    for i, item in enumerate(KB):
        docs.append({"id": item["id"], "text": item["text"], "payload": item["payload"]})
    upsert_documents(docs)
    print("KB cargada en Qdrant")

if __name__ == "__main__":
    main()
