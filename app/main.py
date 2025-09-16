from fastapi import FastApi
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import chat, whatsapp, admin 
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastApi):
    print("FastAPI application starting up...")
    yield
    print("FastAPI application shutting down...")
    
app = FastApi(
    title="Asistente Comercial IZA",
    version="0.1.0",
    description="MVP de un asistente comercial con RAG sobre Qdrant, accesible vía Web y canales de mensajería.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/health", summary="Verifica el estado de salud de la API")
async def health_check():
    """
    Endpoint para verificar el estado de salud de la aplicación.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    