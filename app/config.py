from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Configuración base de datos
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "chatbot_db")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

    #  Configuración de Redis (cache)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)

    #  Configuración de Sesión / Contexto de Chat
    MAX_CHAT_TURNS: int = int(os.getenv("MAX_CHAT_TURNS", 5))
    SESSION_EXPIRE: int = int(os.getenv("SESSION_EXPIRE", 1800))
    CACHE_EXPIRE: int = int(os.getenv("CACHE_EXPIRE", 300))


    # Gemini/LLM
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    USE_GEMINI: bool = os.getenv("USE_GEMINI", "true").lower() == "true"
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gemini-1.5-flash")
    
    # OpenAI (legacy, mantener para compatibilidad)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Embeddings
    USE_OPENAI_EMBEDDINGS: bool = os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"
    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-small")
    
    # Qdrant
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "company_kb")
    
    # RAG
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))
    RAG_SCORE_THRESHOLD: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.7"))
    
    # CORS
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173", 
        "http://localhost:3000",
        os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    ]

    # WhatsApp
    WHATSAPP_TOKEN: Optional[str] = os.getenv("WHATSAPP_TOKEN")
    WHATSAPP_PHONE_ID: Optional[str] = os.getenv("WHATSAPP_PHONE_ID")
    WHATSAPP_VERIFY_TOKEN: Optional[str] = os.getenv("WHATSAPP_VERIFY_TOKEN")
    
    @property
    def GRAPH_URL(self) -> str:
        if self.WHATSAPP_PHONE_ID:
            return f"https://graph.facebook.com/v17.0/{self.WHATSAPP_PHONE_ID}/messages"
        return ""

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    PUBLIC_BASE_URL: Optional[str] = os.getenv("PUBLIC_BASE_URL")

settings = Settings()