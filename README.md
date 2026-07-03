# ITS RAG Math — Colegio Murialdo Valparaíso

Sistema de Tutoría Inteligente (ITS) inclusivo para estudiantes PIE, con
RAG sobre documentos oficiales del Mineduc, integración multimodal con
Gemini 2.5 Flash y entrada de voz para perfiles TEA/TDAH.

## Stack

- **Frontend**: Streamlit 1.58 con HTTPS (cert autofirmado local)
- **LLM**: Google Gemini 2.5 Flash (texto + audio multimodal)
- **BD relacional**: MySQL 8 (perfil PIE, historial, sesiones)
- **BD vectorial**: ChromaDB persistente (andamiaje curricular)
- **Orquestación**: Docker Compose (servicios `db_relacional` y `app_tutor`)
- **Resiliencia**: `tenacity` para reintentos con backoff exponencial
- **STT/entrada voz**: `streamlit-mic-recorder` → Gemini multimodal

## Estructura

```
.
├── app.py                       # Frontend Streamlit (HTTPS)
├── main.py                      # CLI de prueba del flujo
├── ingest_pipeline.py           # Carga PDFs Mineduc a MySQL + ChromaDB
├── core/
│   ├── config.py                # Carga .env y variables de entorno
│   ├── retries.py               # Conexión MySQL con reintentos tenacity
│   ├── prompts.py               # System instruction socrático
│   └── llm.py                   # Helpers LLM (ventana, parseo multimodal)
├── tests/                       # Smoke tests pytest
├── docker/
│   └── certs/                   # Certs TLS autofirmados (generar con mkcert)
├── .streamlit/
│   └── config.toml              # Configuración Streamlit
├── .env                         # Variables de entorno (no versionado)
├── .env.example                 # Plantilla de .env
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Setup local

### 1. Prerrequisitos
- Python 3.11
- Docker Desktop + Docker Compose
- mkcert (para certs TLS locales)

### 2. Variables de entorno

```bash
cp .env.example .env
# Edita .env y rellena GEMINI_API_KEY
```

### 3. Generar certs TLS autofirmados

```bash
mkcert -install
mkdir -p docker/certs
mkcert -cert-file docker/certs/server.crt \
       -key-file docker/certs/server.key \
       localhost 127.0.0.1
```

Detalle completo en [`docker/certs/README.txt`](docker/certs/README.txt).

### 4. Levantar con Docker Compose

```bash
docker compose up --build
```

Accede a `https://localhost:8501` (acepta el cert autofirmado la primera vez).

## Setup para desarrollo local (sin Docker)

```bash
# Crear venv
uv venv .venv --python 3.11

# Instalar dependencias
uv pip install -r requirements.txt

# Levantar MySQL por separado (puerto 3306, db its_murialdo)

# Correr tests
.venv/bin/pytest tests/

# Correr la app
.venv/bin/streamlit run app.py
```

## Tests

```bash
pytest tests/ -v
```

## Uso

1. Ingresa el RUT del estudiante PIE.
2. La app carga su perfil y muestra el panel.
3. Escribe con el teclado **o** usa el botón 🎤 para hablar.
4. La respuesta del Tutor Socrático aparece con TTS (botón "Escuchar a Sócrates").

## Seguridad

- API Key en `.env` (excluido por `.gitignore`).
- Certs en `docker/certs/` (excluidos).
- Conexión MySQL con reintentos y ping-reconnect.
- Streamlit corre como usuario `appuser` no-root dentro del contenedor.

## Próximos pasos (post-piloto)

- HTTPS institucional (Let's Encrypt o cert del colegio).
- Logging estructurado a archivo / ELK.
- Métricas de uso por estudiante.
- Internacionalización es-CL / en-US.
- Tests e2e con Selenium / Playwright.
