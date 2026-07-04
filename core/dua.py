"""
core/dua.py

Preferencias de accesibilidad DUA (Diseno Universal para el Aprendizaje):
- Modo nocturno (tema oscuro completo)
- Filtro de luz nocturna: slider 0-100% (filtro calido / antiazul)

Persistencia en `preferencias_dua JSON` de las tablas `usuario`
y `estudiante_pie`, segun el actor autenticado.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass

import streamlit as st

from core.retries import ejecutar_query_segura

logger = logging.getLogger("its_rag_math.dua")


@dataclass
class PreferenciasDUA:
    modo_nocturno: bool = False
    filtro_luz_pct: int = 0  # 0 = sin filtro, 100 = maximo

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str | dict | None) -> "PreferenciasDUA":
        if not raw:
            return cls()
        if isinstance(raw, dict):
            data = raw
        else:
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                logger.warning("JSON de preferencias invalido, usando defaults")
                return cls()
        # Compatibilidad: si la BD tiene la version antigua con `filtro_luz` (bool)
        filtro_pct = data.get("filtro_luz_pct")
        if filtro_pct is None and "filtro_luz" in data:
            filtro_pct = 50 if data["filtro_luz"] else 0
        return cls(
            modo_nocturno=bool(data.get("modo_nocturno", False)),
            filtro_luz_pct=max(0, min(100, int(filtro_pct or 0))),
        )


# ---------------------------------------------------------------------------
# Persistencia en BD
# ---------------------------------------------------------------------------

def cargar_preferencias(conn, tabla: str, id_col: str, id_val: str) -> PreferenciasDUA:
    if tabla == "usuario":
        sql = f"SELECT preferencias_dua FROM usuario WHERE {id_col} = %s"
    else:
        sql = f"SELECT preferencias_dua FROM estudiante_pie WHERE {id_col} = %s"
    try:
        row = ejecutar_query_segura(conn, sql, (id_val,), fetch="one")
        if not row:
            return PreferenciasDUA()
        return PreferenciasDUA.from_json(row.get("preferencias_dua"))
    except Exception:
        logger.exception("Error cargando preferencias DUA")
        return PreferenciasDUA()


def guardar_preferencias(conn, tabla: str, id_col: str, id_val: str, prefs: PreferenciasDUA) -> None:
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
# CSS de modo nocturno (cubre todos los elementos de Streamlit)
# ---------------------------------------------------------------------------

DARK_CSS = """
<style>
/* === CONTENEDORES PRINCIPALES === */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stMain"],
.main, .block-container {
    background-color: #0E1117 !important;
    color: #FAFAFA !important;
}

/* === SIDEBAR === */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"] {
    background-color: #262730 !important;
    color: #FAFAFA !important;
}
[data-testid="stSidebar"] * {
    color: #FAFAFA !important;
}

/* === TEXTOS === */
h1, h2, h3, h4, h5, h6,
p, span, label, li, a, div,
.stMarkdown, [data-testid="stMarkdownContainer"],
.stText, .stTitle, .stHeader, .stSubheader,
.stCaption, small {
    color: #FAFAFA !important;
}

/* === INPUTS === */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-baseweb="input"],
[data-baseweb="textarea"] {
    background-color: #1C1E26 !important;
    color: #FAFAFA !important;
    border-color: #4A4A5E !important;
    caret-color: #FAFAFA !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label {
    color: #FAFAFA !important;
}

/* === BOTONES === */
.stButton > button,
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"] {
    background-color: #262730 !important;
    color: #FAFAFA !important;
    border: 1px solid #4A4A5E !important;
    box-shadow: none !important;
}
.stButton > button:hover,
[data-testid="baseButton-secondary"]:hover,
[data-testid="baseButton-primary"]:hover {
    background-color: #3A3A4E !important;
    border-color: #6A6A8E !important;
}

/* === TABS === */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background-color: #1C1E26 !important;
    color: #BABABA !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background-color: #0F2C59 !important;
    color: #FFFFFF !important;
}

/* === RADIO === */
[data-testid="stRadio"] label,
[data-testid="stRadio"] span {
    color: #FAFAFA !important;
}

/* === TOGGLE / SWITCH === */
[data-testid="stToggle"] label,
[data-testid="stToggle"] span {
    color: #FAFAFA !important;
}

/* === CHAT MESSAGES === */
[data-testid="stChatMessage"] {
    background-color: #1C1E26 !important;
    border: 1px solid #3A3A4E !important;
}
[data-testid="stChatMessage"] * {
    color: #FAFAFA !important;
}
[data-testid="stChatMessageAssistant"] {
    border-left: 6px solid #5A8DD6 !important;
}

/* === CHAT INPUT === */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] {
    background-color: #1C1E26 !important;
    color: #FAFAFA !important;
    border-color: #4A4A5E !important;
}

/* === DIVIDERS / HR === */
hr {
    border-color: #3A3A4E !important;
}

/* === ALERTS / INFO BOXES === */
[data-testid="stAlert"],
.stAlert {
    background-color: #1C1E26 !important;
    color: #FAFAFA !important;
    border-color: #4A4A5E !important;
}

/* === FORMS === */
[data-testid="stForm"] {
    background-color: #1C1E26 !important;
    border: 1px solid #3A3A4E !important;
    border-radius: 8px !important;
    padding: 16px !important;
}

/* === SELECTBOX / MULTISELECT === */
[data-baseweb="select"] > div,
[data-baseweb="popover"] {
    background-color: #1C1E26 !important;
    color: #FAFAFA !important;
    border-color: #4A4A5E !important;
}

/* === PERFIL CARD Y BADGES DE SESION === */
.perfil-card-estudiante {
    background-color: #1C1E26 !important;
    border-color: #3A3A4E !important;
    color: #FAFAFA !important;
}
.perfil-card-estudiante * {
    color: #FAFAFA !important;
}

/* === SLIDER === */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background-color: #5A8DD6 !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] > div > div {
    background-color: #5A8DD6 !important;
}

/* === HEADERS DE PANEL === */
.header-title-murialdo {
    color: #5A8DD6 !important;
}
.header-subtitle-murialdo {
    color: #BABABA !important;
}
</style>
"""


def aplicar_estilos(prefs: PreferenciasDUA) -> None:
    """Inyecta CSS segun las preferencias del usuario."""
    if prefs.modo_nocturno:
        st.markdown(DARK_CSS, unsafe_allow_html=True)
    if prefs.filtro_luz_pct > 0:
        sepia = prefs.filtro_luz_pct / 100.0
        # Combinamos sepia + leve cambio de tono para que se sienta calido sin perder legibilidad
        hue = -10 * sepia
        saturate = 1.0 - 0.2 * sepia
        st.markdown(
            f"""
            <style>
            .stApp {{
                filter: sepia({sepia:.2f}) hue-rotate({hue:.1f}deg) saturate({saturate:.2f}) !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# UI en el sidebar
# ---------------------------------------------------------------------------

def render_toggles(key_prefix: str = "dua") -> PreferenciasDUA:
    """Renderiza los controles DUA en el sidebar y devuelve el estado actual."""
    nocturno_key = f"{key_prefix}_nocturno"
    filtro_key = f"{key_prefix}_filtro_pct"

    if nocturno_key not in st.session_state:
        st.session_state[nocturno_key] = False
    if filtro_key not in st.session_state:
        st.session_state[filtro_key] = 0

    st.session_state[nocturno_key] = st.toggle(
        "🌙 Modo Nocturno",
        value=st.session_state[nocturno_key],
        key=f"{key_prefix}_tog_nocturno",
        help="Tema oscuro completo. Reduce la fatiga visual.",
    )

    st.session_state[filtro_key] = st.slider(
        "🔅 Filtro de Luz Nocturna",
        min_value=0,
        max_value=100,
        value=st.session_state[filtro_key],
        step=5,
        format="%d%%",
        key=f"{key_prefix}_sld_filtro",
        help="Intensidad del filtro cálido/antiazul. 0% = sin filtro, 100% = máximo.",
    )

    if st.session_state[filtro_key] > 0:
        st.caption(f"Filtro cálido activo: {st.session_state[filtro_key]}%")

    return PreferenciasDUA(
        modo_nocturno=st.session_state[nocturno_key],
        filtro_luz_pct=st.session_state[filtro_key],
    )
