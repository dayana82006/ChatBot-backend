from typing import List
import os
import logging
from app.config import settings

logger = logging.getLogger(__name__)

USE_OPENAI = settings.USE_OPENAI_EMBEDDINGS
EMBED_MODEL = settings.EMBED_MODEL

# --- FastEmbed path (recommended local for MVP) ---
try:
    if not USE_OPENAI:
        from fastembed import TextEmbedding
        _fastembed_model = TextEmbedding(model_name=EMBED_MODEL)
except Exception as e:
    logger.warning("FastEmbed not available or model missing: %s", e)
    _fastembed_model = None

# --- OpenAI path (optional) ---
if USE_OPENAI:
    import openai
    openai.api_key = settings.OPENAI_API_KEY

async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Devuelve una lista de vectores (float list) para cada texto.
    Usa FastEmbed por defecto, o OpenAI si USE_OPENAI_EMBEDDINGS=True.
    """
    if not texts:
        return []

    if not USE_OPENAI and _fastembed_model:
        # FastEmbed soporta batches
        vectors = _fastembed_model.embed(texts)
        return [list(map(float, v)) for v in vectors]

    # fallback a OpenAI embeddings
    if USE_OPENAI:
        res = openai.Embedding.create(model="text-embedding-3-small", input=texts)
        return [r["embedding"] for r in res["data"]]

    raise RuntimeError("No embedding backend available. Configure FastEmbed or OpenAI.")
