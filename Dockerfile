# backend/Dockerfile
# Usar una imagen base de Python
FROM python:3.11-slim-bookworm

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requisitos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY ./app /app/app

# Exponer el puerto en el que correrá FastAPI
EXPOSE 8000

# Comando para iniciar la aplicación Uvicorn
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Usar el comando del docker-compose.yml para mayor flexibilidad