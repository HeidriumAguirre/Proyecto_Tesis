"""
Carga y validacion de variables de entorno.
Centraliza la lectura desde .env / entorno del sistema.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=False)
    logger.info("Cargadas variables de entorno desde %s", ENV_PATH)
else:
    logger.info("No se encontro .env (%s); usando solo variables de entorno del sistema", ENV_PATH)


def _get(key: str, default: str | None = None, required: bool = False) -> str | None:
    val = os.getenv(key, default)
    if required and not val:
        raise RuntimeError(
            f"Variable de entorno requerida no definida: {key}. "
            f"Revisa tu archivo .env o las variables del contenedor."
        )
    return val


# --- Gemini ---
GEMINI_API_KEY: str = _get("GEMINI_API_KEY", required=True)  # type: ignore[assignment]

# --- MySQL ---
MYSQL_HOST: str = _get("MYSQL_HOST", "db_relacional")  # type: ignore[assignment]
MYSQL_PORT: int = int(_get("MYSQL_PORT", "3306"))  # type: ignore[arg-type]
MYSQL_USER: str = _get("MYSQL_USER", "root")  # type: ignore[assignment]
MYSQL_PASSWORD: str = _get("MYSQL_PASSWORD", "demo")  # type: ignore[assignment]
MYSQL_DATABASE: str = _get("MYSQL_DATABASE", "its_murialdo")  # type: ignore[assignment]

# --- Streamlit ---
STREAMLIT_SERVER_PORT: int = int(_get("STREAMLIT_SERVER_PORT", "8501"))  # type: ignore[arg-type]
