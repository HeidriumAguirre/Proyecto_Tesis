"""
core/admin.py

CRUD del docente PIE sobre `estudiante_pie` y `sesion_tutoria`.
Implementa soft delete (deleted_at) y badges de color para estado de sesion.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from core.retries import ejecutar_query_segura

logger = logging.getLogger("its_rag_math.admin")

# Colores de badges por estado
COLOR_POR_ESTADO = {
    "Activa": "#FFD700",      # amarillo
    "Completada": "#28A745",  # verde
    "Abandonada": "#DC3545",  # rojo
}
EMOJI_POR_ESTADO = {
    "Activa": "🟡",
    "Completada": "🟢",
    "Abandonada": "🔴",
}

CURSOS_VALIDOS = ["1_Basico", "2_Basico", "3_Basico", "4_Basico"]
SUBDIVISIONES_VALIDAS = ["A", "B"]
NIVELES_ADAPTACION = ["Alto", "Medio", "Bajo"]


# ---------------------------------------------------------------------------
# Modelos de datos
# ---------------------------------------------------------------------------

@dataclass
class Estudiante:
    id_estudiante: str
    id_usuario: str
    rut: str
    nombre_completo: str
    correo_electronico: str | None
    curso: str
    curso_subdivision: str | None
    nivel_adaptacion_lenguaje: str
    requiere_apoyo_pictorico: bool
    created_by_usuario: str | None

    @classmethod
    def from_row(cls, row: dict) -> "Estudiante":
        return cls(
            id_estudiante=row["id_estudiante"],
            id_usuario=row.get("id_usuario") or "",
            rut=row["rut"],
            nombre_completo=row["nombre_completo"],
            correo_electronico=row.get("correo_electronico"),
            curso=row["curso"],
            curso_subdivision=row.get("curso_subdivision"),
            nivel_adaptacion_lenguaje=row.get("nivel_adaptacion_lenguaje") or "Medio",
            requiere_apoyo_pictorico=bool(row.get("requiere_apoyo_pictorico")),
            created_by_usuario=row.get("created_by_usuario"),
        )


@dataclass
class SesionTutoria:
    id_sesion: str
    id_estudiante: str
    curso_subdivision: str | None
    fecha_inicio: str
    fecha_fin: str | None
    estado_sesion: str

    @classmethod
    def from_row(cls, row: dict) -> "SesionTutoria":
        return cls(
            id_sesion=row["id_sesion"],
            id_estudiante=row["id_estudiante"],
            curso_subdivision=row.get("curso_subdivision"),
            fecha_inicio=str(row.get("fecha_inicio") or ""),
            fecha_fin=str(row.get("fecha_fin") or "") if row.get("fecha_fin") else None,
            estado_sesion=row.get("estado_sesion") or "Activa",
        )


# ---------------------------------------------------------------------------
# Listados
# ---------------------------------------------------------------------------

def listar_estudiantes_por_curso(
    conn, curso: str, subdivision: str | None = None, incluir_eliminados: bool = False
) -> list[Estudiante]:
    """Lista los estudiantes PIE filtrados por curso (+ subdivision opcional)."""
    where = ["e.curso = %s"]
    params: list[Any] = [curso]
    if subdivision:
        where.append("e.curso_subdivision = %s")
        params.append(subdivision)
    if not incluir_eliminados:
        where.append("e.deleted_at IS NULL")

    sql = f"""
        SELECT e.id_estudiante, e.id_usuario, e.rut, e.nombre_completo, e.correo_electronico,
               e.curso, e.curso_subdivision, e.nivel_adaptacion_lenguaje,
               e.requiere_apoyo_pictorico, e.created_by_usuario
        FROM estudiante_pie e
        WHERE {' AND '.join(where)}
        ORDER BY e.nombre_completo ASC
    """
    try:
        rows = ejecutar_query_segura(conn, sql, tuple(params), fetch="all") or []
    except Exception:
        logger.exception("Error listando estudiantes")
        return []
    return [Estudiante.from_row(r) for r in rows]


def listar_sesiones_de_curso(
    conn, curso: str, subdivision: str | None = None, limite: int = 30
) -> list[SesionTutoria]:
    """Lista las ultimas sesiones de los estudiantes de un curso."""
    where = ["e.curso = %s"]
    params: list[Any] = [curso]
    if subdivision:
        where.append("s.curso_subdivision = %s")
        params.append(subdivision)
    sql = f"""
        SELECT s.id_sesion, s.id_estudiante, s.curso_subdivision,
               s.fecha_inicio, s.fecha_fin, s.estado_sesion
        FROM sesion_tutoria s
        JOIN estudiante_pie e ON e.id_estudiante = s.id_estudiante
        WHERE {' AND '.join(where)}
        ORDER BY s.fecha_inicio DESC
        LIMIT %s
    """
    params.append(limite)
    try:
        rows = ejecutar_query_segura(conn, sql, tuple(params), fetch="all") or []
    except Exception:
        logger.exception("Error listando sesiones")
        return []
    return [SesionTutoria.from_row(r) for r in rows]


def obtener_estudiante_por_id(conn, id_estudiante: str) -> Estudiante | None:
    sql = """
        SELECT e.id_estudiante, e.id_usuario, e.rut, e.nombre_completo, e.correo_electronico,
               e.curso, e.curso_subdivision, e.nivel_adaptacion_lenguaje,
               e.requiere_apoyo_pictorico, e.created_by_usuario
        FROM estudiante_pie e
        WHERE e.id_estudiante = %s AND e.deleted_at IS NULL
    """
    try:
        row = ejecutar_query_segura(conn, sql, (id_estudiante,), fetch="one")
    except Exception:
        logger.exception("Error buscando estudiante")
        return None
    return Estudiante.from_row(row) if row else None


# ---------------------------------------------------------------------------
# Diagnosticos (para selects del formulario)
# ---------------------------------------------------------------------------

def listar_diagnosticos(conn) -> list[dict]:
    sql = "SELECT id_diagnostico, codigo, nombre_completo FROM diagnostico ORDER BY codigo"
    try:
        return ejecutar_query_segura(conn, sql, fetch="all") or []
    except Exception:
        logger.exception("Error listando diagnosticos")
        return []


def obtener_diagnosticos_de_estudiante(conn, id_estudiante: str) -> list[str]:
    sql = """
        SELECT d.codigo
        FROM estudiante_diagnostico ed
        JOIN diagnostico d ON d.id_diagnostico = ed.id_diagnostico
        WHERE ed.id_estudiante = %s
    """
    try:
        rows = ejecutar_query_segura(conn, sql, (id_estudiante,), fetch="all") or []
    except Exception:
        logger.exception("Error leyendo diagnosticos del estudiante")
        return []
    return [r["codigo"] for r in rows]


def set_diagnosticos_de_estudiante(
    conn, id_estudiante: str, codigos: list[str], id_docente: str
) -> None:
    """Reemplaza el set de diagnosticos del estudiante."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM estudiante_diagnostico WHERE id_estudiante = %s",
                (id_estudiante,),
            )
            for codigo in codigos:
                cur.execute(
                    "SELECT id_diagnostico FROM diagnostico WHERE codigo = %s",
                    (codigo,),
                )
                row = cur.fetchone()
                if not row:
                    continue
                cur.execute(
                    """
                    INSERT INTO estudiante_diagnostico
                        (id_estudiante, id_diagnostico, fecha_asignacion, id_usuario_registro)
                    VALUES (%s, %s, CURDATE(), %s)
                    """,
                    (id_estudiante, row["id_diagnostico"], id_docente),
                )
        conn.commit()
    except Exception:
        logger.exception("Error actualizando diagnosticos")
        conn.rollback()
        raise


# ---------------------------------------------------------------------------
# CREATE / UPDATE
# ---------------------------------------------------------------------------

def crear_estudiante(
    conn,
    *,
    rut: str,
    nombre_completo: str,
    correo_electronico: str | None,
    curso: str,
    curso_subdivision: str | None,
    nivel_adaptacion_lenguaje: str,
    requiere_apoyo_pictorico: bool,
    id_docente: str,
) -> Estudiante:
    """Crea un usuario tipo Estudiante y su registro en estudiante_pie."""
    if curso not in CURSOS_VALIDOS:
        raise ValueError(f"Curso invalido: {curso}")
    if nivel_adaptacion_lenguaje not in NIVELES_ADAPTACION:
        raise ValueError(f"Nivel invalido: {nivel_adaptacion_lenguaje}")
    if curso_subdivision and curso_subdivision not in SUBDIVISIONES_VALIDAS:
        raise ValueError(f"Subdivision invalida: {curso_subdivision}")

    with conn.cursor() as cur:
        # 1) Crear usuario tipo Estudiante
        id_usuario = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO usuario
                (id_usuario, rut, nombre_completo, correo_electronico, clave_hash, rol)
            VALUES (%s, %s, %s, %s, %s, 'Estudiante')
            """,
            (id_usuario, rut, nombre_completo, correo_electronico or None, "!"),
        )
        # 2) Crear estudiante_pie (id_estudiante se genera por DEFAULT UUID() en la BD)
        cur.execute(
            """
            INSERT INTO estudiante_pie
                (id_usuario, rut, nombre_completo, correo_electronico,
                 curso, curso_subdivision, nivel_adaptacion_lenguaje,
                 requiere_apoyo_pictorico, created_by_usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                id_usuario, rut, nombre_completo, correo_electronico or None,
                curso, curso_subdivision, nivel_adaptacion_lenguaje,
                1 if requiere_apoyo_pictorico else 0, id_docente,
            ),
        )
    conn.commit()
    # Recuperar el id_estudiante generado por la BD (DEFAULT UUID())
    row = ejecutar_query_segura(
        conn,
        "SELECT id_estudiante FROM estudiante_pie WHERE id_usuario = %s",
        (id_usuario,),
        fetch="one",
    )
    if not row:
        raise RuntimeError("No se pudo recuperar el id_estudiante tras el INSERT")
    return obtener_estudiante_por_id(conn, row["id_estudiante"])  # type: ignore[return-value]


def actualizar_estudiante(
    conn,
    *,
    id_estudiante: str,
    nombre_completo: str,
    correo_electronico: str | None,
    curso: str,
    curso_subdivision: str | None,
    nivel_adaptacion_lenguaje: str,
    requiere_apoyo_pictorico: bool,
) -> None:
    sql = """
        UPDATE estudiante_pie SET
            nombre_completo = %s,
            correo_electronico = %s,
            curso = %s,
            curso_subdivision = %s,
            nivel_adaptacion_lenguaje = %s,
            requiere_apoyo_pictorico = %s
        WHERE id_estudiante = %s AND deleted_at IS NULL
    """
    ejecutar_query_segura(
        conn,
        sql,
        (
            nombre_completo,
            correo_electronico or None,
            curso,
            curso_subdivision,
            nivel_adaptacion_lenguaje,
            1 if requiere_apoyo_pictorico else 0,
            id_estudiante,
        ),
        fetch="none",
    )


# ---------------------------------------------------------------------------
# Soft delete
# ---------------------------------------------------------------------------

def soft_delete_estudiante(conn, id_estudiante: str) -> None:
    sql = "UPDATE estudiante_pie SET deleted_at = NOW() WHERE id_estudiante = %s"
    ejecutar_query_segura(conn, sql, (id_estudiante,), fetch="none")


def restaurar_estudiante(conn, id_estudiante: str) -> None:
    sql = "UPDATE estudiante_pie SET deleted_at = NULL WHERE id_estudiante = %s"
    ejecutar_query_segura(conn, sql, (id_estudiante,), fetch="none")


# ---------------------------------------------------------------------------
# Gestion de sesiones del docente
# ---------------------------------------------------------------------------

def cerrar_sesion_como_completada(conn, id_sesion: str) -> None:
    sql = """
        UPDATE sesion_tutoria
        SET estado_sesion = 'Completada', fecha_fin = NOW()
        WHERE id_sesion = %s
    """
    ejecutar_query_segura(conn, sql, (id_sesion,), fetch="none")


def marcar_sesion_abandonada(conn, id_sesion: str) -> None:
    sql = """
        UPDATE sesion_tutoria
        SET estado_sesion = 'Abandonada', fecha_fin = NOW()
        WHERE id_sesion = %s
    """
    ejecutar_query_segura(conn, sql, (id_sesion,), fetch="none")


def sesiones_activas_por_estudiante(conn, id_estudiante: str) -> list[SesionTutoria]:
    sql = """
        SELECT id_sesion, id_estudiante, curso_subdivision, fecha_inicio, fecha_fin, estado_sesion
        FROM sesion_tutoria
        WHERE id_estudiante = %s AND estado_sesion = 'Activa'
        ORDER BY fecha_inicio DESC
    """
    try:
        rows = ejecutar_query_segura(conn, sql, (id_estudiante,), fetch="all") or []
    except Exception:
        logger.exception("Error listando sesiones activas")
        return []
    return [SesionTutoria.from_row(r) for r in rows]


# ---------------------------------------------------------------------------
# Helpers de UI
# ---------------------------------------------------------------------------

def badge_html(estado: str, id_sesion: str | None = None) -> str:
    """Devuelve HTML para un badge de color segun el estado de sesion."""
    color = COLOR_POR_ESTADO.get(estado, "#888888")
    emoji = EMOJI_POR_ESTADO.get(estado, "⚪")
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:12px;font-size:12px;font-weight:600;">'
        f'{emoji} {estado}</span>'
    )
