"""
database/reparar_estudiantes_bug.py

Repara los registros de estudiante_pie que quedaron con el bug del
INSERT desalineado en crear_estudiante(): el id_usuario de la BD
quedo escrito en la columna rut, y el id_estudiante de Python
quedo en id_usuario.

Este script:
1. Encuentra estudiante_pie donde el id_usuario NO existe en
   usuario.id_usuario (FK rota).
2. Para cada uno, busca el usuario correcto por rut.
3. Actualiza estudiante_pie.id_usuario al id_usuario real.

Uso:
    docker compose exec app_tutor python database/reparar_estudiantes_bug.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import (  # noqa: E402
    MYSQL_DATABASE, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, MYSQL_USER,
)
from core.retries import conectar_con_reintentos  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("its_rag_math.reparar")


def main() -> None:
    logger.info("Conectando a MySQL %s:%s/%s", MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE)
    conn = conectar_con_reintentos(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DATABASE,
    )

    # Detectar estudiante_pie con id_usuario que NO apunta a un usuario real
    sql_diagnostico = """
        SELECT e.id_estudiante, e.rut, e.nombre_completo, e.id_usuario
        FROM estudiante_pie e
        LEFT JOIN usuario u ON u.id_usuario = e.id_usuario
        WHERE u.id_usuario IS NULL
          AND e.deleted_at IS NULL
    """
    with conn.cursor() as cur:
        cur.execute(sql_diagnostico)
        huerfanos = cur.fetchall()

    if not huerfanos:
        logger.info("No se encontraron registros huerfanos. Nada que reparar.")
        conn.close()
        return

    logger.warning("Encontrados %d registros huerfanos. Reparando...", len(huerfanos))

    reparados = 0
    fallidos = 0
    for row in huerfanos:
        id_est = row["id_estudiante"]
        rut = row["rut"]
        # Buscar el usuario real por RUT
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_usuario FROM usuario WHERE rut = %s AND rol = 'Estudiante' AND deleted_at IS NULL",
                (rut,),
            )
            u = cur.fetchone()
        if not u:
            logger.error(
                "  [SKIP] id_estudiante=%s rut=%s: no se encontro usuario con ese RUT",
                id_est, rut,
            )
            fallidos += 1
            continue
        id_usuario_real = u["id_usuario"]
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE estudiante_pie SET id_usuario = %s WHERE id_estudiante = %s",
                (id_usuario_real, id_est),
            )
        conn.commit()
        logger.info(
            "  [OK] id_estudiante=%s rut=%s -> id_usuario=%s",
            id_est[:8], rut, id_usuario_real[:8],
        )
        reparados += 1

    conn.close()
    logger.info("Reparacion finalizada: %d reparados, %d fallidos", reparados, fallidos)


if __name__ == "__main__":
    main()
