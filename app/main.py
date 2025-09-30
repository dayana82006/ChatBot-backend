from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
from app.routers import chat, whatsapp, admin
from app.config import settings
from app.database.database import init_db, execute_schema
from app.services.qdrant_service import ensure_collection, get_collection_info

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando aplicación FastAPI...")
    
    try:
        # Inicializar base de datos
        logger.info("Inicializando base de datos...")
        init_db()
        execute_schema()
        
        # Inicializar Qdrant
        logger.info("Inicializando Qdrant...")
        ensure_collection()
        collection_info = get_collection_info()
        logger.info(f"Colección Qdrant: {collection_info}")
        
        # Verificar Gemini
        if settings.USE_GEMINI and settings.GEMINI_API_KEY:
            logger.info("✅ Gemini API configurada")
        else:
            logger.warning("⚠️ Gemini no configurada, usando respuestas de fallback")
        
        logger.info("✅ Aplicación iniciada correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error durante el inicio: {e}")
        raise
    
    yield
    
    logger.info("🔄 Cerrando aplicación...")

# Crear aplicación FastAPI
app = FastAPI(
    title="Asistente Comercial IZA - MVP",
    version="1.0.0",
    description="MVP de asistente comercial omnicanal con RAG sobre Qdrant y Gemini, accesible vía Web y WhatsApp",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de logging para requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log request
    logger.info(f"🔍 {request.method} {request.url.path} - {request.client.host if request.client else 'unknown'}")
    
    response = await call_next(request)
    
    # Log response
    logger.info(f"✅ {request.method} {request.url.path} - {response.status_code}")
    
    return response

# Incluir routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
app.include_router(admin.router, tags=["Admin"])

# Health Check
@app.get("/health", summary="Health Check", tags=["System"])
async def health_check():
    """
    Endpoint para verificar el estado de salud de la aplicación.
    Incluye verificación de componentes críticos.
    """
    try:
        # Verificar Qdrant
        collection_info = get_collection_info()
        qdrant_status = "ok" if collection_info else "error"
        
        # Verificar base de datos
        try:
            init_db()
            db_status = "ok"
        except:
            db_status = "error"
        
        # Verificar Gemini
        llm_status = "ok" if (settings.USE_GEMINI and settings.GEMINI_API_KEY) else "not_configured"
        llm_provider = "gemini" if settings.USE_GEMINI else "fallback"
        
        return {
            "status": "ok",
            "version": "1.0.0",
            "components": {
                "database": db_status,
                "qdrant": qdrant_status,
                "embeddings": "fastembed" if not settings.USE_OPENAI_EMBEDDINGS else "openai",
                "llm": llm_status,
                "llm_provider": llm_provider,
                "llm_model": settings.LLM_MODEL_NAME if settings.USE_GEMINI else "fallback"
            },
            "qdrant_info": collection_info
        }
        
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        return {
            "status": "error", 
            "error": str(e)
        }

@app.get("/", summary="Root", tags=["System"])
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "Asistente Comercial IZA - API v1.0.0 (Powered by Google Gemini)",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )