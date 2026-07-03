# Imagen base: fijamos minor version para builds reproducibles
# Para pinneado estricto, reemplazar por @sha256:<digest> tras `docker pull python:3.11.13-slim`
FROM python:3.11.13-slim

# libgomp1 es requerido por chromadb/hnswlib en slim
# ca-certificates habilita HTTPS outbound a Google APIs
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para correr la app
RUN groupadd --system --gid 1001 appuser \
    && useradd --system --uid 1001 --gid appuser --create-home --shell /bin/bash appuser

WORKDIR /app

# Instalar dependencias primero (mejor cacheo de capas)
COPY --chown=appuser:appuser requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el resto del codigo
COPY --chown=appuser:appuser . .

# Crear carpetas de datos con permisos correctos
RUN mkdir -p /app/chroma_db /app/certs \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('https://localhost:8501/_stcore/health', context=__import__('ssl')._create_unverified_context()).read()" || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.sslCertFile=/app/certs/server.crt", \
     "--server.sslKeyFile=/app/certs/server.key", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
