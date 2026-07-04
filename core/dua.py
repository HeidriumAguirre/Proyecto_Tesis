"""
core/dua.py

Preferencias de accesibilidad DUA (Diseno Universal para el Aprendizaje):
- Modo nocturno
- Filtro de luz nocturna (filtro calido / antiazul)

Persistencia en `preferencias_dua JSON` de las tablas `usuario`
y `estudiante_pie`, segun el actor autenticado.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from typing import Literal

import streamlit as st

from core.retries import ejecutar_query_segura

logger = logging.getLogger("its_rag_math.dua")


@dataclass
class PreferenciasDUA:
    modo_nocturno: bool = False
    filtro_luz: bool = False

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str | None) -> "PreferenciasDUA":
        if not raw:
            return cls()
        try:
            data = json.loads(raw)
            return cls(
                modo_nocturno=bool(data.get("modo_nocturno", False)),
                filtro_luz=bool(data.get("filtro_luz", False)),
            )
        except (json.JSONDecodeError, TypeError):
            logger.warning("JSON de preferencias invalido, usando defaults")
            return cls()


# ---------------------------------------------------------------------------
# Persistencia en BD
# ---------------------------------------------------------------------------

def cargar_preferencias(conn, tabla: Literal["usuario", "estudiante_pie"], id_col: str, id_val: str) -> PreferenciasDUA:
    """Lee preferencias_dua de la tabla especificada. Defaults si no hay."""
    if tabla == "usuario":
        sql = f"SELECT preferencias_dua FROM usuario WHERE {id_col} = %s"
    else:
        sql = f"SELECT preferencias_dua FROM estudiante_pie WHERE {id_col} = %s"
    try:
        row = ejecutar_query_segura(conn, sql, (id_val,), fetch="one")
        if not row:
            return PreferenciasDUA()
        raw = row.get("preferencias_dua")
        # PyMySQL devuelve dict si JSON; string si texto
        if isinstance(raw, dict):
            return PreferenciasDUA(
                modo_nocturno=bool(raw.get("modo_nocturno", False)),
                filtro_luz=bool(raw.get("filtro_luz", False)),
            )
        return PreferenciasDUA.from_json(raw)
    except Exception:
        logger.exception("Error cargando preferencias DUA")
        return PreferenciasDUA()


def guardar_preferencias(conn, tabla: str, id_col: str, id_val: str, prefs: PreferenciasDUA) -> None:
    """Persiste preferencias_dua como JSON."""
    if tabla == "usuario":
        sql = "UPDATE usuario SET preferencias_dua = %s WHERE id_usuario = %s"
    elif tabla == "estudiante_pie":
        sql = "UPDATE estudiante_pie SET preferencias_dua = %s WHERE id_estudiante = %s"
    else:
        raise ValueError(f"Tabla no soportada: {tabla}")
    try:
        ejecutar_query_segura(conn, sql, (prefs.to_json(), id_val), fetch="none")
    except Exception:
        logger.exception("Error guardando preferencias DUA")


# ---------------------------------------------------------------------------
# UI helpers (CSS inyectado)
# ---------------------------------------------------------------------------

CSS_BASE = """
<style>
/* Variables DUA - se sobreescriben segun modo */
:root {
    --dua-bg: #FFFFFF;
    --dua-fg: #111111;
    --dua-card: #F8F9FA;
    --dua-border: #E1E8ED;
    --dua-accent: #0F2C59;
}
.dua-dark {
    --dua-bg: #1A1A1A;
    --dua-fg: #E6E6E6;
    --dua-card: #2A2A2A;
    --dua-border: #3A3A3A;
    --dua-accent: #5A8DD6;
}
.dua-warm .stApp {
    filter: sepia(0.32) saturate(0.85) hue-rotate(-12deg) !important;
}
.stApp { background-color: var(--dua-bg) !important; }
p, span, label, li, h1, h2, h3, h4, h5, h6 { color: var(--dua-fg) !important; }
div[data-testid="stChatMessage"] { background-color: var(--dua-card) !important; }
.perfil-card-estudiante { background-color: var(--dua-card) !important; }
</style>
"""


def aplicar_estilos(prefs: PreferenciasDUA) -> None:
    """Inyecta CSS segun preferencias."""
    st.markdown(CSS_BASE, unsafe_allow_html=True)
    if prefs.modo_nocturno:
        st.markdown(
            '<style>body, .stApp { background-color: #1A1A1A !important; }</style>',
            unsafe_allow_html=True,
        )
    if prefs.filtro_luz:
        st.markdown(
            """
            <style>
            .stApp { filter: sepia(0.32) saturate(0.85) hue-rotate(-12deg) !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )


def render_toggles(key_prefix: str = "dua") -> PreferenciasDUA:
    """Renderiza los toggles en el sidebar y devuelve el estado actual."""
    if f"{key_prefix}_nocturno" not in st.session_state:
        st.session_state[f"{key_prefix}_nocturno"] = False
    if f"{key_prefix}_filtro" not in st.session_state:
        st.session_state[f"{key_prefix}_filtro"] = False

    st.session_state[f"{key_prefix}_nocturno"] = st.toggle(
        "🌙 Modo Nocturno",
        value=st.session_state[f"{key_prefix}_nocturno"],
        key=f"{key_prefix}_tog_nocturno",
        help="Fondo oscuro para reducir fatiga visual.",
    )
    st.session_state[f"{key_prefix}_filtro"] = st.toggle(
        "🔅 Filtro de Luz Nocturna",
        value=st.session_state[f"{key_prefix}_filtro"],
        key=f"{key_prefix}_tog_filtro",
        help="Filtro calido/antiazul para reducir la sobreestimulacion visual.",
    )

    return PreferenciasDUA(
        modo_nocturno=st.session_state[f"{key_prefix}_nocturno"],
        filtro_luz=st.session_state[f"{key_prefix}_filtro"],
    )
