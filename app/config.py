from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Configuracion base de datos 

    DB_HOST:str = os.getenv("DB_HOST", "localhost")
    DB_USER: str  = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "chatbot_db")
    DB_PORT: str = int(os.getenv("DB_PORT", 3306))


    OPENAI_API_KEY: Optional[str] = None
    USE_OPENAI_EMBEDDINGS: bool = False
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "company_kb"
    EMBED_MODEL: str = "intfloat/multilingual-e5-small"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # 👉 Nuevo: lista de orígenes permitidos para CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # WhatsApp
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_ID: Optional[str] = None

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    PUBLIC_BASE_URL: Optional[str] = None # webhook de Telegram

    # Persistencia de chats
    DATABASE_URL: str = "sqlite:///./sql_app.db"  # SQLite por defecto

    # Configuración de Langroid/LLM
    LLM_MODEL_NAME: str = "gpt-3.5-turbo"  # Opcional, para futuros ajustes del LLM
    RAG_TOP_K: int = 3
    RAG_SCORE_THRESHOLD: float = 0.7




settings = Settings()
