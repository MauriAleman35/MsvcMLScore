# # Imagen base oficial de Python
# FROM python:3.11-slim

# # Variables de entorno para Python (no .pyc, UTF-8)
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# # Crear el directorio de la app
# WORKDIR /app

# # Instalar dependencias del sistema necesarias
# RUN apt-get update && \
#     apt-get install -y build-essential gcc && \
#     apt-get clean

# # Copiar requirements y dependencias
# COPY requirements.txt /app/requirements.txt

# # Instalar dependencias Python
# RUN pip install --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt

# # Copiar el código fuente
# COPY . /app

# # Comando para ejecutar el consumidor de RabbitMQ
# CMD ["python", "-m", "app.events.rabbit_consumer"]

# Imagen base oficial de Python
FROM python:3.11-slim

# Variables de entorno para Python (no .pyc, UTF-8)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_MODE=consumer  
ENV API_HOST=0.0.0.0

# Crear el directorio de la app
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && \
    apt-get install -y build-essential gcc && \
    apt-get clean

# Copiar requirements y dependencias
COPY requirements.txt /app/requirements.txt

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . /app

# Crear script de entrada
RUN echo '#!/bin/sh \n\
    if [ "$APP_MODE" = "api" ]; then \n\
    echo "Iniciando en modo API..." \n\
    python -m app.main \n\
    else \n\
    echo "Iniciando en modo Consumer..." \n\
    python -m app.events.rabbit_consumer \n\
    fi' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

EXPOSE 8001
# Usar el script de entrada
ENTRYPOINT ["/app/entrypoint.sh"]