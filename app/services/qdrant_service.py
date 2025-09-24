import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config import settings
from app.services.embeddings import embed_texts

logger = logging.getLogger(__name__)

QDRANT_URL = settings.QDRANT_URL
COLLECTION = settings.QDRANT_COLLECTION
EMBED_DIM = 384  # para intfloat/multilingual-e5-small

# Cliente síncrono (qdrant-client también soporta async, pero mantenemos sync aquí)
client = QdrantClient(url=QDRANT_URL)


def ensure_collection():
    """
    Crea la colección si no existe.
    """
    try:
        if COLLECTION not in [c.name for c in client.get_collections().collections]:
            logger.info("Creando colección Qdrant: %s", COLLECTION)
            client.recreate_collection(
                collection_name=COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=EMBED_DIM, distance=qmodels.Distance.COSINE
                ),
            )
            logger.info("Colección creada")
        else:
            logger.debug("Colección ya existe")
    except Exception as e:
        logger.exception("Error al asegurar la colección: %s", e)
        raise


async def upsert_documents(docs: List[Dict[str, Any]]):
    """
    docs: [{ 'id': str|int, 'text': str, 'payload': {...} }, ...]
    """
    ensure_collection()
    texts = [d["text"] for d in docs]

    # embed_texts es async, así que lo esperamos
    vectors = await embed_texts(texts)

    points = []
    for d, vec in zip(docs, vectors):
        points.append(
            qmodels.PointStruct(id=d.get("id"), vector=vec, payload=d.get("payload", {}))
        )

    client.upsert(collection_name=COLLECTION, points=points)
    logger.info("Upserted %d documents to Qdrant", len(points))


async def search(query: str, top_k: int = 3, score_threshold: Optional[float] = None):
    """
    Busca los top_k fragmentos similares al query.
    Retorna lista de dicts: [{id, score, payload}, ...]
    """
    # generar vector de la consulta
    vectors = await embed_texts([query])
    query_vec = vectors[0]

    hits = client.search(
    collection_name=COLLECTION,
    query_vector=query_vec,
    limit=top_k,
    with_payload=True,
)


    results = []
    for h in hits:
        item = {"id": h.id, "score": h.score, "payload": h.payload}
        if score_threshold is None or h.score >= score_threshold:
            results.append(item)
    return results
