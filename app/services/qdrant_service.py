# app/services/qdrant_service.py
import logging
from typing import List

logger = logging.getLogger(__name__)

# Si quieres usar qdrant-client, importa y configura aquí.
# from qdrant_client import QdrantClient

async def query_qdrant_for_context(query_text: str, top_k: int = 3) -> List[str]:
    """
    Stub para consulta semántica a Qdrant.
    Reemplaza la implementación por qdrant-client + embeddings.
    Por ahora devuelve una lista de ejemplos.
    """
    # Ejemplo: cuando no está disponible Qdrant, devolver resultados dummy
    # Implementación real: calcular embedding (OpenAI, etc.), luego client.search(...)
    logger.debug(f"query_qdrant_for_context(query={query_text}, top_k={top_k}) called")
    return [
        "Fragmento de documentación 1 relacionado",
        "Fragmento de documento 2 (FAQ)",
        "Fragmento 3 - guía rápida"
    ]
