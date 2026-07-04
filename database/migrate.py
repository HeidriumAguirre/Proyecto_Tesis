"""
database/migrate.py

Aplica las migraciones del schema en orden idempotente.
Detecta que tablas/columnas ya existen y solo crea lo faltante.

Uso:
    python database/migrate.py
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import (  # noqa: E402
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)
from core.retries import conectar_con_reintentos  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("its_rag_math.migrate")


# Lista de sentencias idempotentes.
# Cada tupla es (nombre_logico, sql).
MIGRACIONES: list[tuple[str, str]] = [
    # --- Extensiones a usuario ---
    (
        "usuario.preferencias_dua",
        """
        ALTER TABLE usuario
        ADD COLUMN IF NOT EXISTS preferencias_dua JSON NULL
        """,
    ),
    (
        "usuario.deleted_at",
        """
        ALTER TABLE usuario
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL
        """,
    ),
    # --- Extensiones a estudiante_pie ---
    (
        "estudiante_pie.curso_subdivision",
        """
        ALTER TABLE estudiante_pie
        ADD COLUMN IF NOT EXISTS curso_subdivision ENUM('A','B') NULL AFTER curso
        """,
    ),
    (
        "estudiante_pie.preferencias_dua",
        """
        ALTER TABLE estudiante_pie
        ADD COLUMN IF NOT EXISTS preferencias_dua JSON NULL
        """,
    ),
    (
        "estudiante_pie.deleted_at",
        """
        ALTER TABLE estudiante_pie
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL
        """,
    ),
    (
        "estudiante_pie.created_by_usuario",
        """
        ALTER TABLE estudiante_pie
        ADD COLUMN IF NOT EXISTS created_by_usuario CHAR(36) NULL
        """,
    ),
    # --- Extensiones a sesion_tutoria ---
    (
        "sesion_tutoria.curso_subdivision",
        """
        ALTER TABLE sesion_tutoria
        ADD COLUMN IF NOT EXISTS curso_subdivision ENUM('A','B') NULL AFTER id_oa
        """,
    ),
    (
        "sesion_tutoria.id_usuario",
        """
        ALTER TABLE sesion_tutoria
        ADD COLUMN IF NOT EXISTS id_usuario CHAR(36) NULL AFTER id_estudiante
        """,
    ),
    (
        "sesion_tutoria.updated_at",
        """
        ALTER TABLE sesion_tutoria
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        """,
    ),
    # --- Tablas nuevas ---
    (
        "intento_login",
        """
        CREATE TABLE IF NOT EXISTS intento_login (
          id_intento BIGINT AUTO_INCREMENT PRIMARY KEY,
          email VARCHAR(150) NOT NULL,
          exitoso TINYINT(1) NOT NULL,
          ip_origen VARCHAR(45) NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_intento_email_fecha (email, created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ),
    (
        "auditoria_docente",
        """
        CREATE TABLE IF NOT EXISTS auditoria_docente (
          id_auditoria BIGINT AUTO_INCREMENT PRIMARY KEY,
          id_usuario CHAR(36) NOT NULL,
          accion VARCHAR(50) NOT NULL,
          tabla_afectada VARCHAR(50) NULL,
          id_registro VARCHAR(36) NULL,
          detalle JSON NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_aud_usuario (id_usuario, created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ),
]


def ejecutar_migraciones() -> None:
    logger.info("Conectando a MySQL %s:%s/%s", MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE)
    conn = conectar_con_reintentos(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )

    ejecutadas = 0
    saltadas = 0
    for nombre, sql in MIGRACIONES:
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            ejecutadas += 1
            logger.info("[OK]   %s", nombre)
        except pymysql.err.OperationalError as e:
            if e.args and e.args[0] in (1060, 1061):  # duplicate column / duplicate key
                saltadas += 1
                logger.info("[SKIP] %s (ya existe)", nombre)
            else:
                logger.exception("[ERR]  %s", nombre)
                raise
        except pymysql.err.ProgrammingError as e:
            if e.args and "Duplicate" in str(e):
                saltadas += 1
                logger.info("[SKIP] %s (ya existe)", nombre)
            else:
                logger.exception("[ERR]  %s", nombre)
                raise

    conn.close()
    logger.info("Migraciones completas: %d aplicadas, %d ya existian", ejecutadas, saltadas)


if __name__ == "__main__":
    ejecutar_migraciones()
