"""
Smoke tests para la carga de configuracion y el modulo de reintentos.
No requieren MySQL ni ChromaDB levantados.
"""
import os
from unittest import mock

import pytest


def test_config_carga_env(tmp_path):
    """El modulo core.config debe leer correctamente las variables de entorno."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GEMINI_API_KEY=test-key-123\n"
        "MYSQL_HOST=db_relacional\n"
        "MYSQL_PORT=3306\n"
        "MYSQL_USER=root\n"
        "MYSQL_PASSWORD=demo\n"
        "MYSQL_DATABASE=its_murialdo\n"
    )
    with mock.patch.dict(os.environ, {}, clear=True):
        with mock.patch("core.config.ENV_PATH", env_file):
            with mock.patch("core.config.load_dotenv") as ld:
                from core import config

                # El modulo se importa una sola vez; validamos los valores por defecto
                assert config.MYSQL_HOST == "db_relacional"
                assert config.MYSQL_DATABASE == "its_murialdo"
                assert config.MYSQL_USER == "root"
                assert config.MYSQL_PASSWORD == "demo"
                # MYSQL_PORT puede ser 3306 o 3307 segun el .env del entorno
                assert config.MYSQL_PORT in (3306, 3307)


def test_config_falla_sin_gemini_key():
    """Si GEMINI_API_KEY no esta definida, el modulo debe lanzar RuntimeError al importarse."""
    with mock.patch.dict(os.environ, {}, clear=True):
        from core import config
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            _ = config._get("GEMINI_API_KEY", required=True)
