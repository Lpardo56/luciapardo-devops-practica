# Dockerfile de la Tienda Online (API FastAPI)
# Autora: Lucía Pardo

# Imagen base ligera de Python
FROM python:3.12-slim

# No generar .pyc, ver los logs al momento y valores por defecto de las variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    LOG_LEVEL=info

WORKDIR /app

# 1) Primero solo las dependencias, así Docker reutiliza esta capa
#    mientras no cambie requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Usuario sin privilegios para no ejecutar la app como root
RUN useradd --create-home --shell /usr/sbin/nologin appuser

# 3) Código fuente
COPY src/ ./src/

# 4) Permisos: el usuario appuser es el dueño del código y puede leerlo y ejecutarlo
RUN chown -R appuser:appuser /app && chmod -R u+rwX /app
USER appuser

WORKDIR /app/src
EXPOSE 8000

# Comando de inicio: arranca la API con uvicorn en el puerto de la variable PORT
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --log-level ${LOG_LEVEL}"]
