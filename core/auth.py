"""
core/auth.py

Autenticacion dual:
- Estudiante: solo correo (valida contra usuario + estudiante_pie).
- Docente: correo + contrasena (bcrypt) con rate limit.

La capa de UI (app.py) orquesta los formularios y maneja session_state.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

import bcrypt
import pymysql

from core.retries import ejecutar_query_segura

logger = logging.getLogger("its_rag_math.auth")

MAX_INTENTOS_FALLIDOS = 5
VENTANA_RATE_MINUTOS = 15

RolUsuario = Literal["Estudiante", "Educador_PIE", "Administrador", "Profesor_Asignatura"]


@dataclass
class SesionEstudiante:
    """Payload que la UI guarda en session_state al autenticar un estudiante."""
    id_usuario: str
    id_estudiante: str
    correo_electronico: str
    nombre_completo: str
    curso: str
    curso_subdivision: str | None
    # Campos sensibles (NO mostrar al alumno, solo al LLM):
    nivel_adaptacion_lenguaje: str
    requiere_apoyo_pictorico: bool
    diagnosticos: str | None


@dataclass
class SesionDocente:
    """Payload que la UI guarda en session_state al autenticar un docente."""
    id_usuario: str
    correo_electronico: str
    nombre_completo: str
    rol: RolUsuario


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _registrar_intento(conn, email: str, exitoso: bool) -> None:
    sql = "INSERT INTO intento_login (email, exitoso) VALUES (%s, %s)"
    try:
        ejecutar_query_segura(conn, sql, (email, 1 if exitoso else 0), fetch="none")
    except Exception:
        logger.exception("No se pudo registrar intento de login para %s", email)


def _contar_intentos_fallidos(conn, email: str, minutos: int = VENTANA_RATE_MINUTOS) -> int:
    """Cuenta los intentos fallidos en los ultimos N minutos."""
    sql = """
        SELECT COUNT(*) AS total FROM intento_login
        WHERE email = %s
          AND exitoso = 0
          AND created_at >= (NOW() - INTERVAL %s MINUTE)
    """
    try:
        row = ejecutar_query_segura(conn, sql, (email, minutos), fetch="one")
        return int(row["total"]) if row else 0
    except Exception:
        logger.exception("Error contando intentos fallidos")
        return 0


def _verificar_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Login Estudiante
# ---------------------------------------------------------------------------

def autenticar_estudiante(conn, correo: str) -> SesionEstudiante | None:
    """
    Busca el correo en `usuario` y exige que tenga un estudiante_pie activo.
    Sin contrasena. Devuelve None si no existe o esta soft-deleted.
    """
    if not correo or "@" not in correo:
        return None

    sql = """
        SELECT
            u.id_usuario,
            u.correo_electronico,
            u.nombre_completo,
            e.id_estudiante,
            e.curso,
            e.curso_subdivision,
            e.nivel_adaptacion_lenguaje,
            e.requiere_apoyo_pictorico,
            (SELECT GROUP_CONCAT(d.codigo SEPARATOR ', ')
             FROM estudiante_diagnostico ed
             JOIN diagnostico d ON d.id_diagnostico = ed.id_diagnostico
             WHERE ed.id_estudiante = e.id_estudiante) AS diagnosticos
        FROM usuario u
        JOIN estudiante_pie e ON e.id_usuario = u.id_usuario
        WHERE u.correo_electronico = %s
          AND u.rol = 'Estudiante'
          AND u.deleted_at IS NULL
          AND e.deleted_at IS NULL
    """
    try:
        row = ejecutar_query_segura(conn, sql, (correo.strip().lower(),), fetch="one")
    except Exception:
        logger.exception("Error en lookup de estudiante %s", correo)
        return None

    _registrar_intento(conn, correo, exitoso=row is not None)

    if not row:
        return None

    return SesionEstudiante(
        id_usuario=row["id_usuario"],
        id_estudiante=row["id_estudiante"],
        correo_electronico=row["correo_electronico"],
        nombre_completo=row["nombre_completo"],
        curso=row["curso"],
        curso_subdivision=row.get("curso_subdivision"),
        nivel_adaptacion_lenguaje=row.get("nivel_adaptacion_lenguaje") or "Medio",
        requiere_apoyo_pictorico=bool(row.get("requiere_apoyo_pictorico")),
        diagnosticos=row.get("diagnosticos"),
    )


# ---------------------------------------------------------------------------
# Login Docente
# ---------------------------------------------------------------------------

def autenticar_docente(
    conn, correo: str, password: str
) -> tuple[SesionDocente | None, str | None]:
    """
    Verifica correo + contrasena. Aplica rate limit.
    Retorna (sesion, mensaje_error).
    """
    if not correo or "@" not in correo:
        return None, "Correo invalido."

    email_norm = correo.strip().lower()

    # Rate limit
    fallidos = _contar_intentos_fallidos(conn, email_norm)
    if fallidos >= MAX_INTENTOS_FALLIDOS:
        msg = f"Demasiados intentos fallidos. Espera {VENTANA_RATE_MINUTOS} minutos."
        logger.warning("Bloqueo por rate limit para %s", email_norm)
        return None, msg

    sql = """
        SELECT id_usuario, correo_electronico, nombre_completo, rol, clave_hash
        FROM usuario
        WHERE correo_electronico = %s
          AND rol IN ('Educador_PIE', 'Administrador', 'Profesor_Asignatura')
          AND deleted_at IS NULL
    """
    try:
        row = ejecutar_query_segura(conn, sql, (email_norm,), fetch="one")
    except Exception:
        logger.exception("Error en lookup de docente %s", email_norm)
        return None, "Error de conexion. Intenta de nuevo."

    if not row:
        _registrar_intento(conn, email_norm, exitoso=False)
        return None, "Credenciales invalidas."

    if not _verificar_password(password, row["clave_hash"]):
        _registrar_intento(conn, email_norm, exitoso=False)
        return None, "Credenciales invalidas."

    _registrar_intento(conn, email_norm, exitoso=True)

    return SesionDocente(
        id_usuario=row["id_usuario"],
        correo_electronico=row["correo_electronico"],
        nombre_completo=row["nombre_completo"],
        rol=row["rol"],
    ), None


# ---------------------------------------------------------------------------
# Logout / helpers de sesion
# ---------------------------------------------------------------------------

def cerrar_sesion() -> None:
    """Limpia la sesion en st.session_state. La UI debe rerun()."""
    import streamlit as st

    for k in [
        "tipo_usuario",
        "estudiante",
        "docente",
        "id_sesion_tutoria",
        "messages",
    ]:
        if k in st.session_state:
            del st.session_state[k]


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------

def registrar_auditoria(
    conn, id_usuario: str, accion: str, tabla: str | None = None,
    id_registro: str | None = None, detalle: dict | None = None,
) -> None:
    import json as _json

    sql = """
        INSERT INTO auditoria_docente (id_usuario, accion, tabla_afectada, id_registro, detalle)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        ejecutar_query_segura(
            conn,
            sql,
            (id_usuario, accion, tabla, id_registro, _json.dumps(detalle) if detalle else None),
            fetch="none",
        )
    except Exception:
        logger.exception("No se pudo registrar auditoria %s para usuario %s", accion, id_usuario)
