from typing import List
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Configuración
USE_OPENAI = settings.USE_OPENAI_EMBEDDINGS
EMBED_MODEL = settings.EMBED_MODEL

# FastEmbed (recomendado para MVP)
_fastembed_model = None
if not USE_OPENAI:
    try:
        from fastembed import TextEmbedding
        _fastembed_model = TextEmbedding(model_name=EMBED_MODEL)
        logger.info(f"FastEmbed modelo cargado: {EMBED_MODEL}")
    except Exception as e:
        logger.warning(f"FastEmbed no disponible: {e}")
        _fastembed_model = None

# OpenAI (opcional)
if USE_OPENAI:
    try:
        import openai
        openai.api_key = settings.OPENAI_API_KEY
        logger.info("OpenAI embeddings configurado")
    except ImportError:
        logger.warning("OpenAI no disponible")

async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Genera embeddings para una lista de textos.
    Usa FastEmbed por defecto o OpenAI si está configurado.
    """
    if not texts:
        return []

    try:
        # Usar FastEmbed por defecto
        if not USE_OPENAI and _fastembed_model:
            logger.debug(f"Generando embeddings con FastEmbed para {len(texts)} textos")
            embeddings = list(_fastembed_model.embed(texts))
            return [list(map(float, embedding)) for embedding in embeddings]

        # Fallback a OpenAI
        if USE_OPENAI and settings.OPENAI_API_KEY:
            logger.debug(f"Generando embeddings con OpenAI para {len(texts)} textos")
            import openai
            response = await openai.Embedding.acreate(
                model="text-embedding-3-small",
                input=texts
            )
            return [item["embedding"] for item in response["data"]]

        raise RuntimeError("No hay backend de embeddings disponible")
        
    except Exception as e:
        logger.exception(f"Error generando embeddings: {e}")
        raise

def get_embedding_dimension() -> int:
    """Retorna la dimensión de los embeddings según el modelo configurado"""
    if USE_OPENAI:
        return 1536  # text-embedding-3-small
    else:
        # FastEmbed models dimensions
        dimensions = {
            "intfloat/multilingual-e5-small": 384,
            "BAAI/bge-small-en-v1.5": 384,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
        }
        return dimensions.get(EMBED_MODEL, 384) 