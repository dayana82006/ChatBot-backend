
Backend del asistente con FastAPI, Qdrant y Docker.

---

## 🔹 Conexión con Docker

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