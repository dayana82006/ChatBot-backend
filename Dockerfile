# backend/Dockerfile
# Usar una imagen base ligera de Python
FROM python:3.11-slim-bookworm

# Evitar que Python genere archivos .pyc y usar logging en consola
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias (ej: para psycopg2, mysqlclient, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejora caching de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY ./app /app/app

# Exponer el puerto en el que correrá FastAPI
EXPOSE 8000

# Comando por defecto (comentado si docker-compose lo sobreescribe)
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
