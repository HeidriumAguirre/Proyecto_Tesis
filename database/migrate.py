"""
database/migrate.py

Aplica las migraciones SQL del directorio data/migrations en orden.
Detecta que sentencias ya se ejecutaron y solo corre las nuevas.

Uso:
    python database/migrate.py

Notas:
- Cada archivo .sql de data/migrations se ejecuta una vez y se registra
  en la tabla `schema_migration`.
- El script es idempotente: si una migracion ya se aplico, se salta.
"""
from __future__ import annotations

import logging
import os
import re
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

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "migrations"


def asegurar_tabla_migracion(conn) -> None:
    """Crea la tabla de control de migraciones si no existe."""
    sql = """
        CREATE TABLE IF NOT EXISTS schema_migration (
          id            INT AUTO_INCREMENT PRIMARY KEY,
          filename      VARCHAR(255) NOT NULL UNIQUE,
          applied_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def obtener_migraciones_aplicadas(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM schema_migration")
        return {row["filename"] for row in cur.fetchall()}


def split_sql_statements(sql_text: str) -> list[str]:
    """
    Divide un script SQL en sentencias individuales.
    Ignora comentarios (-- ...) y respeta strings entre comillas.
    """
    # Quitar comentarios de linea
    sin_comentarios = re.sub(r"--[^\n]*", "", sql_text)
    # Quitar lineas vacias
    lineas = [l.strip() for l in sin_comentarios.splitlines() if l.strip()]
    texto = "\n".join(lineas)
    # Split por ;
    sentencias = [s.strip() for s in texto.split(";") if s.strip()]
    return sentencias


def ejecutar_archivo_sql(conn, path: Path) -> tuple[int, int]:
    """Ejecuta un archivo .sql. Devuelve (ejecutadas, saltadas)."""
    sql_text = path.read_text(encoding="utf-8")
    sentencias = split_sql_statements(sql_text)
    ejecutadas = 0
    saltadas = 0
    for stmt in sentencias:
        # Si la sentencia es solo un comentario, saltar
        if not stmt or stmt.startswith("--"):
            continue
        try:
            with conn.cursor() as cur:
                cur.execute(stmt)
            ejecutadas += 1
        except pymysql.err.OperationalError as e:
            code = e.args[0] if e.args else None
            if code in (1060, 1061, 1062, 1091):
                # 1060: duplicate column
                # 1061: duplicate key
                # 1062: duplicate entry
                # 1091: can't drop nonexistent
                saltadas += 1
                logger.info("  [SKIP] ya aplicada: %s...", stmt[:80].replace("\n", " "))
            else:
                logger.error("  [ERR ] operacion %s: %s", code, e)
                raise
        except pymysql.err.ProgrammingError as e:
            if "Duplicate" in str(e):
                saltadas += 1
            else:
                logger.error("  [ERR ] %s", e)
                raise
    conn.commit()
    return ejecutadas, saltadas


def registrar_migracion(conn, filename: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO schema_migration (filename) VALUES (%s) "
            "ON DUPLICATE KEY UPDATE applied_at = CURRENT_TIMESTAMP",
            (filename,),
        )
    conn.commit()


def ejecutar_migraciones() -> None:
    logger.info("Conectando a MySQL %s:%s/%s", MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE)
    conn = conectar_con_reintentos(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DATABASE,
    )

    asegurar_tabla_migracion(conn)
    aplicadas = obtener_migraciones_aplicadas(conn)
    logger.info("Migraciones ya aplicadas: %d", len(aplicadas))

    if not MIGRATIONS_DIR.exists():
        logger.warning("No existe el directorio %s", MIGRATIONS_DIR)
        return

    archivos = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not archivos:
        logger.info("Sin migraciones pendientes.")
        return

    for path in archivos:
        filename = path.name
        if filename in aplicadas:
            logger.info("[SKIP] %s (ya aplicada)", filename)
            continue
        logger.info("[APPLY] %s", filename)
        try:
            ejecutadas, saltadas = ejecutar_archivo_sql(conn, path)
            logger.info("  -> %d ejecutadas, %d ya existian", ejecutadas, saltadas)
            registrar_migracion(conn, filename)
        except Exception:
            logger.exception("Fallo aplicando %s. Abortando.", filename)
            conn.close()
            sys.exit(1)

    conn.close()
    logger.info("Migraciones finalizadas.")


if __name__ == "__main__":
    ejecutar_migraciones()
