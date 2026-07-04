"""
database/seed.py

Inserta datos semilla idempotentes para el piloto:
- 1 usuario docente PIE (Educador_PIE) con clave bcrypt
- 3 usuarios Estudiante + 3 registros en estudiante_pie
- Vinculaciones estudiante_diagnostico

Uso:
    python database/seed.py
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import bcrypt
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
logger = logging.getLogger("its_rag_math.seed")


DOCENTE = {
    "rut": "16.234.567-8",
    "nombre_completo": "Heidi Aguirrre Rivera",
    "correo_electronico": "heidrium.aguirre@murialdo.cl",
    "password": "Demo2026!",
    "rol": "Educador_PIE",
}

ESTUDIANTES = [
    {
        "rut": "25.123.456-7",
        "nombre_completo": "Mateo Gonzalez Perez",
        "correo_electronico": "mateo.gonzalez@murialdo.cl",
        "curso": "1_Basico",
        "curso_subdivision": "A",
        "nivel_adaptacion_lenguaje": "Alto",
        "requiere_apoyo_pictorico": 1,
        "diagnostico_codigo": "TEA",
    },
    {
        "rut": "25.234.567-8",
        "nombre_completo": "Sofia Martinez Lopez",
        "correo_electronico": "sofia.martinez@murialdo.cl",
        "curso": "2_Basico",
        "curso_subdivision": "B",
        "nivel_adaptacion_lenguaje": "Medio",
        "requiere_apoyo_pictorico": 1,
        "diagnostico_codigo": "TDAH",
    },
    {
        "rut": "25.345.678-9",
        "nombre_completo": "Lucas Rojas Silva",
        "correo_electronico": "lucas.rojas@murialdo.cl",
        "curso": "3_Basico",
        "curso_subdivision": "A",
        "nivel_adaptacion_lenguaje": "Bajo",
        "requiere_apoyo_pictorico": 0,
        "diagnostico_codigo": "DEA",
    },
]


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _upsert_usuario(conn, data: dict, password_hash: str | None = None) -> str:
    """Inserta o recupera el id_usuario por correo."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id_usuario FROM usuario WHERE correo_electronico = %s",
            (data["correo_electronico"],),
        )
        row = cur.fetchone()
        if row:
            logger.info("Usuario ya existe: %s (%s)", data["correo_electronico"], row["id_usuario"])
            return row["id_usuario"]

        clave_hash = password_hash or data.get("clave_hash") or "!"
        sql = """
            INSERT INTO usuario (id_usuario, rut, nombre_completo, correo_electronico,
                                 clave_hash, rol)
            VALUES (UUID(), %s, %s, %s, %s, %s)
        """
        cur.execute(
            sql,
            (
                data["rut"],
                data["nombre_completo"],
                data["correo_electronico"],
                clave_hash,
                data["rol"],
            ),
        )
        cur.execute(
            "SELECT id_usuario FROM usuario WHERE correo_electronico = %s",
            (data["correo_electronico"],),
        )
        row = cur.fetchone()
        conn.commit()
        logger.info("Usuario creado: %s -> %s", data["correo_electronico"], row["id_usuario"])
        return row["id_usuario"]


def _upsert_estudiante(conn, data: dict, id_docente: str) -> str:
    """Inserta o actualiza estudiante_pie. Devuelve id_estudiante."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id_estudiante FROM estudiante_pie WHERE rut = %s",
            (data["rut"],),
        )
        row = cur.fetchone()
        if row:
            logger.info("Estudiante ya existe: %s", data["rut"])
            return row["id_estudiante"]

        # Primero crear usuario tipo Estudiante
        id_usuario_est = _upsert_usuario(
            conn,
            {
                "rut": data["rut"],
                "nombre_completo": data["nombre_completo"],
                "correo_electronico": data["correo_electronico"],
                "rol": "Estudiante",
            },
        )

        sql = """
            INSERT INTO estudiante_pie
                (id_estudiante, id_usuario, rut, nombre_completo, correo_electronico,
                 curso, curso_subdivision, nivel_adaptacion_lenguaje,
                 requiere_apoyo_pictorico, created_by_usuario)
            VALUES (UUID(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(
            sql,
            (
                id_usuario_est,
                data["rut"],
                data["nombre_completo"],
                data["correo_electronico"],
                data["curso"],
                data["curso_subdivision"],
                data["nivel_adaptacion_lenguaje"],
                data["requiere_apoyo_pictorico"],
                id_docente,
            ),
        )
        cur.execute(
            "SELECT id_estudiante FROM estudiante_pie WHERE rut = %s",
            (data["rut"],),
        )
        row = cur.fetchone()
        id_estudiante = row["id_estudiante"]
        conn.commit()
        logger.info("Estudiante creado: %s (%s)", data["nombre_completo"], id_estudiante)
        return id_estudiante


def _vincular_diagnostico(conn, id_estudiante: str, codigo: str, id_docente: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id_diagnostico FROM diagnostico WHERE codigo = %s",
            (codigo,),
        )
        row = cur.fetchone()
        if not row:
            logger.warning("Diagnostico %s no existe, saltando vinculacion", codigo)
            return
        id_diag = row["id_diagnostico"]

        cur.execute(
            """
            SELECT 1 FROM estudiante_diagnostico
            WHERE id_estudiante = %s AND id_diagnostico = %s
            """,
            (id_estudiante, id_diag),
        )
        if cur.fetchone():
            return

        cur.execute(
            """
            INSERT INTO estudiante_diagnostico
                (id_estudiante, id_diagnostico, fecha_asignacion, id_usuario_registro)
            VALUES (%s, %s, CURDATE(), %s)
            """,
            (id_estudiante, id_diag, id_docente),
        )
        conn.commit()
        logger.info("Vinculado %s -> diagnostico %s", id_estudiante[:8], codigo)


def _seed_objetivo_aprendizaje(conn) -> str | None:
    """Inserta un OA generico por nivel si la tabla esta vacia."""
    with conn.cursor() as cur:
        cur.execute("SELECT id_oa FROM objetivo_aprendizaje LIMIT 1")
        row = cur.fetchone()
        if row:
            return row["id_oa"]
        sql = """
            INSERT INTO objetivo_aprendizaje
                (id_oa, codigo, descripcion, nivel_curso, unidad_tematica, eje)
            VALUES
                (UUID(), 'OA01-MAT-1B', 'Contar numeros del 0 al 20 de uno en uno y de dos en dos.', '1_Basico', 'Numeros', 'Numeros y operaciones'),
                (UUID(), 'OA01-MAT-2B', 'Contar numeros del 0 al 100 de uno en uno y de diez en diez.', '2_Basico', 'Numeros', 'Numeros y operaciones'),
                (UUID(), 'OA01-MAT-3B', 'Contar numeros del 0 al 1000.', '3_Basico', 'Numeros', 'Numeros y operaciones'),
                (UUID(), 'OA01-MAT-4B', 'Contar numeros del 0 al 10000.', '4_Basico', 'Numeros', 'Numeros y operaciones')
        """
        cur.execute(sql)
        conn.commit()
        cur.execute("SELECT id_oa FROM objetivo_aprendizaje WHERE nivel_curso='1_Basico' LIMIT 1")
        row = cur.fetchone()
        return row["id_oa"] if row else None


def ejecutar_seed() -> None:
    logger.info("Conectando a MySQL %s:%s/%s", MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE)
    conn = conectar_con_reintentos(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )

    # 1) Docente
    docente_hash = _hash_password(DOCENTE["password"])
    id_docente = _upsert_usuario(conn, DOCENTE, password_hash=docente_hash)

    # 2) Estudiantes + diagnosticos
    for est in ESTUDIANTES:
        id_est = _upsert_estudiante(conn, est, id_docente)
        _vincular_diagnostico(conn, id_est, est["diagnostico_codigo"], id_docente)

    # 3) OA generico
    _seed_objetivo_aprendizaje(conn)

    conn.close()
    logger.info("Seed completo.")
    logger.info("Credenciales docente: %s / %s", DOCENTE["correo_electronico"], DOCENTE["password"])
    for est in ESTUDIANTES:
        logger.info("Correo estudiante: %s", est["correo_electronico"])


if __name__ == "__main__":
    ejecutar_seed()
