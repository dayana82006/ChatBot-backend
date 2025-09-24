import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import ResponseHandlingException
from app.config import settings
from app.services.embeddings import embed_texts, get_embedding_dimension

logger = logging.getLogger(__name__)

# Configuración
QDRANT_URL = settings.QDRANT_URL
COLLECTION = settings.QDRANT_COLLECTION
EMBED_DIM = get_embedding_dimension()

# Cliente Qdrant
client = QdrantClient(url=QDRANT_URL)

def ensure_collection():
    """Crea la colección si no existe"""
    try:
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if COLLECTION not in collection_names:
            logger.info(f"Creando colección Qdrant: {COLLECTION}")
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=EMBED_DIM, 
                    distance=qmodels.Distance.COSINE
                ),
            )
            logger.info(f"Colección {COLLECTION} creada exitosamente")
        else:
            logger.debug(f"Colección {COLLECTION} ya existe")
            
    except Exception as e:
        logger.exception(f"Error asegurando colección: {e}")
        raise

async def upsert_documents(docs: List[Dict[str, Any]]):
    """
    Inserta documentos en Qdrant.
    docs: [{'id': str, 'text': str, 'payload': {...}}, ...]
    """
    if not docs:
        logger.warning("No hay documentos para insertar")
        return
        
    try:
        ensure_collection()
        
        # Extraer textos para generar embeddings
        texts = [doc["text"] for doc in docs]
        logger.info(f"Generando embeddings para {len(texts)} documentos")
        
        # Generar embeddings
        vectors = await embed_texts(texts)
        
        # Crear puntos para Qdrant
        points = []
        for doc, vector in zip(docs, vectors):
            point = qmodels.PointStruct(
                id=doc.get("id", str(hash(doc["text"]))),
                vector=vector,
                payload={
                    **doc.get("payload", {}),
                    "text": doc["text"]  # Asegurar que el texto esté en payload
                }
            )
            points.append(point)
        
        # Insertar en Qdrant
        client.upsert(collection_name=COLLECTION, points=points)
        logger.info(f"✅ {len(points)} documentos insertados en Qdrant")
        
    except Exception as e:
        logger.exception(f"Error insertando documentos en Qdrant: {e}")
        raise

async def search(query: str, top_k: int = 3, score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
    """
    Busca documentos similares en Qdrant.
    Retorna: [{'id': ..., 'score': float, 'payload': {...}}, ...]
    """
    try:
        ensure_collection()
        
        # Generar embedding del query
        logger.debug(f"Buscando: {query}")
        query_vectors = await embed_texts([query])
        query_vector = query_vectors[0]
        
        # Búsqueda en Qdrant
        search_results = client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        
        # Filtrar por score si se especifica
        results = []
        for result in search_results:
            if score_threshold is None or result.score >= score_threshold:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
        
        logger.info(f"Encontrados {len(results)} documentos relevantes (score >= {score_threshold})")
        return results
        
    except Exception as e:
        logger.exception(f"Error buscando en Qdrant: {e}")
        return []

def get_collection_info() -> Dict[str, Any]:
    """Obtiene información de la colección"""
    try:
        ensure_collection()
        info = client.get_collection(COLLECTION)
        return {
            "name": COLLECTION,
            "status": info.status,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "config": {
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance
            }
        }
    except Exception as e:
        logger.exception(f"Error obteniendo info de colección: {e}")
        return {}