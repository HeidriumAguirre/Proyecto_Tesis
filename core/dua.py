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
/* ================================================================
   PALETA MODO NOCTURNO - tonos calidos azul-grisaceos
   Inspirado en Material Design 3 dark + GitHub Dark Dimmed
   ================================================================
   --bg-app:        #0F1419  fondo principal (no negro puro)
   --bg-sidebar:    #1A1F29  sidebar (mas claro para jerarquia)
   --bg-elevated:   #232936  cards, formularios, mensajes chat
   --bg-input:      #1C2028  inputs y textareas
   --border-subtle: #2D3540  bordes sutiles
   --text-primary:  #E6E8EC  texto principal (off-white)
   --text-secondary:#A0A4AD  captions, labels secundarios
   --text-muted:    #6B7280  placeholders
   --accent:        #6B9DD9  azul Murialdo (mas calido)
   --accent-hover:  #8AB4E0
   --success:       #4ADE80
   --warning:       #FCD34D
   --error:         #F87171
*/

/* === CONTENEDORES PRINCIPALES === */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stMain"],
.main, .block-container {
    background-color: #0F1419 !important;
    color: #E6E8EC !important;
}

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #0F1419; }
::-webkit-scrollbar-thumb { background: #2D3540; border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: #3D4550; }

/* === SIDEBAR === */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"] {
    background-color: #1A1F29 !important;
    color: #E6E8EC !important;
}
[data-testid="stSidebar"] * {
    color: #E6E8EC !important;
}
[data-testid="stSidebar"] hr {
    border-color: #2D3540 !important;
}

/* === TEXTOS === */
h1, h2, h3, h4, h5, h6,
.stMarkdown, [data-testid="stMarkdownContainer"],
.stText, .stTitle, .stHeader, .stSubheader,
.stCaption, small {
    color: #E6E8EC !important;
}
p, span, label, li, a, div {
    color: #E6E8EC;
}
small, .stCaption, [data-testid="stCaptionContainer"] {
    color: #A0A4AD !important;
}

/* === INPUTS (texto, area, numero) === */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-baseweb="input"],
[data-baseweb="textarea"] {
    background-color: #1C2028 !important;
    color: #E6E8EC !important;
    border: 1px solid #2D3540 !important;
    border-radius: 6px !important;
    caret-color: #6B9DD9 !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-baseweb="input"]:focus,
[data-baseweb="textarea"]:focus {
    border-color: #6B9DD9 !important;
    box-shadow: 0 0 0 1px #6B9DD9 !important;
    outline: none !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #6B7280 !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label {
    color: #A0A4AD !important;
    font-weight: 500 !important;
}

/* === BOTONES === */
.stButton > button,
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"] {
    background-color: #232936 !important;
    color: #E6E8EC !important;
    border: 1px solid #2D3540 !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}
.stButton > button:hover,
[data-testid="baseButton-secondary"]:hover,
[data-testid="baseButton-primary"]:hover {
    background-color: #2D3540 !important;
    border-color: #6B9DD9 !important;
    color: #FFFFFF !important;
}
.stButton > button:active {
    background-color: #232936 !important;
    transform: translateY(1px);
}
.stButton > button:focus {
    border-color: #6B9DD9 !important;
    box-shadow: 0 0 0 1px #6B9DD9 !important;
}
[data-testid="baseButton-primary"] {
    background-color: #6B9DD9 !important;
    color: #0F1419 !important;
    border-color: #6B9DD9 !important;
    font-weight: 600 !important;
}
[data-testid="baseButton-primary"]:hover {
    background-color: #8AB4E0 !important;
    border-color: #8AB4E0 !important;
    color: #0F1419 !important;
}

/* === TABS === */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    gap: 4px;
    border-bottom: 1px solid #2D3540;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #A0A4AD !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 10px 20px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: #1C2028 !important;
    color: #E6E8EC !important;
}
.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    color: #6B9DD9 !important;
    border-bottom: 2px solid #6B9DD9 !important;
    font-weight: 600 !important;
}

/* === RADIO (subdivision A/B) === */
[data-testid="stRadio"] label,
[data-testid="stRadio"] span {
    color: #E6E8EC !important;
}
[data-testid="stRadio"] [role="radiogroup"] {
    gap: 12px;
}

/* === TOGGLE / SWITCH === */
[data-testid="stToggle"] label,
[data-testid="stToggle"] span {
    color: #E6E8EC !important;
    font-weight: 500 !important;
}

/* === CHAT MESSAGES === */
[data-testid="stChatMessage"] {
    background-color: #232936 !important;
    border: 1px solid #2D3540 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
}
[data-testid="stChatMessage"] * {
    color: #E6E8EC !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    background-color: #1C2433 !important;
    border-left: 4px solid #6B9DD9 !important;
}
[data-testid="stChatMessageAssistant"] {
    background-color: #232936 !important;
    border-left: 4px solid #8AB4E0 !important;
}

/* === CHAT INPUT (caja inferior del chat) === */
[data-testid="stChatInput"] {
    background-color: transparent !important;
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] [data-baseweb="textarea"] {
    background-color: #1C2028 !important;
    color: #E6E8EC !important;
    border: 1px solid #2D3540 !important;
    border-radius: 12px !important;
    caret-color: #6B9DD9 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #6B7280 !important;
}
[data-testid="stChatInput"] button {
    background-color: #6B9DD9 !important;
    color: #0F1419 !important;
    border: none !important;
    border-radius: 8px !important;
}
[data-testid="stChatInput"] button:hover {
    background-color: #8AB4E0 !important;
}

/* === DIVIDERS / HR === */
hr {
    border-color: #2D3540 !important;
    margin: 1.5rem 0 !important;
}

/* === ALERTS / INFO BOXES === */
[data-testid="stAlert"],
.stAlert {
    background-color: #1C2028 !important;
    color: #E6E8EC !important;
    border: 1px solid #2D3540 !important;
    border-radius: 8px !important;
    border-left-width: 4px !important;
}
[data-testid="stAlert"] svg {
    color: #6B9DD9 !important;
}

/* === FORMS === */
[data-testid="stForm"] {
    background-color: #232936 !important;
    border: 1px solid #2D3540 !important;
    border-radius: 10px !important;
    padding: 20px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
}

/* === SELECTBOX / MULTISELECT === */
[data-baseweb="select"] > div,
[data-baseweb="popover"],
[data-baseweb="menu"] {
    background-color: #232936 !important;
    color: #E6E8EC !important;
    border-color: #2D3540 !important;
}
[data-baseweb="select"]:hover > div {
    border-color: #6B9DD9 !important;
}

/* === PERFIL CARD === */
.perfil-card-estudiante {
    background-color: #232936 !important;
    border: 1px solid #2D3540 !important;
    border-top: 4px solid #6B9DD9 !important;
    color: #E6E8EC !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
}
.perfil-card-estudiante * {
    color: #E6E8EC !important;
}
.perfil-card-estudiante b {
    color: #8AB4E0 !important;
}

/* === TRANSCRIPCION BOX (audio) === */
.transcripcion-box {
    background-color: #1C2433 !important;
    border-left: 3px solid #8AB4E0 !important;
    color: #A0A4AD !important;
}

/* === SLIDER === */
[data-testid="stSlider"] [data-baseweb="slider"] > div > div {
    background-color: #2D3540 !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background-color: #6B9DD9 !important;
    box-shadow: 0 0 0 4px rgba(107,157,217,0.2) !important;
}

/* === HEADERS DE PANEL === */
.header-title-murialdo {
    color: #6B9DD9 !important;
    letter-spacing: -0.5px !important;
}
.header-subtitle-murialdo {
    color: #A0A4AD !important;
}

/* === DATAFRAME / TABLES === */
[data-testid="stDataFrame"] {
    background-color: #232936 !important;
    border: 1px solid #2D3540 !important;
    border-radius: 8px !important;
}

/* === MICROPHONE BUTTON (streamlit-mic-recorder) === */
iframe[title*="streamlit_mic_recorder"] {
    background-color: transparent !important;
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
