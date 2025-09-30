from typing import List
import logging
from app.config import settings
from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)

# Configuración
USE_OPENAI = settings.USE_OPENAI_EMBEDDINGS
EMBED_MODEL = settings.EMBED_MODEL
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) if USE_OPENAI else None

# FastEmbed (recomendado para MVP)
_fastembed_model = None
if not USE_OPENAI:
    try:
        from fastembed import TextEmbedding
        # Modelos soportados en FastEmbed
        # Usar uno de estos modelos
        SUPPORTED_MODELS = {
            "BAAI/bge-small-en-v1.5": 384,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "BAAI/bge-base-en-v1.5": 768,
        }
        
        # Si el modelo configurado no está soportado, usar uno por defecto
        if EMBED_MODEL not in SUPPORTED_MODELS:
            logger.warning(f"Modelo {EMBED_MODEL} no soportado. Usando BAAI/bge-small-en-v1.5")
            EMBED_MODEL = "BAAI/bge-small-en-v1.5"
        
        _fastembed_model = TextEmbedding(model_name=EMBED_MODEL)
        logger.info(f"FastEmbed modelo cargado: {EMBED_MODEL}")
    except Exception as e:
        logger.warning(f"FastEmbed no disponible: {e}")
        _fastembed_model = None

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
        if USE_OPENAI and settings.OPENAI_API_KEY and client:
            logger.debug(f"Generando embeddings con OpenAI para {len(texts)} textos")
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return [item.embedding for item in response.data]
        
        raise RuntimeError("No hay backend de embeddings disponible. Configure USE_OPENAI_EMBEDDINGS=true con OPENAI_API_KEY o instale FastEmbed correctamente.")
        
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
            "BAAI/bge-small-en-v1.5": 384,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "BAAI/bge-base-en-v1.5": 768,
        }
        return dimensions.get(EMBED_MODEL, 384)