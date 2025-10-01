# Asistente Comercial IZA 

Asistente comercial omnicanal con RAG sobre Qdrant para café premium colombiano, accesible vía interfaz web y WhatsApp.

## 🚀 Stack Tecnológico

### Backend
- **Python 3.11+** con **FastAPI**
- **Qdrant** como base de datos vectorial
- **Langroid** para orquestación del agente
- **FastEmbed/OpenAI** para embeddings
- **MySQL** para persistencia de chats
- **OpenAI GPT** como LLM principal

## 📋 Características MVP

### ✅ Funcionalidades Implementadas
- **Chat HTTP**: Endpoint `/chat` para interacción web
- **WhatsApp Integration**: Webhook para recibir/enviar mensajes
- **RAG System**: Recuperación de conocimiento desde Qdrant
- **Admin Panel**: Vista de solo lectura para chats y estadísticas
- **Base de Conocimiento**: FAQ y productos de café precargados
- **Persistencia**: Historial de conversaciones en MySQL

### 🎯 Casos de Uso
- Consultas sobre productos de café
- Información de precios y promociones
- Detalles de envío y métodos de pago
- Soporte al cliente automatizado
- Panel administrativo para supervisión

## 🛠️ Instalación y Configuración

### 1. Prerequisitos
```bash
# Python 3.11+
python --version

# Docker y Docker Compose
```

### Conexión con Docker

1. **Verificar instalación de Docker y Docker Compose**
  
  ` docker --version`
  ` docker compose version`

Levantar los servicios (backend + Qdrant)

` docker compose up -d --build`

Listar contenedores en ejecución

`docker ps`

🔹 Logs y debugging
Ver logs del backend:

`docker logs -f chatbot_backend`

Ver logs de Qdrant:

`docker logs -f qdrant_vector_db`

🔹 Endpoints principales

Documentación Swagger UI:
👉` http://localhost:8000/docs`

Documentación Redoc:
👉 `http://localhost:8000/redoc`

Health check (para validar que el backend corre):

`curl http://localhost:8000/health`

### 2. Clonado y Dependencias

```bash
# Backend
git clone <url-del-repositorio>

cd nameProject
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# En Windows:
.venv\Scripts\activate

# En macOS/Linux:
source .venv/bin/activate


```

 **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

**Ejecutar Proyecto** 
   ```bash
    uvicorn app.main:app --reload --port 8000
   ```

### 3. Variables de Entorno

Crear archivo `.env` en la raíz:

```env
# Base de Datos
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=chatbot_db
DB_PORT=3306

# OpenAI
OPENAI_API_KEY=tu_api_key_aqui
LLM_MODEL_NAME=gpt-3.5-turbo

# Embeddings
USE_OPENAI_EMBEDDINGS=false
EMBED_MODEL=intfloat/multilingual-e5-small

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=company_kb

# RAG
RAG_TOP_K=3
RAG_SCORE_THRESHOLD=0.7

# WhatsApp (opcional)
WHATSAPP_TOKEN=tu_token_whatsapp
WHATSAPP_PHONE_ID=tu_phone_id
WHATSAPP_VERIFY_TOKEN=tu_verify_token

# CORS
FRONTEND_ORIGIN=http://localhost:5173
```

### 4. Inicialización de Servicios

```bash
# Levantar Qdrant 
docker run -p 6333:6333 qdrant/qdrant

# Ejecutar schema de base de datos (MySQL)
# Ejecutar script schema.sql en tu cliente MySQL

# Cargar base de conocimiento
cd scripts
python scripts/load_kb.py
```

### 5. Ejecutar la Aplicación

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## 🔧 APIs y Endpoints

### Chat HTTP
```bash
POST /chat/
{
  "message": "¿Qué tipos de café tienen?",
  "user_id": "demo_user"
}
```

### WhatsApp Webhook
```bash
# Verificación
GET /whatsapp/webhook?hub.mode=subscribe&hub.verify_token=tu_token&hub.challenge=123

# Recepción de mensajes
POST /whatsapp/webhook
```

## 📊 Base de Conocimiento

La KB incluye información sobre:
- **Productos**: Tipos de café, orígenes, tuestes
- **Precios**: Rangos de precios, descuentos, promociones
- **Envíos**: Tiempos, costos, cobertura geográfica
- **Métodos de Pago**: Opciones disponibles
- **Soporte**: Contactos, garantías, políticas

### Cargar/Actualizar KB
```bash
cd scripts
python load_kb.py
```


**Desarrollado con ❤️ para IZA Café Premium Colombiano**